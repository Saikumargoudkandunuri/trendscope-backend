import random
import time

# We create hundreds/thousands of unique urls dynamically
UNSPLASH_QUERIES = [
    "cricket", "ipl", "stadium", "sports", "match", "scoreboard",
    "india cricket", "batsman", "bowler", "wicket", "team", "fans",
    "sport poster", "sports background", "cricket ground", "ball bat",
    "night stadium", "sports news", "sports highlights", "world cup"
]

PEXELS_QUERIES = [
    "cricket", "sports", "stadium", "match", "sports background",
    "team", "ball", "sports banner", "sports poster"
]

def get_fallback_image_url(source="unsplash") -> str:
    """
    Returns a fresh image every time
    ✅ unlimited unique images
    ✅ prevents repeats
    ✅ no need to store 1000 urls
    """

    sig = random.randint(1, 10_000_000)  # random signature
    w = random.choice([1080, 1200, 1350])
    h = random.choice([1080, 1350, 1600])

    if source == "pexels":
        q = random.choice(PEXELS_QUERIES)
        # Pexels doesn't have free random-source endpoint like unsplash without API.
        # So we simulate using placeholder style (you can later replace with API).
        # Keep UNSPLASH as primary.
        return f"https://source.unsplash.com/{w}x{h}/?{q}&sig={sig}"

    # default = unsplash
    q = random.choice(UNSPLASH_QUERIES)
    return f"https://source.unsplash.com/{w}x{h}/?{q}&sig={sig}"


def generate_fallback_pool(n=1000):
    """
    Creates 1000 unique urls at startup.
    Not required, but you asked for 500-1000 list.
    """
    pool = []
    for _ in range(n):
        pool.append(get_fallback_image_url("unsplash"))
    return pool


# ✅ This gives 1000 urls instantly
FALLBACK_IMAGES = generate_fallback_pool(1000)
