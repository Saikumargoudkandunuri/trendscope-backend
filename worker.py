import time
from app import post_category_wise_news
from cricket_engine import cricket_worker_loop
import threading

# Start Cricket Engine
t2 = threading.Thread(
    target=cricket_worker_loop,
    args=(generate_news_image, upload_image_to_cloudinary, post_to_instagram, logger),
    daemon=True
)
t2.start()


print("🚀 TrendScope Background Worker started")

while True:
    try:
        # This function now handles the 1AM-6AM IST check inside itself
        post_category_wise_news()
    except Exception as e:
        print(f"Worker Loop Error: {e}")

    # Wait 1 hour before checking for fresh news again
    # This prevents the bot from constantly hitting the RSS feeds
    print("💤 Worker sleeping for 1 hour...")
    time.sleep(3600)