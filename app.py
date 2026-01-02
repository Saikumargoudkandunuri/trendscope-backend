from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, requests, os
import re

# -------------------------------------------------
# APP INIT
# -------------------------------------------------
app = FastAPI()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# -------------------------------------------------
# GLOBAL CACHE
# -------------------------------------------------
NEWS_CACHE = {}

RSS_SOURCES = {
    "HT": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "TOI": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
}

# -------------------------------------------------
# TREND LOGIC (FREE + STABLE)
# -------------------------------------------------
TREND_KEYWORDS = [
    "breaking", "election", "budget", "crisis", "attack", "launch",
    "ai", "ipo", "war", "court", "policy", "startup", "india", "modi",
    "stock", "market", "tech", "google", "apple", "microsoft"
]

def ai_short_news(text):
    words = re.findall(r"\w+", text)
    return " ".join(words[:8])

def ai_caption(text):
    short = ai_short_news(text)
    return f"{short} 🔥 #Trending #News"

def ai_category(text):
    t = text.lower()
    if any(k in t for k in ["election", "government", "policy", "modi"]):
        return "Politics"
    if any(k in t for k in ["market", "stock", "ipo", "economy"]):
        return "Business"
    if any(k in t for k in ["ai", "tech", "google", "apple"]):
        return "Tech"
    if any(k in t for k in ["match", "cricket", "football", "tournament"]):
        return "Sports"
    return "General"

def ai_trending_score(title):
    score = 20
    title_l = title.lower()
    for k in TREND_KEYWORDS:
        if k in title_l:
            score += 10
    return str(min(score, 95))

def trend_color(score):
    s = int(score)
    if s >= 70:
        return "#ff3d00"
    elif s >= 40:
        return "#ff9100"
    else:
        return "#607d8b"

# -------------------------------------------------
# FETCH NEWS
# -------------------------------------------------
def fetch_news(source_filter=None):
    global NEWS_CACHE
    NEWS_CACHE = {}
    articles = []
    idx = 0

    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
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

    if NEWSAPI_KEY:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines?country=in",
            headers={"X-Api-Key": NEWSAPI_KEY}
        ).json()

        for a in r.get("articles", [])[:10]:
            article = {
                "id": idx,
                "title": a["title"],
                "summary": a.get("description", a["title"]),
                "link": a["url"],
                "source": a["source"]["name"],
                "trend": ai_trending_score(a["title"]),
                "category": ai_category(a.get("description", a["title"]))
            }
            NEWS_CACHE[idx] = article
            articles.append(article)
            idx += 1

    return articles

# -------------------------------------------------
# HOME UI
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(category: str = Query(None)):
    news = fetch_news()
    news.sort(key=lambda x: int(x["trend"]), reverse=True)

    if category:
        news = [n for n in news if n["category"] == category]

    html = """
    <html>
    <head>
        <title>TrendScope</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #f5f7fa, #e3eeff);
                margin: 0;
                padding: 20px;
            }
            h1 {
                font-weight: 800;
                letter-spacing: -1px;
                color: #1a237e;
            }
            .tabs a {
                margin-right: 12px;
                font-weight: 600;
                color: #3949ab;
                text-decoration: none;
            }
            .card {
                background: #ffffff;
                border-radius: 14px;
                padding: 16px;
                margin: 14px 0;
                box-shadow: 0 8px 20px rgba(0,0,0,0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .card a {
                font-size: 17px;
                font-weight: 600;
                color: #212121;
                text-decoration: none;
            }
            .trend {
                font-size: 14px;
                font-weight: 700;
            }
        </style>
    </head>
    <body>

    <h1>📰 TrendScope</h1>

    <div class="tabs">
        <a href="/">All</a>
        <a href="/?category=Politics">Politics</a>
        <a href="/?category=Tech">Tech</a>
        <a href="/?category=Sports">Sports</a>
        <a href="/?category=Business">Business</a>
    </div>
    """

    for n in news:
        html += f"""
        <div class="card">
            <a href="/news/{n['id']}">{n['title']}</a>
            <span class="trend" style="color:{trend_color(n['trend'])}">
                🔥 {n['trend']}%
            </span>
        </div>
        """

    html += "</body></html>"
    return html

# -------------------------------------------------
# DETAIL PAGE (BEAUTIFUL)
# -------------------------------------------------
@app.get("/news/{news_id}", response_class=HTMLResponse)
def news_page(news_id: int):
    item = NEWS_CACHE.get(news_id)
    if not item:
        return "<h3>Not found</h3>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])
    category = ai_category(item["summary"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1a237e, #3949ab);
                color: white;
                padding: 20px;
            }}
            .box {{
                background: white;
                color: #212121;
                border-radius: 16px;
                padding: 20px;
                max-width: 600px;
                margin: auto;
                box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            }}
            h2 {{
                font-weight: 800;
                margin-bottom: 10px;
            }}
            textarea {{
                width: 100%;
                height: 80px;
                border-radius: 10px;
                padding: 10px;
                border: none;
                background: #f5f5f5;
                margin-bottom: 12px;
            }}
            button {{
                width: 100%;
                padding: 14px;
                margin-top: 10px;
                border-radius: 10px;
                border: none;
                font-size: 15px;
                font-weight: 700;
                background: #3949ab;
                color: white;
            }}
            a {{
                color: #bbdefb;
                text-decoration: none;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <a href="/">⬅ Back</a>

        <div class="box">
            <h2>{item['title']}</h2>
            <p><b>Category:</b> {category}</p>

            <p><b>Short News</b></p>
            <textarea readonly>{short}</textarea>

            <p><b>Instagram Caption</b></p>
            <textarea readonly>{caption}</textarea>

            <button onclick="window.open('{item['link']}', '_blank')">
                🔗 Open Full News
            </button>

            <button onclick="navigator.share({{
                title: '{item['title']}',
                text: '{short}',
                url: '{item['link']}'
            }})">
                📤 Share
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
    return {"message": "TrendScope MVP API is running"}
