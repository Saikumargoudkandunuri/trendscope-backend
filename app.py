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

# -------------------------------------------------
# INDIA-HEAVY RSS SOURCES (≈80% INDIA)
# -------------------------------------------------
RSS_SOURCES = {
    # Major Indian News
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
    "News18": "https://www.news18.com/rss/india.xml",
    "Deccan Herald": "https://www.deccanherald.com/rss/india.rss",
    "ANI": "https://aninews.in/rss/national/general.xml",

    # Business (India)
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "Business Standard": "https://www.business-standard.com/rss/latest.rss",
    "LiveMint": "https://www.livemint.com/rss/news",

    # Government / Official
    "PIB": "https://pib.gov.in/rssfeed.aspx",

    # Limited Global (≈20%)
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

# -------------------------------------------------
# TREND LOGIC (FREE + STABLE)
# -------------------------------------------------
TREND_KEYWORDS = [
    "breaking", "india", "government", "modi", "budget", "election",
    "court", "supreme court", "policy", "attack", "crisis",
    "market", "stock", "ipo", "economy",
    "ai", "technology", "startup", "launch", "isro",
    "cricket", "match", "team india", "tournament"
]

# -------------------------------------------------
# CONTENT GENERATION (IMPROVED QUALITY)
# -------------------------------------------------
def ai_short_news(text):
    """
    18–25 words, clean, human-readable (Inshorts-style)
    """
    words = re.findall(r"\w+", text)
    short = " ".join(words[:22])
    return short + "."

def ai_caption(text):
    """
    Instagram-ready caption (longer, viral friendly)
    """
    short = ai_short_news(text)
    return (
        f"{short}\n\n"
        "📢 Stay informed in seconds, not minutes.\n"
        "Follow for daily trending updates 🇮🇳\n\n"
        "#IndiaNews #TrendingNow #BreakingNews #DailyUpdates #NewsInShort"
    )

def ai_category(text):
    t = text.lower()
    if any(k in t for k in ["election", "government", "policy", "modi", "minister"]):
        return "Politics"
    if any(k in t for k in ["market", "stock", "ipo", "economy", "business"]):
        return "Business"
    if any(k in t for k in ["ai", "tech", "isro", "startup", "launch"]):
        return "Tech"
    if any(k in t for k in ["cricket", "match", "team", "tournament", "sports"]):
        return "Sports"
    return "India"

def ai_trending_score(title):
    score = 25
    title_l = title.lower()
    for k in TREND_KEYWORDS:
        if k in title_l:
            score += 8
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

    <h1>🇮🇳 TrendScope India</h1>

    <div class="tabs">
        <a href="/">All</a>
        <a href="/?category=India">India</a>
        <a href="/?category=Politics">Politics</a>
        <a href="/?category=Tech">Tech</a>
        <a href="/?category=Business">Business</a>
        <a href="/?category=Sports">Sports</a>
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
# DETAIL PAGE
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
                max-width: 650px;
                margin: auto;
                box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            }}
            h2 {{ font-weight: 800; }}
            textarea {{
                width: 100%;
                height: 110px;
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
            a {{ color: #bbdefb; text-decoration: none; font-weight: 600; }}
        </style>
    </head>
    <body>
        <a href="/">⬅ Back</a>

        <div class="box">
            <h2>{item['title']}</h2>
            <p><b>Category:</b> {category} | <b>Source:</b> {item['source']}</p>

            <p><b>Short News</b></p>
            <textarea readonly>{short}</textarea>

            <p><b>Instagram Caption</b></p>
            <textarea readonly>{caption}</textarea>

            <button onclick="window.open('{item['link']}', '_blank')">
                🔗 Read Full Article
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
    return {"message": "TrendScope India is running"}
