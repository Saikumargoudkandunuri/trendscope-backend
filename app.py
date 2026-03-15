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
from contextlib import asynccontextmanager
from fallback_images import FALLBACK_IMAGES, get_fallback_image_url


import os
import threading
import asyncio
import uuid
import random
from fastapi import FastAPI

from telegram_engine import telegram_fetch_loop
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
from contextlib import asynccontextmanager
import os
import threading
import asyncio
import uuid
import time
from fastapi import FastAPI
import os
import uuid
import random
import threading
import time
import asyncio
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from fallback_images import FALLBACK_IMAGES, get_fallback_image_url



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
def clean_html(raw_html):
    """
    Removes HTML tags (like <a href...>) from text.
    Fixes the issue where raw code appears in the image.
    """
    if not raw_html:
        return ""
    # Regex to remove anything between < and >
    clean = re.sub(r'<.*?>', '', str(raw_html))
    return clean.strip()
# ======================================================
# 5. AI LOGIC (The RVCJ Hinglish Converter)
# ======================================================

# ======================================================
# AI ENGINE: THE "BRAIN" (Multi-Provider Waterfall)
# ======================================================

# ======================================================
# AI ENGINE: MULTI-PROVIDER WATERFALL (Strict Mode)
# ======================================================

# ======================================================
# AI ENGINE: MULTI-PROVIDER WATERFALL (Storyteller Mode)
# ======================================================

# ======================================================
# AI ENGINE: MULTI-PROVIDER WATERFALL (Storyteller Mode)
# ======================================================

# ======================================================
# 5. AI LOGIC (The RVCJ Hinglish Converter)
# ======================================================

def ai_rvcj_converter(text):
    """
    Storyteller Mode: 
    Writes 2-3 sentence summaries and strict JSON to avoid errors.
    """
    import requests
    import json
    import re
    import os
    
    text = (text or "").strip()
    if not text: return _fallback_data_safe()

    # 🔥 STRICT PROMPT: No bullet points, no "Here is the JSON" text
    prompt = f"""
    Act as a Senior Editor for a viral Instagram News Page (like RVCJ Media or Tatva India).
    
    TASK: Read the news below and convert it into a valid JSON object.
    
    CRITICAL RULES:
    1. Output JSON ONLY. Start with {{ and end with }}.
    2. DO NOT write "Here is the JSON" or any introductory text.
    3. "headline": Short punchy headline (Max 7 words, Uppercase).
    4. "image_info": Write a short paragraph (2-3 sentences max). Explain the context: What happened? Why is it important? Use conversational English/Hinglish. NO bullet points.
    5. "short_caption": Engaging caption for Instagram with 3-4 hashtags.
    6. "search_keyword": The EXACT visual subject for AI image generator. If it's a person, output: "Portrait of [Name] face realistic". NEVER use metaphors.

    Input News: {text[:2000]}
    """

    # 1. SPEED LAYER
    res = _call_openai_compat("Groq", "https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY"), "llama-3.3-70b-versatile", prompt)
    if res: return res

    res = _call_openai_compat("Cerebras", "https://api.cerebras.ai/v1", os.getenv("CEREBRAS_API_KEY"), "llama3.1-70b", prompt)
    if res: return res

    # 2. INTELLIGENCE LAYER
    res = _call_openai_compat("Nvidia", "https://integrate.api.nvidia.com/v1", os.getenv("NVIDIA_API_KEY"), "meta/llama-3.1-405b-instruct", prompt)
    if res: return res

    res = _call_openai_compat("Together", "https://api.together.xyz/v1", os.getenv("TOGETHER_API_KEY"), "meta-llama/Llama-3.3-70B-Instruct-Turbo", prompt)
    if res: return res

    # 3. GOOGLE LAYER
    try:
        if os.getenv("GEMINI_API_KEY"):
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            logger.info("🧠 AI WINNER: Gemini 2.0 Flash")
            return _parse_ai_json(r.text)
    except Exception as e:
        logger.warning(f"⚠️ Gemini Skipped: {e}")

    # 4. BACKUP LAYER
    res = _call_openai_compat("OpenRouter", "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY"), "openai/gpt-4o-mini", prompt)
    if res: return res

    logger.error("❌ CRITICAL: All AI providers failed. Using manual fallback.")
    return _fallback_data_safe()

