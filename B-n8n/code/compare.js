const pages = $input.all();
const planned = $('Build page list').all();
if (!pages.length || pages.length !== planned.length) throw new Error('Eksik sayfa; kısmi sonuç kaydedilmeyecek.');
const timestamp = $('Configuration').first().json.timestamp;
const products = [];
const seen = new Set();
for (let pageIndex = 0; pageIndex < pages.length; pageIndex++) {
  const page = pages[pageIndex].json;
  const fields = ['names', 'prices', 'reviews', 'links'];
  if (fields.some(key => !Array.isArray(page[key])) || !page.names.length ||
      fields.some(key => page[key].length !== page.names.length)) {
    throw new Error(`Sayfa ${pageIndex + 1}: boş ürün listesi veya eksik alan.`);
  }
  for (let i = 0; i < page.names.length; i++) {
    const name = String(page.names[i]).trim();
    const rawPrice = String(page.prices[i]).trim();
    const rawReviews = String(page.reviews[i]).trim();
    const href = String(page.links[i]);
    if (!name || !/^\$(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$/.test(rawPrice) || !/^\d+$/.test(rawReviews) ||
        !/^\/test-sites\/e-commerce\/static\/product\/\d+$/.test(href)) {
      throw new Error(`Sayfa ${pageIndex + 1}: ürün alanları doğrulanamadı.`);
    }
    const price = Number(rawPrice.replace(/[$,]/g, ''));
    const reviews = Number(rawReviews);
    const url = 'https://webscraper.io' + href;
    if (!Number.isFinite(price) || price < 0 || !Number.isSafeInteger(reviews)) throw new Error('Geçersiz sayısal değer.');
    if (seen.has(url)) throw new Error('Yinelenen ürün: sayfalama tutarsız; önceki durum korunacak.');
    seen.add(url);
    products.push({timestamp, name, price, reviews, url, currency: 'USD'});
  }
}
const state = $getWorkflowStaticData('global');
const previous = state.previous || {};
const snapshot = {};
const changes = [];
for (const product of products) {
  const old = previous[product.url];
  snapshot[product.url] = {price: product.price, name: product.name};
  if (!old) changes.push({...product, change: 'new', oldPrice: null});
  else if (Math.round(old.price * 100) !== Math.round(product.price * 100)) {
    changes.push({...product, change: 'price_changed', oldPrice: old.price});
  }
}
const text = [`Laptop fiyat takibi — ${timestamp}`, `${pages.length} sayfa / ${products.length} ürün / ${changes.length} değişiklik`,
  state.previous ? 'Önceki başarılı çalışmayla karşılaştırıldı.' : 'İlk çalışma: tüm ürünler yeni olarak bildiriliyor.', '',
  ...changes.map(p => `${p.change === 'new' ? 'YENİ' : 'FİYAT'} | ${p.name} | ${p.oldPrice === null ? '—' : '$' + p.oldPrice.toFixed(2)} → $${p.price.toFixed(2)} | ${p.url}`)
].join('\n');
// State is only committed AFTER file writing and any notification succeed.
return [{json: {timestamp, products, snapshot, changes, hasChanges: changes.length > 0, text,
  subject: `Laptop takip: ${changes.length} yeni/fiyatı değişen ürün`}}];
