import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scraper import get_top_tweet
from notifier import send_telegram_message

# Load environment variables from .env file
load_dotenv()

def main():
    # Configuration
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")
    
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: BOT_TOKEN or CHAT_ID not found in environment variables.")
        print("Please set them in your .env file or system environment variables.")
        sys.exit(1)

    # Calculate date range (Last 24 hours)
    # We look for tweets since yesterday
    # Calculate date range (Yesterday full day)
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 1. Find Most Liked Tweet
    print("--- Searching for Most Liked Tweet ---")
    # Strict date range: since yesterday until today (covers yesterday 00:00 to 23:59)
    query_likes = f"lang:tr min_faves:25000 since:{yesterday} until:{today}"
    top_like_tweet = get_top_tweet(query_likes, sort_metric="likes", headless=True)
    
    if top_like_tweet:
        print(f"Found top liked tweet: {top_like_tweet['link']}")
        send_telegram_message(BOT_TOKEN, CHAT_ID, top_like_tweet, title="🔥 Günün En Çok Beğenilen Tweeti 🔥", metric_type="likes")
    else:
        print("No liked tweets found.")

    # 2. Find Most Retweeted Tweet
    print("--- Searching for Most Retweeted Tweet ---")
    # Lower threshold to 1000 to catch more candidates, let our sorter find the real top
    query_rts = f"lang:tr min_retweets:1000 since:{yesterday} until:{today}"
    top_rt_tweet = get_top_tweet(query_rts, sort_metric="retweets", headless=True)
    
    if top_rt_tweet:
        print(f"Found top RT tweet: {top_rt_tweet['link']}")
        send_telegram_message(BOT_TOKEN, CHAT_ID, top_rt_tweet, title="🔄 Günün En Çok RT Alan Tweeti 🔄", metric_type="retweets")
    else:
        print("No RT tweets found.")

if __name__ == "__main__":
    main()
