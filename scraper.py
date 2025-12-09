import json
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def get_cookies(path="cookies.json"):
    try:
        with open(path, 'r') as f:
            cookies = json.load(f)
            # Sanitize cookies for Playwright
            sanitized = []
            for c in cookies:
                # Remove fields that Playwright might not like or that are specific to the extension
                c.pop('id', None)
                c.pop('storeId', None)
                c.pop('session', None)
                c.pop('hostOnly', None)
                c.pop('expirationDate', None) # Sometimes float vs int issues, let Playwright handle session
                
                # Fix sameSite
                if 'sameSite' in c:
                    if c['sameSite'] not in ["Strict", "Lax", "None"]:
                        c.pop('sameSite') # Remove invalid values
                
                sanitized.append(c)
            return sanitized
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: cookies.json not found or invalid.")
        return None

def save_cookies(context, path="cookies.json"):
    cookies = context.cookies()
    with open(path, 'w') as f:
        json.dump(cookies, f)

def parse_number(text):
    if not text:
        return 0
    
    multiplier = 1
    text = text.replace('\xa0', '').replace(' ', '')
    
    if 'B' in text: # Bin (Thousand)
        multiplier = 1000
        text = text.replace('B', '')
    elif 'K' in text: # Thousand (English)
        multiplier = 1000
        text = text.replace('K', '')
    elif 'Mn' in text: # Million (Turkish)
        multiplier = 1000000
        text = text.replace('Mn', '')
    elif 'M' in text: # Million (English)
        multiplier = 1000000
        text = text.replace('M', '')
    
    # Turkish decimal uses comma
    text = text.replace(',', '.')
    
    # Remove any other non-numeric chars just in case (except dot)
    text = ''.join([c for c in text if c.isdigit() or c == '.'])
    
    if text:
        return int(float(text) * multiplier)
    return 0

def get_top_tweet(query_text: str, sort_metric: str = "likes", headless: bool = True):
    """
    Searches for tweets matching the query and returns the top one based on sort_metric.
    sort_metric: "likes" or "retweets"
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Load cookies if available
        cookies = get_cookies()
        if cookies:
            context.add_cookies(cookies)
            print("Cookies loaded.")
        else:
            print("No cookies found. Proceeding as guest (might fail).")

        page = context.new_page()
        
        import urllib.parse
        encoded_query = urllib.parse.quote(query_text)
        search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=top"
        try:
            page.goto(search_url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(10) # Wait for React to render
            
            if "login" in page.url and "search" not in page.url:
                print("Redirected to login page. Cookies might be invalid.")
                if headless:
                    return None
            
            # Initialize scrolling
            print("Starting scraper...")
            last_height = page.evaluate("document.body.scrollHeight")
            
            unique_tweets = {}
            
            for i in range(50):
                # --- SCRAPE VISIBLE TWEETS START ---
                # We scrape *during* scrolling because Twitter removes top tweets from DOM (Virtualization)
                tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
                for tweet in tweet_elements:
                    try:
                        # Extract Link first to check uniqueness
                        time_el = tweet.query_selector('time')
                        link = ""
                        if time_el:
                            parent_link = time_el.query_selector('xpath=..')
                            if parent_link:
                                href = parent_link.get_attribute("href")
                                link = f"https://x.com{href}"
                        
                        if not link or link in unique_tweets:
                            continue

                        # Extract Text
                        text_el = tweet.query_selector('div[data-testid="tweetText"]')
                        text = text_el.inner_text() if text_el else "No Text"
                        
                        # Extract Likes
                        like_el = tweet.query_selector('div[data-testid="like"]') or tweet.query_selector('button[data-testid="like"]')
                        likes = 0
                        if like_el:
                            val_el = like_el.query_selector('span[data-testid="app-text-transition-container"] > span > span')
                            if val_el:
                                likes = parse_number(val_el.inner_text())
                        
                        # Extract Retweets
                        rt_el = tweet.query_selector('div[data-testid="retweet"]') or tweet.query_selector('button[data-testid="retweet"]')
                        retweets = 0
                        if rt_el:
                            val_el = rt_el.query_selector('span[data-testid="app-text-transition-container"] > span > span')
                            if val_el:
                                retweets = parse_number(val_el.inner_text())

                        # Extract Username and Handle
                        user_el = tweet.query_selector('div[data-testid="User-Name"]')
                        display_name = "Unknown"
                        handle = "@unknown"
                        
                        if user_el:
                            parts = user_el.inner_text().split('\n')
                            if len(parts) >= 2:
                                display_name = parts[0]
                                handle = parts[1]
                            else:
                                display_name = parts[0]
                        
                        # Add to collection
                        unique_tweets[link] = {
                            "text": text,
                            "likes": likes,
                            "retweets": retweets,
                            "link": link,
                            "display_name": display_name,
                            "handle": handle
                        }
                    except Exception as e:
                        continue
                # --- SCRAPE VISIBLE TWEETS END ---

                # 1. Scroll down
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(1)
                
                # 2. Human-like behavior: random small scrolls
                if i % 3 == 0:
                     page.evaluate("window.scrollBy(0, -200)")
                     time.sleep(0.5)
                     page.evaluate("window.scrollBy(0, 200)")
                
                # 3. Random mouse movement
                page.mouse.move(100, 100)
                page.mouse.move(200, 300)
                
                # 4. Handle "Retry" button if present
                retry_button = page.query_selector('div[role="button"]:has-text("Retry")')
                if retry_button:
                    print("Retry button detected, clicking...")
                    retry_button.click()
                    time.sleep(3)
                
                # 5. Wait for network idle
                time.sleep(2)

                # Check scroll progress
                new_height = page.evaluate("document.body.scrollHeight")
                
                if i % 5 == 0:
                    print(f"Progress: {i}/50 | Height: {new_height} | Tweets: {len(unique_tweets)}")
                
                # Handle stuck scrolling
                if new_height == last_height and i > 5:
                     print("Scrolling stuck, attempting to force scroll...")
                     page.keyboard.press("End")
                     time.sleep(5)
                
                last_height = new_height
            
            print(f"Total unique tweets found: {len(unique_tweets)}")
            parsed_tweets = list(unique_tweets.values())
            
            # Sort by metric
            if sort_metric == "retweets":
                parsed_tweets.sort(key=lambda x: x['retweets'], reverse=True)
            else:
                parsed_tweets.sort(key=lambda x: x['likes'], reverse=True)
            
            if parsed_tweets:
                return parsed_tweets[0]
            else:
                return None

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    # Test run
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    query = f"lang:tr min_faves:100 since:{yesterday}"
    print(f"Testing with query: {query}")
    top_tweet = get_top_tweet(query, headless=False) # Headless False to see it working
    print("Top Tweet:", top_tweet)
