from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, requests, os, datetime
from openai import OpenAI
from datetime import timezone

# Initialize FastAPI and OpenAI
app = FastAPI()

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def force_ui_root():
    return """
    <html>
    <head>
        <title>TrendScope UI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                background: #fff;
                color: #000;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <h2>📰 TrendScope UI</h2>
        <p>If you see this on mobile, routing is FIXED.</p>
        <p><a href="/health">API Health</a></p>
    </body>
    </html>
    """

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Global cache for the session
NEWS_CACHE = {}

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

def trending_score_visual(published_dt):
    """Returns fire emojis based on how recent the news is."""
    score = 1
    if published_dt:
        now = datetime.datetime.now(timezone.utc)
        delta = now - published_dt
        if delta.total_seconds() < 3600:  # Less than 1 hour old
            score += 2
        elif delta.total_seconds() < 10800: # Less than 3 hours old
            score += 1
    return "🔥" * score

def ai_trending_score(title: str):
    """Returns a trending percentage (0–100) using AI."""
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a news trend analyst. Rate how trending this headline is (0-100). Respond with ONLY the number."},
                {"role": "user", "content": title}
            ]
        )
        score = r.choices[0].message.content.strip()
        return ''.join(c for c in score if c.isdigit()) or "0"
    except:
        return "0"

# -----------------------------
# AGGREGATION
# -----------------------------



def fetch_news(source_filter=None):
    global NEWS_CACHE
    NEWS_CACHE = {} # Resetting cache for the demo; in production use a DB
    articles = []
    idx = 0

    # 1. Process RSS Sources
    for source, url in RSS_SOURCES.items():
        if source_filter and source != source_filter:
            continue
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            # Parse RSS date to datetime object
            pub_dt = datetime.datetime(*e.published_parsed[:6], tzinfo=timezone.utc) if hasattr(e, 'published_parsed') else None
            
            article = {
                "id": idx,
                "title": e.title,
                "summary": e.get("summary", e.title),
                "link": e.link,
                "source": source,
                "published": pub_dt,
                "trend_ai": ai_trending_score(e.title)
            }
            articles.append(article)
            NEWS_CACHE[idx] = article
            idx += 1

    # 2. Process NewsAPI Source
    if NEWSAPI_KEY and not (source_filter and source_filter not in ["HT", "TOI"]):
        try:
            r = requests.get(
                f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWSAPI_KEY}"
            ).json()

            for a in r.get("articles", [])[:10]:
                # Parse ISO date string to datetime object
                pub_date_str = a.get("publishedAt")
                pub_dt = datetime.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')) if pub_date_str else None

                article = {
                    "id": idx,
                    "title": a["title"],
                    "summary": a.get("description", a["title"]) or "No summary available.",
                    "link": a["url"],
                    "source": a["source"]["name"],
                    "published": pub_dt,
                    "trend_ai": ai_trending_score(a["title"])
                }
                articles.append(article)
                NEWS_CACHE[idx] = article
                idx += 1
        except Exception as err:
            print(f"NewsAPI Error: {err}")

    return articles

# -----------------------------
# ROUTES
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def home(source: str = Query(None)):
    news_list = fetch_news(source)

    html = f"""
    <html>
    <head>
        <title>TrendScope</title>
        <meta http-equiv="refresh" content="300">
        <style>
            body {{ background:#fff; color:#000; font-family:sans-serif; max-width: 800px; margin: auto; padding: 20px; }}
            a {{ color:#000; text-decoration:none; }}
            .box {{ padding:15px; border-bottom:1px solid #ddd; display:flex; justify-content:space-between; align-items:center; }}
            .tag {{ font-size:12px; color:#666; }}
            .nav {{ margin-bottom: 20px; padding: 10px; background: #f4f4f4; border-radius: 5px; }}
        </style>
    </head>
    <body>
    <h2>TrendScope</h2>
    <div class="nav">
        <a href="/">All</a> | 
        <a href="/?source=HT">Hindustan Times</a> | 
        <a href="/?source=TOI">Times of India</a>
    </div>
    """

    for n in news_list:
        fire_icons = trending_score_visual(n['published'])
        html += f"""
        <div class="box">
            <div style="flex: 1;">
                <a href="/news/{n['id']}"><b>{n['title']}</b></a><br>
                <span class="tag">{n['source']} | AI Trend: {n['trend_ai']}%</span>
            </div>
            <div style="font-size: 20px;">{fire_icons}</div>
        </div>
        """

    html += "</body></html>"
    return html

    from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home_page():
    # Force refresh of news cache
    fetch_news()

    return """
    <html>
    <head>
        <title>TrendScope</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {
                background: #fff;
                color: #000;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
            a {
                color: #000;
                text-decoration: none;
            }
            .box {
                padding: 15px;
                border-bottom: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <h2>📰 TrendScope</h2>
        <p>If you see this page, UI routing is working.</p>

        <div class="box">
            <a href="/news/0"><b>Tap here to test first news</b></a>
        </div>
    </body>
    </html>
    """


@app.get("/news/{news_id}", response_class=HTMLResponse)
def news_page(news_id: int):
    item = NEWS_CACHE.get(news_id)

    if not item:
        return "<h2>Detail not found. <a href='/'>Go back</a></h2>"

    # AI Processing
    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])
    category = ai_category(item["summary"])

    return f"""
    <html>
    <head>
        <title>{item['title']}</title>
        <style>
            body {{ background:#111; color:#eee; font-family:sans-serif; max-width: 600px; margin: auto; padding: 20px; }}
            textarea {{ width:100%; height:100px; background:#222; color:#0f0; border:1px solid #444; padding:10px; margin-bottom:20px; }}
            button {{ padding:12px 20px; background:#007bff; color:white; border:none; cursor:pointer; border-radius:5px; }}
            a {{ color:#aaa; }}
        </style>
    </head>
    <body>
        <a href="/">⬅ Back to Feed</a>
        <h3>{item['title']}</h3>
        <p><b>Category:</b> <span style="color:#007bff">{category}</span></p>

        <p><b>Short News (Instagram Style)</b></p>
        <textarea readonly>{short}</textarea>

        <p><b>Suggested Caption</b></p>
        <textarea readonly>{caption}</textarea>

        <button onclick="window.open('{item['link']}', '_blank')">🔗 Read Full Article</button>
    </body>
    </html>
    """
@app.get("/health")
def health():
    return {"message": "TrendScope MVP API is running"}