import time
from app import post_category_wise_news

print("🚀 TrendScope Background Worker started")

while True:
    try:
        post_category_wise_news()
    except Exception as e:
        print("Worker error:", e)

    time.sleep(3600)  # 1 hour
