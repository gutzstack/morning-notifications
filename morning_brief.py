"""Morning brief: three fun facts (nature, medicine, economics), a question of
the day to ask strangers, one US news snippet and one global news snippet.

Delivery is configured with environment variables (any combination):
  NTFY_TOPIC         push notification via https://ntfy.sh (free, no account)
  SMTP_HOST/...      email (see README)
Output is always printed to stdout as well.

Facts and the question come from Claude when ANTHROPIC_API_KEY is set,
otherwise from the built-in banks in fallback_content.py.
"""

import datetime as dt
import html
import json
import os
import re
import smtplib
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.message import EmailMessage

import fallback_content

US_FEED = os.environ.get("US_NEWS_FEED", "https://feeds.npr.org/1003/rss.xml")
WORLD_FEED = os.environ.get("WORLD_NEWS_FEED", "https://feeds.bbci.co.uk/news/world/rss.xml")
USER_AGENT = "morning-notifications/1.0"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

FACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "nature": {"type": "string"},
        "medicine": {"type": "string"},
        "economics": {"type": "string"},
        "question": {"type": "string"},
    },
    "required": ["nature", "medicine", "economics", "question"],
    "additionalProperties": False,
}


# ---------- facts & question ----------

def fallback_facts(today: dt.date) -> dict:
    day = today.timetuple().tm_yday
    pick = lambda bank: bank[day % len(bank)]
    return {
        "nature": pick(fallback_content.NATURE),
        "medicine": pick(fallback_content.MEDICINE),
        "economics": pick(fallback_content.ECONOMICS),
        "question": pick(fallback_content.QUESTIONS),
    }


def claude_facts(today: dt.date) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    prompt = (
        f"Today is {today:%A, %B %d, %Y}. Write a morning brief for one curious reader:\n"
        "- one surprising, accurate fun fact about nature\n"
        "- one about medicine or the human body\n"
        "- one about economics\n"
        "- one light, friendly 'question of the day' they could ask a stranger "
        "to start a conversation (not too personal).\n"
        "Each fact is one or two sentences, well-established (no shaky claims), "
        "and not one of the most overused trivia facts. Vary topics day to day."
    )
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=2000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": FACTS_SCHEMA},
        },
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"Claude stopped with {response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def get_facts(today: dt.date) -> dict:
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return claude_facts(today)
        except Exception as e:  # never skip the morning brief over an API hiccup
            print(f"Claude unavailable ({e!r}); using built-in facts.", file=sys.stderr)
    return fallback_facts(today)


# ---------- news ----------

def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def top_story(feed_xml: bytes) -> dict | None:
    """Return the first item of an RSS feed as {title, summary, link}."""
    item = ET.fromstring(feed_xml).find("./channel/item")
    if item is None:
        return None
    summary = clean(item.findtext("description"))
    if len(summary) > 280:
        summary = summary[:277].rsplit(" ", 1)[0] + "..."
    return {
        "title": clean(item.findtext("title")),
        "summary": summary,
        "link": (item.findtext("link") or "").strip(),
    }


def fetch_story(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return top_story(resp.read())
    except Exception as e:
        print(f"Could not fetch {url}: {e!r}", file=sys.stderr)
        return None


# ---------- formatting & delivery ----------

def format_story(story: dict | None) -> str:
    if not story:
        return "(unavailable today)"
    lines = [story["title"]]
    if story["summary"] and story["summary"] != story["title"]:
        lines.append(story["summary"])
    if story["link"]:
        lines.append(story["link"])
    return "\n".join(lines)


def build_brief(facts: dict, us: dict | None, world: dict | None) -> str:
    return "\n".join([
        "🌿 Nature: " + facts["nature"],
        "🩺 Medicine: " + facts["medicine"],
        "💰 Economics: " + facts["economics"],
        "",
        "💬 Question of the day: " + facts["question"],
        "",
        "🇺🇸 US news: " + format_story(us),
        "",
        "🌍 World news: " + format_story(world),
    ])


def send_ntfy(topic: str, title: str, body: str) -> None:
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    req = urllib.request.Request(
        f"{server}/{topic}",
        data=body.encode("utf-8"),
        # Header values must be latin-1, so the title stays plain ASCII.
        headers={"Title": title, "Tags": "sunrise", "User-Agent": USER_AGENT},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=20).close()


def send_email(title: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"] = os.environ.get("EMAIL_FROM") or os.environ["SMTP_USER"]
    msg["To"] = os.environ["EMAIL_TO"]
    msg.set_content(body)
    port = int(os.environ.get("SMTP_PORT", "465"))
    host = os.environ["SMTP_HOST"]
    smtp = smtplib.SMTP_SSL(host, port) if port == 465 else smtplib.SMTP(host, port)
    with smtp:
        if port != 465:
            smtp.starttls()
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(msg)


def run(deliver: bool = True) -> dict:
    """Build today's brief and, if deliver is set, send it. Returns a dict with
    date, title, body, facts, us, world, and ok (False if any delivery failed)."""
    today = dt.date.today()
    title = f"Good morning! Your brief for {today:%a %b} {today.day}"
    facts, us, world = get_facts(today), fetch_story(US_FEED), fetch_story(WORLD_FEED)
    body = build_brief(facts, us, world)
    brief = {"date": today, "title": title, "body": body,
             "facts": facts, "us": us, "world": world, "ok": True}
    print(title, body, sep="\n\n")
    if not deliver:
        return brief

    if topic := os.environ.get("NTFY_TOPIC"):
        try:
            send_ntfy(topic, title, body)
        except Exception as e:
            print(f"ntfy delivery failed: {e!r}", file=sys.stderr)
            brief["ok"] = False
    if os.environ.get("SMTP_HOST") and os.environ.get("EMAIL_TO"):
        try:
            send_email(title, body)
        except Exception as e:
            print(f"Email delivery failed: {e!r}", file=sys.stderr)
            brief["ok"] = False
    return brief


def main() -> int:
    return 0 if run()["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
