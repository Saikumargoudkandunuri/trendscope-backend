from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import feedparser, re
import requests
import os
from dotenv import load_dotenv

# ================== NEW (Instagram config) ==================
load_dotenv()

IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
# ============================================================

app = FastAPI()

NEWS_CACHE = {}

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
}

def ai_short_news(text):
    words = re.findall(r"\w+", text)
    return " ".join(words[:22]) + "."

def ai_caption(text):
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

# ================== NEW (Instagram helper) ==================
def post_to_instagram(image_url: str, caption: str):
    # Step 1: create media
    media_res = requests.post(
        f"https://graph.facebook.com/v24.0/{IG_BUSINESS_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": PAGE_ACCESS_TOKEN
        }
    ).json()

    if "id" not in media_res:
        return {"error": media_res}

    creation_id = media_res["id"]

    # Step 2: publish media
    publish_res = requests.post(
        f"https://graph.facebook.com/v24.0/{IG_BUSINESS_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": PAGE_ACCESS_TOKEN
        }
    ).json()

    return publish_res
# ============================================================

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
</style>
</head>
<body>

<div class="header">
<b>TrendScope 🇮🇳</b>
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

</body>
</html>
"""

@app.get("/news/{i}", response_class=HTMLResponse)
def news(i: int):
    news = fetch_news()
    item = next((n for n in news if n["id"] == i), None)

    if not item:
        return "<h3>News not found</h3>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])

    return f"""
    <html>
    <body style="font-family:Arial;padding:16px">
        <h3>{item['title']}</h3>
        <img src="{item['image']}" style="width:100%;border-radius:10px">
        <p><b>Short:</b> {short}</p>
        <p><b>Instagram Caption:</b><br>{caption}</p>
        <button onclick="postToIG()">🚀 Post to Instagram</button>

        <script>
        function postToIG(){{
            fetch("/instagram/post", {{
                method:"POST",
                headers:{{"Content-Type":"application/json"}},
                body: JSON.stringify({{
                    imageUrl: "{item['image']}",
                    caption: `{caption}`
                }})
            }).then(r=>r.json()).then(alert);
        }}
        </script>
    </body>
    </html>
    """

# ================== NEW (Instagram API endpoint) ==================
@app.post("/instagram/post")
def instagram_post(data: dict):
    image_url = data.get("imageUrl")
    caption = data.get("caption")

    if not image_url or not caption:
        return JSONResponse({"error": "Missing image or caption"}, status_code=400)

    result = post_to_instagram(image_url, caption)
    return result
# ============================================================
