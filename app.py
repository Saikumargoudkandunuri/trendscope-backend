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
from datetime import datetime
from contextlib import asynccontextmanager

import cloudinary
import cloudinary.uploader
from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

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

def load_posted():
    if not os.path.exists(POSTED_FILE): return set()
    try:
        with open(POSTED_FILE, "r") as f: return set(json.load(f))
    except: return set()

def save_posted(ids):
    with open(POSTED_FILE, "w") as f: json.dump(list(ids), f)

def is_quiet_hours():
    """Logic to stop posting between 1 AM and 6 AM IST"""
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
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
    """Converts boring news into viral Hinglish RVCJ Style"""
    prompt = f"""
    Act as an RVCJ Instagram Content Creator. 
    Convert this news into Hinglish (Mixed Hindi and English).
    Return ONLY a JSON object:
    {{
      "headline": "Viral Hinglish headline (MAX 10 words, e.g. 'Bhaari Nuksan!')",
      "description": "Engaging Hinglish story (MAX 30 words, start with 'Dosto...')"
    }}
    News: {text}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return {
            "headline": "🚨 BIG BREAKING NEWS!", 
            "description": f"Dosto, badi khabar aa rahi hai: {text[:50]}... Stay tuned! 🔥"
        }

# Aliases to prevent website crashes
def ai_short_news(text):
    return ai_rvcj_converter(text)['headline']

def ai_caption(text):
    return ai_rvcj_converter(text)['description']

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

def fetch_news():
    global NEWS_CACHE
    NEWS_CACHE = {}
    out, i = [], 0
    for src, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:6]:
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

# ======================================================
# 7. INSTAGRAM & AUTO-POST CORE
# ======================================================

def post_to_instagram(image_url, caption):
    # Step 1: Create Container
    res = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": PAGE_ACCESS_TOKEN}
    ).json()
    
    if "id" not in res: return res

    # Step 2: Critical Wait for Image Processing
    time.sleep(45)

    # Step 3: Publish
    return requests.post(
        f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media_publish",
        data={"creation_id": res["id"], "access_token": PAGE_ACCESS_TOKEN}
    ).json()

def post_category_wise_news():
    global IS_POSTING_BUSY
    if IS_POSTING_BUSY or is_quiet_hours():
        logger.info("Engine Paused: Busy or Quiet Hours (1AM-6AM IST)")
        return

    try:
        IS_POSTING_BUSY = True
        logger.info("🚜 RVCJ Engine Waking Up...")
        news_items = fetch_news()
        posted_ids = load_posted()
        
        for n in news_items:
            if n["link"] in posted_ids: continue

            try:
                # 1. RVCJ Hinglish Conversion
                data = ai_rvcj_converter(n.get("summary", n["title"]))
                
                # 2. Generate Unique Filename (UUID FIX)
                unique_name = f"rvcj_{uuid.uuid4().hex}.png"

                # 3. Build Image
                path = generate_news_image(data['headline'], n["image"], unique_name)

                # 4. Upload & Post
                url = upload_image_to_cloudinary(path)
                ig_res = post_to_instagram(url, data['description'])

                if "id" in ig_res:
                    posted_ids.add(n["link"])
                    save_posted(posted_ids)
                    if os.path.exists(path): os.remove(path)
                    logger.info(f"✅ RVCJ SUCCESS: {data['headline']}")
                    # Natural gap to prevent Instagram Shadowban
                    time.sleep(1200) 
                else:
                    logger.error(f"IG Post Error: {ig_res}")

            except Exception as e:
                logger.error(f"Item process error: {e}")
                continue
    finally:
        IS_POSTING_BUSY = False

# ======================================================
# 8. BACKGROUND WORKER & LIFESPAN
# ======================================================

def run_background_worker():
    while True:
        try:
            # Check for news every 5 minutes (300 seconds)
            post_category_wise_news()
            time.sleep(300) 
        except: time.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Render doesn't crash if folder is missing
    os.makedirs(os.path.join("images", "output"), exist_ok=True)
    # Start the engine thread
    threading.Thread(target=run_background_worker, daemon=True).start()
    yield

app = FastAPI(lifespan=lifespan)

# ======================================================
# 9. WEBSITE HTML PAGES (The Original 600-line UI)
# ======================================================

@app.get("/", response_class=HTMLResponse)
def home(category: str = Query(None)):
    news = fetch_news()
    news.sort(key=lambda x: x["trend"], reverse=True)
    if category:
        news = [n for n in news if n["category"] == category]

    flash = news[:5]

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
    news_list = fetch_news()
    item = next((n for n in news_list if n["id"] == i), None)
    if not item: return "<h3>News not found</h3>"

    rvcj = ai_rvcj_converter(item["summary"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin:0; font-family: Arial; background:#0d47a1; color:white; }}
            .container {{ padding:16px; }}
            .card {{ background:white; color:black; padding:16px; border-radius:14px; }}
            img {{ width:100%; border-radius:12px; margin-bottom:12px; }}
            .title {{ font-size:20px; font-weight:bold; margin-bottom:10px; color:#1a237e; }}
            .label {{ font-weight:bold; margin-top:14px; color:#555; font-size:12px; }}
            .box {{ background:#f1f3f6; padding:10px; border-radius:8px; margin-top:6px; line-height:1.5; border-left:4px solid #0d47a1; }}
            .btn {{ width:100%; padding:12px; margin-top:12px; border:none; border-radius:10px; font-size:16px; font-weight:bold; cursor:pointer; }}
            .read {{ background:#ff9800; color:white; }}
            .share {{ background:#1e88e5; color:white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" style="color:white; text-decoration:none; font-weight:bold;">⬅ Back</a>
            <div class="card" style="margin-top:15px">
                <img src="{item['image']}">
                <div class="title">{rvcj['headline']}</div>
                <div class="label">📸 RVCJ STORY (HINGLISH)</div>
                <div class="box">{rvcj['description']}</div>
                <button class="btn share" onclick="navigator.share({{title:'{rvcj['headline']}', url:'{item['link']}'}})">🔗 Share News</button>
                <button class="btn read" onclick="window.open('{item['link']}', '_blank')">Read Full Article</button>
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
    threading.Thread(target=post_category_wise_news).start()
    return {"status": "success"}

@app.get("/login", response_class=HTMLResponse)
def login():
    return "<h2 style='padding:20px'>Login (Coming Soon)</h2><a href='/'>Back</a>"