# Fortnite Update Bot

A Discord bot that monitors Fortnite for game updates (version bumps) and notifies your server when a new downloadable update is available.

## How It Works

Every 30 minutes the bot polls the [Fortnite API](https://fortnite-api.com) for the current game version. When the version string changes, it sends a ping to your Discord channel.

## Project Structure

```
fortnite-update-bot/
├── bot.py             # Main bot logic
├── requirements.txt   # Python dependencies
├── Procfile           # Railway process config
├── runtime.txt        # Python version for Railway
├── .env.example       # Example environment variables
└── README.md          # This file
```

---

## Step-by-Step Setup

### 1. Create a Discord Application & Bot

1. Go to https://discord.com/developers/applications
2. Click **New Application** -> give it a name (e.g. "Fortnite Updates")
3. Go to the **Bot** tab -> click **Reset Token** -> copy the token
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Go to **OAuth2 > URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Messages/View Channels`
   - Open the generated URL in your browser and invite the bot to your server

### 2. Get Your Discord Channel ID

1. Open Discord -> **User Settings > Advanced > Developer Mode** (toggle ON)
2. Right-click the channel you want notifications in -> **Copy Channel ID**

### 3. Test Locally

```powershell
# Create a virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
$env:DISCORD_TOKEN="your_bot_token"
$env:CHANNEL_ID="your_channel_id"

# Run the bot
python bot.py
```

You should see a "Bot started" message in your Discord channel. Wait for the next check or just test it.

### 4. Deploy to Railway (Free 24/7)

1. Push your code to a GitHub repository:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit"
   ```
2. Go to https://railway.app -> **New Project** -> **Deploy from GitHub repo**
3. Connect your GitHub account and select the repo
4. **Do NOT use the Start Command they suggest** -- Railway auto-detects the `Procfile`
5. Go to the **Variables** tab and add:
   - `DISCORD_TOKEN` = your bot token
   - `CHANNEL_ID` = your channel ID
   - `CHECK_INTERVAL` = `1800` (optional, 30 min)
6. The bot will deploy and start automatically

**Railway free tier:** $5 of free credits per month. A simple Python bot uses ~$0.50/month, so it stays free indefinitely.

> **Note:** Netlify cannot run a persistent Python bot. Railway is the correct choice.

### 5. Verify It's Working

Check your Discord channel -- the bot sends a startup message. If you want to force a test notification, temporarily restart the bot after changing the `version_data.json` file (or just wait for a real Fortnite update).

## Environment Variables

| Variable         | Required | Default | Description                            |
|------------------|----------|---------|----------------------------------------|
| `DISCORD_TOKEN`  | Yes      | --      | Discord bot token                      |
| `CHANNEL_ID`     | Yes      | --      | Discord channel ID for notifications   |
| `CHECK_INTERVAL` | No       | 1800    | Polling interval in seconds (30 min)   |

## Notes

- The bot only checks for **game version updates** (new builds), not item shop rotations.
- It uses the free public API at https://fortnite-api.com -- no API key needed.
- If Fortnite-API is down, the bot logs a warning and retries next cycle.
