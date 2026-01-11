import os
import re
import json
import time
import uuid
import requests
from datetime import datetime

def get_ai_keys():
    return {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", "").strip(),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY", "").strip(),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", "").strip(),
    }


# -----------------------------
# CONFIG
# -----------------------------
CRICAPI_KEY = os.getenv("CRICAPI_KEY", "").strip()

# Store posted events to avoid duplicates
CRICKET_STATE_FILE = "cricket_posted.json"

# Polling interval (seconds)
POLL_INTERVAL = 40

# Post periodic match updates every N minutes
MATCH_UPDATE_MINUTES = 18

# -----------------------------
# HELPERS: STATE SAVE/LOAD
# -----------------------------
def load_cricket_state():
    if not os.path.exists(CRICKET_STATE_FILE):
        return {
            "posted_events": [],
            "last_match_updates": {},   # match_id -> timestamp
            "last_scores": {},          # match_id -> score hash
            "last_milestones": {}       # match_id -> {"bat50":[], "bat100":[], "bowl3":[], "bowl5":[]}
        }
    try:
        with open(CRICKET_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "posted_events": [],
            "last_match_updates": {},
            "last_scores": {},
            "last_milestones": {}
        }


def save_cricket_state(state):
    try:
        with open(CRICKET_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# -----------------------------
# FREE API: CURRENT MATCHES
# -----------------------------
def fetch_current_matches():
    """
    Free CricAPI endpoint:
    https://api.cricapi.com/v1/currentMatches?apikey=KEY&offset=0
    """
    if not CRICAPI_KEY:
        raise RuntimeError("CRICAPI_KEY missing")

    url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"

    r = requests.get(url, timeout=25)
    data = r.json()

    # expected: {"status":"success","data":[...]}
    matches = data.get("data", []) if isinstance(data, dict) else []
    return matches


# -----------------------------
# FILTER: INDIA / WPL / IPL
# -----------------------------
def is_target_match(m):
    """
    Accepts:
    - India matches (team contains "India")
    - WPL matches (Women's Premier League / WPL)
    - IPL matches
    """
    name = (m.get("name") or "").lower()
    teams = " ".join(m.get("teams", [])).lower()
    series = (m.get("series_id") or "")

    # Match must be active/live-ish
    status = (m.get("status") or "").lower()
    if "scheduled" in status:
        return False

    # India matches
    if "india" in teams:
        return True

    # WPL
    if "wpl" in name or "women's premier league" in name or "womens premier league" in name:
        return True

    # IPL
    if "ipl" in name or "indian premier league" in name:
        return True

    return False


def get_match_id(m):
    # CricAPI usually has "id"
    return str(m.get("id") or m.get("match_id") or m.get("unique_id") or "")


# -----------------------------
# EVENT DETECTION
# -----------------------------
def score_hash(m):
    """
    Convert score object into a stable hash string to detect changes.
    """
    score = m.get("score", [])
    status = m.get("status", "")
    return json.dumps({"score": score, "status": status}, sort_keys=True)


def extract_score_summary(m):
    """
    Create human-readable score line.
    Example output:
    'IND 145/3 (16.2 ov) | PAK 144/8 (20 ov)'
    """
    parts = []
    for s in (m.get("score") or []):
        inning = s.get("inning") or ""
        r = s.get("r")
        w = s.get("w")
        o = s.get("o")
        if r is None:
            continue
        parts.append(f"{inning}: {r}/{w} ({o} ov)")
    if not parts:
        # fallback
        parts.append((m.get("status") or "LIVE").strip())
    return " | ".join(parts)


def detect_wicket_or_big_change(old_hash, new_hash):
    """
    Basic change detector. If score changed, we treat as update.
    For wicket detection, we can detect if wickets increased.
    """
    try:
        old = json.loads(old_hash)
        new = json.loads(new_hash)
    except Exception:
        return {"changed": True, "wicket": False}

    old_scores = old.get("score", [])
    new_scores = new.get("score", [])

    wicket = False
    try:
        for i in range(min(len(old_scores), len(new_scores))):
            ow = old_scores[i].get("w", 0)
            nw = new_scores[i].get("w", 0)
            if nw > ow:
                wicket = True
                break
    except Exception:
        wicket = False

    changed = old_hash != new_hash
    return {"changed": changed, "wicket": wicket}


def is_time_for_match_update(state, match_id):
    """
    periodic match update (every MATCH_UPDATE_MINUTES)
    """
    now = int(time.time())
    last = int(state["last_match_updates"].get(match_id, 0))
    return (now - last) > (MATCH_UPDATE_MINUTES * 60)


def mark_match_update_time(state, match_id):
    state["last_match_updates"][match_id] = int(time.time())


# -----------------------------
# OPTIONAL: COMMENTARY / TEXT EVENTS
# -----------------------------
DROP_PATTERNS = [
    r"dropped",
    r"chance missed",
    r"put down",
    r"dropped catch",
]

def detect_dropped_catch(text):
    text = (text or "").lower()
    return any(re.search(p, text) for p in DROP_PATTERNS)


# -----------------------------
# AI CAPTION GENERATION (3 brains like your app.py)
# -----------------------------
def safe_openai_style_content(resp_json):
    """
    Safe extractor for OpenAI/Groq/OpenRouter chat completion responses.
    Returns message content string or None.
    """
    try:
        if not isinstance(resp_json, dict):
            return None
        choices = resp_json.get("choices", [])
        if not choices:
            return None
        msg = choices[0].get("message", {})
        if not msg:
            return None
        return msg.get("content")
    except Exception:
        return None


def ai_cricket_caption(prompt, logger=None):
    import requests
    import json
    import re

    keys = get_ai_keys()
    GOOGLE_API_KEY = keys["GOOGLE_API_KEY"]
    GROQ_API_KEY = keys["GROQ_API_KEY"]
    OPENROUTER_API_KEY = keys["OPENROUTER_API_KEY"]
    """
    Uses:
    - Gemini (google-genai)
    - Groq
    - OpenRouter
    Same fallback style as your app.py
    """


    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    def normalize(raw):
        try:
            match = re.search(r"\{.*\}", raw, re.S)
            if match:
                raw = match.group(0)

            data = json.loads(raw)

            headline = (data.get("headline") or "").strip()
            image_info = (data.get("image_info") or "").strip()
            short_caption = (data.get("short_caption") or "").strip()

            if not headline:
                headline = "INDIA MATCH UPDATE"
            if not image_info:
                image_info = "Stay tuned for updates"
            if not short_caption:
                short_caption = headline + " 🔥"

            return {"headline": headline, "image_info": image_info, "short_caption": short_caption}
        except Exception:
            return None

    # prompt to AI
    ai_prompt = f"""
Act as viral Telugu cricket editor (Wirally style).

Return ONLY JSON:
{{
  "headline": "MAX 8 words Telugu/Hinglish hook",
  "image_info": "3-4 short lines (facts, score, key player)",
  "short_caption": "1-line Telugu + emoji punch"
}}

Context:
{prompt}
"""

    # 1) GEMINI
    try:
        if GOOGLE_API_KEY:
            from google import genai
            client = genai.Client(api_key=GOOGLE_API_KEY)
            res = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=ai_prompt
            )
            raw = res.text or ""
            out = normalize(raw)
            if out:
                return out
    except Exception as e:
        if logger:
            logger.warning(f"Cricket AI Gemini failed -> Groq ({e})")

    # 2) GROQ
    try:
        if GROQ_API_KEY:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            body = {
                "model": "llama-3.1-70b-versatile",
                "messages": [{"role": "user", "content": ai_prompt}],
                "temperature": 0.6
            }
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=30)
            raw = r.json()["choices"][0]["message"]["content"]
            out = normalize(raw)
            if out:
                return out
    except Exception as e:
        if logger:
            logger.warning(f"Cricket AI Groq failed -> OpenRouter ({e})")

    # 3) OPENROUTER
    try:
        if OPENROUTER_API_KEY:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            body = {
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": ai_prompt}],
                "temperature": 0.6
            }
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body, timeout=30)
            raw = r.json()["choices"][0]["message"]["content"]
            out = normalize(raw)
            if out:
                return out
    except Exception as e:
        if logger:
            logger.error(f"Cricket AI OpenRouter failed ({e})")

    return None