def _call_openai_compat(provider_name, url, key, model, prompt):
    if not key: return None
    import requests
    try:
        headers = {
            "Authorization": f"Bearer {key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trendscope.app",
            "X-Title": "TrendScope"
        }
        data = {
            "model": model,
            "messages":[{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 500
        }
        r = requests.post(f"{url}/chat/completions", headers=headers, json=data, timeout=15)
        
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            logger.info(f"🧠 AI WINNER: {provider_name}")
            return _parse_ai_json(content)
        else:
            logger.warning(f"⚠️ {provider_name} Error: {r.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ {provider_name} Exception: {e}")
    return None

def _parse_ai_json(raw):
    """
    ✅ FIXED: Aggressively finds valid JSON { } and ignores 'Here is the JSON...' text.
    """
    import json
    import re

    try:
        # Regex to find the first JSON object enclosed in braces
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            clean_json = match.group(0)
            data = json.loads(clean_json)
        else:
            raise ValueError("No JSON brackets found")

        return {
            "headline": data.get("headline", "BREAKING NEWS").upper(),
            "image_info": data.get("image_info", "Details coming soon..."),
            "short_caption": data.get("short_caption", "TrendScope Update #News 🔥"),
            "search_keyword": data.get("search_keyword", "")
        }
    except Exception as e:
        logger.error(f"JSON Parse Failed: {e}. Raw text was: {raw[:50]}...")
        return _fallback_data_safe()

def _fallback_data_safe():
    return {
        "headline": "BREAKING NEWS",
        "image_info": "Latest updates on this developing story. Stay tuned for more details as information becomes available.",
        "short_caption": "Breaking Update 🔥 #News",
        "search_keyword": "breaking news studio"
    }

# ======================================================
# 6. NEWS ENGINE (Scoring & Fetching)
# ======================================================
# ======================================================
# HELPER FUNCTIONS (Must be below the main function)
# ======================================================

def _call_openai_compat(provider_name, url, key, model, prompt):
    """
    Generic caller for OpenAI-compatible APIs.
    Logs the provider name on success.
    """
    if not key: return None
    try:
        headers = {
            "Authorization": f"Bearer {key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trendscope.app", # For OpenRouter
            "X-Title": "TrendScope" # For OpenRouter
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 500
        }
        r = requests.post(f"{url}/chat/completions", headers=headers, json=data, timeout=15)
        
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            logger.info(f"🧠 AI WINNER: {provider_name}") # <--- Logs the specific winner
            return _parse_ai_json(content)
        else:
            logger.warning(f"⚠️ {provider_name} Error: {r.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ {provider_name} Exception: {e}")
    return None

def _parse_ai_json(raw):
    """
    ✅ FIXED: Aggressively finds valid JSON { } and ignores 'Here is the JSON...' text.
    """
    import json
    import re

    try:
        # 1. Regex to find the first JSON object enclosed in braces
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            clean_json = match.group(0)
            data = json.loads(clean_json)
        else:
            raise ValueError("No JSON brackets found")

        # 2. Validate Keys
        return {
            "headline": data.get("headline", "BREAKING NEWS").upper(),
            "image_info": data.get("image_info", "Details coming soon..."),
            "short_caption": data.get("short_caption", "TrendScope Update #News 🔥"),
            "search_keyword": data.get("search_keyword", "")
        }

    except Exception as e:
        logger.error(f"JSON Parse Failed: {e}. Raw text was: {raw[:50]}...")
        # If parsing fails, DO NOT return the raw text. Return safe defaults.
        return _fallback_data_safe()

def _fallback_data_safe():
    """
    ✅ FIXED: Returns generic safe text instead of garbage code.
    """
    return {
        "headline": "BREAKING NEWS",
        "image_info": "Latest updates on this developing story.\nStay tuned for more details.",
        "short_caption": "Breaking Update 🔥 #News",
        "search_keyword": "breaking news studio" # Ensures a safe image is found
    }

# Note: Remove the old _fallback_data(text) function entirely.
# ======================================================
# HELPER FUNCTIONS (Update this function in app.py)
# ======================================================

def _call_openai_compat(provider_name, url, key, model, prompt):
    """
    Generic caller for OpenAI-compatible APIs.
    Now accepts 'provider_name' (5th argument) to log who won.
    """
    if not key: return None
    try:
        headers = {
            "Authorization": f"Bearer {key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trendscope.app",
            "X-Title": "TrendScope"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 500
        }
        # Log who we are trying
        # logger.info(f"Trying {provider_name}...") 
        
        r = requests.post(f"{url}/chat/completions", headers=headers, json=data, timeout=15)
        
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            logger.info(f"🧠 AI WINNER: {provider_name}") # Logs the specific winner
            return _parse_ai_json(content)
        else:
            logger.warning(f"⚠️ {provider_name} Error: {r.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ {provider_name} Exception: {e}")
    return None

def _parse_ai_json(raw):
    """
    ✅ FIXED: Aggressively finds valid JSON { } and ignores 'Here is the JSON...' text.
    """
    import json
    import re

    try:
        # 1. Regex to find the first JSON object enclosed in braces
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            clean_json = match.group(0)
            data = json.loads(clean_json)
        else:
            raise ValueError("No JSON brackets found")

        # 2. Validate Keys
        return {
            "headline": data.get("headline", "BREAKING NEWS").upper(),
            "image_info": data.get("image_info", "Details coming soon..."),
            "short_caption": data.get("short_caption", "TrendScope Update #News 🔥"),
            "search_keyword": data.get("search_keyword", "")
        }

    except Exception as e:
        logger.error(f"JSON Parse Failed: {e}. Raw text was: {raw[:50]}...")
        # If parsing fails, DO NOT return the raw text. Return safe defaults.
        return _fallback_data_safe()

def _fallback_data_safe():
    """
    ✅ FIXED: Returns generic safe text instead of garbage code.
    """
    return {
        "headline": "BREAKING NEWS",
        "image_info": "Latest updates on this developing story.\nStay tuned for more details.",
        "short_caption": "Breaking Update 🔥 #News",
        "search_keyword": "breaking news studio" # Ensures a safe image is found
    }

# Note: Remove the old _fallback_data(text) function entirely.
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

from fallback_images import FALLBACK_IMAGES, get_fallback_image_url

import random


def extract_image(entry):
    # 1) RSS image
    if "media_content" in entry and entry.media_content:
        img = entry.media_content[0].get("url")
        if img:
            return img

    # 2) RSS thumbnail
    if "media_thumbnail" in entry and entry.media_thumbnail:
        img = entry.media_thumbnail[0].get("url")
        if img:
            return img

    # 3) enclosure links
    if "links" in entry:
        for l in entry.links:
            if l.get("type", "").startswith("image/"):
                return l.get("href")

    # ✅ Dynamic fallback
    return get_fallback_image_url("unsplash")

def fetch_news(filter_posted=False):
    global NEWS_CACHE
    NEWS_CACHE = {}
    out, i = [], 0
    
    posted_ids = load_posted() if filter_posted else set()
    
    for src, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:6]:
                # Filter posted
                if filter_posted and e.link in posted_ids:
                    continue
                
                # --- FIX: CLEAN HTML FROM SUMMARY ---
                raw_summary = e.get("summary", "")
                clean_text = clean_html(raw_summary)
                
                # If cleaning makes it empty (or it's just a link), use the Title instead
                if len(clean_text) < 20:
                    clean_text = e.title
                
                art = {
                    "id": i, 
                    "title": e.title, 
                    "summary": clean_text, # Now safe to use
                    "link": e.link, 
                    "image": extract_image(e),
                    "trend": ai_trending_score(e.title), 
                    "category": ai_category(e.title)
                }
                NEWS_CACHE[i] = art
                out.append(art)
                i += 1
        except Exception as e:
            continue
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

def post_to_instagram(local_image_path: str, caption: str):
    """
    FULL Instagram posting function with Cloudinary:
    ✅ Upload local image to Cloudinary
    ✅ Global limiter (post_limiter.py)
    ✅ IG cooldown file if blocked
    ✅ Cache buster to avoid repeated image
    ✅ Create + Publish
    ✅ Returns publish response
    """

    import time
    import random
    import json
    import os
    import requests

    # --- Global limiter ---
    from post_limiter import can_post_now, mark_posted_now

    # --- Cloudinary uploader (your existing function) ---
    # Uses: cloudinary.config(...) already defined globally
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

    # 1) global cooldown limiter check
    if not can_post_now():
        logger.warning("⏳ Global post limiter: skipping this post")
        return {"error": "rate_limit_global"}

    # 2) validate IG env
    if not IG_BUSINESS_ID or not PAGE_ACCESS_TOKEN:
        logger.error("❌ Missing IG_BUSINESS_ID or PAGE_ACCESS_TOKEN")
        return {"error": "missing_ig_config"}

    # 3) caption safety
    caption = (caption or "").strip()
    if not caption:
        caption = "🔥 Trending update"

    # 4) upload image to cloudinary
    public_url = upload_image_to_cloudinary(local_image_path)
    if not public_url:
        logger.error("❌ Cloudinary upload failed")
        return {"error": "cloudinary_upload_failed"}

    # 5) IG cooldown file
    COOLDOWN_FILE = "ig_cooldown.json"

    def load_cooldown():
        if not os.path.exists(COOLDOWN_FILE):
            return {"blocked_until": 0}
        try:
            with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"blocked_until": 0}

    def save_cooldown(data):
        try:
            with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except:
            pass

    cd = load_cooldown()
    now = int(time.time())
    blocked_until = int(cd.get("blocked_until", 0))

    if now < blocked_until:
        mins = int((blocked_until - now) / 60)
        logger.warning(f"⏳ IG cooldown active. {mins} min remaining.")
        return {"error": "cooldown_active", "blocked_until": blocked_until}

    # 6) Cache buster so IG will NOT reuse same cloudinary image
    cache_buster_url = f"{public_url}?v={random.randint(100000, 999999)}"

    # ------------------------------
    # STEP 1: CREATE MEDIA CONTAINER
    # ------------------------------
    try:
        create_res = requests.post(
            f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media",
            data={
                "image_url": cache_buster_url,
                "caption": caption,
                "access_token": PAGE_ACCESS_TOKEN
            },
            timeout=45
        ).json()
    except Exception as e:
        logger.error(f"IG CREATE EXCEPTION: {e}")
        return {"error": str(e)}

    # handle create errors
    if "error" in create_res:
        logger.error(f"IG CREATE ERROR: {create_res}")

        err = create_res.get("error", {})
        if err.get("code") == 4 or err.get("error_subcode") == 2207051:
            cd["blocked_until"] = int(time.time()) + 70 * 60
            save_cooldown(cd)
            logger.error("🚫 IG blocked. Cooling down for 60 minutes.")
        return create_res

    if "id" not in create_res:
        logger.error(f"IG CREATE ERROR (no id): {create_res}")
        return create_res

    creation_id = create_res["id"]

    # ------------------------------
    # STEP 2: WAIT FOR PROCESSING
    # ------------------------------
    time.sleep(20)

    # ------------------------------
    # STEP 3: PUBLISH MEDIA
    # ------------------------------
    try:
        publish_res = requests.post(
            f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": PAGE_ACCESS_TOKEN
            },
            timeout=45
        ).json()
    except Exception as e:
        logger.error(f"IG PUBLISH EXCEPTION: {e}")
        return {"error": str(e)}

    logger.info(f"PUBLISH RESPONSE: {publish_res}")

    # handle publish errors
    if "error" in publish_res:
        logger.error(f"❌ IG failed: {publish_res}")

        err = publish_res.get("error", {})
        if err.get("code") == 4 or err.get("error_subcode") == 2207051:
            cd["blocked_until"] = int(time.time()) + 60 * 60
            save_cooldown(cd)
            logger.error("🚫 IG blocked after publish. Cooling down.")
        return publish_res

    # ✅ mark posted now
    mark_posted_now()

    # ✅ return both cloudinary + IG publish
    return {
        "status": "success",
        "cloudinary_url": public_url,
        "ig_publish": publish_res
    }


