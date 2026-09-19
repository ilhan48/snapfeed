# snapfeed 📰 → 📄

Yapay zeka, Rust ve Go gündemini her sabah **Türkçe PDF bülten** olarak
getiren ücretsiz sistem. PDF motoru: [snappdf](https://github.com/ilhan48/snappdf)
(Türkçe karakterli, reklamsız, yer imli).

Tablet + kalemle öğrenmek için üretilir: **4:3 tablet sayfası, sepia tema,
12 punto**, çevirilerde bilgi bandı (orijinal link dahil), gün başında
`00. bulten-indeks.pdf` içindekiler sayfası.

## Nasıl çalışıyor?

1. `feeds-tr.txt`'teki RSS kaynaklarından yeni yazılar çekilir (`bulten.py`)
2. Türkçe kaynaklar doğrudan, İngilizce derin yazılar **ücretsiz çevrimdışı
   çeviriyle** Türkçeye çevrilir (`cevir.py`, Argos — kod ve tablolar korunur)
3. snappdf ile tablet + sepia + 12pt PDF üretilir
4. `index.py` gün indeksini hazırlar (`00. bulten-indeks.pdf`)
5. PDF'ler Telegram'a gönderilir (`send_telegram.py`, indeks önce)
6. Görülen linkler hatırlanır, ertesi gün tekrarlanmaz

## Kaynaklar

| Konu | Kaynak | Tür |
|---|---|---|
| yapay-zeka | Webrazzi Yapay Zeka, Yapay Zeka Postası, Yapay Bülten | yerli |
| yapay-zeka | Hugging Face Blog | çeviri |
| rust | Rust Blog, This Week in Rust | çeviri |
| golang | GoSuda | yerli |
| golang | Go Blog | çeviri |

## hermes kurulumu (birincil yol)

```bash
cargo install --git https://github.com/ilhan48/snappdf
pip install argostranslate
git clone https://github.com/ilhan48/snapfeed && cd snapfeed
./run.sh                        # ilk bülten ~/Bulten/YYYY-MM-DD/ altına
```

Her sabah 07:00 için cron:

```bash
crontab -e
# 0 7 * * * cd $HOME/snapfeed && ./run.sh >> logs/cron.log 2>&1
```

## Telegram (isteğe bağlı)

Repo Settings → Secrets → Actions'a `TELEGRAM_BOT_TOKEN` +
`TELEGRAM_CHAT_ID` ekle, Actions → `gunluk-bulten` → Run workflow.
Not: GitHub runner ağından Bot API'ye POST'lar 404 alıyor (GET çalışıyor);
nedeni belirsiz — birincil yol hermes + cron.
