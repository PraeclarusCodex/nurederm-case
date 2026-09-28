# Süreç notu — kararlar, hatalar ve çözümler

Çalışma sırasında yapay zekâ aracının attığı adımların ve karşılaşılan hataların kronolojik özeti. Promptların kendisi `codex-tam-prompt-dokumu.md` dosyasında.

1. Brief ve `mesajlar.json` okundu; görev A ve B olarak ikiye ayrıldı.
2. DummyJSON ve Web Scraper kaynakları, n8n şablon kütüphanesi ve resmî düğüm kaynak kodları araştırıldı. #837 şablonunun gerçek JSON'u indirilip düğümleri incelendi.
3. İlk Python HTTPS istekleri makinenin varsayılan sertifika deposu eksik olduğu için başarısız oldu. TLS doğrulaması kapatılmadı; certifi CA paketi kullanıldı.
4. İlk Python DummyJSON çağrıları HTTP 403 döndürdü; curl çağrısı çalıştı. Açık bir User-Agent ve Accept başlığı taşıyan Python isteği başarılı oldu; istemci buna göre düzeltildi.
5. Web aracı DummyJSON veri endpoint'lerini açamadı. Doğrulama gerçek HTTPS istekleriyle yerel istemcide yapıldı.
6. n8n kaynak dosyaları için ilk ConvertToFile ve ReadWriteFile yolları 404 döndü. Resmî depo içinde doğru `Files/` alt dizini bulunup parametre adları kontrol edildi. Eski static-data doküman URL'si de bulunamadı; resmî n8n blogu ve kaynak kodlarıyla devam edildi.
7. A: önce hassas konu, sonra sipariş sahiplik kontrolü uygulanacak şekilde kurallı işleyici yazıldı. Veri olmayan yerlerde fiyat, kargo veya ürün iddiası üretmeme kararı alındı.
8. A'nın ilk test turunda `Siparişim 200 ml krem, fiyat 500 TL` metnindeki 200 yanlışlıkla sipariş numarası sayıldı. Birim ve para birimi son ekleri filtrelendi. Düzenleme sırasında sınır kontrolünün sayı grubuna uygulanması sağlandı. 16 testin tamamı geçti.
9. A canlı API ile çalıştırıldı: 15 talep ve 5 devir. Sipariş 12'nin bu mesajın müşterisine ait olmadığı görüldü; detaylar çıktıya eklenmedi.
10. B: modern n8n düğümleriyle tüm sayfaları keşfeden, CSV oluşturan, değişiklik ve hata e-postaları olan akış yeniden kuruldu. Başarılı snapshot yalnızca dosya ve bildirim sonrasında güncellenir.
11. B test bağımlılıklarının hazırlanmasında ilk dosya yazma komutu yanlış çalışma dizini nedeniyle başarısız oldu. Başlayan gereksiz npm işlemi durduruldu; doğru dizinde package.json oluşturulup bağımlılıklar kuruldu. Eski `whatwg-encoding` için transitif deprecation uyarısı alındı; kurulumu engellemedi.
12. İlk B mantık testlerinin 11'i geçti. Ardından canlı 20 sayfa okundu. Üçüncü sayfada `$399` ve `$679` biçimleri görülünce iki ondalık zorunluluğu nedeniyle doğrulama hata verdi. Kuruşsuz fiyatlar desteklendi ve regresyon testi eklendi. 12 B testi geçti.
13. Aynı 20 canlı HTML sayfasıyla toplam 117 ürün çıkarıldı. İlk çalışmada 117 yeni ürün, aynı veriyle ikinci çalışmada 0 değişiklik ve tek fiyatı değiştiren simülasyonda 1 değişiklik doğrulandı.
14. HTML paneli için yerel önizleme açılmaya çalışıldı. Tarayıcı yönetici güvenlik politikasını doğrulayamadığı için erişimi engelledi. Denetim aşılmadı; screenshot veya görsel QA yapıldığı iddia edilmedi.
15. README, akış açıklaması, şablon kaynak kaydı ve test dokümanları hazırlandı.
16. n8n'e import edildi; 20 sayfa tarama ve 117 satırlık CSV çalıştı. Disk yazımı `The file or directory does not exist` hatası verdi: n8n web sürümünde sunucu diski yok. Disk yerine Data Table kullanan sürüm ve 5 ek test hazırlandı.
17. Data Table, Gmail SMTP, iki zamanlanmış çalışma ve ayrı bir kopyada erişilemeyen adresle hata e-postası canlı test edildi (bkz. `TEST-SONUCLARI.md`).
18. Claude Code ile ürün arama bonusu ve 3 testi eklendi, depo düzenlenip yayınlandı.
19. Sınıflandırmanın yalnızca verilen 15 mesaja göre ayarlandığı fark edildi. 30 yeni etiketli mesajla kör ölçüm 19/30 çıktı; kelime listeleri genişletildi.
20. 15 mesajlık ikinci kör sette 10/15 çıktı ve iki istenmeyen etki mesajı devredilmedi. Kelime eklemek yerine "vücut bölgesi + kullanım sonrası" güvenlik ağı eklendi; gereksiz devir, kaçan şikâyete tercih edildi. İki set regresyon testine dönüştürüldü.
21. GitHub Actions ile her push'ta testler çalıştırıldı; README adımları temiz bir klonda denendi.
22. 15 çıktı canlı DummyJSON yanıtlarıyla tek tek karşılaştırıldı. Mesaj 12 (genel kargo sorusu) ve 15 (hayvan testi) için taslaklar soruya uymuyordu, yalnızca ürün adı istiyordu. Bu iki soru türüne uygun taslaklar ve bir test eklendi.
23. B yeniden kontrol edildi: canlı sitede 20 sayfa / 117 ürün tekrar tarandı; teslim edilen workflow.json, n8n'de çalışan akışın export'uyla karşılaştırıldı (tek fark kişisel e-posta adreslerinin kaldırıldığı Configuration düğümü).
