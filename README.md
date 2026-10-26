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

## Hosting on Vercel (alternative to GitHub Actions)

`vercel.json` sets up a Vercel Cron job that calls `api/morning.py` once a day at 11:47 UTC.
To use it:

1. Import this repo into Vercel. No build settings are needed.
2. Under Project → Settings → Environment Variables, add the same values as the secrets above.
   Optionally add `CRON_SECRET`, set to any long random string. Vercel sends it with each cron
   request, and the endpoint then rejects any request that doesn't include it. Without it,
   anyone who knows your app's URL can trigger a brief.
3. Redeploy. Then turn off the GitHub Actions schedule, or you'll get two briefs every morning.

To trigger it manually, open `https://<your-app>.vercel.app/api/morning?key=<CRON_SECRET>` in a browser,
or run `curl -H "Authorization: Bearer $CRON_SECRET" https://<your-app>.vercel.app/api/morning`.
With `CRON_SECRET` set, opening `/api/morning` without the key shows "Unauthorized". That is
expected: it stops strangers from sending you briefs. Without `CRON_SECRET`, just open `/api/morning`.

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
