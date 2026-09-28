"""Anahtarsız, temsilci onaylı müşteri mesajı işleme aracı."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import html
import json
from pathlib import Path
import re
import ssl
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

TOPICS = ('urun-sorusu', 'fiyat', 'siparis-durumu', 'iade-sikayet', 'istenmeyen-etki', 'diger')
BASE = Path(__file__).resolve().parent


def normalize(text):
    text = text.replace('ı', 'i').replace('İ', 'i').lower()
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


def classify(text):
    """Tek konu; güvenlik > iade > sipariş > fiyat > ürün > diğer."""
    t = normalize(text)
    if re.search(r'yan(di|ma|iyor)|yak(ti|iyor|ma)|kizar|alerj|tahris|kasin|kasint|sisti|sisme|sislik|dokuntu|sivilce|akne|reaksiyon'
                 r'|irritasyon|burn|rash|allerg|irritat|swelling|itch|breakout', t):
        return 'istenmeyen-etki'
    # Güvenlik ağı: kullanım sonrası + vücut bölgesi anlatımı belirtisi tanınmasa da insana gider (yanlış pozitif kabul edilir).
    if (re.search(r'\b(yuz|cilt|cild|goz|dudak|boyun|el(im|lerim)|skin|face|eye|lip)', t)
            and re.search(r'sonra(si)?\b|kullandim|kullaninca|surdum|surdukten|surunce|after (using|applying)', t)):
        return 'istenmeyen-etki'
    if re.search(r'iade|sikayet|ezik|kirik|hasar|bozuk|yanlis urun|eksik (geldi|urun|cikti)|bos (geldi|cikti)|degistir'
                 r'|geri istiyorum|memnun (kalmadim|degilim)|gec geldi|son kullanma tarihi gecmis|farkli (renk|urun)|istemedim'
                 r'|refund|return|damaged|complaint|wrong item|expired', t):
        return 'iade-sikayet'
    if re.search(r'siparis|\border\b|\btracking\b', t):
        return 'siparis-durumu'
    if re.search(r'fiyat|ne kadar|kac (tl|para|lira)|ucret|indirim|kupon|kampanya|price|cost|discount|how much', t):
        return 'fiyat'
    if re.search(r'urun|serum|retinol|krem|tonik|vitamin|cilt|cild|icerik|alkol|\bml\b|sampuan|maske|parfum|sac|uygun mu'
                 r'|kullanil|hamile|vegan|paraben|icinde|jel|product|moistur|sunscreen|skin', t):
        return 'urun-sorusu'
    return 'diger'


def order_ids(text):
    t = normalize(text)
    patterns = [r'\b(\d+)\s*(?:numarali|nolu|no\.?lu)\s*siparis',
                r'siparis(?:im(?:in)?)?\s*(?:numarasi|numaram|no(?:su)?|#)?\s*[:#-]?\s*(\d+)',
                r'\border\s*(?:number|no\.?)?\s*[:#-]?\s*(\d+)',
                r'#\s*(\d+)']
    suffix = r'\b(?!\s*(?:ml|litre|lt|gr|gram|kg|tl|usd|eur)\b)'
    return sorted({int(n) for p in patterns for n in re.findall(p.replace(r'(\d+)', r'(\d+)' + suffix), t)})


class ApiFailure(Exception):
    pass


class Api:
    def __init__(self):
        # Sertifika doğrulamasını kapatmadan macOS Python CA kurulumunu destekler.
        try:
            import certifi
            self.context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            self.context = ssl.create_default_context()
        self.cache = {}

    def _get(self, url):
        """JSON döndürür; HTTP 404 için None. Geçici hatalarda en fazla 3 deneme."""
        request = Request(url, headers={'User-Agent': 'TalepMasasi/1.0', 'Accept': 'application/json'})
        for attempt in range(3):
            try:
                with urlopen(request, timeout=10, context=self.context) as response:
                    data = json.load(response)
                if not isinstance(data, dict):
                    raise ApiFailure('API yanıtı nesne değil')
                return data
            except HTTPError as exc:
                if exc.code == 404:
                    return None
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise ApiFailure(f'API HTTP {exc.code}') from None
            except (URLError, TimeoutError, OSError):
                if attempt == 2:
                    raise ApiFailure('API bağlantı/zaman aşımı hatası') from None
            except (ValueError, UnicodeError):
                raise ApiFailure('API geçersiz JSON döndürdü') from None
            time.sleep(0.5 * (2 ** attempt))

    def cart(self, number):
        if number not in self.cache:
            data = self._get(f'https://dummyjson.com/carts/{number}')
            if data is not None and re.search(r'cart.*not found', str(data.get('message', '')), re.I):
                data = None
            self.cache[number] = data
        return self.cache[number]

    def search(self, query):
        """Bonus: /products/search. Yalnızca ürün listesini döndürür."""
        key = ('search', query)
        if key not in self.cache:
            data = self._get(f'https://dummyjson.com/products/search?q={quote(query)}&limit=10'
                             '&select=title,price,category')
            products = (data or {}).get('products')
            self.cache[key] = products if isinstance(products, list) else []
        return self.cache[key]


# Bonus arama: Türkçe ürün terimi -> test mağazasının İngilizce arama sözcükleri.
SEARCH_TERMS = [
    (r'gunes kremi|spf|sunscreen', ['sunscreen']),
    (r'nemlendirici|moistur', ['moisturizer', 'lotion']),
    (r'retinol', ['retinol']),
    (r'c vitamini|vitamin c', ['vitamin c']),
    (r'serum', ['serum']),
    (r'tonik|toner', ['toner']),
    (r'krem|cream', ['cream']),
]
BEAUTY_CATEGORIES = {'beauty', 'skin-care', 'fragrances'}


def search_terms(text):
    t = normalize(text)
    terms = []
    for pattern, queries in SEARCH_TERMS:
        if re.search(pattern, t):
            terms += [q for q in queries if q not in terms]
    return terms


def product_suggestions(text, api, limit=3):
    """Başlığında arama sözcüğü geçen kozmetik kategorisindeki ürünler (ör. 'Ice Cream' elenir)."""
    terms = search_terms(text)
    found, seen = [], set()
    for term in terms:
        for p in api.search(term):
            if not isinstance(p, dict) or not isinstance(p.get('title'), str) or p.get('id') in seen:
                continue
            if p.get('category') not in BEAUTY_CATEGORIES or term.lower() not in p['title'].lower():
                continue
            if isinstance(p.get('price'), bool) or not isinstance(p.get('price'), (int, float)):
                continue
            seen.add(p.get('id'))
            found.append(p)
    return terms, found[:limit]


def process(message, api):
    text = message['mesaj']
    topic = classify(text)
    result = dict(id=message['id'], konu=topic, devret=False, cevap_taslagi='', not_='')
    def finish(reply, note, handoff=False):
        result.update(cevap_taslagi=reply, devret=handoff)
        result.pop('not_', None)
        result['not'] = note
        return result
    if topic in ('istenmeyen-etki', 'iade-sikayet'):
        return finish('Mesajınızı değerlendirmesi için müşteri temsilcimize yönlendiriyorum.',
                      'Hassas konu; yalnızca insana devir. Ürün önerisi veya teşhis üretilmedi.', True)
    if topic == 'siparis-durumu':
        ids = order_ids(text)
        english = bool(re.search(r'\b(my order|where is|tracking)\b', text, re.I))
        if len(ids) != 1:
            return finish('Kontrol edebilmemiz için tek bir sipariş numarası paylaşır mısınız?',
                          'Sipariş numarası yok veya birden fazla; kargo firması hakkında doğrulanmış bilgi yok.', True)
        number = ids[0]
        try:
            cart = api.cart(number)
        except ApiFailure as exc:
            return finish('Siparişinizi şu anda kontrol edemiyoruz. Talebinizi temsilcimize yönlendiriyorum.',
                          str(exc), True)
        if cart is None:
            return finish(f'{number} numaralı sipariş bulunamadı. Lütfen sipariş numaranızı kontrol edin.',
                          'API: sipariş bulunamadı; manuel kontrol gerekli.', True)
        # Sahip kontrolü ürünlere erişmeden önce yapılır. Yanıta sahip kimliği yazılmaz.
        if type(cart.get('userId')) is not int or cart['userId'] != message['musteri_id']:
            return finish('Siparişi hesabınızla doğrulayamadık. Kontrol için temsilcimize yönlendiriyorum.',
                          'Sahiplik doğrulanamadı; ürün, tutar ve diğer müşterinin kimliği paylaşılmadı.', True)
        try:
            if type(cart.get('id')) is not int or cart['id'] != number:
                raise ValueError()
            products = cart['products']
            if not isinstance(products, list) or not products:
                raise ValueError()
            lines = []
            for p in products:
                if not isinstance(p.get('title'), str) or not p['title'].strip() or type(p.get('quantity')) is not int or p['quantity'] <= 0:
                    raise ValueError()
                lines.append(f"{p['title']} × {p['quantity']}")
            if isinstance(cart['total'], bool):
                raise ValueError()
            total = Decimal(str(cart['total']))
            if not total.is_finite() or total < 0:
                raise ValueError()
        except (KeyError, TypeError, ValueError, InvalidOperation, AttributeError):
            return finish('Sipariş verileri doğrulanamadı. Talebinizi temsilcimize yönlendiriyorum.',
                          'API şema/veri doğrulama hatası.', True)
        listing = '; '.join(lines)
        reply = (f'Order #{number}: {listing}. Total: {total:.2f} (test API amount; currency unspecified). '
                 'The API does not provide shipping status or a delivery date.' if english else
                 f'{number} numaralı siparişiniz: {listing}. Toplam: {total:.2f} (test API tutarı; para birimi belirtilmiyor). '
                 'Bu API kargo durumu veya teslim tarihi sağlamıyor.')
        note = 'Sahiplik doğrulandı; ürünler ve total API’den alındı. Kargo tarihi uydurulmadı.'
        if re.search(r'fiyat|ne kadar|price', normalize(text)):
            reply += ' Ürün fiyatı sorunuz için ürünün tam adını paylaşabilirsiniz.'
            note += ' Birden çok niyet: sipariş önceliklendirildi, fiyat sorusu korundu.'
        return finish(reply, note)
    if topic in ('fiyat', 'urun-sorusu'):
        if topic == 'fiyat':
            reply = 'Güncel fiyat veya kampanyayı doğrulayabilmemiz için ilgilendiğiniz ürünün tam adını paylaşır mısınız?'
            note = 'Doğrulanmış marka fiyat/kampanya kaynağı yok; fiyat uydurulmadı.'
        else:
            reply = 'Ürün bilgisini kontrol edebilmemiz için tam ürün adını veya ürün bağlantısını paylaşır mısınız?'
            note = 'Doğrulanmış marka kataloğu yok; cilt uygunluğu, içerik veya hayvan testi iddiası üretilmedi.'
        try:
            terms, found = product_suggestions(text, api)
        except ApiFailure as exc:
            return finish(reply, f'{note} Bonus ürün araması yapılamadı: {exc}.')
        if not terms:
            return finish(reply, f'{note} Bonus arama: mesajda aranacak ürün terimi yok.')
        if found:
            listing = '; '.join(f"{p['title']} ({p['price']:.2f})" for p in found)
            reply += f' Test mağazasında eşleşen ürünler: {listing}. Fiyatlar test API değeridir.'
            note += f" Bonus arama ({', '.join(terms)}): {len(found)} ürün eklendi."
        else:
            note += f" Bonus arama ({', '.join(terms)}): test mağazasında eşleşen kozmetik ürün yok."
        return finish(reply, note)
    return finish('', 'Kapsam dışı veya reklam mesajı; otomatik cevap taslağı üretilmedi.')


def validate_messages(messages):
    if not isinstance(messages, list):
        raise ValueError('Girdi bir JSON listesi olmalı.')
    ids = set()
    for m in messages:
        if not isinstance(m, dict) or not all(k in m for k in ('id', 'kanal', 'musteri_id', 'mesaj')):
            raise ValueError('Mesaj alanları eksik.')
        if type(m['id']) is not int or m['id'] <= 0 or m['id'] in ids:
            raise ValueError('Mesaj kimlikleri benzersiz pozitif tam sayı olmalı.')
        if type(m['musteri_id']) is not int or m['musteri_id'] <= 0:
            raise ValueError('Müşteri kimliği pozitif tam sayı olmalı.')
        if m['kanal'] not in ('whatsapp', 'instagram') or not isinstance(m['mesaj'], str) or not m['mesaj'].strip():
            raise ValueError('Geçersiz kanal veya boş mesaj.')
        ids.add(m['id'])


def render_summary(messages, results, timestamp):
    esc = lambda v: html.escape(str(v), quote=True)
    counts = Counter(r['konu'] for r in results)
    tiles = ''.join(f'<div class="topic"><span>{esc(t)}</span><b>{counts[t]}</b></div>' for t in TOPICS)
    source = {m['id']: m for m in messages}
    rows = []
    for r in sorted(results, key=lambda r: (not r['devret'], r['id'])):
        m = source[r['id']]
        rows.append(f'<article data-topic="{esc(r["konu"])}" data-handoff="{str(r["devret"]).lower()}"><div class="rowtop"><span>#{r["id"]:02d} · {esc(m["kanal"])}</span><span class="badge {"warm" if r["devret"] else ""}">{"Temsilciye devret" if r["devret"] else "Taslak hazır" if r["cevap_taslagi"] else "Yanıt yok"}</span></div><h3>{esc(m["mesaj"])}</h3><div class="label">{esc(r["konu"])}</div><p>{esc(r["cevap_taslagi"]) or "—"}</p><details><summary>Karar gerekçesi</summary><p>{esc(r["not"])}</p></details></article>')
    template = (BASE / 'summary-template.html').read_text(encoding='utf-8')
    values = dict(TIME=esc(timestamp), TOTAL=str(len(results)), HANDOFF=str(sum(r['devret'] for r in results)),
                  DRAFTS=str(sum(bool(r['cevap_taslagi']) and not r['devret'] for r in results)),
                  TILES=tiles, ROWS=''.join(rows))
    return re.sub(r'@@(\w+)@@', lambda match: values[match.group(1)], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BASE / 'mesajlar.json')
    parser.add_argument('--output-dir', type=Path, default=BASE)
    args = parser.parse_args()
    try:
        messages = json.loads(args.input.read_text(encoding='utf-8'))
        validate_messages(messages)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'Girdi hatası: {exc}\n')
    api = Api()
    results = [process(m, api) for m in messages]
    timestamp = datetime.now(timezone.utc).isoformat()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in [('talepler.json', json.dumps(results, ensure_ascii=False, indent=2) + '\n'),
                          ('ozet.html', render_summary(messages, results, timestamp))]:
        target = args.output_dir / name
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(target)
    print(json.dumps({'toplam': len(results), 'konular': {t: sum(r['konu'] == t for r in results) for t in TOPICS},
                      'devredilecek': sum(r['devret'] for r in results)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
