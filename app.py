from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, re

# -------------------------------------------------
# APP INIT
# -------------------------------------------------
app = FastAPI()

# -------------------------------------------------
# GLOBAL CACHE
# -------------------------------------------------
NEWS_CACHE = {}

# -------------------------------------------------
# INDIA-HEAVY RSS SOURCES
# -------------------------------------------------
RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
}

# -------------------------------------------------
# SIMPLE AI HELPERS
# -------------------------------------------------
def ai_short_news(text):
    words = re.findall(r"\w+", text)
    return " ".join(words[:22]) + "."

def ai_caption(text):
    short = ai_short_news(text)
    return f"{short}\n\n#IndiaNews #Trending"

def ai_category(text):
    t = text.lower()
    if "cricket" in t:
        return "Sports"
    if "market" in t or "ipo" in t:
        return "Business"
    if "ai" in t or "tech" in t:
        return "Tech"
    return "India"

def ai_trending_score(title):
    score = 30
    for k in ["breaking", "india", "modi", "court", "market", "cricket"]:
        if k in title.lower():
            score += 10
    return min(score, 95)

# -------------------------------------------------
# FETCH NEWS
# -------------------------------------------------
def fetch_news():
    global NEWS_CACHE
    NEWS_CACHE = {}
    articles = []
    idx = 0

    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:6]:
            article = {
                "id": idx,
                "title": e.title,
                "summary": e.get("summary", e.title),
                "link": e.link,
                "source": source,
                "trend": ai_trending_score(e.title),
                "category": ai_category(e.get("summary", e.title))
            }
            NEWS_CACHE[idx] = article
            articles.append(article)
            idx += 1

    return articles

# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(category: str = Query(None)):
    news = fetch_news()
    news.sort(key=lambda x: x["trend"], reverse=True)

    if category:
        news = [n for n in news if n["category"] == category]

    html = """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { margin:0; font-family: Arial; background:#f1f3f6; }
        .header {
            background:#131921;
            color:white;
            padding:12px;
            display:flex;
            justify-content:space-between;
        }
        .category {
            background:#232f3e;
            padding:10px;
        }
        .category a {
            color:white;
            margin-right:10px;
            text-decoration:none;
            font-weight:bold;
        }
        .card {
            background:white;
            margin:10px;
            padding:12px;
            border-radius:10px;
        }
        .trend {
            float:right;
            font-weight:bold;
            color:#ff5722;
        }
    </style>
    </head>

    <body>

    <div class="header">
        <b>TrendScope 🇮🇳</b>
        <div>🔔 ☰</div>
    </div>

    <div class="category">
        <a href="/">All</a>
        <a href="/?category=India">India</a>
        <a href="/?category=Tech">Tech</a>
        <a href="/?category=Business">Business</a>
        <a href="/?category=Sports">Sports</a>
    </div>
    """

    for n in news:
        html += f"""
        <div class="card">
            <a href="/news/{n['id']}">{n['title']}</a>
            <span class="trend">🔥 {n['trend']}%</span>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return html

# -------------------------------------------------
# DETAIL PAGE
# -------------------------------------------------
@app.get("/news/{news_id}", response_class=HTMLResponse)
def news_page(news_id: int):
    item = NEWS_CACHE.get(news_id)
    if not item:
        return "<h3>Not found</h3>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial;
            background:#1a237e;
            color:white;
            padding:20px;
        }}
        .box {{
            background:white;
            color:black;
            padding:20px;
            border-radius:12px;
        }}
        textarea {{
            width:100%;
            height:90px;
        }}
        button {{
            width:100%;
            padding:12px;
            margin-top:10px;
        }}
    </style>
    </head>

    <body>
        <a href="/" style="color:white;">⬅ Back</a>

        <div class="box">
            <h2>{item['title']}</h2>

            <p><b>Short News</b></p>
            <textarea readonly>{short}</textarea>

            <p><b>Instagram Caption</b></p>
            <textarea readonly>{caption}</textarea>

            <button onclick="window.open('{item['link']}', '_blank')">
                Read Full News
            </button>
        </div>
    </body>
    </html>
    """

# -------------------------------------------------
# HEALTH
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "OK"}
