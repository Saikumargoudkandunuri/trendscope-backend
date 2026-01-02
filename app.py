from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import requests
import feedparser
from datetime import datetime, timezone
from collections import Counter

app = FastAPI()

# ================= CONFIG =================
NEWS_API_KEY = "5b8cdcf858a1405b87ac7fbe53ae86f6"

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
    "India Today": "https://www.indiatoday.in/rss/home"
}

NEWSAPI_URL = "https://newsapi.org/v2/everything"

# ================= AI CATEGORY ENGINE =================
CATEGORY_KEYWORDS = {
    "Politics": ["election", "government", "parliament", "minister", "bjp", "congress", "policy", "law", "vote"],
    "Tech": ["ai", "artificial intelligence", "tech", "software", "iphone", "android", "google", "microsoft", "startup"],
    "Sports": ["cricket", "football", "ipl", "match", "tournament", "fifa", "olympics", "score"],
    "Entertainment": ["movie", "film", "actor", "actress", "cinema", "bollywood", "hollywood", "trailer"],
    "Business": ["stock", "market", "share", "investment", "economy", "finance", "bank", "startup"],
    "World": ["usa", "china", "russia", "ukraine", "global", "international", "world"]
}

def classify_category(title, summary):
    text = f"{title} {summary}".lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}

    for cat, words in CATEGORY_KEYWORDS.items():
        for w in words:
            if w in text:
                scores[cat] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Viral"

# ================= HELPERS =================
def parse_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

def trending_score(count):
    if count >= 4:
        return "🔥🔥🔥"
    elif count >= 2:
        return "🔥🔥"
    else:
        return "🔥"

# ================= FETCH RSS =================
def fetch_rss():
    articles = []
    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]:
            title = entry.title
            summary = entry.get("summary", "")
            articles.append({
                "title": title,
                "summary": summary,
                "link": entry.link,
                "source": source,
                "published": parse_time(entry),
                "category": classify_category(title, summary)
            })
    return articles

# ================= FETCH NEWSAPI =================
def fetch_newsapi():
    params = {
        "q": "india",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 30,
        "apiKey": NEWS_API_KEY
    }
    r = requests.get(NEWSAPI_URL, params=params)
    data = r.json()
    articles = []

    for a in data.get("articles", []):
        title = a.get("title", "")
        summary = a.get("description", "")
        articles.append({
            "title": title,
            "summary": summary,
            "link": a.get("url", "#"),
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "published": datetime.now(timezone.utc),
            "category": classify_category(title, summary)
        })
    return articles

# ================= MAIN PAGE =================
@app.get("/page", response_class=HTMLResponse)
def page(category: str = Query("all")):

    news = fetch_rss() + fetch_newsapi()
    titles = [n["title"] for n in news]
    counts = Counter(titles)

    news.sort(key=lambda x: x["published"], reverse=True)

    cards = ""
    for n in news:
        if category != "all" and n["category"] != category:
            continue

        fire = trending_score(counts[n["title"]])

        cards += f"""
        <div class="card">
            <div class="badge">{fire} {n['category']} • {n['source']}</div>
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
            body {{ background:#0f172a;color:#e5e7eb;font-family:Inter;margin:0 }}
            header {{ padding:16px;text-align:center;font-size:22px;font-weight:700;background:#020617 }}
            .filters {{ display:flex;gap:8px;padding:10px;overflow-x:auto;background:#020617 }}
            .btn {{ padding:8px 14px;background:#1e293b;border-radius:20px;font-size:14px;cursor:pointer }}
            .container {{ padding:14px }}
            .card {{ background:#020617;border-radius:16px;padding:16px;margin-bottom:14px }}
            .badge {{ font-size:12px;color:#a78bfa;margin-bottom:6px }}
            h2 {{ font-size:18px }}
            p {{ font-size:14px;color:#cbd5f5 }}
            .footer {{ display:flex;justify-content:space-between;font-size:12px;color:#94a3b8 }}
            a {{ color:#38bdf8;text-decoration:none;font-weight:600 }}
        </style>

        <script>
            function filter(cat) {{
                window.location = "/page?category=" + cat;
            }}
            setTimeout(()=>location.reload(),60000);
        </script>
    </head>

    <body>
        <header>TrendScope AI</header>

        <div class="filters">
            <div class="btn" onclick="filter('all')">🔥 All</div>
            <div class="btn" onclick="filter('Politics')">🏛 Politics</div>
            <div class="btn" onclick="filter('Tech')">💻 Tech</div>
            <div class="btn" onclick="filter('Sports')">⚽ Sports</div>
            <div class="btn" onclick="filter('Entertainment')">🎬 Entertainment</div>
            <div class="btn" onclick="filter('Business')">💼 Business</div>
            <div class="btn" onclick="filter('World')">🌍 World</div>
        </div>

        <div class="container">
            {cards}
        </div>
    </body>
    </html>
    """

    return html
