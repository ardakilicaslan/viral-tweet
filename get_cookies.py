from playwright.sync_api import sync_playwright
import json
import time

def main():
    print("Twitter Cookie Extractor")
    print("------------------------")
    print("1. A browser window will open.")
    print("2. Log in to Twitter (X) if not already logged in.")
    print("3. Once you are on the home page, close the browser window.")
    print("4. Cookies will be saved to 'cookies.json'.")
    print("------------------------")
    
    with sync_playwright() as p:
        # Launch with headless=False so user can see and interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Opening Twitter...")
        page.goto("https://x.com")
        
        try:
            # Wait for user to close the page/browser
            # We loop and check if page is closed
            while not page.is_closed():
                time.sleep(1)
        except Exception:
            pass
            
        print("Browser closed. Saving cookies...")
        cookies = context.cookies()
        
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
            
        print(f"Successfully saved {len(cookies)} cookies to 'cookies.json'.")
        print("Copy the content of this file to your GitHub Secret 'TWITTER_COOKIES'.")

if __name__ == "__main__":
    main()
