import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import morning


def call(headers):
    h = morning.handler.__new__(morning.handler)
    h.headers = headers
    h.wfile = io.BytesIO()
    h.request_version = "HTTP/1.1"
    h.requestline = "GET /api/morning HTTP/1.1"
    h.command = "GET"
    h.client_address = ("test", 0)
    h.log_message = lambda *a: None
    h.do_GET()
    return h.wfile.getvalue().decode()


class HandlerTest(unittest.TestCase):
    def test_rejects_missing_or_wrong_secret(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"}), \
             mock.patch.object(morning.morning_brief, "run") as run:
            self.assertIn(" 401 ", call({}))
            self.assertIn(" 401 ", call({"Authorization": "Bearer nope"}))
            run.assert_not_called()

    def test_runs_brief_with_correct_secret(self):
        with mock.patch.dict(os.environ, {"CRON_SECRET": "s3cret"}), \
             mock.patch.object(morning.morning_brief, "run",
                               return_value=("Title", "Body", True)):
            out = call({"Authorization": "Bearer s3cret"})
        self.assertIn(" 200 ", out)
        self.assertIn("Body", out)


if __name__ == "__main__":
    unittest.main()