# -----------------------------
# POST: CRICKET UPDATE
# -----------------------------
def post_cricket_update(m, event_type, generate_news_image, upload_image_to_cloudinary, post_to_instagram, logger):
    """
    event_type examples:
    - WICKET
    - MILESTONE
    - MATCH_UPDATE
    - RESULT
    - DROP_CATCH (if commentary)
    """
    match_name = m.get("name", "Cricket Match")
    status = m.get("status", "LIVE")
    score_line = extract_score_summary(m)

    context = f"""
Match: {match_name}
Status: {status}
Score: {score_line}
Event: {event_type}
"""

    # AI output (optional)
    ai = ai_cricket_caption(context, logger=logger)

    if ai:
        headline = ai["headline"]
        image_info = ai["image_info"] + f"\n\n{score_line}"
        caption = ai["short_caption"] + "\n\n" + score_line
    else:
        # template fallback captions
        headline = (event_type.replace("_", " ") + " 🔥")[:60]
        image_info = f"{match_name}\n{status}\n{score_line}"
        caption = f"{match_name}\n{event_type} 🔥\n{score_line}"

    # Build image
    img_name = f"cricket_{uuid.uuid4().hex}.png"
    img_path = generate_news_image(
        headline=headline,
        info_text=image_info,
        image_url=(m.get("teamInfo", [{}])[0].get("img") if m.get("teamInfo") else ""),
        output_name=img_name
    )

    # Upload and post
    public_url = upload_image_to_cloudinary(img_path)
    if not public_url:
        logger.error("Cricket: Cloudinary upload failed.")
        return False

    ig_res = post_to_instagram(public_url, caption)
    if ig_res and "id" in ig_res:
        logger.info(f"✅ Cricket posted: {event_type} | {match_name}")
        return True

    logger.error(f"❌ Cricket IG failed: {ig_res}")
    return False


