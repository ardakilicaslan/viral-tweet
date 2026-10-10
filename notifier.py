import os
import html
import requests
from datetime import datetime

def send_telegram_message(token, chat_id, tweet_data, title="🔥 Günün En Çok Beğenilen Tweeti 🔥", metric_type="likes"):
    """
    Sends the tweet data to Telegram using HTML parse mode to avoid markdown parsing errors.
    metric_type: "likes" or "retweets"
    """
    if not tweet_data:
        print("No tweet data to send.")
        return False

    if not token or not chat_id:
        print("Warning: Telegram BOT_TOKEN or CHAT_ID is missing. Skipping Telegram notification.")
        return False

    date_str = datetime.now().strftime("%d.%m.%Y")

    def format_number(num):
        return "{:,}".format(int(num or 0)).replace(",", ".")

    likes_count = format_number(tweet_data.get('likes', 0))
    rt_count = format_number(tweet_data.get('retweets', 0))

    if metric_type == "likes":
        stats_line = f"❤️ <b>Beğeni:</b> {likes_count} | 🔄 <b>RT:</b> {rt_count}"
    else:
        stats_line = f"🔄 <b>RT:</b> {rt_count} | ❤️ <b>Beğeni:</b> {likes_count}"

    clean_name = html.escape(str(tweet_data.get('display_name', 'Bilinmeyen')))
    clean_handle = html.escape(str(tweet_data.get('handle', '@bilinmeyen')))
    clean_text = html.escape(str(tweet_data.get('text', '')))
    if len(clean_text) > 300:
        clean_text = clean_text[:297] + "..."

    message = f"""<b>{html.escape(title)}</b>
📅 <i>{date_str}</i>

👤 <b>Kullanıcı:</b> {clean_name} ({clean_handle})
📊 {stats_line}

💬 <i>{clean_text}</i>

🔗 <a href="{tweet_data['link']}">Tweeti Görüntüle</a>"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("Telegram message sent successfully!")
            return True
        else:
            print(f"Failed to send Telegram message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

if __name__ == "__main__":
    dummy_data = {
        "display_name": "Test Kullanıcı",
        "handle": "@test_user_123",
        "likes": 12345,
        "retweets": 3456,
        "text": "Bu bir test tweetidir. Merhaba dünya!",
        "link": "https://x.com/test/status/123456"
    }
    print("Testing notifier format:")
    print("Notifier module ready.")
