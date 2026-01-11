import time
import feedparser
import logging

logger = logging.getLogger("uvicorn.error")

# ✅ Add as many accounts as you want
TWITTER_ACCOUNTS = [
    "BCCI",
    "ICC",
    "Cricbuzz",
    "ESPNcricinfo",
    "crictracker",
    "Cricket_World",
    "IPL",
    "WPL",
    "Sportstarweb",
    "RevSportz",
    "MyCric101",
    "cricbuzz",
    "StarSportsIndia",
    "ImTanujSingh",
    "CricCrazyJohns",
    "mufaddal_vohra",
    "CricSubhayan",
]

# ✅ FREE RSS servers (fallback)
NITTER_HOSTS = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lunar.icu",
]

SEEN_TWEETS = set()


def build_nitter_rss_url(username: str, host: str):
    username = username.strip().replace("@", "")
    return f"{host}/{username}/rss"


def fetch_twitter_rss(username: str):
    """
    Tries multiple nitter hosts.
    Returns feed entries list.
    """
    for host in NITTER_HOSTS:
        try:
            url = build_nitter_rss_url(username, host)
            feed = feedparser.parse(url)
            if feed and feed.entries:
                return feed.entries
        except:
            continue
    return []


def twitter_fetch_loop(on_event=None, logger=None, poll_seconds=60):
    """
    ✅ Free Twitter (X) fetcher using RSS (Nitter)
    calls:
        on_event(text, source)
    """

    if logger:
        logger.info("🐦 Twitter RSS Engine Started...")

    while True:
        try:
            for acc in TWITTER_ACCOUNTS:
                entries = fetch_twitter_rss(acc)

                for e in entries[:5]:
                    link = getattr(e, "link", "")
                    title = getattr(e, "title", "")

                    if not link or not title:
                        continue

                    # ✅ avoid duplicates
                    if link in SEEN_TWEETS:
                        continue
                    SEEN_TWEETS.add(link)

                    # cleanup title text
                    text = title.strip()
                    source = f"twitter:{acc}"

                    if logger:
                        logger.info(f"✅ Tweet from {acc}: {text[:80]}")

                    if on_event:
                        try:
                            # on_event can be async or sync
                            res = on_event(text, source)
                            if hasattr(res, "__await__"):
                                import asyncio
                                asyncio.run(res)
                        except Exception as cb_err:
                            if logger:
                                logger.error(f"❌ Twitter callback error: {cb_err}")

            time.sleep(poll_seconds)

        except Exception as e:
            if logger:
                logger.error(f"❌ Twitter loop error: {e}")
            time.sleep(60)
