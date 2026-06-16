import discord
import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fortnite-bot")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "1800"))
VERSION_FILE = "version_data.json"
AES_URL = "https://fortnite-api.com/v2/aes"
NEWS_URL = "https://fortnite-api.com/v2/news/br"
USER_AGENT = "FortniteUpdateBot/1.0"


class FortniteUpdateBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self._cached_version = None

    def _load_version(self):
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE) as f:
                data = json.load(f)
            self._cached_version = data.get("version")
            logger.info("Loaded cached version: %s", self._cached_version)

    def _save_version(self, version, release, cl):
        data = {
            "version": version,
            "release": release,
            "cl": cl,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(VERSION_FILE, "w") as f:
            json.dump(data, f, indent=2)
        self._cached_version = version
        logger.info("Saved version: %s", version)

    async def _fetch_json(self, session, url):
        async with session.get(url, timeout=15) as resp:
            if resp.status != 200:
                logger.warning("%s returned %s", url, resp.status)
                return None
            return await resp.json()

    async def _fetch_motd(self, session):
        body = await self._fetch_json(session, NEWS_URL)
        if not body:
            return None, None
        data = body.get("data") or {}
        motds = data.get("motds") or []
        if motds:
            m = motds[0]
            return m.get("title"), m.get("body")
        return None, None

    async def on_ready(self):
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        self._load_version()
        asyncio.create_task(self._poll_loop())

    async def _poll_loop(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            logger.error("Channel ID %s not found!", CHANNEL_ID)
            return
        await self._check_once(channel, startup=True)
        while not self.is_closed():
            await asyncio.sleep(CHECK_INTERVAL)
            await self._check_once(channel, startup=False)

    async def _check_once(self, channel, startup=False):
        try:
            headers = {"User-Agent": USER_AGENT}
            async with aiohttp.ClientSession(headers=headers) as session:
                body = await self._fetch_json(session, AES_URL)
                if not body:
                    return

                data = body.get("data") or {}
                build_str = data.get("build")
                if not build_str:
                    logger.warning("No build field in API response")
                    return

                version = build_str
                release = "?"
                cl = "?"
                if "Release-" in build_str:
                    parts = build_str.split("Release-")[1].split("-CL-")
                    if len(parts) == 2:
                        release, cl = parts

                is_new = version != self._cached_version and self._cached_version is not None

                if is_new:
                    motd_title, motd_body = await self._fetch_motd(session)

                    embed = discord.Embed(
                        title="\U0001f680 Fortnite Update Detected!",
                        description="A new Fortnite update is available for download!",
                        color=0x00BFFF,
                    )
                    embed.add_field(name="Release", value=release, inline=True)
                    embed.add_field(name="Build (CL)", value=cl, inline=True)
                    if motd_title:
                        embed.add_field(
                            name="\U0001f4f0 What's New",
                            value=f"**{motd_title}**\n{motd_body[:250]}{'...' if len(motd_body) > 250 else ''}",
                            inline=False,
                        )
                    embed.add_field(
                        name="\U0001f4d6 Patch Notes",
                        value="[View on Fortnite News](https://www.fortnite.com/news)",
                        inline=False,
                    )
                    embed.set_footer(text="Download size varies — check the Epic Games Launcher")
                    embed.timestamp = datetime.now(timezone.utc)

                    logger.info("New version detected: %s", version)
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        logger.error("Bot lacks permission to send in channel %s", CHANNEL_ID)
                    except Exception as exc:
                        logger.error("Failed to send Discord message: %s", exc)
                else:
                    msg = ""
                    if startup:
                        msg = (
                            f"\U0001f916 Fortnite Update Bot is online!\n"
                            f"Current version: **Release {release} (CL {cl})**\n"
                            f"I'll ping here when a new update drops."
                        )
                    else:
                        logger.info("No update (current: %s)", version)

                    if msg and channel:
                        try:
                            await channel.send(msg)
                        except Exception:
                            pass

                self._save_version(version, release, cl)

        except asyncio.TimeoutError:
            logger.warning("API request timed out")
        except Exception as exc:
            logger.error("Check failed: %s", exc)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN environment variable")
    if CHANNEL_ID == 0:
        raise SystemExit("Missing or invalid CHANNEL_ID environment variable")

    bot = FortniteUpdateBot()
    bot.run(DISCORD_TOKEN)
