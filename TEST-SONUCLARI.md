# Doğrulama sonuçları

28 Eylül 2026 tarihinde Python 3.13 ve Node.js 20.20.2 ile kontrol edildi.

| Kontrol | Sonuç | Kanıt / kapsam |
|---|---|---|
| Python testleri | 16 / 16 geçti | `python3 -m unittest discover -s A-mesaj-otomasyonu/tests -v` |
| A canlı DummyJSON | 15 çıktı / 5 devir | `A-mesaj-otomasyonu/talepler.json` |
| n8n kod ve yapı testleri | 12 / 12 geçti | `cd B-n8n && npm test` |
| Canlı HTML taraması | 20 sayfa / 117 ürün | `B-n8n/live-check.json` |
| Aynı snapshot'ı tekrar işleme | 0 değişiklik | Canlı HTML üzerinde Code node testi |
| Simüle tek fiyat değişimi | 1 değişiklik | Canlı HTML kopyasında tek fiyat değiştirilerek |
| n8n uygulamasına import | Yapılmadı | JSON yapı ve referansları kontrol edildi; uygulama kabulü sınanmadı |
| n8n motorunda yürütme | Yapılmadı | Code mantık testleri uçtan uca n8n testi değildir |
| Gerçek CSV node / SMTP gönderimi | Yapılmadı | Kullanıcı kurulumunda doğrulanmalı |
| HTML görsel kontrolü | Engellendi | Tarayıcı yönetici güvenlik kontrolünü doğrulayamadı |

A testleri: verilen 15 mesajın konusu, hassas öncelik, sahiplik sızıntısı, ürünlere erişmeden önce sahip kontrolü, geçerli sipariş, bulunamama, bağlantı hatası, eksik/çoklu/ölçü birimli numara, Türkçe/İngilizce numara, çoklu niyet, İngilizce cevap, bozuk API alanları, HTML kaçışlama, girdi doğrulama, 404 önbelleği ve sınırlı tekrar.

B testleri: son sayfanın keşfi, bozuk sayfalama, HTML seçicileri, ilk/aynı/değişen snapshot, kısmi/boş/yinelenen/bozuk ürünler, binlik ayıracı, kuruşsuz fiyat, CSV formül kaçışlama, yalnızca son adımda durum kaydı, düğüm bağlantıları ve hata yolları.

Başarısız ilk denemeler `promptlar/surec-notu.md` içinde saklanmıştır. Otomatik test başarısı, görülmemiş tüm girdiler veya kurulmamış dış servisler için kusursuzluk garantisi değildir.

## Kullanıcıyla canlı kontrol ve web uyarlaması

Kullanıcının sonraki ekran görüntüleri import, 20 sayfa ve 117 satırlık CSV üretimini doğruladı; önceki tabloda bu adımlara ilişkin “yapılmadı” kaydı ilk hazırlık anını anlatır. Disk kaydı eksik klasör hatası verdi. `workflow-web.json` için 5 ek yerel test geçti; ardından canlı Data Table/SMTP, zamanlanmış kalıcılık ve hata bildirimi de kullanıcı ortamında doğrulandı; ayrıntılar yukarıdaki canlı test kaydındadır.
