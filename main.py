import os
import sys
import io
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from scraper import get_top_tweet
from notifier import send_telegram_message

# Load environment variables
load_dotenv()

def run_tracker(headless: bool = True, target_date: str = None):
    # Telegram Configuration
    BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

    if not BOT_TOKEN or not CHAT_ID:
        print("\n[BİLGİ] Telegram BOT_TOKEN veya CHAT_ID .env dosyasında bulunamadı.")
        print("[BİLGİ] Sonuçlar sadece konsola yazdırılacak.\n")

    # Date range calculation
    if target_date:
        # User specified custom date (YYYY-MM-DD)
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        since_date = dt.strftime("%Y-%m-%d")
        until_date = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # Default: Last 24-48 hours (since yesterday)
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        since_date = yesterday
        until_date = today

    print(f"Hedef Tarih Aralığı: {since_date} -> {until_date}")

    # 1. EN ÇOK BEĞENİLEN TWEET ARAMASI
    print("\n" + "=" * 50)
    print("🔥 EN ÇOK BEĞENİLEN TWEET ARANIYOR...")
    print("=" * 50)

    # Adaptive search thresholds to ensure results even on lower volume days
    like_thresholds = [20000, 10000, 5000, 1000]
    top_like_tweet = None

    for min_faves in like_thresholds:
        query_likes = f"lang:tr min_faves:{min_faves} since:{since_date}"
        print(f"Denetlenen sorgu: {query_likes}")
        top_like_tweet = get_top_tweet(query_likes, sort_metric="likes", headless=headless)
        if top_like_tweet:
            break
        print(f"Eşik ({min_faves}) ile sonuç bulunamadı, daha düşük eşik deneniyor...")

    if top_like_tweet:
        print("\n✅ En Çok Beğenilen Tweet Bulundu:")
        print(f"   Kullanıcı : {top_like_tweet['display_name']} ({top_like_tweet['handle']})")
        print(f"   Beğeni    : {top_like_tweet['likes']:,}")
        print(f"   RT        : {top_like_tweet['retweets']:,}")
        print(f"   Link      : {top_like_tweet['link']}")
        print(f"   Metin     : {top_like_tweet['text'][:120]}...")

        if BOT_TOKEN and CHAT_ID:
            send_telegram_message(
                BOT_TOKEN,
                CHAT_ID,
                top_like_tweet,
                title="🔥 Günün En Çok Beğenilen Tweeti 🔥",
                metric_type="likes"
            )
    else:
        print("❌ Uygun beğenilen tweet bulunamadı.")

    # 2. EN ÇOK RETWEET ALAN TWEET ARAMASI
    print("\n" + "=" * 50)
    print("🔄 EN ÇOK RETWEET (RT) ALAN TWEET ARANIYOR...")
    print("=" * 50)

    rt_thresholds = [1000, 500, 200, 50]
    top_rt_tweet = None

    for min_rts in rt_thresholds:
        query_rts = f"lang:tr min_retweets:{min_rts} since:{since_date}"
        print(f"Denetlenen sorgu: {query_rts}")
        top_rt_tweet = get_top_tweet(query_rts, sort_metric="retweets", headless=headless)
        if top_rt_tweet:
            break
        print(f"Eşik ({min_rts}) ile sonuç bulunamadı, daha düşük eşik deneniyor...")

    if top_rt_tweet:
        print("\n✅ En Çok RT Alan Tweet Bulundu:")
        print(f"   Kullanıcı : {top_rt_tweet['display_name']} ({top_rt_tweet['handle']})")
        print(f"   RT        : {top_rt_tweet['retweets']:,}")
        print(f"   Beğeni    : {top_rt_tweet['likes']:,}")
        print(f"   Link      : {top_rt_tweet['link']}")
        print(f"   Metin     : {top_rt_tweet['text'][:120]}...")

        if BOT_TOKEN and CHAT_ID:
            send_telegram_message(
                BOT_TOKEN,
                CHAT_ID,
                top_rt_tweet,
                title="🔄 Günün En Çok RT Alan Tweeti 🔄",
                metric_type="retweets"
            )
    else:
        print("❌ Uygun RT alan tweet bulunamadı.")

def main():
    parser = argparse.ArgumentParser(description="ViralTweet - Top Tweet Tracker")
    parser.add_argument("--no-headless", action="store_true", help="Tarayıcıyı görünür modda çalıştırır")
    parser.add_argument("--date", type=str, default=None, help="Özel tarih filtresi (YYYY-MM-DD)")
    args = parser.parse_args()

    run_tracker(headless=not args.no_headless, target_date=args.date)

if __name__ == "__main__":
    main()
