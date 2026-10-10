import os
import sys
import json
import time
import re
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()

def parse_number(text):
    """
    Parses number strings from X (Turkish & English formats).
    Examples:
    '25.432' -> 25432
    '150 Beğeni' -> 150
    '1,234 Likes' -> 1234
    '12.4K' -> 12400
    '1,5 B' -> 1500
    '25 B' -> 25000
    '2.5M' -> 2500000
    '2,5 Mn' -> 2500000
    '150 Bin' -> 150000
    """
    if not text:
        return 0
    text = str(text).strip().replace('\xa0', ' ')

    # 1. Check for abbreviated format: '12.4K', '1,5 B', '25B', '2.5M', '2,5 Mn'
    match_abbr = re.search(r'([\d.,]+)\s*(Mn|mn|M|m|K|k|B|b)\b', text)
    if match_abbr:
        num_str = match_abbr.group(1)
        suffix = match_abbr.group(2).upper()
        multiplier = 1_000_000 if suffix in ['M', 'MN'] else 1_000
        num_str = num_str.replace(',', '.')
        try:
            return int(float(num_str) * multiplier)
        except ValueError:
            pass

    # 2. Check for standard integer / separated number
    match_num = re.search(r'([\d.,]+)', text)
    if match_num:
        num_str = match_num.group(1)
        multiplier = 1
        if re.search(r'\b(bin)\b', text, re.IGNORECASE):
            multiplier = 1_000
        elif re.search(r'\b(milyon)\b', text, re.IGNORECASE):
            multiplier = 1_000_000

        if '.' in num_str and ',' in num_str:
            if num_str.rfind('.') > num_str.rfind(','):
                num_str = num_str.replace(',', '')
            else:
                num_str = num_str.replace('.', '').replace(',', '.')
        elif ',' in num_str:
            if multiplier > 1 or len(num_str.split(',')[-1]) != 3:
                num_str = num_str.replace(',', '.')
            else:
                num_str = num_str.replace(',', '')
        elif '.' in num_str:
            if multiplier > 1 or len(num_str.split('.')[-1]) != 3:
                pass
            else:
                num_str = num_str.replace('.', '')

        try:
            return int(float(num_str) * multiplier)
        except ValueError:
            return 0
    return 0

def get_cookies(path="cookies.json"):
    """
    Loads cookies from cookies.json or environment variables.
    Supports:
    1. Local cookies.json
    2. TWITTER_COOKIES environment variable (JSON string)
    3. TWITTER_AUTH_TOKEN and TWITTER_CT0 environment variables
    """
    raw_cookies = None

    # 1. Local file
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_cookies = json.load(f)
            print(f"Loaded cookies from '{path}'.")
        except Exception as e:
            print(f"Warning: Failed to load '{path}': {e}")

    # 2. TWITTER_COOKIES environment variable
    if not raw_cookies and os.environ.get("TWITTER_COOKIES"):
        try:
            raw_cookies = json.loads(os.environ.get("TWITTER_COOKIES"))
            print("Loaded cookies from TWITTER_COOKIES environment variable.")
        except Exception as e:
            print(f"Warning: Failed to parse TWITTER_COOKIES env var: {e}")

    # 3. Direct auth_token & ct0
    if not raw_cookies and os.environ.get("TWITTER_AUTH_TOKEN"):
        auth_token = os.environ.get("TWITTER_AUTH_TOKEN").strip()
        ct0 = os.environ.get("TWITTER_CT0", "").strip()
        raw_cookies = [
            {
                "name": "auth_token",
                "value": auth_token,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
                "httpOnly": True
            }
        ]
        if ct0:
            raw_cookies.append({
                "name": "ct0",
                "value": ct0,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            })
        print("Constructed cookies from TWITTER_AUTH_TOKEN environment variable.")

    if not raw_cookies:
        return None

    # Sanitize and normalize cookies for Playwright
    sanitized = []
    for c in raw_cookies:
        if not isinstance(c, dict):
            continue
        cookie_copy = dict(c)
        domain = cookie_copy.get('domain', '.x.com')
        if 'twitter.com' in domain:
            domain = domain.replace('twitter.com', 'x.com')
        cookie_copy['domain'] = domain

        # Remove keys that Playwright might reject
        for key in ['id', 'storeId', 'session', 'hostOnly', 'expirationDate']:
            cookie_copy.pop(key, None)

        if 'sameSite' in cookie_copy:
            if cookie_copy['sameSite'] not in ["Strict", "Lax", "None"]:
                cookie_copy.pop('sameSite', None)

        sanitized.append(cookie_copy)

    return sanitized

def save_cookies(context, path="cookies.json"):
    cookies = context.cookies()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2)

def extract_metric_count(element):
    """
    Extracts number from like/retweet element using aria-label, inner_text,
    or child transition container.
    """
    if not element:
        return 0

    # 1. aria-label (usually contains '12.432 Beğeni' or '12.4K Likes')
    aria = element.get_attribute("aria-label") or ""
    val = parse_number(aria)
    if val > 0:
        return val

    # 2. Text in app-text-transition-container
    container = element.query_selector('[data-testid="app-text-transition-container"]')
    if container:
        val = parse_number(container.inner_text())
        if val > 0:
            return val

    # 3. Direct inner_text
    val = parse_number(element.inner_text())
    return val

