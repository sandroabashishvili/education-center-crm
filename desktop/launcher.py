"""Run via python -m desktop; packaging supplies the no-console executable."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from .runtime import app_config, default_data_dir, instance_lock


def run(data_dir):
    # Keep existing Flask module names until the web package is migrated separately.
    app_dir = Path(__file__).resolve().parents[1] / 'app'
    sys.path.insert(0, str(app_dir))
    from app_factory import create_app
    from .server import LocalServer
    import webview

    with instance_lock(data_dir):
        config = app_config(data_dir)
        handler = RotatingFileHandler(data_dir / 'logs/desktop.log', maxBytes=1_000_000, backupCount=3, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger = logging.getLogger('crm.desktop')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        server = None
        try:
            app = create_app(config)
            server = LocalServer(app)
            server.start()
            webview.settings['ALLOW_DOWNLOADS'] = True
            webview.settings['ALLOW_FILE_URLS'] = False
            webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True
            webview.create_window('Education Center CRM', server.start_url, width=1280, height=850, min_size=(800, 600), text_select=True)
            logger.info('Desktop started; schema initialized; local server ready')
            webview.start(gui='edgechromium' if sys.platform == 'win32' else None, private_mode=True, debug=False)
        except Exception:
            logger.exception('Desktop startup failed')
            raise
        finally:
            if server:
                server.close()
            logger.info('Desktop stopped')
            handler.close()
            logger.removeHandler(handler)


def main():
    parser = argparse.ArgumentParser(description='Education Center CRM desktop')
    parser.add_argument('--smoke-test', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--data-dir', type=Path, default=default_data_dir(), help='Isolated data folder (testing/support)')
    args = parser.parse_args()
    try:
        if args.smoke_test:
            from tools.desktop_smoke import main as smoke
            sys.argv = [sys.argv[0]]
            return smoke()
        run(args.data_dir.expanduser().resolve())
    except Exception as exc:
        # A native dialog also works when packaged without a console.
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(exc), 'Education Center CRM', 0x10)
        else:
            print(str(exc), file=sys.stderr)
        return 1
    return 0
