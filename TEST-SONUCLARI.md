# Test sonuçları

28 Eylül 2026 · Python 3.13 · Node.js 20 · Her push'ta GitHub Actions ile tekrar çalışır. Temiz klonda README adımları ayrıca denendi.

## Otomatik testler

| Kontrol | Sonuç | Komut |
|---|---|---|
| A: birim testleri | 22 / 22 | `python3 -m unittest discover -s A-mesaj-otomasyonu/tests -v` |
| A: sınıflandırma, 45 ek mesaj | 45 / 45 (kör ölçüm: 19/30 ve 10/15) | `python3 A-mesaj-otomasyonu/degerlendir.py` |
| A: canlı DummyJSON | 15 mesaj, 5 devir | `python3 A-mesaj-otomasyonu/main.py` |
| B: workflow mantık ve yapı testleri | 17 / 17 | `cd B-n8n && npm test` |
| B: canlı site taraması | 20 sayfa, 117 ürün | `cd B-n8n && npm run test:live` → `live-check.json` |

**A testlerinin kapsamı:** verilen 15 mesajın konuları, hassas konunun siparişten önce gelmesi, başka müşterinin sipariş bilgisinin sızmaması, ürünlere bakmadan önce sahiplik kontrolü, geçerli sipariş, bulunamayan sipariş, bağlantı hatası, eksik/çoklu/birimli numara, Türkçe ve İngilizce numara çıkarma, çoklu niyet, bozuk API alanları, HTML kaçışlama, girdi doğrulama, 404 önbelleği, sınırlı tekrar, ürün arama bonusu (kategori/başlık filtresi, eşleşme yok, API hatası, hassas mesajda arama yapılmaması).

**B testlerinin kapsamı:** son sayfanın bulunması, bozuk sayfalama, HTML seçicileri, ilk/aynı/değişen snapshot, kısmi/boş/yinelenen/bozuk ürün, binlik ayıracı ve kuruşsuz fiyat, CSV formül kaçışlama, durumun yalnızca en sonda kaydedilmesi, Data Table satır doğrulaması, düğüm bağlantıları ve hata yolları.

## Canlı n8n doğrulaması (n8n web)

| Kontrol | Sonuç |
|---|---|
| Data Table kaydı | 117 satır; price ve reviews sayısal |
| Verify saved rows | 117 satırın sayısı, URL'si, alanları ve türleri doğrulandı |
| CSV | `laptops.csv`, 117 satır |
| 1. zamanlanmış çalışma (11:18) | Başarılı; 117 yeni ürün, bildirim e-postası alındı |
| 2. zamanlanmış çalışma (11:20) | Başarılı; 0 değişiklik, e-posta gönderilmedi |
| Hata senaryosu (11:26) | Ayrı kopyada erişilemeyen adres: `getaddrinfo ENOTFOUND` hata e-postası alındı, çalışma başarısız işaretlendi |
| Son dışa aktarım | `0 9 * * *`, Europe/Istanbul |

Fiyat değişikliği bildirimi canlıda beklenmedi. Bu durum yerel testte tek fiyat değiştirilerek simüle edildi ve 1 değişiklik yakalandı.
