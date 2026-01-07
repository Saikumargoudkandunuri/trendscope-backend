print("APP.PY LOADED FROM:", __file__)

# --- 1. ALL IMPORTS FIRST ---
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

from image_generator import generate_news_image

# --- 2. LOAD CONFIGURATION ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
api_key_val = os.getenv("GEMINI_API_KEY")

# Initialize the client with the explicit key
client = genai.Client(api_key=api_key_val)
logger = logging.getLogger("uvicorn.error")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
# --- MISSING CLOUDINARY UPLOAD FUNCTION ---

def upload_image_to_cloudinary(local_path):
    try:
        # We use 'use_filename=True' to help with SEO and Meta crawling
        res = cloudinary.uploader.upload(
            local_path, 
            folder="trendscope",
            resource_type="image",
            access_mode="public" # 🚨 CRITICAL: Forces the image to be public
        )
        
        public_url = res.get("secure_url") # 🚨 Use secure_url for HTTPS
        print(f"DEBUG: Cloudinary Image URL -> {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Cloudinary Error: {e}")
        return None
# Change the client initialization at the top to this:

IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# --- 3. GLOBAL VARIABLES ---
# --- 3. GLOBAL VARIABLES ---
NEWS_CACHE = {}
IS_POSTING_BUSY = False 
POSTED_FILE = "posted.json"

# Ensure the dictionary is opened with { and every line ends with a comma
RSS_SOURCES = {
    "GoogleLive": "https://news.google.com/rss/search?q=when:1h+breaking+news+India&hl=en-IN&gl=IN&ceid=IN:en",
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
}

POST_CONFIG = {"Sports": 1, "Business": 1, "Tech": 1}

# --- 4. THE LIFESPAN FUNCTION ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This creates the folder on Render to prevent "Directory not found" errors
    os.makedirs(os.path.join("images", "output"), exist_ok=True)
    # This starts your background worker automatically
    threading.Thread(target=run_background_worker, daemon=True).start()
    yield

# --- 5. DEFINE THE APP (CRITICAL: MUST BE ABOVE ALL @APP ROUTES) ---
app = FastAPI(lifespan=lifespan)

# --- 6. NOW YOU CAN START YOUR ROUTES ---
class ImageRequest(BaseModel):
    headline: str
    description: str
    image_url: str | None = None

@app.post("/api/generate-image")
def api_generate_image(data: ImageRequest):
    # This code MUST be indented (pushed to the right)
    filename = f"{uuid.uuid4().hex}.png"
    path = generate_news_image(
        headline=data.headline,
        description=data.description,
        image_url=data.image_url or "",
        output_name=filename
    )
    return {
        "status": "success",
        "image_path": path
    }

# This line should NOT be indented (it is outside the function)
POST_DELAY_SECONDS = 900

# ======================================================

POSTED_FILE = "posted.json"

