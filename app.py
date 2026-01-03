from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import feedparser, re

app = FastAPI()

NEWS_CACHE = {}

RSS_SOURCES = {
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-india-news",
}

def ai_short_news(text):
    words = re.findall(r"\w+", text)
    return " ".join(words[:22]) + "."

def ai_caption(text):
    return ai_short_news(text) + "\n\n#IndiaNews"

def ai_category(text):
    t = text.lower()
    if "cricket" in t: return "Sports"
    if "market" in t: return "Business"
    if "tech" in t or "ai" in t: return "Tech"
    return "India"

def ai_trending_score(title):
    return min(95, 40 + sum(k in title.lower() for k in ["india","court","market","cricket"]) * 10)

def extract_image(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url")
    return "https://via.placeholder.com/400x200?text=News"

def fetch_news():
    global NEWS_CACHE
    NEWS_CACHE = {}
    out, i = [], 0
    for src, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:6]:
            art = {
                "id": i,
                "title": e.title,
                "summary": e.get("summary", e.title),
                "link": e.link,
                "image": extract_image(e),
                "trend": ai_trending_score(e.title),
                "category": ai_category(e.title)
            }
            NEWS_CACHE[i] = art
            out.append(art)
            i += 1
    return out

@app.get("/", response_class=HTMLResponse)
def home(category: str = Query(None)):
    news = fetch_news()
    news.sort(key=lambda x: x["trend"], reverse=True)
    if category:
        news = [n for n in news if n["category"] == category]

    flash = news[:5]

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">

<style>
html, body {{
    margin:0;
    padding:0;
    width:100%;
    overflow-x:hidden;
    font-family:Arial;
    background:#f1f3f6;
}}

a {{ text-decoration:none; color:black; }}

.header {{
    background:#131921;
    color:white;
    padding:12px;
    display:flex;
    justify-content:space-between;
}}

.category {{
    background:#232f3e;
    padding:10px;
    white-space:nowrap;
    overflow-x:auto;
}}

.category a {{
    color:white;
    margin-right:12px;
    font-weight:bold;
}}

.flash-box {{
    background:white;
    margin:10px;
    padding:10px;
    border-radius:12px;
}}

.flash-row {{
    display:flex;
    gap:10px;
    overflow-x:auto;
}}

.flash-card {{
    flex:0 0 260px;
}}

.flash-card img {{
    width:100%;
    height:140px;
    object-fit:cover;
    border-radius:8px;
}}

.card {{
    background:white;
    margin:10px;
    padding:12px;
    border-radius:10px;
}}

.trend {{
    float:right;
    color:#ff5722;
    font-weight:bold;
}}

.overlay {{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.4);
    display:none;
    z-index:9;
}}

.menu {{
    position:fixed;
    top:0;
    right:0;
    width:260px;
    height:100%;
    background:white;
    padding:20px;
    transform: translateX(100%); /* 🔥 REAL FIX */
    transition: transform 0.3s ease;
    z-index:10;
}}

.menu.open {{
    transform: translateX(0);
}}

.menu button {{
    width:100%;
    padding:10px;
    margin-top:10px;
}}
</style>

<script>
function toggleMenu(){{
  const m=document.getElementById('menu');
  const o=document.getElementById('overlay');
  m.classList.toggle('open');
  o.style.display=m.classList.contains('open')?'block':'none';
  document.body.style.overflow=m.classList.contains('open')?'hidden':'auto';
}}
</script>
</head>

<body>
<div id="overlay" class="overlay" onclick="toggleMenu()"></div>

<div class="header">
<b>TrendScope 🇮🇳</b>
<span onclick="toggleMenu()">☰</span>
</div>

<div class="category">
<a href="/">All</a>
<a href="/?category=India">India</a>
<a href="/?category=Tech">Tech</a>
<a href="/?category=Business">Business</a>
<a href="/?category=Sports">Sports</a>
</div>

<div class="flash-box">
<b>🔥 Flash News</b>
<div class="flash-row">
{''.join(f"<div class='flash-card'><a href='{f['link']}' target='_blank'><img src='{f['image']}'><p>{f['title']}</p></a></div>" for f in flash)}
</div>
</div>

{''.join(f"<div class='card'><a href='/news/{n['id']}'>{n['title']}</a><span class='trend'>🔥 {n['trend']}%</span></div>" for n in news)}

<div id="menu" class="menu">
<button onclick="location.href='/login'">Login</button>
<button>Language</button>
<button>Notifications</button>
</div>

</body>
</html>
"""

@app.get("/login", response_class=HTMLResponse)
def login():
    return "<h2 style='padding:20px'>Login (UI only)</h2><a href='/'>Back</a>"

@app.get("/news/{i}", response_class=HTMLResponse)
def news(i: int):
    news = fetch_news()
    item = None

    for n in news:
        if n["id"] == i:
            item = n
            break

    if not item:
        return "<h3>News not found</h3>"

    short = ai_short_news(item["summary"])
    caption = ai_caption(item["summary"])

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin:0;
                font-family: Arial;
                background:#0d47a1;
                color:white;
            }}
            .container {{
                padding:16px;
            }}
            .card {{
                background:white;
                color:black;
                padding:16px;
                border-radius:14px;
            }}
            img {{
                width:100%;
                border-radius:12px;
                margin-bottom:12px;
            }}
            .title {{
                font-size:20px;
                font-weight:bold;
                margin-bottom:10px;
            }}
            .label {{
                font-weight:bold;
                margin-top:14px;
            }}
            .box {{
                background:#f1f3f6;
                padding:10px;
                border-radius:8px;
                margin-top:6px;
            }}
            .btn {{
                width:100%;
                padding:12px;
                margin-top:12px;
                border:none;
                border-radius:10px;
                font-size:16px;
            }}
            .read {{
                background:#ff9800;
                color:black;
            }}
            .share {{
                background:#1e88e5;
                color:white;
            }}
            a {{
                color:white;
                text-decoration:none;
                display:inline-block;
                margin-bottom:12px;
            }}
        </style>

        <script>
            function shareNews() {{
                if (navigator.share) {{
                    navigator.share({{
                        title: "{item['title']}",
                        text: "{caption}",
                        url: "{item['link']}"
                    }});
                }} else {{
                    alert("Sharing not supported on this browser");
                }}
            }}
        </script>
    </head>

    <body>
        <div class="container">
            <a href="/">⬅ Back</a>

            <div class="card">
                <img src="{item['image']}">

                <div class="title">{item['title']}</div>

                <div class="label">📰 Short News</div>
                <div class="box">{short}</div>

                <div class="label">📸 Instagram Caption</div>
                <div class="box">{caption}</div>

                <button class="btn share" onclick="shareNews()">🔗 Share</button>
                <button class="btn read" onclick="window.open('{item['link']}', '_blank')">
                    Read Full News
                </button>
            </div>
        </div>
    </body>
    </html>
    """
