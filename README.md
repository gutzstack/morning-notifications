# Morning Notifications

A daily morning brief, pushed to your phone:

- 🌿 a fun fact about **nature**
- 🩺 a fun fact about **medicine**
- 💰 a fun fact about **economics**
- 💬 a **question of the day** to ask strangers
- 🇺🇸 one **US news** snippet (NPR top story)
- 🌍 one **global news** snippet (BBC World top story)

It runs every morning on GitHub Actions, so you don't need a server.

## Setup (about 5 minutes)

1. **Get the notifications on your phone.** Install the free [ntfy](https://ntfy.sh) app
   (iOS/Android). Subscribe to a topic with a hard-to-guess name, such as
   `elijah-morning-7f3k2q`. Anyone who knows the name can read the topic.
2. **Add repo secrets** (Settings → Secrets and variables → Actions):
   | Secret | Required | Purpose |
   |---|---|---|
   | `NTFY_TOPIC` | yes* | the topic name from step 1 |
   | `ANTHROPIC_API_KEY` | optional | fresh facts and questions written by Claude every day. Without it, the app rotates through the built-in lists in `fallback_content.py`. |
   | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO` | optional | also sends the brief by email (for Gmail: `smtp.gmail.com`, `465`, and an [app password](https://myaccount.google.com/apppasswords)) |

   \*You need ntfy or email, or both.
3. **Test it:** go to Actions → *Morning brief* → *Run workflow*.

## Schedule

The workflow is set in `.github/workflows/morning-brief.yml` to run at 11:47 UTC. That's
6:47am Eastern in winter and 7:47am in summer. GitHub cron uses UTC, so change the
time to suit your time zone. Scheduled runs can be a few minutes late.

## Run locally

```bash
pip install -r requirements.txt
NTFY_TOPIC=your-topic python morning_brief.py   # leave NTFY_TOPIC unset to only print it
python -m unittest discover -s tests
```

Optional overrides: `US_NEWS_FEED`, `WORLD_NEWS_FEED` (any RSS URL), `CLAUDE_MODEL`, `NTFY_SERVER`.
