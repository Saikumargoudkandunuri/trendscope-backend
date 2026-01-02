from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

API_KEY = "5b8cdcf858a1405b87ac7fbe53ae86f6"


@app.get("/")
def home():
    return {"message": "TrendScope running"}


@app.get("/news")
def news():
    url = f"https://newsapi.org/v2/everything?q=india&apiKey={API_KEY}"
    articles = requests.get(url).json().get("articles", [])[:10]

    result = []
    for a in articles:
        result.append({
            "title": a["title"],
            "caption": f"Breaking News: {a['title']} #news #trending #india"
        })
    return result


@app.get("/page", response_class=HTMLResponse)
def page():
    return """
    <html>
    <head>
        <title>TrendScope</title>
        <link rel="manifest" href="/manifest.json">

    </head>
    <body>
        <h1>TrendScope – Live News</h1>
        <button onclick="loadNews()">Load News</button>
        <div id="news"></div>

        <script>
        function loadNews() {
            fetch('/news')
            .then(r => r.json())
            .then(data => {
                document.getElementById('news').innerHTML = '';
                data.forEach(n => {
                    document.getElementById('news').innerHTML += `
                        <div style="margin-bottom:15px;">
                            <p><b>${n.title}</b></p>
                            <textarea rows="2" cols="60">${n.caption}</textarea><br>
                            <button onclick="navigator.clipboard.writeText('${n.caption}')">
                                Copy Caption
                            </button>
                        </div>
                    `;
                });
            });
        }
        </script>
    </body>
    </html>
    """
from fastapi.responses import FileResponse

@app.get("/manifest.json")
def manifest():
    return FileResponse("manifest.json")
