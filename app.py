from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import requests
import feedparser
from datetime import datetime, timezone
from collections import Counter
import time

app = FastAPI()

# =========================
# CONFIG
# =========================
NEWS_API_KEY = "5b8cdcf858a1405b87ac7fbe53ae86f6"

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
    "India Today": "https://www.indiatoday.in/rss/home"
}

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"

# =========================
# HELPERS
# =========================
def parse_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

def trending_score(title, count):
    if count >= 4:
        return "🔥🔥🔥"
    elif count >= 2:
        return "🔥🔥"
    else:
        return "🔥"

# =========================
# FETCH RSS
# =========================
def fetch_rss():
    articles = []
    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]:
            articles.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link,
                "source": source,
                "published": parse_time(entry)
            })
    return articles

# =========================
# FETCH NEWSAPI
# =========================
def fetch_newsapi():
    params = {
        "country": "in",
        "apiKey": NEWS_API_KEY,
        "pageSize": 30
    }
    r = requests.get(NEWSAPI_URL, params=params)
    data = r.json()
    articles = []
    for a in data.get("articles", []):
        articles.append({
            "title": a.get("title", ""),
            "summary": a.get("description", ""),
            "link": a.get("url", "#"),
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "published": datetime.now(timezone.utc)
        })
    return articles

# =========================
# MAIN PAGE
# =========================
@app.get("/page", response_class=HTMLResponse)
def page(source: str = Query("all")):

    rss_news = fetch_rss()
    api_news = fetch_newsapi()

    all_news = rss_news + api_news

    # Deduplicate by title
    titles = [n["title"] for n in all_news]
    title_count = Counter(titles)

    # Sort by time
    all_news.sort(key=lambda x: x["published"], reverse=True)

    cards = ""
    for n in all_news:
        if source != "all" and n["source"] != source:
            continue

        fire = trending_score(n["title"], title_count[n["title"]])

        cards += f"""
        <div class="card">
            <div class="badge">{fire} {n['source']}</div>
            <h2>{n['title']}</h2>
            <p>{n['summary']}</p>
            <div class="footer">
                <span>{n['published'].strftime('%H:%M')}</span>
                <a href="{n['link']}" target="_blank">Read</a>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>TrendScope</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">

        <style>
            body {{
                margin: 0;
                font-family: Inter, sans-serif;
                background: #0f172a;
                color: #e5e7eb;
            }}
            header {{
                padding: 16px;
                text-align: center;
                font-size: 22px;
                font-weight: 700;
                background: #020617;
            }}
            .filters {{
                display: flex;
                gap: 8px;
                padding: 10px;
                overflow-x: auto;
                background: #020617;
            }}
            .btn {{
                padding: 8px 14px;
                background: #1e293b;
                border-radius: 20px;
                font-size: 14px;
                cursor: pointer;
                white-space: nowrap;
            }}
            .btn.active {{
                background: #38bdf8;
                color: #020617;
                font-weight: 600;
            }}
            .container {{
                padding: 14px;
            }}
            .card {{
                background: #020617;
                border-radius: 16px;
                padding: 16px;
                margin-bottom: 14px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.4);
            }}
            .badge {{
                font-size: 12px;
                margin-bottom: 6px;
                color: #a78bfa;
                font-weight: 600;
            }}
            h2 {{
                font-size: 18px;
                line-height: 1.3;
            }}
            p {{
                font-size: 14px;
                color: #cbd5f5;
            }}
            .footer {{
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
                font-size: 12px;
                color: #94a3b8;
            }}
            a {{
                color: #38bdf8;
                text-decoration: none;
                font-weight: 600;
            }}
        </style>

        <script>
            function filter(src) {{
                window.location = "/page?source=" + src;
            }}
            setTimeout(() => {{
                location.reload();
            }}, 60000);
        </script>
    </head>

    <body>
        <header>TrendScope</header>

        <div class="filters">
            <div class="btn active" onclick="filter('all')">🔥 All</div>
            <div class="btn" onclick="filter('Hindustan Times')">HT</div>
            <div class="btn" onclick="filter('Times of India')">TOI</div>
            <div class="btn" onclick="filter('The Hindu')">Hindu</div>
            <div class="btn" onclick="filter('NDTV')">NDTV</div>
            <div class="btn" onclick="filter('India Today')">India Today</div>
        </div>

        <div class="container">
            {cards}
        </div>
    </body>
    </html>
    """

    return html

