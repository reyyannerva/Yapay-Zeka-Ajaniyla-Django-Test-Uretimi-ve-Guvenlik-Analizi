# TestKalkan Arayüz Tasarımı (Figma)

**Figma dosyası ve tıklanabilir prototip:** [Figma bağlantısı](https://www.figma.com/proto/r5UAC665Yj8XTsMIPtOzaq/Yapay-Zek%C3%A2-Ajan%C4%B1yla-Django-Test-%C3%9Cretimi-ve-G%C3%BCvenlik-Analizi?node-id=2-2&t=OCkJfJzB8gPKZSkh-1)

Prototip, **01 Giriş** ekranından başlar. Figma'da sağ üstteki ▶ (Present) düğmesiyle çalıştırılabilir.

## Tasarım yaklaşımı

TestKalkan, Django ve DRF projeleri için yapay zekâ destekli test üretimi ve güvenlik analizi yapan bir ürün olarak tasarlanmıştır. Arayüz, React + Vite + TypeScript ile geliştirilecek frontend yapısına doğrudan aktarılabilecek şekilde ortak bir tasarım sistemi üzerine kurulmuştur.

- **Renkler:** Ana renk (#0F5C6E) yalnızca birincil eylemlerde ve gezinmede kullanılmıştır. Durum renkleri mimari ve akış diyagramlarıyla aynıdır: PASS yeşil, FAIL turuncu, teknik hata kırmızı, süreç mavi.
- **Yazı:** Arayüz metinlerinde IBM Plex Sans; kod, endpoint ve test adlarında IBM Plex Mono kullanılmıştır.
- **Ortak bileşenler:** Kenar menüsü, üst bar, butonlar, analiz durum rozetleri, analiz aşama şeridi, tablolar, metrik kartları, bildirimler, boş ve yükleniyor durumları tüm ekranlarda aynıdır.

Tasarım sistemi Figma dosyasının **00-Design System** sayfasında yer almaktadır.

## Ekranlar

### Ana akış

| # | Ekran | İçerik | İlgili isterler |
|---|---|---|---|
| 01 | [Giriş](ekranlar/01-giris.png) | JWT tabanlı oturum açma, ürün tanıtımı | İST-10 |
| 02 | [Genel bakış](ekranlar/02-genel-bakis.png) | Özet metrikler, devam eden analiz, analiz geçmişi | İST-13 |
| 03 | [Proje yükleme](ekranlar/03-proje-yukleme.png) | Arşiv veya izinli dizin seçimi, ön kontrol, desteklenen yapılar | İST-01, İST-16 |
| 04 | [Referans gereksinimler](ekranlar/04-referans-gereksinimler.png) | Roller, rol bazlı beklenen HTTP yanıtları, dağıtım beklentileri, JSON önizleme | İST-03 |
| 05 | [Analiz ayarları](ekranlar/05-analiz-ayarlari.png) | Kural tabanlı, doğrudan LLM ve hibrit yöntem; model seçimi ve fallback; sandbox sınırları | İST-04, İST-05, İST-07 |
| 06 | [Endpointler](ekranlar/06-endpointler.png) | AST ile bulunan URL, view, metot, kimlik doğrulama ve izin bilgileri; kapsam dışı yapılar | İST-02, İST-16 |
| 07 | [Üretilen testler](ekranlar/07-uretilen-testler.png) | Test listesi, kod önizleme, doğrulama durumu, model erişilemediğinde fallback bildirimi | İST-04, İST-05, İST-06 |
| 08 | [Test sonuçları](ekranlar/08-test-sonuclari.png) | PASS / FAIL / teknik hata ayrımı, ölçülen metrikler | İST-07, İST-09 |
| 09 | [Güvenlik bulguları](ekranlar/09-guvenlik-bulgulari.png) | Doğrulanmış / olası / belirsiz sınıflandırma, önem derecesi, kanıt ve düzeltme önerisi | İST-08 |
| 10 | [Rapor](ekranlar/10-rapor.png) | Rapor önizlemesi, PDF / JSON dışa aktarma, önceki raporlar | İST-09 |

### Durum ekranları

| # | Ekran | Gösterilen durum |
|---|---|---|
| 11 | [Giriş hatası](ekranlar/11-giris-hatasi.png) | Hatalı e-posta veya şifre, kalan deneme hakkı |
| 12 | [Oturum süresi doldu](ekranlar/12-oturum-suresi-doldu.png) | JWT oturumunun sona ermesi |
| 13 | [Yetkisiz erişim](ekranlar/13-yetkisiz-erisim.png) | Başka bir kullanıcıya ait analize erişim denemesi (403) |
| 14 | [İlk kullanım](ekranlar/14-ilk-kullanim.png) | Hiç proje olmadığında boş durum |
| 15 | [Geçersiz proje](ekranlar/15-gecersiz-proje.png) | Arşivde Django projesi bulunamaması |
| 16 | [Analiz sürüyor](ekranlar/16-analiz-suruyor.png) | Celery ile yürütülen analizin canlı ilerlemesi |
| 17 | [Analiz başarısız](ekranlar/17-analiz-basarisiz.png) | Sandbox başlatılamadığında hata ayrıntısı ve kısmi sonuçlar |
| 18 | [Test üretilemedi](ekranlar/18-test-uretilemedi.png) | Desteklenen endpoint bulunamadığında boş sonuç |

### Gezinme ve etkileşim ekranları

| # | Ekran | İçerik |
|---|---|---|
| 19 | [Projeler](ekranlar/19-projeler.png) | Yüklenen projeler, referans kuralı durumu ve son analiz |
| 20 | [Analizler](ekranlar/20-analizler.png) | Tüm analizlerin durum, proje ve yönteme göre filtrelenebilir listesi |
| 21 | [Raporlar](ekranlar/21-raporlar.png) | Tam ve kısmi raporlar, PDF ve JSON biçimleri |
| 22 | [Kullanıcı menüsü](ekranlar/22-kullanici-menusu.png) | Profil, şifre değiştirme ve oturumu kapatma |
| 23 | [Kural ekleme](ekranlar/23-kural-ekleme.png) | Bir endpoint için rol bazlı beklenen HTTP yanıtlarının girilmesi (İST-03) |
| 24 | [Model seçimi](ekranlar/24-model-secimi.png) | Groq, Gemini ve Ollama (yerel) modelleri ile erişilebilirlik durumları (İST-05, İST-14) |
| 25 | [Rapor indirildi](ekranlar/25-rapor-indirildi.png) | PDF indirme sonrası kullanıcıya verilen onay (İST-09) |
| 26 | [Şifre sıfırlama](ekranlar/26-sifre-sifirlama.png) | E-posta ile şifre sıfırlama bağlantısı isteği |
| 27 | [Profil](ekranlar/27-profil.png) | Hesap bilgileri, şifre değiştirme ve oturumu kapatma |
| 28 | [Durdurma onayı](ekranlar/28-durdurma-onayi.png) | Devam eden analizi durdurmadan önce kullanıcıdan alınan onay |
| 29 | [Analiz durduruldu](ekranlar/29-analiz-durduruldu.png) | Kullanıcının durdurduğu analiz ve saklanan kısmi sonuçlar |
| 30 | [Proje silme onayı](ekranlar/30-proje-silme-onayi.png) | Projeyi ve ona bağlı tüm analiz verilerini silmeden önce alınan onay |
| 31 | [JSON ile kural yükleme](ekranlar/31-json-ile-kural-yukleme.png) | Referans gereksinimlerin JSON dosyasıyla yüklenmesi ve şema doğrulaması (İST-03) |

## Kullanıcı akışı

```
01 Giriş ──► 02 Genel bakış
               ├─► Yeni analiz: 03 Proje yükleme ─► 04 Referans gereksinimler ─► 05 Analiz ayarları ─► 16 Analiz sürüyor
               ├─► Tamamlanan analiz: 06 Endpointler ─► 07 Üretilen testler ─► 08 Test sonuçları ─► 09 Güvenlik bulguları ─► 10 Rapor
               ├─► Başarısız analiz: 17 Analiz başarısız ─► Yeniden başlat ─► 16 Analiz sürüyor
               ├─► Kenar menü: 19 Projeler · 20 Analizler · 21 Raporlar
               ├─► Kullanıcı menüsü: 22 ─► 27 Profil  |  Çıkış yap ─► 01 Giriş
               └─► Analiz sürüyor: 16 ─► Analizi durdur ─► 28 Onay ─► 29 Analiz durduruldu
```

Durum ekranları da (11–18) ilgili ekranlara bağlanmıştır; örneğin oturum süresi dolduğunda kullanıcı giriş ekranına, geçersiz proje yüklendiğinde genel bakışa yönlendirilir. Referans gereksinimler ekranındaki kural ekleme penceresi (23), analiz ayarlarındaki model listesi (24) ve rapor indirme onayı (25) da prototipte tıklanarak açılabilir.

## Diyagramlarla tutarlılık

- Analiz aşama şeridi ve durum rozetleri, `AnalysisRun` durumlarına (`queued → analyzing → generating → validating → executing → scanning → completed | failed`) karşılık gelir.
- Test sonuçlarındaki PASS / FAIL / teknik hata ayrımı ve tek düzeltme kuralı, [Docker yürütme akış diyagramındaki](../diagrams/akis-docker-guvenlik-raporlama.svg) kurallarla aynıdır.
- Değerlendirme metrikleri (precision, recall, F1-skoru, mutasyon skoru) yalnızca deneylerde hesaplandığı için kullanıcı arayüzünde gösterilmemiştir; arayüzde yalnızca çalıştırılabilir test oranı, kod kapsamı, süre ve token kullanımı yer alır.

## Kapsam notları

Mockup, geliştirilecek sistemin kapsamını tanımlar. Aşağıdaki kararlar bu kapsamın bir parçasıdır:

- **HTTP metotları:** Öneri formunda ilk sürüm için GET ve POST öngörülmüştü. Yetkilendirme açıklarının önemli bir kısmı kayıt silme ve güncelleme işlemlerinde ortaya çıktığı için kapsam, mockup aşamasında GET, POST, PUT, PATCH ve DELETE metotlarını kapsayacak şekilde genişletilmiştir. HEAD ve OPTIONS kapsam dışıdır. Dinamik rotalar ve özel izin sınıfları da kapsam dışıdır ve raporda ayrıca listelenir (İST-16).
- **Dil modeli sağlayıcıları:** Groq birincil sağlayıcıdır. Gemini, yöntem karşılaştırma deneyleri için ikinci sağlayıcı olarak kullanılır. Ollama ile yerel model seçeneği sunulur; yerel sunucu çalışmıyorsa model listesinde erişilemez olarak gösterilir. Tüm çağrılar LiteLLM üzerinden yapılır.
- **Hesaplar:** Kullanıcı hesapları yönetici tarafından Django yönetim panelinden oluşturulur; arayüzde ayrı bir kayıt ekranı bulunmaz.
- **Profil:** Kullanıcı kendi bilgilerini görüntüleyebilir ve şifresini değiştirebilir; ad ve e-posta yönetici tarafından güncellenir.
- **Analiz durdurma:** Devam eden analiz, kullanıcı onayıyla durdurulabilir. Görev iptal edilir, sandbox silinir, durum `cancelled` olur ve tamamlanan testlerin sonuçları kısmi sonuç olarak saklanır.
- **Veri yönetimi (CRUD):** Proje oluşturulur (03), listelenir (19) ve silinir (30). Referans kuralları form veya JSON ile eklenir (23, 31), listelenir (04) ve düzenlenir (23).
- **Yetkilendirme:** Her proje tek bir kullanıcıya aittir. Kullanıcı yalnızca kendi projelerinin analizlerini görebilir; başka bir kullanıcıya ait analize erişim 403 ile reddedilir.
- **Deneyler:** Üç yöntemin karşılaştırılması ve precision, recall, F1-skoru, mutasyon skoru gibi değerlendirme metrikleri arayüzde değil, deney betikleri ve notebook'lar ile yürütülür.
- **Loglar:** Sistem logları sunucuda tutulur; arayüzde yalnızca başarısız analizlerin hata ayrıntısı gösterilir.

## Sorumluluk dağılımı

| Ekranlar | Sorumlu |
|---|---|
| 03, 04, 05, 06, 07, 15, 18, 23, 24, 31 | Reyyan Erva Gökkaya |
| 01, 02, 08, 09, 10, 11, 12, 13, 14, 19, 20, 21, 22, 25, 26, 27, 28, 29, 30 | Merve Çaloğlu |
| 00 Tasarım sistemi, 16, 17 | Ortak |
