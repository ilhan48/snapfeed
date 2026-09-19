# snapfeed 📰 → 📄

Yapay zeka, Rust ve Go gündemini her sabah **Türkçe PDF bülten** olarak
Telegram'ına getiren ücretsiz sistem. PDF motoru: [snappdf](../snappdf)
(Türkçe karakterli, reklamsız, yer imli).

## Nasıl çalışıyor?

1. `feeds-tr.txt`'teki RSS kaynaklarından yeni yazılar çekilir (`bulten.py`)
2. Türkçe kaynaklar doğrudan, İngilizce derin yazılar **ücretsiz çevrimdışı
   çeviriyle** Türkçeye çevrilir (`cevir.py`, Argos — kod blokları korunur)
3. snappdf ile A5 + sepia PDF üretilir (tablet için hazır)
4. PDF'ler Telegram'a konu albümleri halinde gönderilir (`send_telegram.py`)
5. Görülen linkler hatırlanır, ertesi gün tekrarlanmaz

Tamamı **ücretsiz**: GitHub Actions (public repo) + Telegram Bot API.

## Kaynaklar

| Konu | Kaynak | Tür |
|---|---|---|
| yapay-zeka | Webrazzi Yapay Zeka, Yapay Zeka Postası, Yapay Bülten | yerli |
| yapay-zeka | Hugging Face Blog | çeviri |
| rust | Rust Blog, This Week in Rust | çeviri |
| golang | GoSuda | yerli |
| golang | Go Blog | çeviri |

## Yerelde çalıştırma

```bash
FEEDS=feeds-tr.txt ./run.sh   # ~/Bulten/YYYY-MM-DD/ altına üretir
```

## Bulut kurulumu (bir kez)

1. [@BotFather](https://t.me/BotFather)'dan bot açıp token'ı al
2. Bot'a bir mesaj atıp chat-id'yi öğren:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Repo → Settings → Secrets → Actions:
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
4. Actions → `gunluk-bulten` → Run workflow ile test et

Zamanlama: her gün 04:00 UTC = 07:00 TRT (`.github/workflows/bulten.yml`).
