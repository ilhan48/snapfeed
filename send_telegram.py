#!/usr/bin/env python3
"""Günün bülten PDF'lerini Telegram'a gönderir (konu başına albüm).

Kullanım: send_telegram.py --dir bulten-out/2026-09-19
Gereken ortam: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
Yoklarsa uyarıp sessizce çıkar (PDF'ler artifact olarak yine saklanır).
Yalnızca standart kütüphane kullanır.
"""

import argparse
import json
import mimetypes
import os
import sys
import urllib.request
import uuid

API = "https://api.telegram.org"


def multipart(parametreler, dosyalar):
    """parametreler: dict, dosyalar: [(alan, dosyaadı, bytes)] -> (body, content_type)"""
    sinir = uuid.uuid4().hex
    govde = b""
    for k, v in parametreler.items():
        govde += (f"--{sinir}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    for alan, ad, icerik in dosyalar:
        tip = mimetypes.guess_type(ad)[0] or "application/octet-stream"
        govde += (f"--{sinir}\r\nContent-Disposition: form-data; name=\"{alan}\"; filename=\"{ad}\"\r\n"
                  f"Content-Type: {tip}\r\n\r\n").encode() + icerik + b"\r\n"
    govde += f"--{sinir}--\r\n".encode()
    return govde, f"multipart/form-data; boundary={sinir}"


def post(yontem, parametreler=None, dosyalar=None, token=""):
    govde, ct = multipart(parametreler or {}, dosyalar or [])
    req = urllib.request.Request(f"{API}/bot{token}/{yontem}", data=govde,
                                 headers={"Content-Type": ct})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("[telegram] token/chat-id yok, gönderim atlandı")
        return

    try:  # token ön kontrolü (değer loga yazılmaz)
        urllib.request.urlopen(f"{API}/bot{token}/getMe", timeout=30).read()
    except Exception as e:
        print(f"[telegram] token geçersiz: {type(e).__name__}")
        sys.exit(1)

    gun = os.path.basename(os.path.normpath(args.dir))
    konular = sorted(d for d in os.listdir(args.dir)
                     if os.path.isdir(os.path.join(args.dir, d)))
    toplam = 0
    post("sendMessage", {"chat_id": chat,
         "text": f"📰 Günlük bülten — {gun}\nKonular: {', '.join(konular)}"})
    for konu in konular:
        kdir = os.path.join(args.dir, konu)
        pdfler = sorted(f for f in os.listdir(kdir) if f.endswith(".pdf"))
        if not pdfler:
            continue
        medya, dosyalar = [], []
        for i, pdf in enumerate(pdfler[:10]):  # Telegram albüm limiti: 10
            with open(os.path.join(kdir, pdf), "rb") as f:
                icerik = f.read()
            alan = f"belge{i}"
            dosyalar.append((alan, pdf, icerik))
            oge = {"type": "document", "media": f"attach://{alan}"}
            if i == 0:
                oge["caption"] = f"📚 {konu} — {gun} ({len(pdfler)} yazı)"
            medya.append(oge)
        post("sendMediaGroup", {"chat_id": chat, "media": json.dumps(medya)}, dosyalar)
        toplam += len(pdfler)
        print(f"[telegram] {konu}: {len(pdfler)} PDF gönderildi")
    print(f"[telegram] toplam {toplam} PDF")


if __name__ == "__main__":
    main()
