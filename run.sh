#!/usr/bin/env bash
# Günlük bülten: feed'lerdeki yeni yazıları snappdf ile PDF'e çevirir.
#   mod=native → orijinal URL'den doğrudan
#   mod=cevir  → cevir.py ile Türkçeye çevrilir, yerelden sunulup çevrilir
# Çıktı: $OUTBASE/YYYY-MM-DD/<konu>/NN. Başlık.pdf (tek PDF, dosya adında başlık)
# Başarıyla çevrilen link $STATE'e işlenir (ertesi gün tekrarlanmaz).
#
# Ortam değişkenleri (varsayılanlar yerel Mac içindir):
#   SNAPPDF, FEEDS, STATE, OUTBASE, PORT

set -u
shopt -s nullglob
cd "$(dirname "$0")"

SNAPPDF="${SNAPPDF:-$HOME/.cargo/bin/snappdf}"
FEEDS="${FEEDS:-feeds.txt}"
STATE="${STATE:-data/seen.txt}"
OUTBASE="${OUTBASE:-$HOME/Bulten}"
PORT="${PORT:-8931}"
GUN="$(date +%F)"
LOGDIR="$PWD/logs"
mkdir -p "$LOGDIR" data "$(dirname "$STATE")"
LOG="$LOGDIR/$GUN.log"
touch "$STATE"

SERVE="$(mktemp -d)"
python3 -m http.server "$PORT" --directory "$SERVE" >/dev/null 2>&1 &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null; rm -rf $SERVE" EXIT
sleep 1

slugla() {
  local s
  s=$(echo "$1" | tr '[:upper:]' '[:lower:]')
  s=${s//ğ/g}; s=${s//ü/u}; s=${s//ş/s}; s=${s//ı/i}; s=${s//ö/o}; s=${s//ç/c}
  echo "$s" | tr -cs 'a-z0-9' '-' | cut -c1-50 | sed 's/-$//'
}

{
echo "=== bülten $GUN $(date +%T) ==="

python3 bulten.py --feeds "$FEEDS" --state "$STATE" > /tmp/snapfeed-urls.tsv
TOPLAM=$(wc -l < /tmp/snapfeed-urls.tsv | tr -d ' ')
echo "yeni yazı: $TOPLAM"

BASARILI=0
BASARISIZ=0
SIRA=0
while IFS=$'\t' read -r konu mod host url baslik; do
  [ -z "${url:-}" ] && continue
  SIRA=$((SIRA + 1))
  sira=$(printf "%02d" $SIRA)
  hedef="$OUTBASE/$GUN/$konu"
  mkdir -p "$hedef"

  if [ "$mod" = "cevir" ]; then
    echo "--- [$konu] [TR] $baslik"
    f="$SERVE/$sira.html"
    if ! python3 cevir.py "$url" "$f" >> "$LOG" 2>&1; then
      echo "    [hata] çeviri başarısız, yarın tekrar denenecek"
      BASARISIZ=$((BASARISIZ + 1))
      continue
    fi
    baslik="$(cat "$f.title" 2>/dev/null || echo "$baslik")"
    kaynak="http://127.0.0.1:$PORT/$sira.html"
    yazar="$host (TR)"
  else
    echo "--- [$konu] $baslik"
    kaynak="$url"
    yazar="$host"
  fi
  echo "    $url"

  onceki=("$hedef"/*.pdf)
  if "$SNAPPDF" "$kaynak" -o "$hedef" --page-size a5 --theme sepia \
      --lang tr --author "$yazar" >> "$LOG" 2>&1; then
    for p in "$hedef"/*.pdf; do
      eski=0
      for o in ${onceki[@]+"${onceki[@]}"}; do
        [ "$p" = "$o" ] && eski=1 && break
      done
      [ "$eski" = "0" ] && mv "$p" "$hedef/${sira}. $(slugla "$baslik").pdf"
    done
    echo "$url" >> "$STATE"
    BASARILI=$((BASARILI + 1))
  else
    echo "    [hata] PDF üretilemedi, yarın tekrar denenecek"
    BASARISIZ=$((BASARISIZ + 1))
  fi
done < /tmp/snapfeed-urls.tsv

echo "=== bitti: $BASARILI başarılı, $BASARISIZ hatalı ==="
} 2>&1 | tee -a "$LOG"
