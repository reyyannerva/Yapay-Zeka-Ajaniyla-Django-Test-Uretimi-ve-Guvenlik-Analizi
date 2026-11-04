# Teknoloji Yığını ve Kullanım Amaçları

**Proje:** Yapay Zekâ Ajanıyla Django Test Üretimi ve Güvenlik Analizi  
**İlgili görev:** H2-04 / Issue #26  
**Belge kapsamı:** Planlanan teknoloji seçimi ve bileşenlerin sistemdeki görevleri. Bu belge, araçların tamamının uygulandığını veya üretim ortamında doğrulandığını göstermez.

## 1. Teknoloji tablosu

### Kullanıcı arayüzü

| Katman | Teknoloji | Sistemdeki kullanım amacı | Seçim gerekçesi |
|---|---|---|---|
| Kullanıcı arayüzü | React | Proje yükleme, referans gereksinimlerini tanımlama, analiz başlatma, test sonuçlarını, bulguları ve raporları inceleme ekranları | Bileşen tabanlı ekran geliştirme |
| Frontend geliştirme | Vite | React uygulamasının geliştirme ve derleme altyapısı | Hızlı geliştirme döngüsü ve yalın yapılandırma |
| Frontend dili | TypeScript | Arayüz veri modelleri, API yanıtları ve bileşen tipleri | Tip denetimiyle entegrasyon hatalarını azaltma |
| Arayüz tasarımı | Tailwind CSS | Tasarım sistemindeki renk, yazı, boşluk ve bileşen kurallarının uygulanması | Ortak tasarım kurallarını uygulamayı kolaylaştırma |
| Sunucu verisi yönetimi | TanStack Query | API istekleri, önbellek, yüklenme ve hata durumları; devam eden analizin durumunun periyodik sorgulanması | Asenkron sunucu verisini düzenli yönetme |
| Veri görselleştirme | Recharts | Test sonuç dağılımları, bulgu sınıfları ve analiz özetleri | React içinde okunabilir grafikler oluşturma |
| Arayüz prototipleme | Figma | Ekran tasarımı ve tıklanabilir kullanıcı akışları | Kod geliştirmeden önce gezinme ve durumları değerlendirme |

### Backend ve veri

| Katman | Teknoloji | Sistemdeki kullanım amacı | Seçim gerekçesi |
|---|---|---|---|
| Backend | Django | Proje, kullanıcı, analiz ve sonuç kayıtlarının iş kuralları | ORM, kimlik yönetimi ve olgun uygulama altyapısı |
| REST API | Django REST Framework (DRF) | Frontend ile backend arasındaki API uç noktaları | Serileştirme, yetkilendirme ve API geliştirme desteği |
| Kimlik doğrulama | SimpleJWT | API uç noktalarında JWT tabanlı oturum doğrulama | DRF ile bütünleşik token tabanlı erişim |
| Giriş güvenliği | django-axes | Başarısız giriş denemelerinden sonra hesabın geçici olarak kilitlenmesi | Kaba kuvvet denemelerine karşı hazır koruma |
| Şifre sıfırlama | Django parola sıfırlama + SMTP | E-posta ile şifre sıfırlama bağlantısı gönderme | Django'nun yerleşik ve güvenli akışı |
| API dokümantasyonu | drf-spectacular | OpenAPI şeması ve etkileşimli API dokümantasyonu | Uç noktaları sözleşme düzeyinde görünür kılma |
| Kalıcı veri | PostgreSQL | Kullanıcı, proje, referans gereksinimi, analiz, üretilen test, test yürütme ve güvenlik bulgusu kayıtları | İlişkisel bütünlük, kısıtlar ve JSONB desteği |
| Veri erişimi | Django ORM | Model, ilişki, sorgu ve migration yönetimi | Uygulama modellerini veritabanıyla tutarlı tutma |
| Arka plan işleri | Celery | Uzun süren analiz, test üretimi ve çalıştırma işlerini API isteğinden ayırma | Kuyruk tabanlı asenkron iş yürütme |
| Mesaj aracısı | Redis | Celery görev kuyruğu; yalnızca `run_id` taşır | Hızlı ve hafif kuyruk altyapısı |
| PDF rapor | WeasyPrint | HTML şablonundan PDF test ve güvenlik raporu üretme | Rapor tasarımını HTML/CSS ile yönetebilme |

