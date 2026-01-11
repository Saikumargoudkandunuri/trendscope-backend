import os
import asyncio
import logging
import time
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.functions.contacts import ResolveUsernameRequest

logger = logging.getLogger("uvicorn.error")

TELEGRAM_CHANNELS = [
    "Cricinformer",
    "Cricketracker",
    "Cricketgully",
    "RadarXCricket",
    "Ipl_Live_Score_IPL",
    "mufatweets",
    "cricket_raash",
]

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION_FILE = "trendscope_session"

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def safe_resolve_username(username: str):
    """
    Resolve telegram username to entity safely.
    Returns entity or None
    """
    try:
        username = username.strip().replace("@", "").replace("https://t.me/", "").replace("t.me/", "")
        if not username:
            return None

        # check regex requirements (avoids unacceptable username error)
        # must start with letter and 5+ length basically
        if len(username) < 4:
            return None

        result = await client(ResolveUsernameRequest(username))
        if result and result.chats:
            return result.chats[0]
        if result and result.users:
            return result.users[0]
        return None

    except (UsernameInvalidError, UsernameNotOccupiedError) as e:
        logger.error(f"❌ Invalid TG username: {username} -> {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Resolve error {username}: {e}")
        return None


async def telegram_loop():
    logger.info("📨 Telegram Engine Started...")

    await client.start()

    while True:
        try:
            for ch in TELEGRAM_CHANNELS:
                entity = await safe_resolve_username(ch)
                if not entity:
                    continue

                try:
                    async for msg in client.iter_messages(entity, limit=5):
                        text = (msg.message or "").strip()
                        if not text:
                            continue

                        # you can send this text into cricket post generator
                        logger.info(f"TG [{ch}] => {text[:80]}")

                except Exception as ex:
                    logger.error(f"❌ Telegram channel read error {ch}: {ex}")
                    continue

            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Telegram loop error: {e}")
            await asyncio.sleep(60)


def start_telegram_engine():
    asyncio.run(telegram_loop())
