from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

# 🔑 REPLACE WITH YOUR NEWS API KEY
NEWS_API_KEY = "5b8cdcf858a1405b87ac7fbe53ae86f6"

NEWS_URL = (
    "https://newsapi.org/v2/top-headlines"
    "?country=in"
    f"&apiKey={NEWS_API_KEY}"
)

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2 style="font-family:Arial">TrendScope backend is running ✅</h2>
    <p>Open <b>/page</b> to see news</p>
    """

@app.get("/page", response_class=HTMLResponse)
def news_page():
    response = requests.get(NEWS_URL)
    data = response.json()
    articles = data.get("articles", [])[:20]

    cards_html = ""

    for article in articles:
        title = article.get("title") or "No title"
        desc = article.get("description") or "No description"
        source = article.get("source", {}).get("name", "Source")
        url = article.get("url", "#")

        cards_html += f"""
        <div class="card">
            <div class="badge">🔥 Viral</div>
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
    </head>

    <body>
        <header>TrendScope</header>

        <div class="categories">
            <div class="cat active">🔥 Viral</div>
            <div class="cat">🎬 Celeb</div>
            <div class="cat">💻 Tech</div>
            <div class="cat">⚽ Sports</div>
            <div class="cat">🏛 Politics</div>
        </div>

        <div class="container">
            {cards_html}
        </div>
    </body>
    </html>
    """

    return html

