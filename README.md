# Fortnite Update Bot

A Discord bot that monitors Fortnite for game updates (version bumps) and notifies your server when a new downloadable update is available.

## How It Works

On a schedule (every 6 hours via **GitHub Actions**), a small script polls the [Fortnite API](https://fortnite-api.com) for the current game build. When the version string changes, it posts an embed to your Discord channel using Discord's REST API, then exits. The last-seen version is stored in `version_data.json`, which the workflow commits back to the repo after each run so it remembers state between runs.

No always-on server is required, so it runs **for free** — no Railway, no credit card.

## Project Structure

```
fortnite-update-bot/
├── check_update.py                    # Scheduled single-shot check (used by GitHub Actions)
├── bot.py                             # Legacy always-on gateway bot (optional, for Railway/local)
├── .github/workflows/fortnite-check.yml  # Cron schedule that runs the check
├── version_data.json                  # Last-seen version (state, committed by the workflow)
├── requirements.txt                   # Python dependencies
├── .env.example                       # Example environment variables (local testing)
└── README.md                          # This file
```

---

## Step-by-Step Setup (GitHub Actions — free, recommended)

### 1. Create a Discord Application & Bot

1. Go to https://discord.com/developers/applications
2. Click **New Application** -> give it a name (e.g. "Fortnite Updates")
3. Go to the **Bot** tab -> click **Reset Token** -> copy the token
4. Go to **OAuth2 > URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `View Channels`
   - Open the generated URL in your browser and invite the bot to your server

> The bot only sends messages, so no privileged gateway intents are required.

### 2. Get Your Discord Channel ID

1. Open Discord -> **User Settings > Advanced > Developer Mode** (toggle ON)
2. Right-click the channel you want notifications in -> **Copy Channel ID**

### 3. Add your secrets to GitHub

In your repo on GitHub: **Settings > Secrets and variables > Actions > New repository secret**. Add two:

- `DISCORD_TOKEN` = your bot token
- `CHANNEL_ID` = your channel ID

### 4. Push the code

```powershell
git add .
git commit -m "Move to scheduled GitHub Actions check"
git push
```

The workflow is scheduled to run every 6 hours automatically. You can also trigger it manually to test: **Actions** tab -> **Fortnite Update Check** -> **Run workflow**.

### 5. Verify It's Working

Open the **Actions** tab and watch a run. The logs show the fetched version and whether an update was detected. A Discord message is only sent when the version actually changes (so a normal run with no update is silent). To force a test, edit `version_data.json` to an older version, commit, and run the workflow manually — it will detect the "new" version and post.

### Changing the schedule

Edit the `cron` line in `.github/workflows/fortnite-check.yml`. Cron uses **UTC**. Examples:

- `0 0 * * *` — once a day at 00:00 UTC
- `0 */6 * * *` — every 6 hours (default)
- `0 */3 * * *` — every 3 hours

> GitHub's scheduled workflows can be delayed by a few minutes (or occasionally skipped) during peak load — fine for update checks, but not second-precise.

### Test Locally (optional)

```powershell
pip install -r requirements.txt
$env:DISCORD_TOKEN="your_bot_token"
$env:CHANNEL_ID="your_channel_id"
python check_update.py
```

## Environment Variables

| Variable        | Required | Description                          |
|-----------------|----------|--------------------------------------|
| `DISCORD_TOKEN` | Yes      | Discord bot token                    |
| `CHANNEL_ID`    | Yes      | Discord channel ID for notifications |

## Notes

- The check only reports **game version updates** (new builds), not item shop rotations.
- It uses the free public API at https://fortnite-api.com — no API key needed.
- If Fortnite-API is down, the run logs a warning and simply exits; the next scheduled run tries again.
- `bot.py` (the old always-on gateway bot) is kept for reference / local use but is no longer needed for hosting.