### Analiz, yapay zekâ ve test

| Katman | Teknoloji | Sistemdeki kullanım amacı | Seçim gerekçesi |
|---|---|---|---|
| Kaynak kod çözümleme | Python AST | URL, view, HTTP metodu, izin sınıfı ve ayarların kod çalıştırılmadan çıkarılması | Python sözdizimini yapısal olarak inceleme |
| Model sağlayıcı katmanı | LiteLLM | Groq, Gemini ve Ollama modellerine tek arayüzden erişim; token ve süre limitleri | Sağlayıcı değişikliğinin yapılandırmayla yapılabilmesi (İST-05, İST-14) |
| Dil modeli (birincil) | Groq API | Açık ağırlıklı model ile Pytest senaryoları ve test kodu üretme | Hızlı yanıt ve açık ağırlıklı model erişimi |
| Dil modeli (karşılaştırma) | Google Gemini API | Yöntem karşılaştırma deneylerinde ikinci sağlayıcı | Farklı model ailesiyle karşılaştırma imkânı |
| Yerel dil modeli | Ollama | Yerel çalışan model seçeneği; sunucu kapalıysa arayüzde erişilemez gösterilir | Harici API'ye bağlı olmadan çalışabilme |
| Çıktı doğrulama | Pydantic | Dil modeli yanıtlarının beklenen şemaya uygunluğunu denetleme | Yapılandırılmış çıktıların güvenilir biçimde doğrulanması |
| Test çerçevesi | Pytest, pytest-django | Üretilen testleri Django test ortamında çalıştırma ve JUnit XML çıktısı alma | Otomatik test yürütme ve ayrıntılı sonuç raporlama |
| Kod kapsamı | pytest-cov | Üretilen testlerin kod kapsamını ölçme | Arayüzde ve raporda kapsam metriği sunma |
| Mutasyon testi | mutmut | Deneylerde testlerin hata yakalama gücünü mutasyon skoruyla ölçme | Python projeleri için pratik mutasyon testi |
| Statik güvenlik analizi | Bandit | Python kaynak kodunda güvenlik bulgularını kod çalıştırılmadan tarama | Tekrarlanabilir statik analiz çıktıları |
| Dağıtım ayarları denetimi | Django `check --deploy` | DEBUG, güvenli çerez ve HSTS gibi canlı ortam ayarlarını denetleme (sandbox içinde) | Django'nun yerleşik güvenlik denetimi |

### Çalıştırma ve dağıtım

| Katman | Teknoloji | Sistemdeki kullanım amacı | Seçim gerekçesi |
|---|---|---|---|
| İzole çalıştırma | Docker | Hedef projeyi ve üretilen testleri ağ erişimi olmayan, sınırlandırılmış ortamda yürütme | Çalışma ortamını ayrıştırma ve tekrar üretilebilirlik |
| Konteyner yönetimi | Docker SDK for Python | Worker'dan sandbox konteynerini oluşturma, kaynak sınırlarını uygulama, durdurma ve silme | Python kodundan konteyner yaşam döngüsünü yönetme |
| Servis yönetimi | Docker Compose | web, worker, redis, db ve frontend servislerini birlikte çalıştırma | Geliştirme ve dağıtım ortamlarını aynı tanımla kurma |
| Uygulama sunucusu | Gunicorn | Django uygulamasını üretim ortamında çalıştırma | Django ile yaygın kullanılan WSGI sunucusu |
| Web sunucusu | Nginx | Frontend dosyalarını sunma ve `/api` isteklerini backend'e yönlendirme | Statik dosya sunumu ve ters vekil sunucu |

## 2. Bileşenlerin birlikte çalışması

