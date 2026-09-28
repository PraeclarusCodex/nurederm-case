# Canlı n8n doğrulaması — 28 Eylül 2026

Testler kullanıcının n8n ortamında kullanıcı tarafından yürütüldü. Sonuçlar paylaşılan ekran görüntüleri, düğüm çıktıları ve alınan e-postalar üzerinden kontrol edildi; ajan bu canlı yürütmeleri kendisi başlatmadı.

| Kontrol | Gözlenen sonuç |
|---|---|
| Data Table insert | 117 ürün, sayısal price/reviews; sistem id ve oluşturma zamanı döndü. |
| Verify saved rows | 117 satırın sayı, URL ve alan/tür kontrolü geçti. Bu kontrol insert çıktısını denetler; bağımsız tekrar okuma yapmaz. |
| CSV | 117 satır, laptops.csv, 14.7 kB. |
| İlk zamanlanmış çalışma | 11:18, yürütme #10; Succeeded, 8.158 saniye; 117 ürün / 117 değişiklik, bildirim e-postası alındı. |
| İkinci zamanlanmış çalışma | 11:20; success=true, products=117, changes=0; Any changes False Branch. Önceki başarılı snapshot kullanıldı. |
| Hata senaryosu | Ayrı test kopyasında https://nurederm-test.invalid; yürütme #13, 11:26 hata e-postası: getaddrinfo ENOTFOUND nurederm-test.invalid. Kullanıcı akışın hata yoluna gittiğini ve hata aldığını bildirdi. |
| Son dışa aktarım | 11:29 indirilen ana workflow: Europe/Istanbul, cron 0 9 * * *, active=true; gerçek webscraper.io adresi. |

Hata testinde önceki snapshot'ın korunması bağlantı/kod tasarımıyla desteklenir; hata sonrasında saklanan veriye bağımsız okuma yapılmadı. Gerçek fiyat değişikliği beklenmedi; tek fiyat değişimi yerel testte simüle edildi. Günlük 09:00 ayarı dosyada doğrulandı; bu saatteki gelecek çalışma henüz gözlenmedi.

## Teslim kopyası

workflow-web.json, ana akışın dışa aktarımından kişisel e-posta adresleri, SMTP credential referansları, tablo/proje kimlikleri ve instance metadata çıkarılarak hazırlandı. Import güvenliği için active=false. Veri tablosu ve SMTP yeni ortamda yeniden seçilmeli. Düğüm kodu ve bağlantılar korunmuştur; Data Table resource/operation varsayılanları açıkça row/insert yazılmıştır. Kurulum notundaki eski test durumu güncellenmiştir.

İndirilen asıl dosya değiştirilmedi. n8n üzerindeki çalışan akışa bu yerel işlemle herhangi bir değişiklik yapılmadı.
