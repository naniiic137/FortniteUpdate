# Game Update Bot

A Discord bot that monitors **Fortnite**, **VALORANT**, and **CS2** for game updates and notifies your server when a new version drops. Easily extensible to any game with a public version API.

## How It Works

Every 6 hours, a GitHub Actions cron job runs `check_update.py`. The script loops through each registered game, hits its public API for the current version, and compares against the last-seen version stored in `version_data.json`. When a version changes, it posts a rich embed to your Discord channel. No always-on server required — runs **for free**.

| Game | API | Auth | What It Detects |
|------|-----|------|-----------------|
| Fortnite | [fortnite-api.com](https://fortnite-api.com) `/v2/aes` | None | Build version changes |
| VALORANT | [valorant-api.com](https://valorant-api.com) `/v1/version` | None | Client version changes |
| CS2 | [Steam API](https://api.steampowered.com) `ISteamApps/UpToDateCheck` | None | Required server version changes |

## Project Structure

```
game-update-bot/
├── check_update.py                        # Multi-game update checker
├── bot.py                                 # Legacy always-on Fortnite bot (optional)
├── .github/workflows/game-update-check.yml   # Cron schedule
├── version_data.json                      # Last-seen versions (committed by workflow)
├── requirements.txt                       # Python dependencies
├── .env.example                           # Example environment variables
└── README.md
```

---

## Setup

### 1. Create a Discord Bot

1. Go to https://discord.com/developers/applications
2. **New Application** -> name it (e.g. "Game Updates")
3. **Bot** tab -> **Reset Token** -> copy the token
4. **OAuth2 > URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `View Channels`
   - Open the URL and invite the bot to your server

### 2. Get Your Channel ID

1. Discord -> **User Settings > Advanced > Developer Mode** (ON)
2. Right-click the notification channel -> **Copy Channel ID**

### 3. Add Secrets to GitHub

In your repo: **Settings > Secrets and variables > Actions > New repository secret**:

- `DISCORD_TOKEN` = your bot token
- `CHANNEL_ID` = your channel ID

### 4. Push & Run

```powershell
git push
```

The workflow runs every 6 hours automatically. Trigger it manually from the **Actions** tab to test.

---

## Adding a New Game

Adding a game takes ~30 lines of code. Create two functions and add one entry to the registry:

**1. A check function** — fetch the API, return a dict with at least a `"version"` key (used for change detection) and a `"release"` key (human-readable):

```python
def mygame_check():
    body = fetch_json("https://some-api.com/version")
    if not body:
        return None
    return {"version": body["build_id"], "release": body["display_version"]}
```

**2. An embed function** — build the Discord embed dict:

```python
def mygame_embed(info):
    return {
        "title": "\U0001f680 MyGame Update Detected!",
        "description": "A new MyGame update is available!",
        "color": 0xFF5500,
        "fields": [
            {"name": "Version", "value": info["release"], "inline": True},
        ],
        "footer": {"text": "Update your game"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

**3. Register it** — add to the `GAMES` list at the bottom of `check_update.py`:

```python
GAMES = [
    # ... existing games ...
    {"slug": "mygame", "name": "MyGame", "check": mygame_check, "embed": mygame_embed},
]
```

That's it. The main loop handles state tracking, change detection, and Discord notifications automatically.

---

## Changing the Schedule

Edit the `cron` line in `.github/workflows/game-update-check.yml` (UTC):

- `0 */6 * * *` — every 6 hours (default)
- `0 */3 * * *` — every 3 hours
- `0 0 * * *` — once a day at midnight

## Test Locally

```powershell
pip install -r requirements.txt
$env:DISCORD_TOKEN="your_bot_token"
$env:CHANNEL_ID="your_channel_id"
python check_update.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Discord bot token |
| `CHANNEL_ID` | Yes | Discord channel ID for notifications |

## Notes

- All APIs are **free and require no API keys**.
- Each game is checked independently — if one API is down, the others still run.
- The bot only reports **version/build changes**, not in-game events (shop rotations, etc.).
- `bot.py` is the old always-on Fortnite-only bot, kept for reference.
