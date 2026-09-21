"""Native developer smoke test. Opens one temporary window and closes it automatically."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=Path('.desktop-work/native-result.json'))
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
    from app_factory import create_app
    from desktop.server import LocalServer
    from desktop.runtime import app_config, instance_lock
    import webview

    result = {'loaded': False, 'server_stopped': False}
    try:
        with tempfile.TemporaryDirectory(prefix='crm-native-smoke-') as directory:
            data = Path(directory)
            with instance_lock(data):
                server = LocalServer(create_app(app_config(data)))
                watchdog = None
                try:
                    server.start()
                    webview.settings['ALLOW_DOWNLOADS'] = True
                    webview.settings['ALLOW_FILE_URLS'] = False
                    window = webview.create_window('CRM Desktop – integration test', server.start_url, width=1280, height=850)
                    def loaded():
                        try:
                            result.update(window.evaluate_js('({title:document.title, path:location.pathname, fields:document.querySelectorAll("form input").length, cssLoaded:!!document.styleSheets[0]})'))
                            result['loaded'] = True
                        except Exception as exc:
                            result['error'] = str(exc)
                        finally:
                            window.destroy()
                    window.events.loaded += loaded
                    watchdog = threading.Timer(30, window.destroy)
                    watchdog.daemon = True
                    watchdog.start()
                    webview.start(gui='edgechromium' if sys.platform == 'win32' else None, private_mode=True, debug=False)
                finally:
                    if watchdog:
                        watchdog.cancel()
                    server.close()
                result['server_stopped'] = not server.thread.is_alive()
    except Exception as exc:
        result['error'] = str(exc)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    passed = result['loaded'] and result.get('path') == '/setup' and result.get('fields') == 6 and result.get('cssLoaded') and result['server_stopped']
    print('Native smoke:', 'OK' if passed else 'FAILED', '|', args.report)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
