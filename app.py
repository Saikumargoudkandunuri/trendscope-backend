print("APP.PY LOADED FROM:", __file__)

# ======================================================
# 1. STANDARDS & IMPORTS (Massive Import Section)
# ======================================================
import json
import logging
import os
import random
import re
import threading
import time
import uuid
import requests
import feedparser
import pytz
import openai
from datetime import datetime
from contextlib import asynccontextmanager

import cloudinary
import cloudinary.uploader
from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
import asyncio
from contextlib import asynccontextmanager
from telegram_engine import telegram_fetch_loop
from twitter_sources import TWITTER_RSS_SOURCES



# Local Application Import for your design logic
from image_generator import generate_news_image

# ======================================================
# 2. CONFIGURATION & API KEYS
# ======================================================
load_dotenv()
logger = logging.getLogger("uvicorn.error")

# Cloudinary Setup
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Gemini AI Setup (2026 SDK)
api_key_val = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key_val)

# --- UPDATE YOUR CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Instagram Setup
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")



# ======================================================
# 3. GLOBAL VARIABLES & RSS SOURCES
# ======================================================
NEWS_CACHE = {}
IS_POSTING_BUSY = False 
POSTED_FILE = "posted.json"

RSS_SOURCES = {
    "GoogleLive": "https://news.google.com/rss/search?q=when:1h+breaking+news+India&hl=en-IN&gl=IN&ceid=IN:en",
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
}

POST_CONFIG = {"Sports": 1, "Business": 1, "Tech": 1}

# ======================================================
# 4. HELPER UTILITIES
# ======================================================



# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ======================================================
# SUPABASE BRIDGE FUNCTIONS (FIXES NAMEERROR)
# ======================================================

def load_posted():
    """Fetches all previously posted URLs from Supabase to prevent repeats"""
    try:
        # We fetch only the 'url' column from Supabase
        res = supabase.table("posted_news").select("url").execute()
        # Convert the list of dictionaries into a simple Set of URLs
        return {item['url'] for item in res.data}
    except Exception as e:
        logger.error(f"Supabase Load Error: {e}")
        return set()

def save_posted(url):
    """Saves a new URL into the Supabase Vault immediately"""
    try:
        # Check if input is a set (old logic) or a string (new logic)
        if isinstance(url, set) or isinstance(url, list):
            # If the code passes a set, we take the last added item
            url_to_save = list(url)[-1]
        else:
            url_to_save = url

        supabase.table("posted_news").insert({"url": url_to_save}).execute()
        logger.info(f"✅ URL locked in Supabase: {url_to_save}")
    except Exception as e:
        logger.error(f"Supabase Save Error: {e}")

# This alias ensures that if your code calls 'mark_as_posted', it still works
def mark_as_posted(url):
    return save_posted(url)

def is_already_posted(url):
    """Check if URL exists in our Supabase Vault"""
    posted_set = load_posted()
    return url in posted_set

def is_quiet_hours():
    """Logic to stop posting between 1 AM and 6 AM IST"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    # Returns True if hour is 1, 2, 3, 4, or 5
    return 1 <= now.hour < 6

def upload_image_to_cloudinary(local_path):
    try:
        res = cloudinary.uploader.upload(
            local_path, 
            folder="trendscope",
            access_mode="public"
        )
        return res.get("secure_url")
    except Exception as e:
        logger.error(f"Cloudinary Error: {e}")
        return None

# ======================================================
# 5. AI LOGIC (The RVCJ Hinglish Converter)
# ======================================================

def ai_rvcj_converter(text):
    """
    Wirally Engine: Gemini -> Groq -> OpenRouter fallback

    RETURNS ALWAYS:
    {
      "headline": "...",
      "image_info": "...",
      "short_caption": "..."
    }
    """
    import os
    import re
    import json
    import requests

    text = (text or "").strip()

    # ---- Helper: safe extractor for Groq/OpenRouter responses ----
    def safe_openai_style_content(resp_json):
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

    # ---- Helper: normalize AI output into your final format ----
    def normalize_ai_json(raw):
        try:
            raw = (raw or "").strip()

            # Extract JSON if AI adds extra text
            match = re.search(r"\{.*\}", raw, re.S)
            if match:
                raw = match.group(0)

            data = json.loads(raw)

            headline = (data.get("headline") or "").strip()
            image_info = (data.get("image_info") or "").strip()
            short_caption = (data.get("short_caption") or "").strip()

            if not headline:
                headline = "BREAKING UPDATE"
            if not image_info:
                image_info = "More details soon\nStay tuned"
            if not short_caption:
                short_caption = headline + " 🔥"

            return {
                "headline": headline,
                "image_info": image_info,
                "short_caption": short_caption
            }

        except Exception:
            fallback_headline = "BREAKING UPDATE"
            if text:
                fallback_headline = text[:50].upper()

            return {
                "headline": fallback_headline,
                "image_info": (text[:160] if text else "More details soon").replace("\n", " "),
                "short_caption": "Trending update 🔥"
            }

    if not text:
        return {
            "headline": "BREAKING UPDATE",
            "image_info": "More details soon\nStay tuned",
            "short_caption": "Breaking update 🔥"
        }

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

    prompt = f"""