# -----------------------------
# MAIN LOOP
# -----------------------------
def cricket_worker_loop(generate_news_image, upload_image_to_cloudinary, post_to_instagram, logger):
    """
    Runs forever inside worker.py.
    Detects India/WPL/IPL matches and posts updates.
    """

    state = load_cricket_state()

    logger.info("🏏 Cricket Engine Started...")

    while True:
        try:
            matches = fetch_current_matches()
            targets = [m for m in matches if is_target_match(m)]

            if not targets:
                logger.info("Cricket: No India/WPL/IPL matches live. Sleeping...")
                save_cricket_state(state)
                time.sleep(POLL_INTERVAL)
                continue

            for m in targets:
                match_id = get_match_id(m)
                if not match_id:
                    continue

                new_hash = score_hash(m)
                old_hash = state["last_scores"].get(match_id)

                change_info = detect_wicket_or_big_change(old_hash or "", new_hash)

                # Save latest score hash
                state["last_scores"][match_id] = new_hash

                # ---- Trigger 1: RESULT / FINISHED ----
                status = (m.get("status") or "").lower()
                if any(x in status for x in ["won", "match ended", "result", "abandoned", "no result"]):
                    event_id = f"{match_id}_RESULT_{status}"
                    if event_id not in state["posted_events"]:
                        ok = post_cricket_update(
                            m, "RESULT",
                            generate_news_image, upload_image_to_cloudinary, post_to_instagram, logger
                        )
                        if ok:
                            state["posted_events"].append(event_id)

                    continue  # finished match

                # ---- Trigger 2: WICKET ----
                if change_info["wicket"]:
                    event_id = f"{match_id}_WICKET_{int(time.time())//60}"  # one per minute max
                    if event_id not in state["posted_events"]:
                        ok = post_cricket_update(
                            m, "WICKET",
                            generate_news_image, upload_image_to_cloudinary, post_to_instagram, logger
                        )
                        if ok:
                            state["posted_events"].append(event_id)
                            mark_match_update_time(state, match_id)

                # ---- Trigger 3: Periodic Match Update ----
                # if score changed and enough time passed
                if change_info["changed"] and is_time_for_match_update(state, match_id):
                    event_id = f"{match_id}_MATCH_UPDATE_{int(time.time())//(MATCH_UPDATE_MINUTES*60)}"
                    if event_id not in state["posted_events"]:
                        ok = post_cricket_update(
                            m, "MATCH_UPDATE",
                            generate_news_image, upload_image_to_cloudinary, post_to_instagram, logger
                        )
                        if ok:
                            state["posted_events"].append(event_id)
                            mark_match_update_time(state, match_id)

            save_cricket_state(state)

        except Exception as e:
            logger.error(f"Cricket Engine Error: {e}")

        time.sleep(POLL_INTERVAL)
