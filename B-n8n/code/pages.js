// All pagination links include the last page on this static test site.
const html = $input.first().json.data;
if (typeof html !== 'string' || !html.includes('static-pagination')) {
  throw new Error('Sayfalama alanı bulunamadı; site/HTML yapısı değişmiş olabilir.');
}
const pages = [...html.matchAll(/href=["'][^"']*\/static\/computers\/laptops\?page=(\d+)["']/g)]
  .map(match => Number(match[1]));
const lastPage = Math.max(1, ...pages);
if (!Number.isInteger(lastPage) || lastPage > 200) throw new Error('Sayfa güvenlik sınırı aşıldı.');
return Array.from({length: lastPage}, (_, i) => ({json: {
  page: i + 1,
  totalPages: lastPage,
  url: `https://webscraper.io/test-sites/e-commerce/static/computers/laptops?page=${i + 1}`,
}}));
