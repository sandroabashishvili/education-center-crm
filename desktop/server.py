"""An ephemeral loopback Waitress server with per-launch browser access."""
import secrets
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

from flask import abort, redirect, request, make_response, url_for
from waitress import create_server, wasyncore


class LocalServer:
    def __init__(self, app):
        self.token = secrets.token_urlsafe(32)
        self.server = create_server(app, host='127.0.0.1', port=0, threads=4, map={}, asyncore_loop_timeout=0.1)
        self.base_url = f'http://127.0.0.1:{self.server.effective_port}'
        self.thread = threading.Thread(target=self.server.run, name='crm-http', daemon=True)
        # Run before app setup/auth guards; importing the app alone does not expose it.
        def access_guard():
            if request.host != self.base_url.removeprefix('http://'):
                abort(403)
            origin = request.headers.get('Origin')
            if origin and origin != self.base_url:
                abort(403)
            if request.path == '/_desktop/start' and request.method == 'GET':
                if not secrets.compare_digest(request.args.get('token', ''), self.token):
                    abort(403)
                response = make_response(redirect(url_for('index')))
                response.set_cookie('crm_desktop_access', self.token, httponly=True, samesite='Strict')
                response.headers['Referrer-Policy'] = 'no-referrer'
                response.headers['Cache-Control'] = 'no-store'
                return response
            if not secrets.compare_digest(request.cookies.get('crm_desktop_access', ''), self.token):
                abort(403)
        app.before_request_funcs.setdefault(None, []).insert(0, access_guard)

    @property
    def start_url(self):
        return f'{self.base_url}/_desktop/start?token={self.token}'

    def start(self, timeout=10):
        self.thread.start()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                req = Request(self.base_url + '/health', headers={'Cookie': 'crm_desktop_access=' + self.token})
                with urlopen(req, timeout=.5) as response:
                    if response.status == 200:
                        return
            except (OSError, URLError):
                if not self.thread.is_alive():
                    break
            time.sleep(.05)
        self.close()
        raise RuntimeError('Der lokale Dienst konnte nicht gestartet werden.')

    def close(self):
        # Finish in-flight requests before closing their wake-up sockets.
        self.server.task_dispatcher.shutdown(timeout=5)
        self.server.close()
        wasyncore.close_all(map=self.server._map)
        if self.thread.is_alive():
            self.thread.join(timeout=5)
