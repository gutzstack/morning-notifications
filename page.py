"""Renders the morning brief as a standalone HTML page for browsers."""

import datetime as dt
from html import escape
from urllib.parse import urlsplit

FACTS = [
    ("nature", "🌿", "Nature"),
    ("medicine", "🩺", "Medicine"),
    ("economics", "💰", "Economics"),
]

CSS = """
:root {
  --bg: #fbf6ef; --bg-glow: #ffe3c4; --card: #ffffff; --ink: #2b2118;
  --muted: #7a6a5c; --line: #f0e4d6; --accent: #e8743b; --accent-ink: #ffffff;
  --q-from: #ff9a5a; --q-to: #e2557a; --ok: #2f8f5b; --warn: #b4462f;
  --shadow: 0 1px 2px rgba(80,50,20,.06), 0 8px 24px rgba(80,50,20,.07);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #17120f; --bg-glow: #3a2216; --card: #221b16; --ink: #f4ebe2;
    --muted: #b3a394; --line: #33291f; --accent: #ff9a5a; --accent-ink: #1b120c;
    --q-from: #c8602f; --q-to: #a63b63; --ok: #6fd39b; --warn: #ff8a70;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.35);
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; color: var(--ink);
  background: radial-gradient(120% 60% at 50% -10%, var(--bg-glow), transparent 70%), var(--bg);
  background-color: var(--bg);
  font: 16px/1.6 "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  min-height: 100vh;
}
main { max-width: 760px; margin: 0 auto; padding: 56px 16px 64px; }
header { text-align: center; margin-bottom: 40px; }
.sun {
  width: 64px; height: 64px; margin: 0 auto 18px; border-radius: 50%;
  background: radial-gradient(circle at 50% 60%, #ffd27a, #ff9a5a 60%, #e8743b);
  box-shadow: 0 0 0 10px rgba(255,170,90,.18), 0 0 60px rgba(255,140,60,.45);
}
.eyebrow {
  margin: 0; font-size: 13px; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent);
}
h1 {
  margin: 6px 0 0; font: 600 clamp(32px, 7vw, 46px)/1.1 "Fraunces", Georgia, serif;
  letter-spacing: -.01em;
}
.sub { margin: 10px 0 0; color: var(--muted); }
h2 {
  margin: 40px 0 14px; font-size: 13px; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; color: var(--muted);
}
.question {
  position: relative; overflow: hidden; border-radius: 20px; padding: 28px 28px 30px;
  color: #fff; background: linear-gradient(135deg, var(--q-from), var(--q-to));
  box-shadow: var(--shadow);
}
.question::after {
  content: "\\201C"; position: absolute; right: 18px; top: -18px;
  font: 700 160px/1 "Fraunces", Georgia, serif; opacity: .18;
}
.question .label { margin: 0; font-size: 13px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; opacity: .85; }
.question p.q { position: relative; margin: 8px 0 0; font: 500 clamp(21px, 4.4vw, 26px)/1.35 "Fraunces", Georgia, serif; }
.grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 16px;
  padding: 20px; box-shadow: var(--shadow);
}
.fact .icon {
  display: inline-grid; place-items: center; width: 40px; height: 40px;
  border-radius: 12px; background: var(--bg); font-size: 20px;
}
.fact h3 { margin: 12px 0 4px; font-size: 15px; font-weight: 600; }
.fact p { margin: 0; color: var(--ink); font-size: 15px; }
.news { display: grid; gap: 14px; }
.story .region { margin: 0; font-size: 13px; font-weight: 600; color: var(--accent); }
.story h3 { margin: 6px 0 6px; font: 600 20px/1.3 "Fraunces", Georgia, serif; }
.story h3 a { color: inherit; text-decoration: none; }
.story h3 a:hover { text-decoration: underline; text-decoration-color: var(--accent); }
.story p { margin: 0; color: var(--muted); font-size: 15px; }
.story .src { display: inline-block; margin-top: 10px; font-size: 13px; color: var(--muted); }
.story.empty h3 { color: var(--muted); }
footer { margin-top: 44px; text-align: center; color: var(--muted); font-size: 14px; }
form { margin: 0 0 14px; }
button {
  appearance: none; border: 0; border-radius: 999px; padding: 13px 26px; cursor: pointer;
  font: 600 15px/1 "Inter", system-ui, sans-serif; color: var(--accent-ink); background: var(--accent);
  box-shadow: var(--shadow); transition: transform .1s ease, filter .15s ease;
}
button:hover { filter: brightness(1.06); }
button:active { transform: scale(.97); }
.status { margin: 0 0 14px; font-weight: 600; }
.status.ok { color: var(--ok); }
.status.fail { color: var(--warn); }
@media (max-width: 480px) {
  main { padding-top: 36px; }
  .question { padding: 22px 20px 24px; }
}
"""


def _story(region: str, story: dict | None) -> str:
    if not story:
        return (f'<article class="card story empty"><p class="region">{region}</p>'
                "<h3>No story available today</h3></article>")
    title = escape(story["title"])
    link = story.get("link") or ""
    host = urlsplit(link).hostname or ""
    if link.startswith(("https://", "http://")):
        title = f'<a href="{escape(link)}" target="_blank" rel="noopener">{title}</a>'
    summary = story.get("summary") or ""
    parts = [f'<article class="card story"><p class="region">{region}</p><h3>{title}</h3>']
    if summary and summary != story["title"]:
        parts.append(f"<p>{escape(summary)}</p>")
    if host:
        parts.append(f'<span class="src">{escape(host.removeprefix("www."))} ↗</span>')
    parts.append("</article>")
    return "".join(parts)


def render(brief: dict, sent: bool | None = None) -> str:
    """Return the full HTML page. sent is None when nothing was sent on this
    request, True if delivery succeeded, False if it failed."""
    date: dt.date = brief["date"]
    facts = brief["facts"]
    fact_cards = "".join(
        f'<article class="card fact"><span class="icon">{icon}</span>'
        f"<h3>{label}</h3><p>{escape(facts[key])}</p></article>"
        for key, icon, label in FACTS
    )
    if sent is None:
        status = ""
    elif sent:
        status = '<p class="status ok">✓ Sent to your phone</p>'
    else:
        status = '<p class="status fail">Couldn\'t send it. Check NTFY_TOPIC in Vercel.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Morning Brief</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌅</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<main>
  <header>
    <div class="sun" aria-hidden="true"></div>
    <p class="eyebrow">Good morning</p>
    <h1>{date:%A, %B} {date.day}</h1>
    <p class="sub">Three things to know, one thing to ask, and what's happening in the world.</p>
  </header>

  <section class="question" aria-label="Question of the day">
    <p class="label">💬 Question of the day</p>
    <p class="q">{escape(facts["question"])}</p>
  </section>

  <h2>Fun facts</h2>
  <section class="grid">{fact_cards}</section>

  <h2>The news</h2>
  <section class="news">
    {_story("🇺🇸 United States", brief["us"])}
    {_story("🌍 World", brief["world"])}
  </section>

  <footer>
    {status}
    <form method="post"><button type="submit">Send to my phone</button></form>
    <p>A new brief arrives every morning at 6:47am Eastern.</p>
  </footer>
</main>
</body>
</html>
"""