# --- HELPERS ---
def load_posted():
    if os.path.exists(POSTED_FILE):
        try:
            with open(POSTED_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def save_posted(ids):
    with open(POSTED_FILE, "w") as f: json.dump(list(ids), f)

def is_quiet_hours():
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    return 1 <= now.hour < 6

# --- MISSING NEWS LOGIC ---

def ai_category(text):
    t = text.lower()
    if any(k in t for k in ["cricket", "ipl", "score", "match"]): return "Sports"
    if any(k in t for k in ["market", "sensex", "nifty", "economy"]): return "Business"
    if any(k in t for k in ["tech", "ai", "iphone", "google"]): return "Tech"
    return "India"

def ai_trending_score(title):
    # Basic logic to give a trend percentage
    return min(95, 40 + sum(k in title.lower() for k in ["india","court","modi","cricket"]) * 10)

def extract_image(entry):
    # Try to find an image in the RSS feed entry
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c"

def fetch_news():
    global NEWS_CACHE
    NEWS_CACHE = {}
    out, i = [], 0
    # Make sure RSS_SOURCES is defined at the top of your file
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
        except Exception as e:
            logger.error(f"Error fetching from {src}: {e}")
            continue
    return out



def ai_caption(text):
    prompt = f"""
    Rewrite this news for an Instagram Breaking News alert.
    
    INSTRUCTIONS:
    - Language: Simple, easy, NO jargon.
    - Start: Use '🚨 BREAKING' or '🚨 JUST IN'.
    - Tone: Emotional and urgent.
    - Limit: 15-20 words total.
    
    Original News: {text}
    """
    try:
        res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return res.text.strip().replace('"', '') # Removes quotes
    except:
        return f"🚨 JUST IN: {text[:50]}... Stay tuned for updates! #IndiaNews"

        
def ai_instagram_rewrite(text):
    """The main RVCJ-style engine"""
    prompt = f"""
    Rewrite this news in the style of RVCJ Instagram.
    RULES:
    1. Start with a viral hook: 🚨 BIG BREAKING, 🔥 TRENDING, or 😱 DID YOU KNOW?
    2. Use short, punchy, emotional sentences.
    3. NO JARGON. Use simple language.
    4. Max 18 words total.
    
    News: {text}
    """
    try:
        res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return res.text.strip().replace('"', '')
    except Exception as e:
        logger.error(f"AI Rewrite Error: {e}")
        return f"🚨 BIG BREAKING: {text[:50]}..."

# These two aliases ensure your website routes don't crash
def ai_short_news(text):
    return ai_instagram_rewrite(text)

def ai_caption(text):
    return ai_instagram_rewrite(text)

# --- CORE LOGIC ---
def post_category_wise_news():
    global IS_POSTING_BUSY
    if IS_POSTING_BUSY or is_quiet_hours():
        return
    try:
        IS_POSTING_BUSY = True
        news = fetch_news()
        posted_ids = load_posted()
        
        for n in news:
            if n["link"] in posted_ids: continue

            # 🚨 STEP 1: Generate AI Breaking News Style Content
            # This follows your request: Short, Emotional, No Jargon
            breaking_headline = n["title"].split('|')[0].upper() # Clean the title
            insta_style_desc = ai_instagram_rewrite(n["summary"]) 

            # 🚨 STEP 2: Generate Image
            # Generate a unique filename using uuid
            filename = f"post_{uuid.uuid4().hex}.png"
            local_img_path = generate_news_image(
                headline=breaking_headline,
                description=insta_style_desc,
                image_url=n["image"],
                output_name=filename
            )

            # Check if file exists before uploading
            if os.path.exists(local_img_path):
                # 🚨 STEP 3: Upload to Cloudinary
                # Make sure this function returns the 'secure_url'
                public_url = upload_image_to_cloudinary(local_img_path)
                
                # 🚨 STEP 4: Post to Instagram
                caption = f"{insta_style_desc}\n\n#BreakingNews #India #TrendScope"
                ig_res = post_to_instagram(public_url, caption)

                if "id" in ig_res:
                    posted_ids.add(n["link"])
                    save_posted(posted_ids)
                    logger.info(f"✅ Success: {n['title']}")
                    
                    # Cleanup local file to save space on Render
                    os.remove(local_img_path)
                    
                    time.sleep(1200) # 20 min gap
            else:
                logger.error(f"Image File Not Found: {local_img_path}")

    finally:
        IS_POSTING_BUSY = False



import requests

IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

def post_to_instagram(image_url, caption):
    # STEP 1: Create media container
    create_res = requests.post(
        f"https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": PAGE_ACCESS_TOKEN
        }
    ).json()

    logger.info(f"CREATE RESPONSE: {create_res}")

    if "id" not in create_res:
        print("Error creating media:", create_res)
        return create_res

    creation_id = create_res["id"]

    # STEP 2: WAIT for Meta to process the image (Crucial!)
    # Give it 30 seconds to download and process your Cloudinary URL
    time.sleep(30)

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



class ImageRequest(BaseModel):
    headline: str
    description: str
    image_url: str | None = None

@app.post("/api/generate-image")
def api_generate_image(data: ImageRequest):
    filename = f"{uuid.uuid4().hex}.png"

    path = generate_news_image(
        headline=data.headline,
        description=data.description,
        image_url=data.image_url or "",
        output_name=filename
    )

    return {
        "status": "success",
        "image_path": path
    }
    

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
html, body {{
    margin:0;
    padding:0;
    width:100%;
    overflow-x:hidden;
    font-family:Arial;
    background:#f1f3f6;
}}

a {{ text-decoration:none; color:black; }}

.header {{
    background:#131921;
    color:white;
    padding:12px;
    display:flex;
    justify-content:space-between;
}}

.category {{
    background:#232f3e;
    padding:10px;
    white-space:nowrap;
    overflow-x:auto;
}}

.category a {{
    color:white;
    margin-right:12px;
    font-weight:bold;
}}

.flash-box {{
    background:white;
    margin:10px;
    padding:10px;
    border-radius:12px;
}}

.flash-row {{
    display:flex;
    gap:10px;
    overflow-x:auto;
}}

.flash-card {{
    flex:0 0 260px;
}}

.flash-card img {{
    width:100%;
    height:140px;
    object-fit:cover;
    border-radius:8px;
}}

.card {{
    background:white;
    margin:10px;
    padding:12px;
    border-radius:10px;
}}

.trend {{
    float:right;
    color:#ff5722;
    font-weight:bold;
}}

.overlay {{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.4);
    display:none;
    z-index:9;
}}

.menu {{
    position:fixed;
    top:0;
    right:0;
    width:260px;
    height:100%;
    background:white;
    padding:20px;
    transform: translateX(100%); /* 🔥 REAL FIX */
    transition: transform 0.3s ease;
    z-index:10;
}}

.menu.open {{
    transform: translateX(0);
}}

