#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import yt_dlp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cli.main_cli import Downloader


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        sys.stderr.write('[web_server] %s - %s\n' % (self.address_string(), format % args))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/health':
            self._send_json(200, {'status': 'ok', 'service': 'mp3-mp4-downloader'})
            return
        if parsed.path == '/':
            self._send_json(200, {'endpoints': ['GET /health', 'POST /download']})
            return
        self._send_json(404, {'error': 'not found'})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/download':
            self._send_json(404, {'error': 'not found'})
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length) if length else b'{}'
            data = json.loads(raw.decode('utf-8'))
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {'error': 'invalid JSON body: %s' % e})
            return

        url = data.get('url', '')
        fmt = data.get('format', 'mp4')
        path = data.get('path') or os.path.join(os.getcwd(), 'descargas')

        if not url:
            self._send_json(400, {'error': 'missing "url" in body'})
            return
        if fmt not in ('mp3', 'mp4'):
            self._send_json(400, {'error': 'format must be "mp3" or "mp4"'})
            return

        ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'binaries', 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_path):
            ffmpeg_path = 'ffmpeg'

        os.makedirs(path, exist_ok=True)

        downloader = Downloader(url=url, format=fmt, path=path, ffmpeg_path=ffmpeg_path)
        try:
            options = downloader._build_options()
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                ydl.download([url])
            self._send_json(200, {'status': 'ok', 'title': title, 'format': fmt, 'path': path})
        except Exception as e:
            self._send_json(500, {'status': 'error', 'error': str(e)})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print('TestSprite wrapper listening on http://127.0.0.1:%d' % port, flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
