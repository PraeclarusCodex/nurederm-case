# Web üzerinden kullanım — Data Table sürümü

Ana dosya `workflow.json`; `workflow-web.json` aynı dosyanın alternatif adıdır. Sunucu klasörü oluşturma veya SSH erişimi gerektirmez. Önceki `workflow-local.json` disk/CSV varyantı korunmuştur. Yeni akış pasif gelir; önceki aktif bir kopya varsa iki kopyayı aynı anda zamanlamayın.

## Tabloyu oluştur

n8n'de workflow ile **aynı proje** içinde Data tables bölümünü açıp yeni bir tablo oluştur. Önerilen ad: `nurederm_price_history`.

| Sütun adı (aynen) | Tür |
|---|---|
| timestamp | String |
| name | String |
| price | Number |
| reviews | Number |
| url | String |
| currency | String |

`timestamp` ISO tarih metni olarak tutulur. Sistem tarafından verilen id/createdAt/updatedAt sütunlarını ayrıca oluşturma. Hesabında Data tables görünmüyorsa bu sürümün desteklenip desteklenmediği kontrol edilmeli; tablo varmış gibi devam edilmemeli.

## Akışı bağla

1. Yeni, boş bir workflow aç ve `workflow.json` dosyasını import et. Masaüstündeki kopyasının adı `Nurederm-web-workflow.json`.
2. **Save price history** düğümünü aç. **Data table → From list** alanından oluşturduğun tabloyu seç. Sahte bir tablo kimliği dosyaya konulmadı.
3. **Mapping Column Mode → Map Automatically** seç. Girdi alanları ile altı sütunun adları birebir aynı olmalı. **Optimize Bulk kapalı** kalmalı; sonraki kontrol kaydedilmiş satırları kullanır.
4. **Save price history → Execute step** ile satırları yazmayı dene. Ardından **Verify saved rows** adımını çalıştır; sayı, alanlar ve sayısal türler doğrulanır.
5. **Create CSV** adımı indirilebilir CSV üretmeye devam eder. Kalıcı tarihli kayıt Data Table içindedir.
6. Configuration düğümündeki gönderen/alıcı adreslerini ayarla; Notify changes ve Notify failure düğümlerinde SMTP credential seç. Şifreleri sohbet veya workflow JSON içine yazma.
7. Gerçek alıcıyı kontrol ederek bildirim testini tamamladıktan sonra günlük akışı etkinleştir.

## Kayıt ve karşılaştırma davranışı

Ana yol: karşılaştırma → ürün satırları → Data Table insert → yazılan satırları doğrula → CSV oluştur → tek değişiklik bildirimi → başarılı snapshot kaydı.

Her çalışma yeni tarihli satırlar ekler. Manuel tekrar yürütme veya hata sonrası yeniden deneme yinelenen tarihli kayıtlar oluşturabilir; tablo arşivdir, yalnızca en güncel fiyat listesi değildir. Tablo büyüklüğü zamanla artar ve n8n kotasına tabidir; uzun süreli kullanımda saklama/temizleme politikası gerekir. Bu değişiklik geçmiş kayıtları otomatik silmez.

Karşılaştırma önceki varyanttaki gibi **son başarılı aktif yürütmenin static data snapshot'ını** kullanır; geçmiş Data Table satırlarından yeniden oluşturulmaz. Tablo yazımı, CSV veya e-posta hatasında snapshot ilerletilmez. Bildirim hatası olsa da o güne ait tablo kayıtları kalabilir. Manuel yürütmeler arasında static data kalıcılığı beklenmemeli; aktif zamanlanmış iki çalışma ayrıca test edilmelidir.

Tablo kaydı/şema hataları hata bildirim yoluna bağlıdır. Kısmi veya beklenenden farklı kayıt çıktısı da hata sayılır. SMTP bozuksa e-posta teslimi garanti edilemez; yürütme başarısız kalır.

## Kontrol durumu

- Önceki sürümün n8n import, 20 sayfa tarama ve 117 ürünlük CSV üretimi kullanıcı ekranlarıyla doğrulandı.
- Sunucu disk yazımı `The file or directory does not exist` hatası verdi; bu sürüm disk düğümünü kaldırır.
- Yeni sürüm için beş yerel test: disk bağımlılığının kaldırılması, tablo alan türleri, tam/kısmi/yanlış tipte kayıt dönüşleri, işlem sırası ve hata bağlantıları geçti.
- Data Table, SMTP, iki zamanlanmış çalışma (117 yeni → 0 değişiklik) ve ayrı kopyadaki DNS hata bildirimi canlı doğrulandı. Ayrıntılar: [CANLI-TESTLER.md](CANLI-TESTLER.md).
- Son ana export Europe/Istanbul ve `0 9 * * *` ayarlarını içeriyor. Teslim kopyası pasiftir; kurulumdan sonra Publish gerekir.

Kaynaklar: [n8n Data Tables](https://github.com/n8n-io/n8n-docs/blob/main/docs/build/work-with-data/data-tables.md), [resmî Insert düğümü](https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/DataTable/actions/row/insert.operation.ts).

Yeniden üretme: önce `python3 B-n8n/build_workflow.py`, ardından `python3 B-n8n/build_web_workflow.py`. Test: `cd B-n8n && npm test`.
