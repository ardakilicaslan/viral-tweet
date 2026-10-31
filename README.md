# ViralTweet — X Zirvesi

Python ve Playwright ile Türkçe X gönderilerini tarayan, etkileşim metriklerini
ayrıştıran ve kaynak bağlantılı raporlar hazırlayan bir araç.

Güncel hesap: [@xzirvesi](https://x.com/xzirvesi)

## Projenin kapsamı

Türkçe gönderilerin beğeni ve repost metriklerini toplayarak günlük
raporlar ve paylaşım taslakları oluşturur. Manuel olarak çalıştırılır.

- Playwright ile dinamik sayfalardan veri toplama
- Türkçe/İngilizce etkileşim sayılarının ayrıştırılması
- Beğeni ve repost (RT) kategorilerinde örneklem liderlerinin seçilmesi
- Telegram için HTML biçiminde bildirim
- JSON raporu ve @xzirvesi için elle paylaşılacak metin taslakları
- Europe/Istanbul üzerinden rapor günü seçimi ve sınırlı tarih sorguları

## Mimari

```text
main.py → scraper.py → X arama sonuçları
   ├── notifier.py → Telegram (isteğe bağlı)
   └── reports/ → JSON + X paylaşım taslakları
```

## Kurulum

Python 3.11 veya üzeri kullanın.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Bağımlılıkları sanal ortamın Python yorumlayıcısıyla yükleyin.
`.env.example` dosyasını `.env` olarak kopyalayın. Gerçek kimlik bilgileri bu
depoya dahil değildir. X oturumu için yerel `cookies.json` veya desteklenen
`TWITTER_*` ortam değişkenleri gerekir. Telegram ayarları isteğe bağlıdır.

## Kullanım

```bash
# X taraması yapar; Telegram mesajı göndermez
python main.py --date 2026-10-31 --dry-run

# Varsayılan: Türkiye saatine göre önceki gün; Telegram ayarlıysa gönderir
python main.py
```

Raporlar `reports/YYYY-MM-DD.json`, taslaklar `reports/YYYY-MM-DD-x.txt`
dosyalarına yazılır. X hesabına otomatik gönderim yapılmaz.
`--dry-run` gerçek X oturumu gerektirir.

Oturum dosyası hazırlamak için `python get_cookies.py` çalıştırıp açılan
tarayıcıda giriş yapabilirsiniz. Oturum dosyalarını paylaşmayın veya commit etmeyin.

## Doğrulama

```bash
python -m unittest discover -s tests -v
```

Testler tarih sorgularını, rapor/taslak üretimini, hata aktarımını ve Telegram
HTML biçimini dış servislere bağlanmadan kontrol eder. Canlı X taraması
bu testlerin kapsamında değildir.

## Sınırlar

X arama sıralaması ve sınırlı kaydırma, tüm platformdaki kesin günlük lideri
bulmayı garanti etmez. Sonuçlar taranan Türkçe gönderilerin liderleridir;
metrikler tarama anındaki değerlerdir. Arayüz değişiklikleri, oturumun sona
erimesi ve erişim kısıtları veri toplamayı etkileyebilir. Türkiye rapor günü
ile X tarih operatörlerinin gerçek zaman sınırları canlı verilerle ayrıca
kontrol edilmelidir. Tekrar Telegram gönderimini engelleyen kalıcı kayıt
henüz yoktur. Ayrıntılı teknik değerlendirme için [REVIEW.md](REVIEW.md).
