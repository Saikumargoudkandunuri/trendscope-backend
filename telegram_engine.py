import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.functions.contacts import ResolveUsernameRequest

TELEGRAM_CHANNELS = [
    "cricinformer",
    "crictracker",
    "cricketgully",
    "RadarXCricket",
    "Ipl_Live_Score_IPL",
    "mufatweets",
    "cricket_raash",
]

API_ID_RAW = os.getenv("TELEGRAM_API_ID", "").strip()
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()
SESSION_FILE = os.getenv("TELEGRAM_SESSION_FILE", "trendscope_session.session").strip()


def _log(logger, msg):
    try:
        if logger:
            logger.info(msg)
    except:
        pass


def _log_err(logger, msg):
    try:
        if logger:
            logger.error(msg)
    except:
        pass


def create_client(logger=None):
    if not API_ID_RAW or not API_HASH:
        _log_err(logger, "❌ Telegram disabled: TELEGRAM_API_ID / TELEGRAM_API_HASH missing")
        return None

    try:
        api_id = int(API_ID_RAW)
    except Exception:
        _log_err(logger, "❌ TELEGRAM_API_ID must be number")
        return None

    try:
        # remove .session extension (Telethon auto adds)
        session_name = SESSION_FILE.replace(".session", "")
        client = TelegramClient(session_name, api_id, API_HASH)
        _log(logger, "✅ Telegram client created")
        return client
    except Exception as e:
        _log_err(logger, f"❌ Telegram client create error: {e}")
        return None


async def safe_resolve_username(client, username: str, logger=None):
    try:
        username = username.strip().replace("@", "").replace("https://t.me/", "").replace("t.me/", "")
        if not username:
            return None

        # Telegram username rules safety
        if len(username) < 5 or len(username) > 32:
            _log(logger, f"⚠️ Skip TG username invalid length: {username}")
            return None

        if not username[0].isalpha():
            _log(logger, f"⚠️ Skip TG username invalid start: {username}")
            return None

        result = await client(ResolveUsernameRequest(username))
        if result and result.chats:
            return result.chats[0]
        if result and result.users:
            return result.users[0]
        return None

    except (UsernameInvalidError, UsernameNotOccupiedError):
        _log_err(logger, f"❌ TG username invalid/not occupied: {username}")
        return None
    except Exception as e:
        _log_err(logger, f"❌ Resolve error {username}: {e}")
        return None


async def telegram_loop(on_event=None, logger=None):
    """
    ✅ Reads Telegram messages.
    ✅ Calls callback:
        await on_event(text, source)
    """
    _log(logger, "📨 Telegram Engine Started...")

    client = create_client(logger)
    if client is None:
        _log(logger, "⚠️ Telegram engine not started. Continuing without Telegram.")
        return

    await client.start()

    last_ids = {}  # channel -> last msg id (avoid duplicates)

    while True:
        try:
            for ch in TELEGRAM_CHANNELS:
                entity = await safe_resolve_username(client, ch, logger)
                if not entity:
                    continue

                try:
                    async for msg in client.iter_messages(entity, limit=5):
                        if not msg or not msg.id:
                            continue

                        text = (msg.message or "").strip()
                        if not text:
                            continue

                        # ✅ prevent repeated processing of same message
                        prev = last_ids.get(ch, 0)
                        if msg.id <= prev:
                            continue

                        # update latest seen
                        last_ids[ch] = msg.id

                        _log(logger, f"TG [{ch}] => {text[:90]}")

                        # ✅ Trigger callback to your app
                        if on_event:
                            try:
                                await on_event(text, f"telegram:{ch}")
                            except Exception as cb_err:
                                _log_err(logger, f"❌ TG callback error: {cb_err}")

                except Exception as ex:
                    _log_err(logger, f"❌ Telegram read error {ch}: {ex}")
                    continue

            await asyncio.sleep(30)

        except Exception as e:
            _log_err(logger, f"Telegram loop error: {e}")
            await asyncio.sleep(60)


def telegram_fetch_loop(on_event=None, logger=None):
    """
    ✅ Call this in a thread.
    Example:
        threading.Thread(target=lambda: telegram_fetch_loop(on_event, logger)).start()
    """
    asyncio.run(telegram_loop(on_event=on_event, logger=logger))
