"""Vercel serverless entry point. Vercel Cron calls GET /api/morning daily
(see vercel.json) with "Authorization: Bearer $CRON_SECRET"."""

import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import morning_brief


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        secret = os.environ.get("CRON_SECRET")
        if not secret or self.headers.get("Authorization") != f"Bearer {secret}":
            self._reply(401, "Unauthorized\n")
            return
        title, body, ok = morning_brief.run()
        self._reply(200 if ok else 502, f"{title}\n\n{body}\n")

    def _reply(self, status: int, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
