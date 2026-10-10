import json
from playwright.sync_api import sync_playwright

def main():
    print("=" * 60)
    print("         Twitter / X Cookie & Session Çıkarıcı")
    print("=" * 60)
    print("1. Otomatik olarak bir Chromium tarayıcı penceresi açılacak.")
    print("2. X (Twitter) hesabınıza giriş yapın.")
    print("3. Ana sayfaya ulaştıktan sonra terminale dönün ve ENTER'a basın.")
    print("4. Çerezler 'cookies.json' dosyasına kaydedilecek.")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            locale="tr-TR"
        )
        page = context.new_page()

        print("\nX (Twitter) açılıyor...")
        page.goto("https://x.com/login")

        input("\n>>> Giriş işlemini tamamladıktan sonra lütfen buraya gelip ENTER tuşuna basın <<< ")

        print("\nÇerezler alınıyor...")
        cookies = context.cookies()

        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

        print(f"✅ Başarılı! {len(cookies)} adet çerez 'cookies.json' dosyasına kaydedildi.")

        # Print auth_token and ct0 for convenience
        auth_token = None
        ct0 = None
        for c in cookies:
            if c.get("name") == "auth_token":
                auth_token = c.get("value")
            elif c.get("name") == "ct0":
                ct0 = c.get("value")

        if auth_token:
            print("\n" + "-" * 60)
            print("🔑 HIZLI KURULUM İÇİN .env DEĞERLERİNİZ:")
            print(f"TWITTER_AUTH_TOKEN={auth_token}")
            if ct0:
                print(f"TWITTER_CT0={ct0}")
            print("-" * 60)

        browser.close()
        print("\nİşlem tamamlandı. Tarayıcı kapatıldı.")

if __name__ == "__main__":
    main()
