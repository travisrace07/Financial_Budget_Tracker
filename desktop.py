"""Desktop entry point. Financial data lives outside the application bundle."""
import argparse
import hmac
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import secrets
import sys
import tempfile
import threading
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler

from flask import jsonify, redirect, request
from platformdirs import user_data_path
from sqlalchemy.engine import URL
from werkzeug.serving import make_server, WSGIRequestHandler

from app import create_app


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        # Do not log the launch credential or financial request URLs.
        pass


class DesktopServer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        url = URL.create('sqlite', database=str(self.data_dir / 'ledger.sqlite3'))
        self.app = create_app(url)
        self.token = secrets.token_urlsafe(32)
        self.cookie = 'ledger_' + secrets.token_hex(8)
        self.server = make_server('127.0.0.1', 0, self.app, threaded=True,
                                  request_handler=QuietHandler)
        self.host = f'127.0.0.1:{self.server.server_port}'
        self.base_url = f'http://{self.host}'
        self.launch_url = f'{self.base_url}/desktop-launch/{self.token}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

        @self.app.before_request
        def desktop_access():
            if request.host != self.host:
                return jsonify(error='Invalid desktop host'), 403
            if request.endpoint == 'desktop_launch':
                return None
            if not hmac.compare_digest(request.cookies.get(self.cookie, ''), self.token):
                return jsonify(error='Open Ledger from its application icon.'), 403

        @self.app.get('/desktop-launch/<token>')
        def desktop_launch(token):
            if not hmac.compare_digest(token, self.token):
                return jsonify(error='Invalid launch credential'), 403
            response = redirect('/')
            response.set_cookie(self.cookie, self.token, httponly=True, samesite='Strict')
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'no-referrer'
            return response

    def start(self):
        self.thread.start()
        return self

    def close(self):
        if self.thread.is_alive():
            self.server.shutdown()
            self.thread.join(timeout=5)
        self.server.server_close()
        self.app.config['DB_SESSION'].kw['bind'].dispose()


def smoke_test():
    """Exercise the packaged backend and assets without using real user data."""
    with tempfile.TemporaryDirectory(prefix='ledger-smoke-') as directory:
        server = DesktopServer(directory).start()
        try:
            client = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
            with client.open(server.launch_url, timeout=10) as response:
                assert b'Financial overview' in response.read()
            for path in ('/static/app.js', '/static/style.css', '/static/sample.csv'):
                with client.open(server.base_url + path, timeout=10) as response:
                    assert response.status == 200 and response.read()
            with client.open(server.base_url + '/api/dashboard', timeout=10) as response:
                assert json.load(response)['total_records'] == 0
        finally:
            server.close()
    print('Desktop bundle smoke test passed.')


def main():
    parser = argparse.ArgumentParser(description='Ledger desktop')
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    if args.smoke_test:
        smoke_test()
        return

    data_dir = user_data_path('Ledger', appauthor=False)
    data_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(data_dir / 'desktop.log', maxBytes=1_000_000, backupCount=2)
    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    server = None
    try:
        import webview
        server = DesktopServer(data_dir).start()
        webview.settings['ALLOW_DOWNLOADS'] = True
        webview.settings['ALLOW_FILE_URLS'] = False
        webview.create_window('Ledger', server.launch_url, width=1280, height=850,
                              min_size=(760, 600), text_select=True)
        webview.start(gui='edgechromium' if sys.platform == 'win32' else None,
                      private_mode=True)
    except Exception:
        logging.exception('Ledger could not start')
        # A windowed executable has no console, so show a useful error dialog.
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Ledger could not start',
            f'Please see the startup log at:\n{data_dir / "desktop.log"}\n\n'
            'On Windows, make sure Microsoft Edge WebView2 Runtime is installed.')
        root.destroy()
        raise
    finally:
        if server is not None:
            server.close()


if __name__ == '__main__':
    main()