Act as a viral news editor for Wirally / RVCJ style.

Return ONLY a JSON object with EXACT keys:
{{
  "headline": "Shocking viral Hinglish hook (MAX 8 words)",
  "image_info": "3 or 4 short lines of facts (each line short)",
  "short_caption": "1-line Hinglish/Telugu hook for Instagram"
}}

News text:
{text}
""".strip()

    # 1) GEMINI
    try:
        if GOOGLE_API_KEY:
            from google import genai
            client = genai.Client(api_key=GOOGLE_API_KEY)
            res = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            raw = getattr(res, "text", "") or ""
            return normalize_ai_json(raw)
    except Exception as e:
        logger.warning(f"Gemini Busy, switching to Groq... ({e})")

    # 2) GROQ
    try:
        if GROQ_API_KEY:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            body = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6
            }
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=30
            )
            resp = r.json() if r.content else {}

            if r.status_code != 200 or "error" in resp:
                raise Exception(f"Groq API Error: status={r.status_code}, resp={resp}")

            raw = safe_openai_style_content(resp)
            if not raw:
                raise Exception(f"Groq response missing content: {resp}")

            return normalize_ai_json(raw)

    except Exception as e:
        logger.warning(f"Groq Busy, switching to OpenRouter... ({e})")

    # 3) OPENROUTER
    try:
        if OPENROUTER_API_KEY:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("APP_PUBLIC_URL", "https://trendscope-backend-fnsu.onrender.com"),
                "X-Title": "Trendscope Wirally Engine"
            }
            body = {
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6
            }
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=30
            )
            resp = r.json() if r.content else {}

            if r.status_code != 200 or "error" in resp:
                raise Exception(f"OpenRouter API Error: status={r.status_code}, resp={resp}")

            raw = safe_openai_style_content(resp)
            if not raw:
                raise Exception(f"OpenRouter response missing content: {resp}")

            return normalize_ai_json(raw)

    except Exception as e:
        logger.error(f"All AI brains failed! ({e})")

    return {
        "headline": "BREAKING UPDATE",
        "image_info": text[:160].replace("\n", " "),
        "short_caption": "Breaking update 🔥"
    }

    # =========================
    # 3) OPENROUTER (LAST RESORT)
    # =========================
    try:
        if OPENROUTER_API_KEY:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",

                # Recommended by OpenRouter
                "HTTP-Referer": os.getenv("APP_PUBLIC_URL", "https://trendscope-backend-fnsu.onrender.com"),
                "X-Title": "Trendscope Wirally Engine"
            }

            body = {
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6
            }

            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=30
            )

            resp = r.json() if r.content else {}

            if r.status_code != 200 or "error" in resp:
                raise Exception(f"OpenRouter API Error: status={r.status_code}, resp={resp}")

            raw = safe_openai_style_content(resp)

            if not raw:
                raise Exception(f"OpenRouter response missing content: {resp}")

            out = normalize_ai_json(raw)
            return out

    except Exception as e:
        logger.error(f"All AI brains failed! ({e})")

    # =========================
    # FINAL FALLBACK
    # =========================
    return {
        "headline": "BREAKING UPDATE",
        "image_info": text[:160].replace("\n", " "),
        "short_caption": "Breaking update 🔥"
    }
""

# ======================================================
# 6. NEWS ENGINE (Scoring & Fetching)
# ======================================================

def ai_category(text):
    t = text.lower()
    if any(k in t for k in ["cricket", "ipl", "score"]): return "Sports"
    if any(k in t for k in ["market", "sensex", "nifty"]): return "Business"
    if any(k in t for k in ["tech", "ai", "iphone"]): return "Tech"
    return "India"

def ai_trending_score(title):
    return min(95, 40 + sum(k in title.lower() for k in ["india","court","modi","breaking"]) * 10)

def extract_image(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c"

def fetch_news(filter_posted=False):
    global NEWS_CACHE
    NEWS_CACHE = {}
    out, i = [], 0
    
    # Only load posted_ids if we actually want to filter them
    posted_ids = load_posted() if filter_posted else set()
    
    for src, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:6]:
                # If filtering is ON, skip already posted links
                if filter_posted and e.link in posted_ids:
                    continue
                    
                art = {
                    "id": i, 
                    "title": e.title, 
                    "summary": e.get("summary", e.title),
                    "link": e.link, 
                    "image": extract_image(e),
                    "trend": ai_trending_score(e.title), 
                    "category": ai_category(e.title)
                }
                NEWS_CACHE[i] = art
                out.append(art)
                i += 1
        except: continue
    return out
def fetch_cricket_news(filter_posted=True):
    """
    Fetch cricket items from CRICKET_RSS_SOURCES
    and return structured items like normal news.
    """
    out = []
    i = 100000  # big id so it doesn't conflict with normal news ids

    posted_ids = load_posted() if filter_posted else set()

    for src, url in CRICKET_RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:10]:
                link = getattr(e, "link", "") or ""
                if filter_posted and link in posted_ids:
                    continue

                title = getattr(e, "title", "Cricket Update")
                summary = e.get("summary", title)

                out.append({
                    "id": i,
                    "source": src,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c",
                    "category": "Cricket",
                    "trend": 99
                })
                i += 1
        except Exception as ex:
            logger.error(f"Cricket RSS Error: {src} -> {ex}")

    return out
def fetch_twitter_cricket(filter_posted=True):
    out = []
    posted = load_posted() if filter_posted else set()
    i = 500000

    for url in TWITTER_RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:10]:
                link = getattr(e, "link", "")
                if filter_posted and link in posted:
                    continue

                title = e.title
                summary = e.get("summary", title)

                # filter only cricket/india
                if not any(k in title.lower() for k in ["india", "wicket", "six", "four", "ipl", "wpl"]):
                    continue

                out.append({
                    "id": i,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c",
                    "category": "Cricket",
                    "trend": 98
                })
                i += 1
        except Exception as e:
            logger.error(f"Twitter RSS error: {e}")

    return out

# ======================================================
# 7. INSTAGRAM & AUTO-POST CORE
# ======================================================
# ======================================================
# 7. INSTAGRAM & AUTO-POST CORE
# ======================================================

def post_to_instagram(image_url: str, caption: str):
    """
    Safe Instagram posting with:
    - global rate limiter
    - IG action-block cooldown
    - cache buster
    """

    import time
    import random
    import json
    import os
    import requests
    from post_limiter import can_post_now, mark_posted_now

    # ---------- GLOBAL RATE LIMIT ----------
    if not can_post_now():
        logger.warning("⏳ Global post limiter: skipping this post")
        return {"error": "rate_limit_global"}

    COOLDOWN_FILE = "ig_cooldown.json"

    def load_cooldown():
        if not os.path.exists(COOLDOWN_FILE):
            return {"blocked_until": 0}
        try:
            with open(COOLDOWN_FILE, "r") as f:
                return json.load(f)
        except:
            return {"blocked_until": 0}

    def save_cooldown(data):
        try:
            with open(COOLDOWN_FILE, "w") as f:
                json.dump(data, f)
        except:
            pass

    # ---------- COOLDOWN CHECK ----------
    cd = load_cooldown()
    now = int(time.time())

    if now < int(cd.get("blocked_until", 0)):
        mins = (cd["blocked_until"] - now) // 60
        logger.warning(f"⏳ IG cooldown active. {mins} min remaining.")
        return {"error": "cooldown_active", "blocked_until": cd["blocked_until"]}

    # ---------- CACHE BUSTER ----------
    image_url = f"{image_url}?v={random.randint(100000,999999)}"

    # ---------- STEP 1: CREATE MEDIA ----------
    try:
        create_res = requests.post(
            f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": PAGE_ACCESS_TOKEN
            },
            timeout=30
        ).json()
    except Exception as e:
        logger.error(f"IG CREATE EXCEPTION: {e}")
        return {"error": str(e)}

    if "error" in create_res:
        logger.error(f"IG CREATE ERROR: {create_res}")

        err = create_res["error"]
        if err.get("code") == 4 or err.get("error_subcode") == 2207051:
            cd["blocked_until"] = now + 3600
            save_cooldown(cd)
            logger.error("🚫 IG action blocked. Cooling down 60 mins.")

        return create_res

    creation_id = create_res.get("id")
    if not creation_id:
        return create_res

    # ---------- STEP 2: WAIT ----------
    time.sleep(20)

    # ---------- STEP 3: PUBLISH ----------
    publish_res = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": PAGE_ACCESS_TOKEN
        },
        timeout=30
    ).json()

    logger.info(f"PUBLISH RESPONSE: {publish_res}")

    if "error" in publish_res:
        err = publish_res["error"]
        if err.get("code") == 4 or err.get("error_subcode") == 2207051:
            cd["blocked_until"] = int(time.time()) + 3600
            save_cooldown(cd)
            logger.error("🚫 IG blocked after publish. Cooling down.")

        return publish_res

    # ---------- SUCCESS ----------
    mark_posted_now()
    return publish_res

    return publish_res


def post_category_wise_news():
    global IS_POSTING_BUSY

    if IS_POSTING_BUSY:
        logger.info("Posting already running. Skipping...")
        return

    try:
        IS_POSTING_BUSY = True
        logger.info("🚜 RVCJ Engine Started...")

        news_items = fetch_news(filter_posted=True)

        for n in news_items:
            try:
                # 1) AI
                data = ai_rvcj_converter(n.get("summary", n.get("title", "")))

                # 2) Unique Filename
                img_name = f"post_{uuid.uuid4().hex}.png"

                # 3) Create Image
                path = generate_news_image(
                    headline=data.get("headline", "BREAKING"),
                    info_text=data.get("image_info", "Details soon"),
                    image_url=n.get("image"),
                    output_name=img_name
                )

                # 4) Upload to Cloudinary
                public_url = upload_image_to_cloudinary(path)
                if not public_url:
                    logger.error("Cloudinary upload failed, skipping item.")
                    continue

                # 5) Post
                caption = data.get("short_caption") or data.get("headline") or "🔥"
                ig_res = post_to_instagram(public_url, caption)

                # 6) Save posted
                if ig_res and "id" in ig_res:
                    mark_as_posted(n["link"])
                    logger.info(f"✅ Posted: {n.get('title')}")
                else:
                    logger.error(f"❌ IG failed: {ig_res}")

                # Avoid spam posting
                time.sleep(60)

            except Exception as item_err:
                logger.error(f"Item error: {item_err}")
                continue

    except Exception as e:
        logger.error(f"post_category_wise_news error: {e}")

    finally:
        IS_POSTING_BUSY = False
def post_cricket_news():
    global IS_POSTING_BUSY

    if IS_POSTING_BUSY:
        logger.info("Posting already running. Skipping cricket cycle...")
        return

    try:
        IS_POSTING_BUSY = True
        logger.info("🏏 Cricket Engine Started...")
     
        twitter_items = fetch_twitter_cricket(filter_posted=True)
        cricket_items.extend(twitter_items)


        for n in cricket_items:
            try:
                # 1) AI convert
                data = ai_rvcj_converter(n.get("summary", n.get("title", "")))

                # 2) Unique image name
                img_name = f"cricket_{uuid.uuid4().hex}.png"

                # 3) Generate image
                path = generate_news_image(
                    headline=data.get("headline", "CRICKET UPDATE"),
                    info_text=data.get("image_info", n.get("title", "")),
                    image_url=n.get("image"),
                    output_name=img_name
                )

                # 4) Upload to Cloudinary
                public_url = upload_image_to_cloudinary(path)
                if not public_url:
                    logger.error("Cloudinary upload failed for cricket item.")
                    continue

                # 5) Post to IG
                caption = data.get("short_caption") or data.get("headline") or "🏏🔥"
                ig_res = post_to_instagram(public_url, caption)

                # 6) Save posted
                if ig_res and "id" in ig_res:
                    mark_as_posted(n["link"])
                    logger.info(f"✅ Cricket Posted: {n.get('title')}")
                else:
                    logger.error(f"❌ IG failed cricket: {ig_res}")

                time.sleep(90)

            except Exception as item_err:
                logger.error(f"Cricket item error: {item_err}")
                continue

    except Exception as e:
        logger.error(f"post_cricket_news error: {e}")

    finally:
        IS_POSTING_BUSY = False


# ======================================================
# 8. BACKGROUND WORKER & LIFESPAN
# ======================================================

def run_background_worker():
    while True:
        try:
            # Normal news cycle
            post_category_wise_news()

            # Cricket cycle
            post_cricket_news()

            time.sleep(300)
        except:
            time.sleep(30 * 60)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Ensure output folder exists
    os.makedirs(os.path.join("images", "output"), exist_ok=True)

    # ✅ Start RSS engine background thread
    threading.Thread(target=run_background_worker, daemon=True).start()

    # ✅ Function runs whenever Telegram message comes
    async def on_telegram_event(text, source):
        logger.info(f"✅ TG EVENT: {text[:80]}...")

        # 1) Convert into viral format
        data = ai_rvcj_converter(text)

        # 2) Create image
        img_name = f"tg_{uuid.uuid4().hex}.png"
        path = generate_news_image(
            headline=data.get("headline", "CRICKET UPDATE"),
            info_text=data.get("image_info", text[:120]),
            image_url="https://images.unsplash.com/photo-1504711434969-e33886168f5c",
            output_name=img_name
        )

        # 3) Upload and post
        public_url = upload_image_to_cloudinary(path)
        if public_url:
            caption = data.get("short_caption") or data.get("headline") or "🔥"
            post_to_instagram(public_url, caption)

    # ✅ Start Telegram engine as another background thread
    def tg_runner():
        asyncio.run(telegram_fetch_loop(on_telegram_event, logger))

    threading.Thread(target=tg_runner, daemon=True).start()

    yield


app = FastAPI(lifespan=lifespan)

# ======================================================
# 9. WEBSITE HTML PAGES (The Original 600-line UI)
# ======================================================

# Change this line:
@app.api_route("/", response_class=HTMLResponse, methods=["GET", "HEAD"])
def home(request: Request, category: str = Query(None)):
    # --- 1. Catch Robots (UptimeRobot/Cron-job) ---
    user_agent = request.headers.get("user-agent", "").lower()
    
    # If it's a HEAD request or a robot, return immediately to save time
    if request.method == "HEAD" or "uptime" in user_agent or "cron" in user_agent:
        # Use Response (Import it from fastapi if not already there)
        return Response(content="TrendScope Awake", media_type="text/plain")

    # --- 2. Regular Visitor Logic ---
    try:
        news = fetch_news(filter_posted=False)
        news.sort(key=lambda x: x["trend"], reverse=True)
        if category:
            news = [n for n in news if n["category"] == category]
        flash = news[:5]
    except Exception as e:
        logger.error(f"Home Page Error: {e}")
        return HTMLResponse(content="<h1>Site Busy. Please refresh.</h1>", status_code=503)

    # ... rest of your original HTML return f""" ...

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<style>
html, body {{ margin:0; padding:0; width:100%; overflow-x:hidden; font-family:Arial; background:#f1f3f6; }}
a {{ text-decoration:none; color:black; }}
.header {{ background:#131921; color:white; padding:12px; display:flex; justify-content:space-between; position:sticky; top:0; z-index:10; }}
.category {{ background:#232f3e; padding:10px; white-space:nowrap; overflow-x:auto; }}
.category a {{ color:white; margin-right:12px; font-weight:bold; font-size:14px; }}
.flash-box {{ background:white; margin:10px; padding:10px; border-radius:12px; }}
.flash-row {{ display:flex; gap:10px; overflow-x:auto; }}
.flash-card {{ flex:0 0 260px; }}
.flash-card img {{ width:100%; height:140px; object-fit:cover; border-radius:8px; }}
.card {{ background:white; margin:10px; padding:12px; border-radius:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.trend {{ float:right; color:#ff5722; font-weight:bold; }}
.overlay {{ position:fixed; inset:0; background:rgba(0,0,0,.4); display:none; z-index:9; }}
.menu {{ position:fixed; top:0; right:0; width:260px; height:100%; background:white; padding:20px; transform: translateX(100%); transition: transform 0.3s ease; z-index:10; }}
.menu.open {{ transform: translateX(0); }}
.menu button {{ width:100%; padding:10px; margin-top:10px; border:none; background:#eee; border-radius:5px; font-weight:bold; }}
</style>
<script>
function toggleMenu(){{
  const m=document.getElementById('menu');
  const o=document.getElementById('overlay');
  m.classList.toggle('open');
  o.style.display=m.classList.contains('open')?'block':'none';
}}
</script>
</head>
<body>
<div id="overlay" class="overlay" onclick="toggleMenu()"></div>
<div class="header"><b>TrendScope 🇮🇳</b><span onclick="toggleMenu()" style="cursor:pointer">☰</span></div>
<div class="category">
<a href="/">All</a><a href="/?category=India">India</a><a href="/?category=Tech">Tech</a><a href="/?category=Business">Business</a><a href="/?category=Sports">Sports</a>
</div>
<div class="flash-box"><b>🔥 Breaking Now</b>
<div class="flash-row">
{''.join(f"<div class='flash-card'><a href='{f['link']}' target='_blank'><img src='{f['image']}'><p>{f['title']}</p></a></div>" for f in flash)}
</div>
</div>
{''.join(f"<div class='card'><span class='trend'>🔥 {n['trend']}%</span><a href='/news/{n['id']}'>{n['title']}</a></div>" for n in news)}
<div id="menu" class="menu">
<h3>Settings</h3>
<button onclick="location.href='/login'">Login</button>
<button onclick="location.href='/admin'">Admin Panel</button>
<button onclick="toggleMenu()">Close</button>
</div>
</body>
</html>
"""
@app.get("/news/{i}", response_class=HTMLResponse)
def news_detail(i: int):
    news_list = fetch_news(filter_posted=False) # Website shows everything
    item = next((n for n in news_list if n["id"] == i), None)
    if not item: return "<h3>News not found</h3>"

    # Use the same AI converter
    rvcj = ai_rvcj_converter(item["summary"])

    return f"""
    <html>
    ... (keep your style section) ...
    <body>
        <div class="container">
            <a href="/">⬅ Back</a>
            <div class="card">
                <img src="{item['image']}">
                <h2>{rvcj['headline']}</h2>
                <div class="label">📰 NEWS HIGHLIGHTS</div>
                <div class="box">{rvcj['image_info'].replace('\\n', '<br>')}</div>
                <button class="btn read" onclick="window.open('{item['link']}', '_blank')">Read Source Article</button>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return """
    <html>
    <body style="font-family:Arial;padding:40px; background:#f1f3f6; text-align:center;">
        <div style="background:white; padding:20px; border-radius:15px; display:inline-block; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <h2>TrendScope Control Panel</h2>
            <p>Click below to force start an automatic RVCJ posting cycle.</p>
            <button onclick="runNow()" style="padding:15px 30px; background:green; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">🚀 TRIGGER AUTO-POST NOW</button>
            <p id="msg"></p>
        </div>
        <script>
        function runNow(){
            document.getElementById('msg').innerText = "Processing...";
            fetch("/cron/hourly").then(r=>r.json()).then(d=> {
                alert("Triggered: " + d.status);
                document.getElementById('msg').innerText = "Last Triggered: Just Now";
            });
        }
        </script>
    </body>
    </html>
    """

@app.get("/cron/hourly")
def cron_trigger():
    # We check if it's already busy. If yes, we just say "Busy" but return 200 OK.
    if IS_POSTING_BUSY:
        return {"status": "already_running_skipping_trigger"}
    
    # Trigger in a separate thread so the web request finishes instantly
    threading.Thread(target=post_category_wise_news).start()
    return {"status": "trigger_received_successfully"}

@app.get("/login", response_class=HTMLResponse)
def login():
    return "<h2 style='padding:20px'>Login (Coming Soon)</h2><a href='/'>Back</a>"

@app.get("/test-supabase")
def test_supabase():
    try:
        # Try to fetch one row from your table
        res = supabase.table("posted_news").select("*").limit(1).execute()
        return {"status": "Connected!", "data_found": len(res.data)}
    except Exception as e:
        return {"status": "Error", "message": str(e)}    