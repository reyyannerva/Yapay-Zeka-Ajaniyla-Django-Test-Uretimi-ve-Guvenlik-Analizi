# PyGoat — İnceleme ve Ayrım Notları (H3-01 / Issue #27)

Bu klasör PyGoat için bir **ayrım ve inceleme notudur**. PyGoat kaynak kodu bu repoya
**kopyalanmaz (vendored edilmez)**; ayrı bir değerlendirme hedefidir.

## Rol ayrımı

- **PyGoat:** OWASP'ın Django ile geliştirilmiş, kasıtlı güvenlik açıkları içeren açık kaynak
  uygulamasıdır. Bu projede **hazır etiketli bir veri kümesi değil**, kaynak kodu ve davranışı
  incelenecek bir **değerlendirme hedefi** olarak kullanılır.
- **Kontrollü DRF fixture'ları:** `benchmarks/drf_fixtures/` (H3-01). PyGoat'ta karşılığı olmayan
  veya izole edilmesi gereken DRF senaryoları için hazırlanan, bu projeye ait küçük ve **kontrollü**
  hedef uygulamadır.
- İki hedef **birbirinden ayrı tutulur**: fixture senaryoları ile PyGoat senaryoları karıştırılmaz;
  ground truth (H3-03) her hedef için ayrı tanımlanır.

**PyGoat kaynağı (referans):** https://github.com/adeyosemanputra/pygoat

## Değerlendirmeye aday modüller / senaryolar

PyGoat, laboratuvarlarını OWASP Top 10 (2021) kategorileri etrafında düzenler. Bu projenin
Hafta 3 kapsamı (Django/DRF HTTP metotları, kimlik doğrulama, yetkilendirme, girdi doğrulama,
güvenlik yapılandırması) ile **doğrudan ilgili** aday kategoriler:

| OWASP 2021 | Bu projedeki karşılık | Öncelik |
|---|---|---|
| A01 Broken Access Control | Yetkilendirme / kaynak sahipliği / BOLA senaryoları | Yüksek |
| A03 Injection | Girdi doğrulama senaryoları | Orta |
| A05 Security Misconfiguration | Güvenlik yapılandırması senaryoları | Orta |
| A07 Identification & Authentication Failures | Kimlik doğrulama senaryoları | Yüksek |

Kapsam dışı (ilk sürümde): dinamik rota/izinler, istemci tarafı açıkları ve kaynak kodla statik
olarak eşlenemeyen çalışma-zamanı-yoğun senaryolar (öneri formu kapsam sınırlarıyla uyumlu).

## Sabitlenecek noktalar (H3-03 / değerlendirme kurulumunda)

- Kullanılacak **PyGoat sürümü (commit/tag)** sabitlenecek; seçilen modül/view listesi ve her biri
  için beklenen güvenli davranış ground truth ile birlikte belgelenecektir.
- PyGoat yalnızca **yetkilendirilmiş ve izole** ortamlarda çalıştırılır (öneri formu güvenlik notu).

> Bu notlar OWASP Top 10 kategori düzeyindedir; modül/dosya düzeyindeki kesin seçim, sabitlenen
> PyGoat sürümüne göre değerlendirme kurulumunda netleştirilecektir.
