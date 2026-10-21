import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fallback_content
import morning_brief

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Feed</title>
<item><title>Big &amp; important story</title>
<description><![CDATA[<p>Something <b>happened</b> today.</p>]]></description>
<link>https://example.com/story</link></item>
<item><title>Second story</title></item>
</channel></rss>"""


class TopStoryTest(unittest.TestCase):
    def test_parses_first_item_and_strips_html(self):
        story = morning_brief.top_story(RSS)
        self.assertEqual(story["title"], "Big & important story")
        self.assertEqual(story["summary"], "Something happened today.")
        self.assertEqual(story["link"], "https://example.com/story")

    def test_empty_feed(self):
        self.assertIsNone(morning_brief.top_story(b"<rss><channel></channel></rss>"))

    def test_long_summary_truncated(self):
        feed = RSS.replace(b"Something <b>happened</b> today.", b"word " * 200)
        self.assertLessEqual(len(morning_brief.top_story(feed)["summary"]), 280)


class FactsTest(unittest.TestCase):
    def test_fallback_rotates_daily(self):
        a = morning_brief.fallback_facts(dt.date(2026, 1, 1))
        b = morning_brief.fallback_facts(dt.date(2026, 1, 2))
        self.assertNotEqual(a["nature"], b["nature"])
        self.assertIn(a["question"], fallback_content.QUESTIONS)

    def test_no_api_key_uses_fallback(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            facts = morning_brief.get_facts(dt.date(2026, 3, 3))
        self.assertEqual(set(facts), {"nature", "medicine", "economics", "question"})


class BriefTest(unittest.TestCase):
    def test_brief_has_every_section(self):
        facts = morning_brief.fallback_facts(dt.date(2026, 5, 5))
        story = morning_brief.top_story(RSS)
        brief = morning_brief.build_brief(facts, story, None)
        for label in ("Nature", "Medicine", "Economics", "Question of the day",
                      "US news", "World news"):
            self.assertIn(label, brief)
        self.assertIn("Big & important story", brief)
        self.assertIn("(unavailable today)", brief)


if __name__ == "__main__":
    unittest.main()
