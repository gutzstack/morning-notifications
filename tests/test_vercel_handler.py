import datetime as dt
import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import morning

BRIEF = {
    "date": dt.date(2026, 10, 26), "title": "Title", "body": "Body", "ok": True,
    "facts": {"nature": "Nature <fact>", "medicine": "Med fact",
              "economics": "Econ fact", "question": "What's up?"},
    "us": {"title": "US story", "summary": "Summary", "link": "https://www.npr.org/x"},
    "world": None,
}

BROWSER = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}


def call(headers, path="/api/morning", method="GET"):
    h = morning.handler.__new__(morning.handler)
    h.headers = headers
    h.path = path
    h.wfile = io.BytesIO()
    h.request_version = "HTTP/1.1"
    h.requestline = f"{method} /api/morning HTTP/1.1"
    h.command = method
    h.client_address = ("test", 0)
    h.log_message = lambda *a: None
    getattr(h, f"do_{method}")()
    return h.wfile.getvalue().decode()


def patch_run(**kw):
    return mock.patch.object(morning.morning_brief, "run", return_value=dict(BRIEF), **kw)


class HandlerTest(unittest.TestCase):
    def test_rejects_missing_or_wrong_secret(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"}), \
             mock.patch.object(morning.morning_brief, "run") as run:
            self.assertIn(" 401 ", call({}))
            self.assertIn(" 401 ", call({"Authorization": "Bearer nope"}))
            self.assertIn(" 401 ", call(BROWSER, method="POST"))
            run.assert_not_called()

    def test_runs_brief_with_correct_secret(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"}), patch_run() as run:
            out = call({"Authorization": "Bearer s3cret"})
        self.assertIn(" 200 ", out)
        self.assertIn("Body", out)
        run.assert_called_once_with()

    def test_accepts_secret_as_query_param(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"}), patch_run() as run:
            self.assertIn(" 401 ", call({}, "/api/morning?key=nope"))
            self.assertIn(" 200 ", call({}, "/api/morning?key=s3cret"))
            run.assert_called_once()

    def test_no_cron_secret_runs_without_auth(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": ""}), patch_run():
            out = call({})
        self.assertIn(" 200 ", out)
        self.assertIn("Body", out)


class PageTest(unittest.TestCase):
    def test_browser_get_shows_page_without_sending(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": ""}), patch_run() as run:
            out = call(BROWSER)
        run.assert_called_once_with(deliver=False)
        self.assertIn("text/html", out)
        self.assertIn("Monday, October 26", out)
        self.assertIn("Nature &lt;fact&gt;", out)  # content is escaped
        self.assertIn('href="https://www.npr.org/x"', out)
        self.assertIn("No story available today", out)
        self.assertNotIn("Sent to your phone", out)

    def test_browser_post_sends_and_confirms(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": ""}), patch_run() as run:
            out = call(BROWSER, method="POST")
        run.assert_called_once_with()
        self.assertIn("Sent to your phone", out)

    def test_post_reports_failed_delivery(self):
        failed = dict(BRIEF, ok=False)
        with mock.patch.dict(os.environ, {"CRON_SECRET": ""}), \
             mock.patch.object(morning.morning_brief, "run", return_value=failed):
            out = call(BROWSER, method="POST")
        self.assertIn("Couldn't send it", out)


if __name__ == "__main__":
    unittest.main()
