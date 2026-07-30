"""Single-shot Fortnite update check.

Runs once, checks the Fortnite build version, and if it changed since the last
run posts an embed to a Discord channel via the REST API, then exits.

Designed to be triggered on a schedule (e.g. GitHub Actions cron) instead of
running as an always-on gateway bot. Uses the same DISCORD_TOKEN and CHANNEL_ID
as the old bot -- no Discord-side changes needed.
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fortnite-check")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "0")
VERSION_FILE = "version_data.json"
AES_URL = "https://fortnite-api.com/v2/aes"
NEWS_URL = "https://fortnite-api.com/v2/news/br"
DISCORD_API = "https://discord.com/api/v10"
USER_AGENT = "FortniteUpdateBot/2.0"


def fetch_json(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    if resp.status_code != 200:
        logger.warning("%s returned %s", url, resp.status_code)
        return None
    return resp.json()


def load_cached_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            data = json.load(f)
        version = data.get("version")
        logger.info("Loaded cached version: %s", version)
        return version
    return None


def save_version(version, release, cl):
    data = {
        "version": version,
        "release": release,
        "cl": cl,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved version: %s", version)


def fetch_motd():
    body = fetch_json(NEWS_URL)
    if not body:
        return None, None
    data = body.get("data") or {}
    motds = data.get("motds") or []
    if motds:
        m = motds[0]
        return m.get("title"), m.get("body")
    return None, None


def send_discord_embed(embed):
    url = f"{DISCORD_API}/channels/{CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json={"embeds": [embed]}, timeout=15)
    if resp.status_code not in (200, 201):
        logger.error("Discord send failed (%s): %s", resp.status_code, resp.text[:300])
        return False
    logger.info("Update message sent to channel %s", CHANNEL_ID)
    return True


def build_embed(release, cl):
    fields = [
        {"name": "Release", "value": release, "inline": True},
        {"name": "Build (CL)", "value": cl, "inline": True},
    ]

    motd_title, motd_body = fetch_motd()
    if motd_title:
        body = motd_body or ""
        trimmed = body[:250] + ("..." if len(body) > 250 else "")
        fields.append({
            "name": "\U0001f4f0 What's New",
            "value": f"**{motd_title}**\n{trimmed}",
            "inline": False,
        })

    fields.append({
        "name": "\U0001f4d6 Patch Notes",
        "value": "[View on Fortnite News](https://www.fortnite.com/news)",
        "inline": False,
    })

    return {
        "title": "\U0001f680 Fortnite Update Detected!",
        "description": "A new Fortnite update is available for download!",
        "color": 0x00BFFF,
        "fields": fields,
        "footer": {"text": "Download size varies — check the Epic Games Launcher"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    if not DISCORD_TOKEN:
        sys.exit("Missing DISCORD_TOKEN environment variable")
    if CHANNEL_ID in ("0", ""):
        sys.exit("Missing or invalid CHANNEL_ID environment variable")

    body = fetch_json(AES_URL)
    if not body:
        logger.error("Could not fetch Fortnite API; skipping this run")
        return

    data = body.get("data") or {}
    build_str = data.get("build")
    if not build_str:
        logger.warning("No build field in API response")
        return

    version = build_str
    release, cl = "?", "?"
    if "Release-" in build_str:
        parts = build_str.split("Release-")[1].split("-CL-")
        if len(parts) == 2:
            release, cl = parts

    cached = load_cached_version()
    is_new = cached is not None and version != cached

    if is_new:
        logger.info("New version detected: %s (was %s)", version, cached)
        send_discord_embed(build_embed(release, cl))
    elif cached is None:
        logger.info("No cached version yet; seeding state with %s", version)
    else:
        logger.info("No update (current: %s)", version)

    save_version(version, release, cl)


if __name__ == "__main__":
    main()
