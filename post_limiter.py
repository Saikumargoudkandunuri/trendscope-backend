import json
import os
import time
import logging

logger = logging.getLogger("uvicorn.error")

POST_LIMIT_FILE = "global_post_limit.json"

# ✅ 1 hour 10 minutes gap
POST_GAP_SECONDS = 70 * 60

def _load_limit_data():
    if not os.path.exists(POST_LIMIT_FILE):
        return {"last_post_time": 0}
    try:
        with open(POST_LIMIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"last_post_time": 0}

def _save_limit_data(data):
    try:
        with open(POST_LIMIT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"❌ Could not save limiter file: {e}")

def can_post_now():
    data = _load_limit_data()
    last_post = int(data.get("last_post_time", 0))
    now = int(time.time())

    # ✅ If last post happened within 70 mins → block posting
    if now - last_post < POST_GAP_SECONDS:
        remaining = POST_GAP_SECONDS - (now - last_post)
        mins = max(1, int(remaining / 60))
        logger.warning(f"⏳ Global post limiter active. {mins} min remaining.")
        return False

    return True

def mark_posted_now():
    data = _load_limit_data()
    data["last_post_time"] = int(time.time())
    _save_limit_data(data)
    logger.info("✅ Global post limiter updated: last_post_time saved.")
