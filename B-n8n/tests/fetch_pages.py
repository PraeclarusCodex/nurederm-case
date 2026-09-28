"""Canlı siteyi okur; bildirim veya n8n çalıştırmaz. HTML test dosyaları gitignore'da."""
from pathlib import Path
import re
import ssl
import time
from urllib.request import Request, urlopen
import certifi

target = Path(__file__).resolve().parents[1] / 'data' / 'live-pages'
target.mkdir(parents=True, exist_ok=True)
context = ssl.create_default_context(cafile=certifi.where())
base = 'https://webscraper.io/test-sites/e-commerce/static/computers/laptops'


def fetch(url):
    request = Request(url, headers={'User-Agent':'TalepMasasi/1.0'})
    with urlopen(request, timeout=20, context=context) as response:
        return response.read().decode('utf-8')


first = fetch(base)
last = max([1] + [int(n) for n in re.findall(r'href=["\'][^"\']*/static/computers/laptops\?page=(\d+)["\']', first)])
if not 1 <= last <= 200:
    raise ValueError('Sayfa sınırı aşıldı')
for page in range(1, last + 1):
    text = first if page == 1 else fetch(f'{base}?page={page}')
    (target / f'{page}.html').write_text(text)
    time.sleep(0.25)
(target / 'count.txt').write_text(str(last))
print(f'{last} sayfa indirildi.')
