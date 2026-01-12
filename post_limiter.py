import time
import os
import json

POST_GAP_SECONDS = 4200  # ✅ 1 hour 10 minutes
STATE_FILE = "post_state.json"


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_post_time": 0}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"last_post_time": 0}


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except:
        pass


def can_post_now():
    state = _load_state()
    last = int(state.get("last_post_time", 0))
    now = int(time.time())
    return (now - last) >= POST_GAP_SECONDS


def mark_posted_now():
    state = _load_state()
    state["last_post_time"] = int(time.time())
    _save_state(state)