def get_top_tweet(query_text: str, sort_metric: str = "likes", headless: bool = True):
    """
    Searches for tweets matching the query and returns the top one based on sort_metric.
    sort_metric: "likes" or "retweets"
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="tr-TR"
        )

        # Anti-detect script
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        cookies = get_cookies()
        if cookies:
            try:
                context.add_cookies(cookies)
                print(f"Cookies loaded ({len(cookies)} entries).")
            except Exception as e:
                print(f"Warning: Failed to inject cookies: {e}")
        else:
            print("Warning: No cookies found! Twitter / X will likely block or redirect search.")

        page = context.new_page()

        encoded_query = urllib.parse.quote(query_text)
        search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=top"

        try:
            print(f"Navigating to search URL: {search_url}")
            page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

            # Wait for content or login redirect
            try:
                page.wait_for_selector('article[data-testid="tweet"], input[name="text"], div[data-testid="empty_state"]', timeout=15000)
            except Exception:
                pass

            current_url = page.url
            if "login" in current_url or "i/flow/login" in current_url:
                print("Error: Redirected to login page. Valid cookies/session are required!")
                return None

            print("Starting tweet collection...")
            unique_tweets = {}
            stuck_count = 0
            last_count = 0

            # Scroll and collect tweets
            max_scrolls = 25
            for i in range(max_scrolls):
                tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
                for tweet in tweet_elements:
                    try:
                        # Extract Link
                        link = ""
                        status_link = tweet.query_selector('a[href*="/status/"]')
                        if status_link:
                            href = status_link.get_attribute("href") or ""
                            if href.startswith("/"):
                                link = f"https://x.com{href.split('?')[0]}"
                            elif "x.com" in href or "twitter.com" in href:
                                link = href.split('?')[0]

                        if not link or link in unique_tweets:
                            continue

                        # Extract Text
                        text_el = tweet.query_selector('div[data-testid="tweetText"]')
                        text = text_el.inner_text().strip() if text_el else "[Görsel / Medya]"

                        # Extract Likes
                        like_el = (
                            tweet.query_selector('button[data-testid="like"]') or
                            tweet.query_selector('button[data-testid="unlike"]') or
                            tweet.query_selector('[data-testid="like"]')
                        )
                        likes = extract_metric_count(like_el)

                        # Extract Retweets
                        rt_el = (
                            tweet.query_selector('button[data-testid="retweet"]') or
                            tweet.query_selector('button[data-testid="unretweet"]') or
                            tweet.query_selector('[data-testid="retweet"]')
                        )
                        retweets = extract_metric_count(rt_el)

                        # Extract Username and Handle
                        user_el = tweet.query_selector('div[data-testid="User-Name"]')
                        display_name = "Bilinmeyen Kullanıcı"
                        handle = "@bilinmeyen"

                        if user_el:
                            raw_lines = [line.strip() for line in user_el.inner_text().split('\n') if line.strip()]
                            if raw_lines:
                                display_name = raw_lines[0]
                                for line in raw_lines[1:]:
                                    if line.startswith('@'):
                                        handle = line
                                        break

                        unique_tweets[link] = {
                            "text": text,
                            "likes": likes,
                            "retweets": retweets,
                            "link": link,
                            "display_name": display_name,
                            "handle": handle
                        }
                    except Exception:
                        continue

                # Progress log
                if i % 5 == 0 or i == max_scrolls - 1:
                    print(f"Scroll {i + 1}/{max_scrolls} | Collected unique tweets: {len(unique_tweets)}")

                # Early break if we have enough tweets and count stopped increasing
                if len(unique_tweets) >= 30 and len(unique_tweets) == last_count:
                    stuck_count += 1
                    if stuck_count >= 3:
                        print("No more new tweets loading, finishing scroll early.")
                        break
                else:
                    stuck_count = 0

                last_count = len(unique_tweets)

                # Scroll down
                page.evaluate("window.scrollBy(0, 1200)")
                time.sleep(1.2)

                # Retry button check
                retry_btn = page.query_selector('div[role="button"]:has-text("Retry"), div[role="button"]:has-text("Yeniden dene")')
                if retry_btn:
                    print("Retry button detected, clicking...")
                    try:
                        retry_btn.click()
                        time.sleep(2)
                    except Exception:
                        pass

            print(f"Total unique tweets collected: {len(unique_tweets)}")
            parsed_tweets = list(unique_tweets.values())

            if not parsed_tweets:
                return None

            # Sort by metric
            if sort_metric == "retweets":
                parsed_tweets.sort(key=lambda x: x['retweets'], reverse=True)
            else:
                parsed_tweets.sort(key=lambda x: x['likes'], reverse=True)

            top = parsed_tweets[0]
            print(f"Top candidate ({sort_metric}): {top['handle']} - Likes: {top['likes']:,} | RT: {top['retweets']:,}")
            return top

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    query = f"lang:tr min_faves:100 since:{yesterday}"
    print(f"Testing with query: {query}")
    result = get_top_tweet(query, headless=False)
    print("Top Tweet Result:", result)
