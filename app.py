from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, requests, os, datetime
from openai import OpenAI

NEWS_CACHE = {}

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

    def ai_trending_score(title: str):
    """
    Returns a trending percentage (0–100) for a news headline
    """
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a news trend analyst. "
                        "Rate how trending this headline is right now "
                        "on a scale of 0 to 100. "
                        "Respond with ONLY the number."
                    )
                },
                {
                    "role": "user",
                    "content": title
                }
            ]
        )

        score = r.choices[0].message.content.strip()
        score = ''.join(c for c in score if c.isdigit())

        return score if score else "0"

    except:
        return "0"


# -----------------------------
# AGGREGATION
# -----------------------------

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

            articles.append(article)
            NEWS_CACHE[idx] = article
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
                "source": a["source"]["name"]
            }
            articles.append(article)
            NEWS_CACHE[idx] = article
            idx += 1

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
        <div class="box" style="display:flex; justify-content:space-between; align-items:center;">
            <a href="/news/{n['id']}">

                <b>{n['title']}</b>
            </a><br>
            <span class="tag">{n['source']} {trending_score(n['published'])}</span>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return html

@app.get("/news/{news_id}", response_class=HTMLResponse)
def news_page(news_id: int):
    item = NEWS_CACHE.get(news_id)

    if not item:
        return "<h2>Detail not found. Go back.</h2>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])
    category = ai_category(item["summary"])

    return f"""
    <html>
    <head>
        <title>{item['title']}</title>
        <style>
            body {{ background:#000; color:#fff; font-family:Arial; }}
            textarea {{ width:100%; height:80px; }}
            button {{ padding:10px; margin:5px; }}
            a {{ color:#ccc; }}
        </style>
    </head>
    <body>
        <h3>{item['title']}</h3>

        <p><b>Category:</b> {category}</p>

        <p><b>Short News (5–10 words)</b></p>
        <textarea readonly>{short}</textarea>

        <p><b>Instagram Description</b></p>
        <textarea readonly>{caption}</textarea>

        <button onclick="window.open('{item['link']}', '_blank')">
            🔗 Open Full News
        </button>

        <br><br>
        <a href="/">⬅ Back</a>
    </body>
    </html>
    """
