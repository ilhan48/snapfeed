#!/usr/bin/env python3
"""Günün bülten indeksini üretir: konulara göre yazı listesi tek sayfa HTML.

Kullanım: index.py --manifest gun.tsv --date 2026-09-19 --out indeks.html
Manifest satırı: konu, mod, başlık, url, dosyaadı (TSV).
Yalnızca standart kütüphane kullanır.
"""

import argparse
import html
from collections import OrderedDict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    konular = OrderedDict()
    with open(args.manifest, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 5:
                continue
            konu, mod, baslik, url, dosya = p
            konular.setdefault(konu, []).append((mod, baslik, url, dosya))

    toplam = sum(len(v) for v in konular.values())
    parcalar = [f"<html><head><meta charset='utf-8'>"
                f"<title>Günlük Bülten — {args.date}</title></head><body>",
                f"<h1>Günlük Bülten — {args.date}</h1>",
                f"<p>{toplam} yazı, {len(konular)} konu. "
                f"Dosyalar konu klasörlerinde, bu listeyle aynı sırada.</p>"]
    for konu, yazilar in konular.items():
        parcalar.append(f"<h2>{html.escape(konu)} ({len(yazilar)})</h2><ol>")
        for mod, baslik, url, dosya in yazilar:
            etiket = " <em>[İngilizceden çeviri]</em>" if mod == "cevir" else ""
            parcalar.append(
                f"<li><strong>{html.escape(baslik)}</strong>{etiket}<br>"
                f"<small>{html.escape(dosya)}<br>{html.escape(url)}</small></li>")
        parcalar.append("</ol>")
    parcalar.append("</body></html>")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(parcalar))
    print(f"[indeks] {toplam} yazı → {args.out}")


if __name__ == "__main__":
    main()
