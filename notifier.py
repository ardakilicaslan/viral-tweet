import requests
from datetime import datetime

def send_telegram_message(token, chat_id, tweet_data, title="🔥 Günün En Çok Beğenilen Tweeti 🔥", metric_type="likes"):
    """
    Sends the tweet data to Telegram.
    metric_type: "likes" or "retweets"
    """
    if not tweet_data:
        print("No tweet data to send.")
        return

    date_str = datetime.now().strftime("%d.%m.%Y")
    
    def format_number(num):
        return "{:,}".format(num).replace(",", ".")

    stats_line = ""
    if metric_type == "likes":
        stats_line = f"❤️ **Beğeni:** {format_number(tweet_data['likes'])}"
    else:
        stats_line = f"🔄 **RT:** {format_number(tweet_data.get('retweets', 0))}"

    message = f"""
{title}
📅 {date_str}

👤 **Kullanıcı:** {tweet_data['display_name']}
              {tweet_data['handle']}
{stats_line}

🔗 [Tweeti Görüntüle]({tweet_data['link']})
    """
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message: {response.text}")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    # Test
    dummy_data = {
        "username": "TestUser",
        "likes": 12345,
        "text": "Bu bir test tweetidir. Merhaba dünya!",
        "link": "https://x.com/test/status/123456"
    }
    # Replace with your token/id for testing if needed, or run main.py
    print("Notifier module ready.")
