from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser
import hashlib
from datetime import datetime, timezone
import os

# ================== CHOOSE AI ==================
USE_OPENAI = True   # set False if using Gemini

# ---------- OpenAI ----------
if USE_OPENAI:
   python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- Gemini ----------
if not USE_OPENAI:
    import google.generativeai as genai
    genai.configure(api_key="YOUR_GEMINI_API_KEY")
    model = genai.GenerativeModel("gemini-pro")

# ================= APP =================
app = FastAPI()

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news"
}

# ================= AI FUNCTIONS =================

def ai_summary(text):
    prompt = f"Summarize this news in 5 to 10 simple words:\n{text}"

    if USE_OPENAI:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20
        )
        return r.choices[0].message.content.strip()

    else:
        return model.generate_content(prompt).text.strip()


def ai_meme_caption(text):
    prompt = f"""
Create a short, funny meme-style Instagram caption for this news.
Use casual Indian tone. No emojis overload.

News:
{text}
"""

    if USE_OPENAI:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80
        )
        return r.choices[0].message.content.strip()

    else:
        return model.generate_content(prompt).text.strip()


def ai_normal_caption(title, source):
    return f"{title}\n\nSource: {source}\n#news #india #breaking #viral"

# ================= FETCH NEWS =================

def fetch_news():
    items = []
    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:20]:
            uid = hashlib.md5(e.title.encode()).hexdigest()
            items.append({
                "id": uid,
                "title": e.title,
                "link": e.link,
                "source": source
            })
    return items

# ================= HOME =================

@app.get("/page", response_class=HTMLResponse)
def home():
    news = fetch_news()

    cards = ""
    for n in news:
        cards += f"""
        <div class="card" onclick="openNews('{n['id']}')">
            <h2>{n['title']}</h2>
            <span>{n['source']}</span>
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
            .card {{ background:#020617;padding:16px;border-radius:14px;margin-bottom:12px;cursor:pointer }}
            h2 {{ font-size:17px }}
            span {{ font-size:12px;color:#94a3b8 }}
        </style>
        <script>
            function openNews(id) {{
                location.href = "/news?id=" + id;
            }}
        </script>
    </head>
    <body>
        <header>TrendScope AI</header>
        <div class="container">{cards}</div>
    </body>
    </html>
    """

# ================= DETAIL PAGE =================

@app.get("/news", response_class=HTMLResponse)
def news_detail(id: str):
    news = fetch_news()
    item = next((n for n in news if n["id"] == id), None)

    if not item:
        return "<h3>News not found</h3>"

    short = ai_summary(item["title"])
    meme = ai_meme_caption(item["title"])
    caption = ai_normal_caption(item["title"], item["source"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background:#0f172a;color:#e5e7eb;font-family:Inter;margin:0 }}
            header {{ padding:16px;text-align:center;font-size:20px;font-weight:700;background:#020617 }}
            .box {{ padding:16px }}
            .card {{ background:#020617;padding:16px;border-radius:14px;margin-bottom:14px }}
            .btn {{ padding:12px;border-radius:10px;margin-top:8px;text-align:center;font-weight:600;cursor:pointer }}
            .copy {{ background:#a78bfa;color:#020617 }}
            .open {{ background:#38bdf8;color:#020617;text-decoration:none;display:block }}
        </style>
        <script>
            function copyText(text) {{
                navigator.clipboard.writeText(text);
                alert("Copied!");
            }}
        </script>
    </head>

    <body>
        <header>Instagram Ready</header>

        <div class="box">
            <div class="card">
                <b>AI Short Summary</b>
                <p>{short}</p>
            </div>

            <div class="card">
                <b>Meme Caption</b>
                <p>{meme}</p>
                <div class="btn copy" onclick="copyText(`{meme}`)">📋 Copy Meme Caption</div>
            </div>

            <div class="card">
                <b>Normal Caption</b>
                <p>{caption}</p>
                <div class="btn copy" onclick="copyText(`{caption}`)">📋 Copy Caption</div>
            </div>

            <a class="btn open" href="{item['link']}" target="_blank">🔗 Open Original News</a>
        </div>
    </body>
    </html>
    """
