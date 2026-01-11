# cricket_sources.py

# 1) LIVE SCORE TRACKER (important)
ESPN_LIVE_SCORE_RSS = [
    # ✅ Your Cricinfo Live Scores RSS (the XML you shared)
    # Paste the exact URL of this live scores RSS here:
    # Example (you must replace with your exact working link):
    "http://www.cricinfo.com/rss/livescores.xml"
]

# 2) CRICKET NEWS + LIVE BLOG FEEDS
CRICKET_NEWS_RSS = [
    # BBC Sport Cricket
    "https://feeds.bbci.co.uk/sport/cricket/rss.xml",

    # Guardian Cricket
    "https://www.theguardian.com/sport/cricket/rss",

    # The Roar Cricket
    "https://www.theroar.com.au/cricket/feed/",

    # Indian Express Cricket
    "https://indianexpress.com/section/sports/cricket/feed/",

    # NDTV Cricket
    "https://sports.ndtv.com/cricket/rss",

    # Times of India Sports / Cricket
    "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",

    # Sportstar Cricket
    "https://sportstar.thehindu.com/cricket/feeder/default.rss",

    # Firstpost FirstCricket
    "https://www.firstpost.com/commonfeeds/v1/mfp/rss/firstcricket.xml",

    # ICC Cricket Schedule RSS
    "https://www.icccricketschedule.com//api/feeds/rss.xml",

    # CricTracker feed (VERY GOOD for live moments + WATCH posts)
    "https://www.crictracker.com/feed",

    # Cricket Addictor
    "https://cricketaddictor.com/feed/",

    # Cricket Country
    "https://www.cricketcountry.com/feed/",

    # Cricket Web
    "https://www.cricketweb.net/feed/",
]


# ---------------------------
# 3) GENERAL SPORTS / INDIA NEWS (your earlier uploads)
# (when you want, we will filter only cricket related items)
# ---------------------------
GENERAL_NEWS_RSS = [
    # You already uploaded these earlier (BBC / Guardian / NDTV / Sportstar / TOI etc.)
    # We will include them in next update step in cricket_engine.py
]


# ---------------------------
# 4) EXTRA (you will add more later)
# ---------------------------
EXTRA_RSS = []
