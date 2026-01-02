from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

# 🔑 PUT YOUR REAL NEWS API KEY HERE
NEWS_API_KEY = "5b8cdcf858a1405b87ac7fbe53ae86f6"

BASE_URL = "https://newsapi.org/v2/top-headlines"

def fetch_news(category=None):
    params = {
        "country": "in",
        "apiKey": NEWS_API_KEY,
        "pageSize": 30
    }
    if category:
        params["category"] = category

    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data.get("articles", [])

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h2>TrendScope backend running ✅</h2><p>Open /page</p>"

@app.get("/page", response_class=HTMLResponse)
def page():
    all_news = fetch_news()

    cards_html = ""
    for article in all_news:
        title = article.get("title") or "No title"
        desc = article.get("description") or "No description"
        source = article.get("source", {}).get("name", "Source")
        url = article.get("url", "#")

        cards_html += f"""
        <div class="card" data-cat="all">
            <div class="badge">🔥 Trending</div>
            <h2>{title}</h2>
            <p>{desc}</p>
            <div class="card-footer">
                <span>{source}</span>
                <a href="{url}" target="_blank">Read</a>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TrendScope</title>

        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">

        <style>
            body {{
                margin: 0;
                font-family: 'Inter', sans-serif;
                background: #0f172a;
                color: #e5e7eb;
            }}

            header {{
                padding: 16px;
                font-size: 22px;
                font-weight: 700;
                text-align: center;
                background: #020617;
                border-bottom: 1px solid #1e293b;
            }}

            .categories {{
                display: flex;
                gap: 10px;
                padding: 12px;
                overflow-x: auto;
                background: #020617;
                position: sticky;
                top: 0;
                z-index: 10;
            }}

            .cat {{
                padding: 8px 14px;
                background: #1e293b;
                border-radius: 20px;
                font-size: 14px;
                white-space: nowrap;
                cursor: pointer;
            }}

            .cat.active {{
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
                box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            }}

            .badge {{
                display: inline-block;
                background: #a78bfa;
                color: #020617;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 8px;
            }}

            .card h2 {{
                font-size: 18px;
                margin: 6px 0;
                line-height: 1.3;
            }}

            .card p {{
                font-size: 14px;
                color: #cbd5f5;
                line-height: 1.4;
            }}

            .card-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 12px;
                font-size: 13px;
                color: #94a3b8;
            }}

            .card-footer a {{
                text-decoration: none;
                color: #38bdf8;
                font-weight: 600;
            }}
        </style>

        <script>
            function activate(btn) {{
                document.querySelectorAll('.cat').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
            }}
        </script>
    </head>

    <body>
        <header>TrendScope</header>

        <div class="categories">
            <div class="cat active" onclick="activate(this)">🔥 All</div>
            <div class="cat" onclick="activate(this)">🎬 Celeb</div>
            <div class="cat" onclick="activate(this)">💻 Tech</div>
            <div class="cat" onclick="activate(this)">⚽ Sports</div>
            <div class="cat" onclick="activate(this)">🏛 Politics</div>
        </div>

        <div class="container">
            {cards_html}
        </div>
    </body>
    </html>
    """

    return html
