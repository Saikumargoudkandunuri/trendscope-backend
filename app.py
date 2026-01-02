from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import requests
import feedparser
import hashlib
from datetime import datetime, timezone

app = FastAPI()

NEWS_API_KEY = "5b8cdcf858a1405b87ac7fbe53ae86f6"

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news"
}

# ---------------- AI LOGIC ----------------

def ai_short_summary(title):
    words = title.split()
    return " ".join(words[:8]) + "…"

def ai_instagram_caption(title, source):
    return f"{title}\n\n🔥 Breaking | Source: {source}\n#news #trending #viral #india"

# ---------------- FETCH NEWS ----------------

def fetch_news():
    news = []
    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:15]:
            uid = hashlib.md5(e.title.encode()).hexdigest()
            news.append({
                "id": uid,
                "title": e.title,
                "summary": e.get("summary", ""),
                "link": e.link,
                "source": source,
                "published": datetime.now(timezone.utc)
            })
    return news

# ---------------- HOME PAGE ----------------

@app.get("/page", response_class=HTMLResponse)
def home():
    news = fetch_news()

    cards = ""
    for n in news:
        cards += f"""
        <div class="card" onclick="openNews('{n['id']}')">
            <h2>{n['title']}</h2>
            <span class="src">{n['source']}</span>
        </div>
        """

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background:#0f172a;color:#e5e7eb;font-family:Inter;margin:0 }}
            header {{ padding:16px;text-align:center;font-size:22px;font-weight:700;background:#020617 }}
            .container {{ padding:14px }}
            .card {{
                background:#020617;
                padding:16px;
                border-radius:14px;
                margin-bottom:12px;
                cursor:pointer;
            }}
            h2 {{ font-size:17px }}
            .src {{ font-size:12px;color:#94a3b8 }}
        </style>
        <script>
            function openNews(id) {{
                window.location = "/news?id=" + id;
            }}
        </script>
    </head>
    <body>
        <header>TrendScope</header>
        <div class="container">{cards}</div>
    </body>
    </html>
    """

# ---------------- DETAIL PAGE ----------------

@app.get("/news", response_class=HTMLResponse)
def news_detail(id: str):
    news = fetch_news()
    item = next((n for n in news if n["id"] == id), None)

    if not item:
        return "<h3>News not found</h3>"

    short = ai_short_summary(item["title"])
    caption = ai_instagram_caption(item["title"], item["source"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background:#0f172a;color:#e5e7eb;font-family:Inter;margin:0 }}
            header {{ padding:16px;text-align:center;font-size:20px;font-weight:700;background:#020617 }}
            .box {{ padding:16px }}
            .card {{
                background:#020617;
                padding:16px;
                border-radius:14px;
                margin-bottom:14px;
            }}
            .btn {{
                display:block;
                text-align:center;
                padding:12px;
                margin-top:10px;
                border-radius:10px;
                text-decoration:none;
                font-weight:600;
            }}
            .open {{ background:#38bdf8;color:#020617 }}
            .copy {{ background:#a78bfa;color:#020617 }}
        </style>
        <script>
            function copyText(text) {{
                navigator.clipboard.writeText(text);
                alert("Copied for Instagram!");
            }}
        </script>
    </head>
    <body>
        <header>News for Instagram</header>

        <div class="box">
            <div class="card">
                <b>Short AI Summary</b>
                <p>{short}</p>
            </div>

            <div class="card">
                <b>Instagram Caption</b>
                <p>{caption}</p>
                <div class="btn copy" onclick="copyText(`{caption}`)">📋 Copy Caption</div>
            </div>

            <a class="btn open" href="{item['link']}" target="_blank">🔗 Open Original News</a>
        </div>
    </body>
    </html>
    """
