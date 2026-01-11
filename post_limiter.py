import time, json, os

LIMIT_FILE = "post_limit.json"
MIN_GAP_SECONDS = 15 * 60   # 15 mins gap globally

def can_post_now():
    if not os.path.exists(LIMIT_FILE):
        return True

    try:
        data = json.load(open(LIMIT_FILE, "r"))
        last = int(data.get("last_post_time", 0))
        return (int(time.time()) - last) >= MIN_GAP_SECONDS
    except:
        return True

def mark_posted_now():
    json.dump({"last_post_time": int(time.time())}, open(LIMIT_FILE, "w"))
