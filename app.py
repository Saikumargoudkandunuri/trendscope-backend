from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, requests, os, datetime
import google.generativeai as genai
from datetime import timezone

# -------------------------------------------------
# APP INIT
# -------------------------------------------------
app = FastAPI()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# -------------------------------------------------
# GLOBAL CACHE
# -------------------------------------------------
NEWS_CACHE = {}

RSS_SOURCES = {
    "HT": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "TOI": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
}

import re
from datetime import datetime, timedelta

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
    return f"{short} 🇮🇳🔥 #Trending #News #India"

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
    score = 10
    title_l = title.lower()

    for k in TREND_KEYWORDS:
        if k in title_l:
            score += 10

    # cap score
    return str(min(score, 95))

# -------------------------------------------------
# FETCH NEWS
# -------------------------------------------------
def fetch_news(source_filter=None):
    global NEWS_CACHE
    NEWS_CACHE = {}
    articles = []
    idx = 0

    for source, url in RSS_SOURCES.items():
        if source_filter and source != source_filter:
            continue

        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            article = {
                "id": idx,
                "title": e.title,
                "summary": e.get("summary", e.title),
                "link": e.link,
                "source": source,
                "trend": ai_trending_score(e.title)
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
                "trend": ai_trending_score(a["title"])
            }
            NEWS_CACHE[idx] = article
            articles.append(article)
            idx += 1

    return articles

# -------------------------------------------------
# HOME UI (ONLY ONE `/`)
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(source: str = Query(None)):
    news = fetch_news(source)

    html = """
    <html>
    <head>
        <title>TrendScope</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; background:#fff; color:#000; max-width:800px; margin:auto; padding:20px; }
            a { text-decoration:none; color:#000; }
            .box { padding:12px; border-bottom:1px solid #ddd; display:flex; justify-content:space-between; }
            .trend { font-weight:bold; }
        </style>
    </head>
    <body>
    <h2>📰 TrendScope</h2>
    """

    for n in news:
        html += f"""
        <div class="box">
            <a href="/news/{n['id']}"><b>{n['title']}</b></a>
            <span class="trend">🔥 {n['trend']}%</span>
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
        return "<h3>Not found. <a href='/'>Back</a></h3>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])
    category = ai_category(item["summary"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background:#000; color:#fff; font-family:Arial; padding:20px; }}
            textarea {{ width:100%; height:90px; }}
            button {{ padding:12px; margin-top:10px; }}
        </style>
    </head>
    <body>
        <a href="/">⬅ Back</a>
        <h3>{item['title']}</h3>
        <p><b>Category:</b> {category}</p>

        <p><b>Short News</b></p>
        <textarea readonly>{short}</textarea>

        <p><b>Instagram Caption</b></p>
        <textarea readonly>{caption}</textarea>

        <button onclick="window.open('{item['link']}', '_blank')">🔗 Open Full News</button>
    </body>
    </html>
    """

# -------------------------------------------------
# HEALTH
# -------------------------------------------------
@app.get("/health")
def health():
    return {"message": "TrendScope MVP API is running"}


@app.get("/debug-gemini")
def debug_gemini():
    try:
        r = model.generate_content("Reply with number 42 only")
        return {
            "gemini_response": r.text,
            "status": "Gemini working"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "Gemini failed"
        }
