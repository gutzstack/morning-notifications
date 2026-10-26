"""Vercel serverless entry point. Vercel Cron calls GET /api/morning daily
(see vercel.json) with "Authorization: Bearer $CRON_SECRET". For testing from
a browser, the secret can also be passed as /api/morning?key=<CRON_SECRET>."""

import hmac
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import morning_brief


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        secret = os.environ.get("CRON_SECRET")
        if not secret:
            self._reply(500, "CRON_SECRET is not set. Add it in Vercel → Settings → "
                             "Environment Variables, then redeploy.\n")
            return
        if not self._authorized(secret):
            self._reply(401, "Unauthorized. To send a brief from a browser, open "
                             "/api/morning?key=<your CRON_SECRET>\n")
            return
        title, body, ok = morning_brief.run()
        self._reply(200 if ok else 502, f"{title}\n\n{body}\n")

    def _authorized(self, secret: str) -> bool:
        header = self.headers.get("Authorization") or ""
        key = parse_qs(urlsplit(self.path or "").query).get("key", [""])[0]
        return (hmac.compare_digest(header, f"Bearer {secret}")
                or hmac.compare_digest(key, secret))

    def _reply(self, status: int, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