.menu button {{
    width:100%;
    padding:10px;
    margin-top:10px;
}}
</style>

<script>
function toggleMenu(){{
  const m=document.getElementById('menu');
  const o=document.getElementById('overlay');
  m.classList.toggle('open');
  o.style.display=m.classList.contains('open')?'block':'none';
  document.body.style.overflow=m.classList.contains('open')?'hidden':'auto';
}}
</script>
</head>

<body>
<div id="overlay" class="overlay" onclick="toggleMenu()"></div>

<div class="header">
<b>TrendScope 🇮🇳</b>
<span onclick="toggleMenu()">☰</span>
</div>

<div class="category">
<a href="/">All</a>
<a href="/?category=India">India</a>
<a href="/?category=Tech">Tech</a>
<a href="/?category=Business">Business</a>
<a href="/?category=Sports">Sports</a>
</div>

<div class="flash-box">
<b>🔥 Flash News</b>
<div class="flash-row">
{''.join(f"<div class='flash-card'><a href='{f['link']}' target='_blank'><img src='{f['image']}'><p>{f['title']}</p></a></div>" for f in flash)}
</div>
</div>

{''.join(f"<div class='card'><a href='/news/{n['id']}'>{n['title']}</a><span class='trend'>🔥 {n['trend']}%</span></div>" for n in news)}

<div id="menu" class="menu">
<button onclick="location.href='/login'">Login</button>
<button>Language</button>
<button>Notifications</button>
</div>

</body>
</html>
"""

@app.get("/login", response_class=HTMLResponse)
def login():
    return "<h2 style='padding:20px'>Login (UI only)</h2><a href='/'>Back</a>"

@app.get("/news/{i}", response_class=HTMLResponse)
def news(i: int):
    news = fetch_news()
    item = None

    for n in news:
        if n["id"] == i:
            item = n
            break

    if not item:
        return "<h3>News not found</h3>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin:0;
                font-family: Arial;
                background:#0d47a1;
                color:white;
            }}
            .container {{
                padding:16px;
            }}
            .card {{
                background:white;
                color:black;
                padding:16px;
                border-radius:14px;
            }}
            img {{
                width:100%;
                border-radius:12px;
                margin-bottom:12px;
            }}
            .title {{
                font-size:20px;
                font-weight:bold;
                margin-bottom:10px;
            }}
            .label {{
                font-weight:bold;
                margin-top:14px;
            }}
            .box {{
                background:#f1f3f6;
                padding:10px;
                border-radius:8px;
                margin-top:6px;
            }}
            .btn {{
                width:100%;
                padding:12px;
                margin-top:12px;
                border:none;
                border-radius:10px;
                font-size:16px;
            }}
            .read {{
                background:#ff9800;
                color:black;
            }}
            .share {{
                background:#1e88e5;
                color:white;
            }}
            a {{
                color:white;
                text-decoration:none;
                display:inline-block;
                margin-bottom:12px;
            }}
        </style>

        <script>
            function shareNews() {{
                if (navigator.share) {{
                    navigator.share({{
                        title: "{item['title']}",
                        text: "{caption}",
                        url: "{item['link']}"
                    }});
                }} else {{
                    alert("Sharing not supported on this browser");
                }}
            }}
        </script>
    </head>

    <body>
        <div class="container">
            <a href="/">⬅ Back</a>

            <div class="card">
                <img src="{item['image']}">

                <div class="title">{item['title']}</div>

                <div class="label">📰 Short News</div>
                <div class="box">{short}</div>

                <div class="label">📸 Instagram Caption</div>
                <div class="box">{caption}</div>

                <button class="btn share" onclick="shareNews()">🔗 Share</button>
                <button class="btn read" onclick="window.open('{item['link']}', '_blank')">
                    Read Full News
                </button>
            </div>
        </div>
    </body>
    </html>
    """





@app.get("/admin", response_class=HTMLResponse)
def admin():
    return """
    <html>
    <body style="font-family:Arial;padding:20px">
        <h2>TrendScope Admin</h2>
        <button onclick="post()">Post Top News Now</button>

        <script>
        function post(){
            fetch("/instagram/post",{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({
                    imageUrl:"https://raw.githubusercontent.com/github/explore/main/topics/instagram/instagram.png",
                    caption:"Manual admin post 🚀"
                })
            }).then(r=>r.json()).then(alert);
        }
        </script>
    </body>
    </html>
    """


# --- WORKER THREAD ---
def run_background_worker():
    while True:
        try:
            # Check for news every 5 minutes (300 seconds)
            post_category_wise_news()
            logger.info("Sleeping 5 minutes...")
            time.sleep(300) 
        except Exception as e:
            logger.error(f"Worker Exception: {e}")
            time.sleep(60) # Wait 1 min if error

@app.get("/cron/hourly")
def cron():
    threading.Thread(target=post_category_wise_news).start()
    return {"status": "Manual post cycle triggered"}