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
    prompt = f"""
    Act as an RVCJ Instagram Creator. Convert this news into Hinglish.
    Return ONLY a JSON object:
    {{
      "headline": "Short viral Hinglish headline (MAX 10 words)",
      "description": "Engaging Hinglish story (MAX 30 words, start with 'Dosto...')"
    }}
    News: {text}
    """

    # --- BRAIN 1: GOOGLE GEMINI (Primary) ---
    try:
        res = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(res.text)
    except Exception as e:
        logger.warning(f"Gemini failed, switching to Groq... Error: {e}")

    # --- BRAIN 2: GROQ (Backup 1 - Llama 3) ---
    if GROQ_API_KEY:
        try:
            groq_client = openai.OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Groq failed, switching to OpenRouter... Error: {e}")

    # --- BRAIN 3: OPENROUTER (Backup 2 - Free Models) ---
    if OPENROUTER_API_KEY:
        try:
            or_client = openai.OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
            res = or_client.chat.completions.create(
                model="meta-llama/llama-3.2-3b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            # Find the JSON block in the text
            json_text = re.search(r'\{.*\}', res.choices[0].message.content, re.DOTALL).group()
            return json.loads(json_text)
        except Exception as e:
            logger.error(f"All AI brains failed! Error: {e}")

    # --- EMERGENCY FALLBACK (No AI needed) ---
    return {
        "headline": "🚨 BIG BREAKING NEWS",
        "description": f"Dosto, badi khabar aa rahi hai. Details ke liye swipe karein! {text[:50]}..."
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

# ======================================================
# 7. INSTAGRAM & AUTO-POST CORE
# ======================================================

def post_to_instagram(image_url, caption):
    # FIX: Add a Cache Buster to the image URL
    # This prevents Instagram from showing a previous post's image
    cache_buster = f"{image_url}?v={random.randint(10000, 99999)}"
    
    logger.info(f"Uploading to Meta with Cache Buster: {cache_buster}")

    # STEP 1: Create media container
    create_res = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media",
        data={
            "image_url": cache_buster, # Use the busted URL here
            "caption": caption,
            "access_token": PAGE_ACCESS_TOKEN
        }
    ).json()

    if "id" not in create_res:
        logger.error(f"CREATE ERROR: {create_res}")
        return create_res

    creation_id = create_res["id"]

    # STEP 2: WAIT for Meta to process the image
    # We use 45 seconds to be safe on Render's network
    time.sleep(45)

    # STEP 3: Publish media
    publish_res = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": PAGE_ACCESS_TOKEN
        }
    ).json()

    logger.info(f"PUBLISH RESPONSE: {publish_res}")
    return publish_res

def post_category_wise_news():
    global IS_POSTING_BUSY
    if IS_POSTING_BUSY or is_quiet_hours():
        return

    try:
        IS_POSTING_BUSY = True
        logger.info("🚜 RVCJ Engine Started...")
        
        # 🚨 FIX: Fetch ONLY news that hasn't been posted yet
        news_items = fetch_news(filter_posted=True)
        
        for n in news_items:
            try:
                # 🚨 FIX: Corrected function name from ai_rvcj_style to ai_rvcj_converter
                data = ai_rvcj_converter(n.get("summary", n["title"]))
                
                unique_filename = f"rvcj_{uuid.uuid4().hex}.png"
                image_path = generate_news_image(
                    headline=data['headline'],
                    image_url=n["image"],
                    output_name=unique_filename
                )

                public_url = upload_image_to_cloudinary(image_path)
                if not public_url: continue

                # Post to Instagram
                cache_buster_url = f"{public_url}?v={random.randint(1000, 9999)}"
                ig_res = post_to_instagram(cache_buster_url, data['description'])

                if "id" in ig_res:
                    mark_as_posted(n["link"])
                    logger.info(f"✅ Posted Success: {data['headline']}")
                    if os.path.exists(image_path): os.remove(image_path)
                    
                    # Wait 20 mins between posts
                    time.sleep(1200) 
                else:
                    logger.error(f"IG Error: {ig_res}")

            except Exception as e:
                logger.error(f"Item error: {e}")
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