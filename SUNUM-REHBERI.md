# Çözümü nasıl anlatırsın?

## 45 saniyelik özet

“İşi iki parçaya ayırdım. İlk parçada mesajları tek konuya atayan, hassas konuları insana devreden ve sipariş sahibini doğrulamadan bilgi göstermeyen bir araç hazırladım. İkinci parçada hazır n8n fiyat takibi şablonundan başlayıp tüm sayfaları gezen, günlük Data Table kaydı ve CSV üreten ve değişiklikte veya hatada e-posta bildiren bir akış tasarladım. Yapay zekâyla kodu hazırladıktan sonra güvenlik ve hata senaryolarını test ettim. A gerçek API ile çalıştı; B de n8n üzerinde çalıştı: 117 ürün kaydedildi, ilk bildirim geldi, sonraki otomatik çalışmada sıfır değişiklik görüldü ve ayrı kopyada hata e-postası test edildi.”

## Sorulabilecek sorular

**Neden her şeyi yapay zekâya bırakmadın?**
Sahiplik doğrulaması ve hassas konu devri sabit kurallar olmalı. Bu küçük testte haricî model hesabı kullanmadan izlenebilir bir çözüm kurdum. Daha kapsamlı bir sürümde modele sadece konu/niyet önerisi verdirip yetkilendirmeyi uygulama tarafında tutarım.

**Sipariş 12 neden görünmüyor?**
Mesajın müşteri kimliği ile API'nin sipariş sahibi uyuşmuyor. Ürünleri, toplamı veya gerçek sahibin kimliğini paylaşmadan temsilciye devrediyorum.

**Neden kargo tarihini söylemiyor?**
DummyJSON sepet API'sinde kargo aşaması ve teslim tarihi yok. Var olmayan veriyi üretmek yerine eksikliği açıkça belirtiyorum.

**Neden Data Table ve CSV?**
Sunucu klasörüne yazma denemesi başarısız oldu. Kalıcı tarihli kayıt için n8n Data Table kullandım; CSV ayrıca indirilebilir çıktı. Karşılaştırma son başarılı çalışmanın static data snapshot'ıyla yapılıyor. Her çalışmada tabloya yeni satırlar eklenir.

**Testler ne yakaladı?**
“200 ml” ifadesinin sipariş numarası sanılması ve sitedeki `$399` fiyatının ondalık zorunluluğu nedeniyle reddedilmesi. İkisi için de düzeltme ve regresyon testi eklendi.

**Site yarıda kapanırsa ne olur?**
Tam sayfa sayısı eşleşmez, hata bildirimi hazırlanır ve önceki başarılı durum korunur. Akış hata durumuyla biter.

**Hiç fiyat değişmezse?**
O günün Data Table kaydı ve CSV çıktısı oluşur, değişiklik e-postası gitmez.

**Gerçek müşteri hizmetine yarın bağlar mısın?**
Önce müşteri kimliğini doğrulayan WhatsApp/Instagram entegrasyonu, gerçek sipariş/katalog kaynağı, daha geniş sınıflandırma değerlendirmesi ve n8n uçtan uca testleri gerekir. Bu teslimin kapsamı case senaryosudur.

## Teslimden önce

1. README komutuyla A'yı kendi bilgisayarında çalıştır ve `ozet.html` dosyasını aç.
2. A'daki beş devrin gerekçesini incele; özellikle 1 ve 3 numaralı mesajları açıklayabildiğinden emin ol.
3. B'nin kurulum ve doğrulanmayan kısımlarını oku. Canlı çalıştırmadıysan çalıştırdığını söyleme.
4. İstersen platformdan tam konuşma dökümünü prompt klasörüne ekle; olmayan prompt veya çalışma saati üretme.
5. Bu klasörü kendi GitHub depona yükle; gizli anahtar veya `.env` ekleme. README'deki yayın durumunu ancak gerçekten yayınladıktan sonra güncelle.
6. Depo bağlantısını ve dürüst kapsam notunu teslim mesajında paylaş. Görev e-postasını aldığın saate göre 3 saat sınırını kendin kontrol et.
