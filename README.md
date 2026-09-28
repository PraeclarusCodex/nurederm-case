# Nurederm — mesaj otomasyonu ve fiyat takibi

> **Önerilen n8n dosyası:** [workflow.json](B-n8n/workflow.json), canlı çalışan Data Table sürümünün kişisel bilgilerden arındırılmış kopyasıdır. [Kurulum](B-n8n/WEB-KURULUM.md) ve [canlı test kanıtları](B-n8n/CANLI-TESTLER.md). `workflow-local.json` önceki, sunucuda yazılabilir klasör gerektiren disk varyantıdır.

İki bölümün kodu, üretilmiş mesaj çıktıları, n8n tasarımı ve doğrulama testleri bu klasördedir. Müşteriye otomatik mesaj gönderilmez; cevaplar temsilci taslağıdır.

## Hızlı başlangıç

Python 3.10 veya üzeri ile depo kökünde:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 A-mesaj-otomasyonu/main.py
python3 -m unittest discover -s A-mesaj-otomasyonu/tests -v
```

Windows'ta etkinleştirme: `.venv\Scripts\activate`. Araç dosya yollarını kendi konumundan bulur. Alternatif girdi ve çıktı dizini için `--input dosya.json --output-dir ciktilar` kullanılabilir.

- [Mesaj paneli](A-mesaj-otomasyonu/ozet.html): tarayıcıda açılır; arama, konu filtresi ve yalnızca devirler seçeneği vardır.
- [talepler.json](A-mesaj-otomasyonu/talepler.json): gerekli beş alanı taşıyan 15 sonuç.
- [workflow.json](B-n8n/workflow.json): önerilen n8n import dosyası (20 düğüm). [Ekran görüntüsü](B-n8n/ekran-goruntusu-workflow.png).
- [Akış kurulumu ve tasarım kararları](B-n8n/akis-aciklama.md).
- [Test kanıtları ve sınırlar](TEST-SONUCLARI.md).

## A — müşteri mesajları

İşleyiş: girdi doğrulama → tek konu → hassas konu kontrolü → gerekiyorsa API → sahiplik kontrolü → cevap taslağı → JSON ve HTML özet.

Konu önceliği: **istenmeyen etki > iade/şikâyet > sipariş > fiyat > ürün > diğer**. Anahtar sözcüklere dayalı, Türkçe karakterleri normalize eden ve temel İngilizce sipariş sorularını destekleyen kurallar kullanıldı. Her metni anlayan bir dil modeli değildir. Üç saatlik görevde dış model hesabı gerektirmeyen, izlenebilir ve tekrarlanabilir davranış tercih edildi. Yapay zekâ kodlama/tasarım aşamasında kullanıldı; çalışma anında LLM çağrısı yapılmıyor.

Siparişin `userId` alanı, verilen `musteri_id` ile tam sayı olarak karşılaştırılır. Bu kontrol geçmeden ürün bilgisi veya tutar cevaba eklenmez. Eşleşmeyen siparişin sahibinin kimliği de çıktıya yazılmaz. Geçerli siparişte `products` ve `total` kullanılır. API para birimi, kargo firması veya teslim tarihi sağlamadığından bunlar uydurulmaz. Olmayan sipariş, bağlantı hatası, bozuk API yanıtı ve eksik/belirsiz numara temsilciye gider.

API isteklerinde 10 saniye zaman aşımı, geçici hatalar için en fazla 3 deneme ve aynı işlem içindeki tekrar sorgular için önbellek bulunur. TLS doğrulaması açıktır. HTML'ye yazılan metinler kaçışlanır. Reklam mesajının taslağı boş bırakılır.

Verilen dosyada kararlar:

| Konu | Adet |
|---|---:|
| siparis-durumu | 6 |
| urun-sorusu | 4 |
| fiyat | 2 |
| iade-sikayet | 1 |
| istenmeyen-etki | 1 |
| diger | 1 |

Canlı API çalışmasında **5 devir** oluştu: mesaj 1 (sahiplik), 3 (bulunamadı), 4 (istenmeyen etki), 5 (iade), 12 (kargo sorusu/numara yok).

- Mesaj 8 hem fiyat hem sipariş soruyor: sipariş konusu seçilir, ek fiyat isteği taslakta korunur.
- Mesaj 12 genel bir kargo sorusu: `siparis-durumu` altında tutuldu; API taşıyıcı bilgisi vermediği için temsilciye yönlendirilir. Bu bir tasarım kararıdır.
- Ürün içerikleri, hayvan testi politikası, cilt uygunluğu ve kampanya bilgisi için doğrulanmış marka kaynağı yoktur. İddia üretmek yerine tam ürün adı/bağlantısı istenir.

## B — n8n fiyat takibi

Başlangıç şablonu: **[Track changes of product prices — #837](https://n8n.io/workflows/837-track-changes-of-product-prices/)**. Orijinal JSON incelendi; zamanlama, HTML'den fiyat okuma, önceki fiyatla karşılaştırma ve hata bildirimi düzeni bu senaryoya uyarlanarak yeniden kuruldu. Şablonun aynen çalıştırıldığı iddia edilmiyor.

Akış her gün İstanbul saatiyle 09:00'da tüm laptop sayfalarını okur. Ürün adı, sayısal fiyat, yorum sayısı, link ve ISO tarih damgası içeren tarihli **Data Table kayıtları** ve indirilebilir CSV oluşturur. Yeni ürünleri ve her iki yöndeki fiyat değişikliklerini önceki başarılı çalışmayla karşılaştırır; tek e-posta özeti yollar. İlk çalışmada bütün ürünler yeni kabul edilir. Hatasız kaydetme ve gerekli bildirimin ardından karşılaştırma durumu güncellenir.

**Import sonrasında kurulacaklar:** iki e-posta düğümünde SMTP credential, Configuration düğümünde gönderen/alıcı adresi, aynı projede altı sütunlu Data Table seçimi (Map Automatically). Sonra akış publish/active yapılır. Credential değerleri repoya konulmamıştır.

Bağımsız mantık testleri için Node.js 18.17+:

```sh
cd B-n8n
npm ci --ignore-scripts
npm test
npm run test:live
```

Son komut siteyi canlı okur, e-posta göndermez. n8n motoru yerine kod ve HTML selector doğrulaması yapar. `code/` değişirse depo kökünden sırasıyla `python3 B-n8n/build_workflow.py` ve `python3 B-n8n/build_web_workflow.py` çalıştırın. Üretici kurulum bağlantıları boş bir şablon üretir; kullanıcıya özel export metadata içermez.

## Kapsam ve dürüst teslim notu

- **Yapıldı:** A'nın gerçek API ile çalışması, 15 çıktı, tek sayfalık HTML uygulaması; B'nin 20 düğümlü web JSON tasarımı, şablon kaynağı, tüm sayfaların gerçek HTML ile kontrolü, testler ve açıklamalar.
- **Doğrulandı:** 19 Python testi + 17 workflow mantık/yapı testi. Canlı sitede 20 sayfa / 117 ürün; aynı veriyle 0 değişiklik; bir simüle fiyat değişikliğinde 1 değişiklik.
- **Canlı doğrulandı:** Data Table 117 satır, CSV, Gmail SMTP teslimi, iki otomatik çalışmada 117 → 0 değişiklik ve ayrı kopyada erişilemeyen site hata e-postası. [Kanıt ve sınırlar](B-n8n/CANLI-TESTLER.md). İlk disk varyantı eksik klasör nedeniyle çalışmadı; önerilen akış Data Table kullanır.
- **Bonus (sonradan eklendi):** `urun-sorusu` ve `fiyat` mesajlarında `/products/search` ile ürün araması. Türkçe terimler test mağazasının İngilizce sözcüklerine çevrilir (ör. nemlendirici → moisturizer/lotion). Yalnızca beauty/skin-care/fragrances kategorisinde ve başlığında arama sözcüğü geçen ürünler taslağa eklenir; böylece "cream" araması "Ice Cream" döndürse de taslağa girmez. Hassas konularda ve sipariş mesajlarında arama yapılmaz. Arama hatası devir sebebi değildir, `not` alanına yazılır. Test mağazası genel bir mağaza olduğundan verilen 6 mesajdan yalnızca mesaj 10'da eşleşme çıktı (Vaseline Men Body and Face Lotion). Diğerlerinde "eşleşme yok" notu düşülür, ürün uydurulmaz. 3 yeni test eklendi (toplam 19).
- **Ekran görüntüsü:** canlı n8n akışı → [B-n8n/ekran-goruntusu-workflow.png](B-n8n/ekran-goruntusu-workflow.png). `ozet.html` için ekran görüntüsü alınmadı.
- **Gerçek kullanım sınırı:** `musteri_id` bu görevde güvenilir test girdisidir. Canlı WhatsApp/Instagram bağlantısında kimlik sunucu tarafında doğrulanmalı; müşteri metninden kabul edilmemelidir. Kurallı sınıflandırma için daha geniş bir değerlendirme seti gerekir. n8n durum saklama yaklaşımı tek, günlük çalışma için tasarlandı; eşzamanlı çalıştırma yapılmamalıdır.

## Süre ve süreç kaydı

- Görev e-postası: **28 Eylül 2026 10:00** (+03:00). Son teslim: **13:00**.
- İlk proje dosyası: 10:05. Teslim hazırlığı: 11:40 civarı.
- Araçlar: **Codex** (10:04–11:3x, kodlama, n8n kurulumu, canlı testler). Codex kullanım limiti dolunca **Claude Code** ile devam edildi (prompt dökümü, son kontroller, GitHub).

### Promptlar

- [promptlar/codex-tam-prompt-dokumu.md](promptlar/codex-tam-prompt-dokumu.md): Codex oturumundaki **56 kullanıcı mesajının tamamı**. Sırayla, olduğu gibi, başarısız denemeler dahil (ör. mesaj 11: disk varyantında `The file or directory does not exist` hatası → Data Table sürümüne geçiş). Oturum kaydından otomatik çıkarıldı; yalnızca kişisel e-posta adresleri maskelendi.
- [promptlar/claude-code-oturumu.md](promptlar/claude-code-oturumu.md): Claude Code oturumundaki promptlar.
- [promptlar/A-claude-code.md](promptlar/A-claude-code.md) ve [promptlar/B-n8n.md](promptlar/B-n8n.md): brief'te önerilen dosya adları. A ve B tek bir Codex sohbetinde birlikte yürütüldüğü için tam döküm ortak dosyadadır.
- [promptlar/surec-notu.md](promptlar/surec-notu.md): başarısız araç denemeleri ve düzeltmeler.
