from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, requests, os, datetime
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

RSS_SOURCES = {
    "HT": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "TOI": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
}

# -----------------------------
# UTILITIES
# -----------------------------
def ai_category(text):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify this news into one category: Politics, Tech, Sports, Business, World, Entertainment"},
            {"role": "user", "content": text}
        ]
    )
    return r.choices[0].message.content.strip()

def ai_short_news(text):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Convert this into 5–10 simple Instagram-style words."},
            {"role": "user", "content": text}
        ]
    )
    return r.choices[0].message.content.strip()

def ai_caption(text):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Write a clean, elegant Instagram caption for this news."},
            {"role": "user", "content": text}
        ]
    )
    return r.choices[0].message.content.strip()

def trending_score(published):
    score = 1
    if published:
        delta = datetime.datetime.now() - published
        if delta.total_seconds() < 3600:
            score += 2
    return "🔥" * score

# -----------------------------
# AGGREGATION
# -----------------------------
def fetch_news(source_filter=None):
    articles = []

    for source, url in RSS_SOURCES.items():
        if source_filter and source != source_filter:
            continue
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            articles.append({
                "title": e.title,
                "summary": e.get("summary", ""),
                "link": e.link,
                "source": source,
                "published": datetime.datetime.now()
            })

    if NEWSAPI_KEY:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines?country=in",
            headers={"X-Api-Key": NEWSAPI_KEY}
        ).json()

        for a in r.get("articles", [])[:10]:
            articles.append({
                "title": a["title"],
                "summary": a.get("description", ""),
                "link": a["url"],
                "source": a["source"]["name"],
                "published": datetime.datetime.now()
            })

    return articles

# -----------------------------
# HOME PAGE
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(source: str = Query(None)):
    news = fetch_news(source)

    html = """
    <html>
    <head>
        <title>TrendScope</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body { background:#fff; color:#000; font-family:Arial; }
            a { color:#000; text-decoration:none; }
            .box { padding:10px; border-bottom:1px solid #ddd; }
            .tag { font-size:12px; color:#555; }
        </style>
    </head>
    <body>
    <h2>TrendScope</h2>
    <p>
        <a href="/">All</a> |
        <a href="/?source=HT">HT</a> |
        <a href="/?source=TOI">TOI</a>
    </p>
    """

    for i, n in enumerate(news):
        html += f"""
        <div class="box">