def post_category_wise_news():
    global IS_POSTING_BUSY

    if IS_POSTING_BUSY:
        logger.info("Posting already running. Skipping...")
        return

    try:
        IS_POSTING_BUSY = True
        logger.info("🚜 RVCJ Engine Started...")

        news_items = fetch_news(filter_posted=True)

        # 🛑 CRITICAL FIX 1: Limit batch size
        # If the bot finds 10 new items, only take the top 3.
        # This prevents the "Machine Gun" effect that gets you banned.
        news_items = news_items[:3]

        for n in news_items:
            local_path = None # Keep track of file to delete it later
            try:
                # ---------------------------------------------------------
                # STEP 1: AI BRAIN (Get Content & Search Keyword)
                # ---------------------------------------------------------
                raw_text = n.get("summary", n.get("title", ""))
                data = ai_rvcj_converter(raw_text)
                
                search_term = data.get("search_keyword", n.get("title", ""))

                # ---------------------------------------------------------
                # STEP 2: SMART IMAGE SOURCING (Aggressive Mode)
                # ---------------------------------------------------------
                from fallback_images import get_image_url
                
                # 1. Get RSS Image
                rss_image = n.get("image") or extract_image(n)
                current_image_url = rss_image
                
                # 2. DECISION LOGIC: When to use AI Search?
                # We force search if:
                # - No RSS image
                # - RSS image is a tiny pixel/placeholder
                # - RSS image is not a proper URL
                # - OR randomly 30% of the time to get fresh AI images instead of boring stock photos
                
                should_search = False
                if not rss_image or "http" not in str(rss_image):
                    should_search = True
                elif "placeholder" in str(rss_image).lower() or "feedburner" in str(rss_image).lower():
                    should_search = True
                
                if should_search:
                    logger.info(f"🔍 RSS Image bad. Generating AI Image for: {search_term}")
                    current_image_url = get_image_url(search_term)

                # ---------------------------------------------------------
                # STEP 3: GENERATE NEWS CARD (Save Locally)
                # ---------------------------------------------------------
                img_name = f"post_{uuid.uuid4().hex}.png"
                
                local_path = generate_news_image(
                    headline=data.get("headline", "BREAKING NEWS"),
                    info_text=data.get("image_info", "Details inside..."),
                    image_url=current_image_url,
                    output_name=img_name
                )

                # ---------------------------------------------------------
                # STEP 4: UPLOAD TO CLOUDINARY
                # ---------------------------------------------------------
                public_url = upload_image_to_cloudinary(local_path)
                
                if not public_url:
                    logger.error("❌ Cloudinary upload failed, skipping item.")
                    continue

                # ---------------------------------------------------------
                # STEP 5: POST TO INSTAGRAM
                # ---------------------------------------------------------
                caption = data.get("short_caption") or data.get("headline") or "Trending 🔥"
                
                ig_res = post_to_instagram(public_url, caption)

                # ---------------------------------------------------------
                # STEP 6: HANDLE RESULT & SAVE TO SUPABASE
                # ---------------------------------------------------------
                if ig_res and "id" in ig_res:
                    mark_as_posted(n["link"])
                    logger.info(f"✅ Posted Successfully: {n.get('title')}")
                    
                    # 🛑 CRITICAL FIX 2: Sleep 5 minutes between posts
                    # This tells Instagram "I am a human, not a spam bot"
                    logger.info("💤 Sleeping 5 minutes to respect Instagram limits...")
                    time.sleep(300) 

                else:
                    logger.error(f"❌ IG failed: {ig_res}")

                    if isinstance(ig_res, dict) and ig_res.get("error") == "cooldown_active":
                        logger.warning("⏳ IG cooldown active. Stop this cycle.")
                        break

            except Exception as item_err:
                logger.error(f"Item processing error: {item_err}")
                continue
            
            finally:
                # ✅ CLEANUP: Remove local file
                if local_path and os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except:
                        pass

    except Exception as e:
        logger.error(f"post_category_wise_news global error: {e}")

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
    """
    Background worker:
    ✅ checks RSS and posts
    ✅ EXACT gap between cycles = 1 hour 10 mins
    ✅ prevents crashing loops
    ✅ respects quiet hours
    """

    GAP_SECONDS = 4200  # ✅ 1 hour 10 minutes

    while True:
        try:
            # quiet hours safety
            if is_quiet_hours():
                logger.warning("🌙 Quiet hours active. Worker sleeping 30 min.")
                time.sleep(1800)  # 30 minutes sleep during quiet hours
                continue

            logger.info("📰 RSS worker cycle started...")

            # ✅ this will automatically post only if not already posted
            post_category_wise_news()

            logger.info(f"✅ Worker sleeping for {GAP_SECONDS} seconds...")
            time.sleep(GAP_SECONDS)

        except Exception as e:
            logger.error(f"❌ Worker loop crashed: {e}")
            time.sleep(600)  # wait 10 min on crash







