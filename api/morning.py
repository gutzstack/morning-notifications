"""Vercel serverless entry point.

Vercel Cron calls GET /api/morning daily (see vercel.json), which builds the
brief and sends it. A browser opening the page (or the site root) sees the brief
as a web page without sending anything; its "Send to my phone" button POSTs here
to send it.

If CRON_SECRET is set, every request must carry it, either as
"Authorization: Bearer $CRON_SECRET" (Vercel Cron does this) or as ?key=<CRON_SECRET>.
If it is not set, the endpoint is open: anyone with the URL can send a brief."""

import hmac
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import morning_brief
import page


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self._check_auth():
            return
        if self._wants_html():
            self._reply(200, page.render(morning_brief.run(deliver=False)), "text/html")
            return
        brief = morning_brief.run()
        self._reply(200 if brief["ok"] else 502, f"{brief['title']}\n\n{brief['body']}\n")

    def do_POST(self):
        if not self._check_auth():
            return
        brief = morning_brief.run()
        if self._wants_html():
            self._reply(200, page.render(brief, sent=brief["ok"]), "text/html")
        else:
            self._reply(200 if brief["ok"] else 502, f"{brief['title']}\n\n{brief['body']}\n")

    def _check_auth(self) -> bool:
        secret = os.environ.get("CRON_SECRET")
        if secret and not self._authorized(secret):
            self._reply(401, "Unauthorized. Open this page as /api/morning?key=<your CRON_SECRET>\n")
            return False
        return True

    def _authorized(self, secret: str) -> bool:
        header = self.headers.get("Authorization") or ""
        key = parse_qs(urlsplit(self.path or "").query).get("key", [""])[0]
        return (hmac.compare_digest(header, f"Bearer {secret}")
                or hmac.compare_digest(key, secret))

    def _wants_html(self) -> bool:
        return "text/html" in (self.headers.get("Accept") or "")

    def _reply(self, status: int, text: str, content_type: str = "text/plain") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
