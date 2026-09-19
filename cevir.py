#!/usr/bin/env python3
"""İngilizce makale HTML'ini Türkçeye çevirir (ücretsiz, çevrimdışı Argos).

Kullanım: cevir.py <url> <cikti.html>
  - <p>, <li>, başlıklar, alıntı, figcaption ve <title> çevrilir
  - <pre>/<code>, <script>/<style>, tablolar aynen korunur (kod çevrilmez!)
  - Görsel/link URL'leri aslından mutlaklaştırılır + <base> enjekte edilir
  - Çevrilmiş sayfa başlığı <cikti.html>.title dosyasına yazılır

Yalnızca standart kütüphane + argostranslate kullanır.
"""

import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

CEVRILEN = {"title", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6",
            "blockquote", "figcaption", "summary", "dt", "dd"}
ATLANAN = {"pre", "code", "script", "style", "table", "textarea", "noscript"}
URL_ATTRS = {"src", "srcset", "data-src", "data-lazy-src", "href", "poster"}


def ozellikleri_yaz(attrs):
    """(ad, değer) listesini HTML parçasına çevirir; değersiz özellikleri korur."""
    parcalar = []
    for k, v in attrs:
        if v is None:
            parcalar.append(f" {k}")
        else:
            parcalar.append(f' {k}="{html.escape(v, quote=True)}"')
    return "".join(parcalar)


def cumlelere_bol(metin, limit=800):
    """Metni cümle sınırlarından ~limit karakterlik parçalara böler."""
    parcalar, cur = [], ""
    for c in re.split(r"(?<=[.!?])\s+", metin):
        if len(cur) + len(c) + 1 > limit and cur:
            parcalar.append(cur)
            cur = c
        else:
            cur = (cur + " " + c).strip() if cur else c
    if cur:
        parcalar.append(cur)
    return parcalar


class Cevirici(HTMLParser):
    def __init__(self, sayfa_url, cevir):
        super().__init__(convert_charrefs=True)
        self.sayfa_url = sayfa_url
        self.cevir = cevir
        self.cikti = []
        self.yigin = []
        self.base_enjekte = False
        self.baslik_parcalari = []
        self._baslikta = False

    def _cevrilebilir(self):
        if not self.yigin:
            return False
        if any(t in ATLANAN for t in self.yigin):
            return False
        return self.yigin[-1] in CEVRILEN

    def _mutlaklastir(self, tag, attrs):
        if tag in ("img", "source", "video", "a", "link"):
            yeniler = []
            for k, v in attrs:
                if k in URL_ATTRS and v and not v.startswith(("http", "data:", "#", "mailto:")):
                    if k == "srcset":
                        v = ", ".join(
                            urljoin(self.sayfa_url, p.split()[0]) +
                            (" " + " ".join(p.split()[1:]) if len(p.split()) > 1 else "")
                            for p in v.split(",") if p.strip())
                    else:
                        v = urljoin(self.sayfa_url, v)
                yeniler.append((k, v))
            return yeniler
        return attrs

    def handle_starttag(self, tag, attrs):
        self.yigin.append(tag)
        if tag == "title":
            self._baslikta = True
        if tag in ("img", "source", "video", "a", "link"):
            attrs = self._mutlaklastir(tag, attrs)
            parca = "<" + tag + ozellikleri_yaz(attrs) + ">"
        else:
            parca = self.get_starttag_text()
        self.cikti.append(parca)
        if tag == "head" and not self.base_enjekte:
            self.cikti.append(f'<base href="{html.escape(self.sayfa_url, quote=True)}">')
            self.base_enjekte = True

    def handle_endtag(self, tag):
        if self.yigin and self.yigin[-1] == tag:
            self.yigin.pop()
        elif tag in self.yigin:
            self.yigin.remove(tag)
        if tag == "title":
            self._baslikta = False
        self.cikti.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        if tag in ("img", "source", "link"):
            attrs = self._mutlaklastir(tag, attrs)
            self.cikti.append("<" + tag + ozellikleri_yaz(attrs) + ">")
        else:
            self.cikti.append(self.get_starttag_text())

    def handle_data(self, data):
        if not data.strip():
            self.cikti.append(data)
            return
        if self._baslikta:
            self.baslik_parcalari.append(data.strip())
        if self._cevrilebilir() and re.search(r"[A-Za-z]{3,}", data):
            bas = data[:len(data) - len(data.lstrip())]
            son = data[len(data.rstrip()):]
            cevrilmis = " ".join(
                self.cevir(p) for p in cumlelere_bol(data.strip()))
            self.cikti.append(bas + html.escape(cevrilmis) + son)
        else:
            self.cikti.append(html.escape(data))

    def handle_comment(self, data):
        self.cikti.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.cikti.append(f"<!{decl}>")

    def handle_pi(self, data):
        self.cikti.append(f"<?{data}>")

    def sonuc(self):
        out = "".join(self.cikti)
        if not self.base_enjekte:
            out = f'<base href="{html.escape(self.sayfa_url, quote=True)}">' + out
        return out


def argos_yukle():
    import argostranslate.package as P
    import argostranslate.translate as T
    kurulu = {(p.from_code, p.to_code) for p in P.get_installed_packages()}
    if ("en", "tr") not in kurulu:
        P.update_package_index()
        pkg = next(p for p in P.get_available_packages()
                   if p.from_code == "en" and p.to_code == "tr")
        pkg.download()
        pkg.install()
    return lambda metin: T.translate(metin, "en", "tr")


def indir(url):
    req = urllib.request.Request(url, headers={"User-Agent": "snapfeed/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ham = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
    return ham.decode(enc, errors="replace")


def main():
    url, cikti = sys.argv[1], sys.argv[2]
    print(f"[çevir] indiriliyor: {url}", flush=True)
    sayfa = indir(url)
    cevir = argos_yukle()
    p = Cevirici(url, cevir)
    p.feed(sayfa)
    with open(cikti, "w", encoding="utf-8") as f:
        f.write(p.sonuc())
    baslik = " ".join(" ".join(p.baslik_parcalari).split())
    baslik_tr = " ".join(cevir(p) for p in cumlelere_bol(baslik)) if baslik else ""
    with open(cikti + ".title", "w", encoding="utf-8") as f:
        f.write(baslik_tr)
    print(f"[çevir] tamam: {cikti} ({len(p.sonuc())} karakter)")


if __name__ == "__main__":
    main()