# ✅ 30 minutes gap between any social posts (Telegram/Twitter)
SOCIAL_LAST_POST_AT = 0
SOCIAL_POST_GAP_SECONDS = 70 * 60   # ✅ 30 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Full lifespan engine:
    ✅ ensures folders exist
    ✅ starts RSS worker thread
    ✅ starts Telegram loop thread
    ✅ converts telegram msgs to post
    ✅ generates image -> cloudinary -> instagram
    ✅ avoids repeated images using FALLBACK_IMAGES rotation
    """

    # ✅ Ensure output folder exists
    os.makedirs(os.path.join("images", "output"), exist_ok=True)

    # ✅ Start RSS worker thread
    threading.Thread(target=run_background_worker, daemon=True).start()
    logger.info("✅ RSS Background worker started")

    # ✅ Telegram handler
    async def on_telegram_event(text, source):
        """
        Runs whenever telegram message arrives.
        Converts it into RVCJ format & posts to IG.
        """
        try:
            text = (text or "").strip()
            if not text:
                return

            logger.info(f"✅ SOCIAL EVENT from {source}: {text[:80]}...")

            # ✅ quiet hours check (your existing feature)
            if is_quiet_hours():
                logger.warning("🌙 Quiet hours active. Skipping telegram post.")
                return

            # ✅ convert telegram text into viral format
            data = ai_rvcj_converter(text)

            # ✅ unique image name
            img_name = f"tg_{uuid.uuid4().hex}.png"

            # ✅ IMPORTANT:
            # Telegram message has no image, so use rotating fallback images
            bg_image_url = random.choice(FALLBACK_IMAGES)

            # ✅ generate image
            path = generate_news_image(
                headline=data.get("headline", "CRICKET UPDATE"),
                info_text=data.get("image_info", text[:120]),
                image_url=bg_image_url,
                output_name=img_name
            )

            # ✅ upload to cloudinary (YOUR FEATURE)
            public_url = upload_image_to_cloudinary(path)
            if not public_url:
                logger.error("❌ Cloudinary upload failed for Telegram post.")
                return

            # ✅ post to instagram (YOUR FEATURE)
            caption = data.get("short_caption") or data.get("headline") or "🔥"
            ig_res = post_to_instagram(public_url, caption)

            # ✅ if posted success
            if ig_res and isinstance(ig_res, dict) and "id" in ig_res:
                # Telegram does not have a URL like RSS
                # So we mark unique telegram signature into Supabase
                unique_key = f"telegram::{source}::{hash(text)}"
                mark_as_posted(unique_key)
                logger.info("✅ Telegram post uploaded successfully.")
            else:
                logger.error(f"❌ Telegram IG failed: {ig_res}")

        except Exception as e:
            logger.error(f"❌ Telegram handler error: {e}")

    # ✅ Telegram runner in background thread
    def tg_runner():
        try:
            asyncio.run(telegram_fetch_loop(on_telegram_event, logger))
        except Exception as e:
            logger.error(f"Telegram engine crashed: {e}")

    threading.Thread(target=tg_runner, daemon=True).start()
    logger.info("✅ Telegram thread started")

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