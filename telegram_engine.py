import os
import asyncio
import json
from telethon import TelegramClient

TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
TG_SESSION = os.getenv("TG_SESSION", "trendscope_session")

STATE_FILE = "telegram_state.json"

# ✅ Add your cricket telegram channels (public usernames)
TELEGRAM_CHANNELS = [
    "Cricinformer",
    "Cricketracker",
    "Cricketgully",
    "RadarXCricket",
    "Ipl_Live_Score_IPL",
    "mufatweets",
    "cricket_raash",
]

KEYWORDS = [
    "india", "wicket", "out", "six", "four", "dropped", "catch",
    "50", "100", "record", "milestone", "run out", "lbw"
]

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_ids": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"last_ids": {}}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def is_cricket_msg(msg: str) -> bool:
    t = (msg or "").lower()
    return any(k in t for k in KEYWORDS)

async def telegram_fetch_loop(on_event, logger):
    if not TG_API_ID or not TG_API_HASH:
        logger.error("❌ Telegram keys missing.")
        return

    client = TelegramClient(TG_SESSION, TG_API_ID, TG_API_HASH)
    state = load_state()

    async with client:
        logger.info("📨 Telegram Engine Started...")

        while True:
            try:
                for ch in TELEGRAM_CHANNELS:
                    last_id = state["last_ids"].get(ch, 0)

                    async for m in client.iter_messages(ch, limit=10):
                        if not m or not m.id or not m.message:
                            continue

                        if m.id <= last_id:
                            continue

                        text = m.message.strip()

                        if not is_cricket_msg(text):
                            continue

                        state["last_ids"][ch] = m.id
                        source_url = f"https://t.me/{ch}/{m.id}"

                        await on_event(text, source_url)

                save_state(state)

            except Exception as e:
                logger.error(f"Telegram loop error: {e}")

            await asyncio.sleep(60)