1. Hedef akışta kullanıcı React arayüzünden bir proje yükler, referans gereksinimlerini form veya JSON dosyasıyla tanımlar ve analizi başlatır.
2. DRF isteği doğrular; Django önce `AnalysisRun` kaydını PostgreSQL'de oluşturur, ardından görevi yalnızca `run_id` ile Celery kuyruğuna gönderir. Redis mesaj aracısı olarak kullanılır.
3. Python AST kaynak kod yapısını çıkarır. Bandit ile ayrı bir statik güvenlik taraması yapılır.
4. LiteLLM üzerinden erişilen dil modeli, referans gereksinimlerle birlikte Pytest testleri üretir. Model erişilemezse temel testler kural tabanlı yöntemle üretilir. Üretilen testler Pydantic şeması, sözdizimi ve referans kurallara göre doğrulanır.
5. Doğrulanan testler, Docker SDK ile açılan izole sandbox içinde Pytest ile çalıştırılır; `check --deploy` da aynı ortamda yürütülür. Görev sonlandırma ve sandbox temizliği, uygulama sırasında ayrıca ele alınacak işletim ayrıntılarıdır.
6. Test sonuçları ve güvenlik bulguları ilgili veritabanı kayıtlarıyla ilişkilendirilir; raporda bulguların dayanakları ve test sonuçları gösterilir.
7. WeasyPrint ile PDF rapor, ayrıca JSON çıktı üretilir.
8. Arayüz, TanStack Query ile API sonuçlarını alır; Recharts ile sonuçları görselleştirir.

Bu akış **hedef mimariyi** açıklar. Çalışan uygulamanın hangi parçalarının tamamlandığı ayrıca geliştirme ve test kayıtlarıyla doğrulanmalıdır. Ayrıntılı akış için `docs/diagrams/` altındaki mimari ve akış diyagramlarına bakılabilir.

## 3. Tasarım kararları ve sınırlar

- **Görev durumu:** Issue #24 kapsamındaki veritabanı şemasında `AnalysisRun` için `QUEUED`, `ANALYZING`, `GENERATING`, `EXECUTING`, `COMPLETED` ve `FAILED` durumları tanımlanmıştır. Arayüz ve API bu kanonik durumlarla tutarlı olmalıdır. Ek ara adımlar yeni bir veritabanı durumu olarak gösterilmez.
- **Veri modeli:** PostgreSQL şeması, Django ORM modelleri ve veri sözlüğü için kanonik kaynak Issue #24 kapsamındaki `docs/database/` dosyalarıdır. Bu belge yeni alan veya ilişki tanımlamaz.
- **Redis:** Celery mesaj aracısı olarak kullanılması planlanır; kalıcı analiz durumu ve sonuç kayıtlarının kaynağı PostgreSQL'dir.
- **LLM çıktıları:** Üretilen test kodu doğrudan güvenilir kabul edilmez; sözdizimi, şema, referans gereksinimler ve test çalıştırma sonuçlarıyla kontrol edilir.
- **Güvenlik:** Docker tek başına tam bir güvenlik sınırı değildir. Kaynak sınırları, ağ erişimi, dosya sistemi izinleri ve çalıştırma yetkileri ayrıca yapılandırılır.
- **Kimlik ve erişim:** SimpleJWT yalnızca kimlik doğrulama mekanizmasıdır; proje sahipliği ve nesne düzeyinde yetkilendirme DRF/Django tarafında ayrıca uygulanır. Her proje tek bir kullanıcıya aittir.
- **Kapsam:** İlk hedef Django/DRF projeleridir. HTTP durum kodları, kimlik doğrulama/yetkilendirme ve girdi doğrulama senaryoları önceliklidir. Desteklenen HTTP metotları ve özel durumlar uygulama testleriyle netleştirilir.

## 4. İlgili teslimler

- **Veritabanı tasarımı:** `docs/database/`, Issue #24
- **ER diyagramları:** `docs/diagrams/er/`, Issue #26
- **Mimari ve akış diyagramları:** `docs/diagrams/`
- **Figma prototipi ve ekranlar:** Ortak Figma prototip bağlantısı, ilgili belge eklendiğinde bu bölümde gösterilecektir
- **Sınıf sunumu:** `docs/presentations/`, Issue #26 (sunum dosyası hazırlandığında)

## 5. Kontrol notu

Tablo; arayüz, backend, veri saklama, kuyruk, kaynak kod analizi, dil modeli, test, güvenlik, raporlama, dağıtım ve prototipleme araçlarını kapsar. Araç sürümleri ve üretim ortamı ayarları bu aşamada kesinleştirilmemiştir.
