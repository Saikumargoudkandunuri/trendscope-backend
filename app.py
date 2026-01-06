print("APP.PY LOADED FROM:", __file__)
# 1. Standard Library Imports (Built-in Python modules)
import json
import logging
import os
import random
import re
import threading
import time
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

# 2. Third-Party Library Imports (Installed via pip)
import cloudinary
import cloudinary.uploader
import feedparser
from google import genai  # Import the new SDK
import pytz
import requests  # Required for Instagram API calls
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# 3. Local Application Imports (Your own files)
from image_generator import generate_news_image

logger = logging.getLogger("uvicorn.error")

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
def upload_image_to_cloudinary(local_path):
    res = cloudinary.uploader.upload(local_path, folder="trendscope")
    return res["secure_url"]



GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the new client
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


app = FastAPI()

NEWS_CACHE = {}

IS_POSTING_BUSY = False

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
}

def ai_short_news(text):
    try:
        if not GEMINI_API_KEY:
            raise Exception("No Gemini key")

        prompt = f"Summarize this Indian news in 15-20 simple words:\n{text}"
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)

        if not res or not res.text:
            raise Exception("Empty Gemini response")

        return res.text.strip()

    except Exception as e:
        # SAFE FALLBACK (never crash UI)
        words = re.findall(r"\w+", text)
        return " ".join(words[:22]) + "."

def ai_caption(text):
    try:
        if not GEMINI_API_KEY:
            raise Exception("No Gemini key")

        prompt = (
            "Write a short Instagram caption (max 2 lines) for this Indian news. "
            "Add 3 relevant hashtags.\n\nNews:\n" + text
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)

        if not res or not res.text:
            raise Exception("Empty Gemini response")

        return res.text.strip()

    except Exception:
        return ai_short_news(text) + "\n\n#IndiaNews"


def ai_category(text):
    t = text.lower()
    if "cricket" in t: return "Sports"
    if "market" in t: return "Business"
    if "tech" in t or "ai" in t: return "Tech"
    return "India"

def ai_trending_score(title):
    return min(95, 40 + sum(k in title.lower() for k in ["india","court","market","cricket"]) * 10)

def extract_image(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    return "https://via.placeholder.com/400x200?text=News"

def fetch_news():
    global NEWS_CACHE
    NEWS_CACHE = {}
    out, i = [], 0
    for src, url in RSS_SOURCES.items():
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
    return out
# ================== AUTO POST CONFIG ==================

POST_CONFIG = {
    "Sports": 1,
    "Business": 1,
    "Tech": 1,
}

POST_DELAY_SECONDS = 900  # gap between posts to avoid spam

# ======================================================

POSTED_FILE = "posted.json"

def load_posted_ids():
    if not os.path.exists(POSTED_FILE):
        return set()
    try:
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_posted_ids(ids):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(ids), f)


def is_quiet_hours_ist():
    """Returns True if current time is between 1 AM and 6 AM IST"""
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    # Check if hour is 1, 2, 3, 4, or 5
    if 1 <= now_ist.hour < 6:
        return True
    return False

def post_category_wise_news():
    global IS_POSTING_BUSY
    
    # Check if another process is already working
    if IS_POSTING_BUSY:
        logger.info("⚠️ Already posting... skipping this cycle.")
        return
        
    if is_quiet_hours_ist():
        logger.info("🌙 Quiet hours (1AM-6AM IST).")
        return

    try:
        IS_POSTING_BUSY = True # LOCK
        news = fetch_news()
        posted_ids = load_posted_ids()
        
        for category, limit in POST_CONFIG.items():
            items = [n for n in news if n["category"] == category]
            items = sorted(items, key=lambda x: x["trend"], reverse=True)[:limit]

            for n in items:
                if n["link"] in posted_ids:
                    continue

                try:
                    # ... (image generation & cloudinary code) ...
                    
                    ig_res = post_to_instagram(public_url, caption)
                    
                    if "id" in ig_res:
                        # ✅ SAVE IMMEDIATELY BEFORE SLEEPING
                        posted_ids.add(n["link"])
                        save_posted_ids(posted_ids)
                        logger.info(f"✅ Success! ID saved. {n['title']}")

                        # Wait between posts
                        delay = random.randint(900, 1800)
                        logger.info(f"🕒 Waiting {delay//60} mins...")
                        time.sleep(delay)
                
                except Exception as e:
                    logger.error(f"Item error: {e}")
                    
    finally:
        IS_POSTING_BUSY = False # UNLOCK




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
@app.get("/cron/hourly")
def hourly_cron():
    # Trigger the function manually via URL
    thread = threading.Thread(target=post_category_wise_news)
    thread.start()
    return {"status": "Post process started in background"}




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


# Create a function to run the loop
def run_background_worker():
    print("🚀 Background Worker Thread Started")
    while True:
        try:
            post_category_wise_news()
        except Exception as e:
            print(f"Worker Error: {e}")
        
        # Wait 1 hour (3600 seconds)
        time.sleep(3600)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs ON STARTUP
    thread = threading.Thread(target=run_background_worker, daemon=True)
    thread.start()
    print("🚀 Background Worker Started via Lifespan")
    yield
    # This runs ON SHUTDOWN (optional)
    print("🛑 Application Shutting Down")

# Update your FastAPI initialization line near the top:
app = FastAPI(lifespan=lifespan)