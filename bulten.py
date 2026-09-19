#!/usr/bin/env python3
"""feeds.txt'teki kaynaklardan en yeni yazıların linklerini çıkarır.

Kullanım:
    bulten.py --feeds feeds.txt --state data/seen.txt

Feed satırı (5 sütun): konu | mod | ad | url | sayı
Eski 4 sütunlu biçim de desteklenir (mod varsayılan: native).

Çıktı: TSV (konu, mod, host, url, başlık) — yalnızca daha önce
görülmemiş (seen.txt'te olmayan) linkler listelenir.
Yalnızca standart kütüphane kullanır; RSS 2.0 ve Atom destekler.
"""

import argparse
import sys
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


def local(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def children_by_name(elem, name):
    return [c for c in elem if local(c.tag) == name]


def first_text(elem, name):
    kids = children_by_name(elem, name)
    if kids and kids[0].text:
        return kids[0].text.strip()
    return ""


def entry_link(entry):
    # RSS: <link>metin</link> | Atom: <link href="..."/>
    for link in children_by_name(entry, "link"):
        if link.text and link.text.strip().startswith("http"):
            return link.text.strip()
        href = (link.get("href") or "").strip()
        if href.startswith("http"):
            return href
    # Yedek: guid / id
    for name in ("guid", "id"):
        val = first_text(entry, name)
        if val.startswith("http"):
            return val
    return ""


def looks_pdfable(url):
    """Video/podcast/isyeri sayfalarını ele."""
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return False
    skip_hosts = ("youtube.com", "youtu.be", "vimeo.com", "podcasts.apple.com",
                  "open.spotify.com", "anchor.fm", "meetup.com", "eventbrite.com")
    skip_exts = (".mp4", ".mp3", ".wav", ".avi", ".mov", ".zip", ".tar.gz")
    if host.endswith(skip_hosts):
        return False
    if url.lower().split("?")[0].endswith(skip_exts):
        return False
    return True


def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    if local(root.tag) == "rss":
        for item in root.iter():
            if local(item.tag) == "item":
                items.append(item)
    else:  # Atom / RDF / diğerleri
        for entry in root.iter():
            if local(entry.tag) in ("entry", "item"):
                items.append(entry)
    out = []
    for it in items:
        title = first_text(it, "title") or "(başlıksız)"
        url = entry_link(it)
        if url and looks_pdfable(url):
            out.append((url, " ".join(title.split())[:120]))
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "snapfeed/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def load_feeds(path):
    feeds = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 5:
                topic, mod, _name, url, count = parts
            elif len(parts) == 4:
                topic, _name, url, count = parts
                mod = "native"
            else:
                print(f"hatalı satır atlandı: {line}", file=sys.stderr)
                continue
            if mod not in ("native", "cevir"):
                print(f"hatalı mod atlandı: {line}", file=sys.stderr)
                continue
            feeds.append((topic, mod, url, int(count)))
    return feeds


def load_seen(path):
    try:
        with open(path, encoding="utf-8") as f:
            return {ln.strip() for ln in f if ln.strip()}
    except FileNotFoundError:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", required=True)
    ap.add_argument("--state", required=True)
    args = ap.parse_args()

    feeds = load_feeds(args.feeds)
    seen = load_seen(args.state)

    for topic, mod, url, count in feeds:
        try:
            entries = parse_feed(fetch(url))[:count]
        except Exception as e:  # tek ölü kaynak bülteni durdurmaz
            print(f"[atla] {url}: {e}", file=sys.stderr)
            continue
        for link, title in entries:
            if link in seen:
                continue
            try:
                host = urlparse(link).netloc or "bilinmeyen"
            except ValueError:
                continue
            print(f"{topic}\t{mod}\t{host}\t{link}\t{title}")


if __name__ == "__main__":
    main()
