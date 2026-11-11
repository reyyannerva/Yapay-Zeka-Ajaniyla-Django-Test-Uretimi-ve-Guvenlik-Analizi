# Django AI Test Agent

**Yapay Zekâ Destekli Otomatik Yazılım Testi Üretimi ve Güvenlik Analizi**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-Framework-092E20?logo=django&logoColor=white)
![Pytest](https://img.shields.io/badge/Testing-Pytest-0A9EDC?logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Execution-Docker-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Hafta%203%20%E2%80%94%20Veri%20ve%20AI%20Baseline-blue)

---

## Proje Hakkında

**Django AI Test Agent**, Django tabanlı yazılım projelerinde otomatik test üretimi ve güvenlik analizini bir araya getirmeyi amaçlayan yapay zekâ destekli bir yazılım mühendisliği projesidir.

Yazılım geliştirme süreçlerinde test senaryolarının manuel olarak hazırlanması zaman almakta; özellikle kimlik doğrulama, yetkilendirme, hatalı girdiler ve beklenmeyen HTTP davranışları gibi durumlarda test kapsamı yetersiz kalabilmektedir. Mevcut test araçları, yazılmış testlerin çalıştırılmasını kolaylaştırsa da test senaryolarının ve beklenen sonuçların belirlenmesi çoğunlukla geliştiricinin sorumluluğundadır.

Bu proje kapsamında geliştirilecek sistem, Django uygulamalarının kaynak kodlarını inceleyerek test edilebilir bileşenleri belirleyecek, büyük dil modellerinden (LLM) yararlanarak Pytest testleri oluşturacak, üretilen testleri doğrulayıp kontrollü bir ortamda çalıştıracak ve elde edilen güvenlik bulgularını raporlayacaktır.

Sistem, kaynak koddan gözlemlenen davranış ile güvenlik açısından beklenen davranışı birbirinden ayıracak şekilde tasarlanacaktır. Böylece uygulamadaki mevcut bir güvenlik hatasının test üretim sürecinde doğru davranış olarak kabul edilmesi riski azaltılacaktır.

## Projenin Amaçları

Projenin temel amacı, Django projeleri için kaynak kod analizine dayalı, ölçülebilir ve geliştirilebilir bir otomatik test üretim altyapısı oluşturmaktır.

Bu doğrultuda aşağıdaki işlevlerin gerçekleştirilmesi hedeflenmektedir:

- Django ve desteklenen Django REST Framework bileşenlerinin kaynak kodlarını analiz etmek.
- URL yönlendirmelerini, view yapılarını, HTTP metotlarını ve erişim kurallarını belirlemek.
- Bağımsız referans gereksinimlerini kullanarak beklenen güvenli davranışları tanımlamak.
- LLM aracılığıyla otomatik Pytest testleri üretmek.
- Üretilen testlerin sözdizimini, yapısını ve referans gereksinimleriyle tutarlılığını kontrol etmek.
- Testleri kaynak kullanımının sınırlandırıldığı Docker ortamında çalıştırmak.
- Bandit ve Django güvenlik kontrolleriyle statik ve yapılandırma analizleri gerçekleştirmek.
- Test sonuçlarını, güvenlik bulgularını ve performans ölçümlerini raporlamak.
- Kural tabanlı, doğrudan LLM tabanlı ve hibrit test üretim yaklaşımlarını karşılaştırmak.

## Sistem Mimarisi

Sistem, birbirini tamamlayan modüllerden oluşacak şekilde tasarlanmaktadır.

### 1. Kaynak Kod Analizi

Hedef Django projesinin Python dosyaları, URL tanımları, view yapıları ve güvenlikle ilişkili yapılandırmaları incelenecektir.

Python AST kullanılarak desteklenen kod yapılarından test üretimine uygun bilgiler çıkarılacaktır. Django REST Framework kullanılan projelerde APIView, serializer ve izin sınıfları da desteklenen kapsam dâhilinde değerlendirilecektir.

### 2. Referans Gereksinimleri

Testlerin beklenen sonuçları yalnızca mevcut kaynak koddan çıkarılmayacaktır.

Kullanıcı rolleri, erişim izinleri, beklenen HTTP yanıt kodları ve temel güvenlik kuralları bağımsız referans gereksinimleri olarak tanımlanacaktır.

Bu yaklaşım, uygulamanın hatalı davranışını tekrar eden testler yerine beklenen güvenlik davranışını doğrulayan testler üretmeyi amaçlamaktadır.

### 3. Yapay Zekâ ile Test Üretimi

Kaynak kod analizinden elde edilen bilgiler ve referans gereksinimleri yapılandırılmış bir test bağlamına dönüştürülecektir.

LLM tabanlı test üretim modülü, bu bağlamı kullanarak Pytest ile uyumlu test senaryoları ve test kodları oluşturacaktır.

Model sağlayıcısından bağımsız bir arayüz tasarlanarak farklı LLM servislerinin değerlendirilmesi hedeflenmektedir.

### 4. Test Doğrulama ve Yürütme

Üretilen testler çalıştırılmadan önce sözdizimi ve yapısal uygunluk açısından kontrol edilecektir.

Geçerli testler, hedef uygulamayla birlikte sınırlandırılmış Docker ortamında Pytest aracılığıyla yürütülecektir.

Teknik nedenlerle çalıştırılamayan testlerde, yalnızca üretilen test koduna yönelik en fazla bir otomatik düzeltme denemesi uygulanması planlanmaktadır.

Hedef uygulamanın kaynak kodu ve bağımsız güvenlik beklentileri otomatik olarak değiştirilmeyecektir.

### 5. Güvenlik Analizi

Test üretiminden bağımsız olarak tamamlayıcı güvenlik kontrolleri gerçekleştirilecektir.

- **Bandit:** Python kaynak kodundaki belirli güvenlik risklerinin statik analizi.
- **Django Deployment Checks:** Dağıtım ortamıyla ilişkili güvenlik yapılandırmalarının kontrolü.
- **Davranışsal Testler:** Kimlik doğrulama, yetkilendirme ve beklenen HTTP davranışlarının test edilmesi.

Statik analiz uyarıları ile çalıştırılan testlerle doğrulanan güvenlik ihlalleri raporda ayrı değerlendirilecektir.

### 6. Sonuçların Raporlanması

Sistem, analiz ve test süreçlerinden elde edilen sonuçları web arayüzü üzerinden sunacak şekilde geliştirilecektir.

Raporlarda testlerin yürütülme durumları, güvenlik bulguları, ilgili kanıtlar, hata nedenleri ve deneysel değerlendirme metrikleri yer alacaktır.

---

## PyGoat ile Değerlendirme

Projenin güvenlik analizi ve test üretimi yeteneklerinin değerlendirilmesinde **OWASP PyGoat** temel hedef uygulama olarak kullanılacaktır.

PyGoat, Django ile geliştirilmiş ve güvenlik çalışmalarına yönelik kasıtlı zafiyetler içeren açık kaynaklı bir uygulamadır.

PyGoat bu projede hazır bir makine öğrenmesi eğitim veri kümesi olarak değil, kaynak kodu ve uygulama davranışları incelenebilecek bir değerlendirme ortamı olarak kullanılacaktır.

Deneysel değerlendirme için:

1. PyGoat'ın proje kapsamına uygun bölümleri belirlenecek.
2. Seçilen güvenlik senaryoları incelenecek.
3. Beklenen güvenli davranışlar ve referans etiketler hazırlanacak.
4. Üretilen testler bu senaryolar üzerinde çalıştırılacak.
5. Güvenlik bulguları referans verilerle karşılaştırılacak.

PyGoat'ta bulunmayan belirli Django REST Framework senaryoları için küçük ve kontrollü örnek uygulamalar hazırlanabilecektir.

**PyGoat kaynak kodu:** https://github.com/adeyosemanputra/pygoat

## Deneysel Değerlendirme

Sistemin başarımı üç temel ölçüt üzerinden değerlendirilecektir.

| Metrik | Hedef | Açıklama |
|---|---|---|
| İlk denemede çalışabilir test oranı | ≥ %70 | Otomatik düzeltme yapılmadan anlamlı bir test sonucu üretebilen testlerin oranı |
| Güvenlik tespiti F1-skoru | ≥ 0,80 | Etiketli güvenlik senaryolarında precision ve recall arasındaki denge |
| Mutasyon skoru | ≥ %50 | Geçerli, eşdeğer olmayan kod mutasyonlarından testlerle tespit edilenlerin oranı |

Bu değerler **proje hedefleridir; elde edilmiş deney sonuçları değildir.**

Kural tabanlı test üretimi, doğrudan LLM tabanlı test üretimi ve önerilen hibrit yaklaşım aynı değerlendirme koşullarında karşılaştırılacaktır.

Ek olarak kod kapsamı, yanıt süresi ve token tüketimi gibi ölçütler uygun olduğu ölçüde incelenecektir.

## Planlanan Teknolojiler

| Teknoloji | Kullanım amacı |
|---|---|
| Python | Temel geliştirme dili |
| Django / Django REST Framework | Hedef uygulama analizi ve ilgili web bileşenleri |
| Python AST | Kaynak kod yapısının incelenmesi |
| LLM API | Otomatik test kodu üretimi |
| Pytest | Testlerin yürütülmesi |
| Bandit | Statik güvenlik analizi |
| Docker | Kontrollü test ortamı ve dağıtım |
| GitHub | Sürüm kontrolü, görev yönetimi ve iş birliği |

Model sağlayıcısı, veritabanı ve ön yüz teknolojileri ilk tasarım aşamasındaki teknik değerlendirmeler sonucunda kesinleştirilecektir.

## Proje Yapısı

Aşağıdaki dizin düzeni planlanan modüler mimariyi göstermektedir. Geliştirme ilerledikçe güncellenecektir.

```text
django-ai-test-agent/
├── agent/
│   ├── source_analysis/
│   ├── test_generation/
│   ├── validation/
│   ├── execution/
│   ├── security/
│   └── reporting/
├── backend/
├── frontend/
├── benchmarks/
│   ├── pygoat/
│   ├── drf_fixtures/
│   └── reference_cases/
├── experiments/
├── tests/
├── docs/
├── scripts/
├── .github/
├── README.md
└── pyproject.toml
```

## Geliştirme Takvimi

Proje, 10 haftalık geliştirme takvimi doğrultusunda yürütülecektir.

| Aşama | Hafta | Planlanan çalışmalar |
|---|---|---|
| Araştırma ve tasarım | 1–3 | Gereksinimler, mimari, Figma, PyGoat incelemesi, değerlendirme senaryoları ve ilk prototip |
| Yerel geliştirme | 4–7 | Backend, veritabanı, arayüz, kaynak analiz modülleri, LLM entegrasyonu ve uçtan uca MVP |
| Canlıya alma | 8 | Docker tabanlı dağıtım, yapılandırma ve kayıt mekanizmaları |
| Test ve teslim | 9–10 | Birim ve entegrasyon testleri, güvenlik değerlendirmesi, deneysel sonuçlar, dokümantasyon ve sunum |

Haftalık görevler GitHub Issues üzerinden takip edilecektir.

## Proje Durumu

**Durum: Hafta 3 — Veri ve AI baseline (devam ediyor).** Hafta 1 (diyagramlar, isterler) ve Hafta 2 (Figma,
veritabanı tasarımı) tamamlandı. Hafta 3'te H3-01–H3-04 tamamlandı; H3-05 (LLM ile Pytest üretimi, #31) ve
H3-06 (metrikler ve karşılaştırma, #32) açıktır. Ürün backend'i, web arayüzü, AST analiz motoru ve Docker
yürütme ortamı sonraki haftaların kapsamındadır; README'de belirtilen hedefler tamamlanmış işlevler olarak
değerlendirilmemelidir.

### Tamamlanan çıktılara hızlı erişim

| Hafta | Çıktı | Konum |
|---|---|---|
| 1 | Sistem mimarisi, akış, use-case ve AI pipeline diyagramları (#18–#22) | [`docs/diagrams/`](docs/diagrams/) |
| 2 | Figma prototipi ve 31 ekran (#23, #25, #26) | [`docs/mockup/README.md`](docs/mockup/README.md) |
| 2 | Kanonik veritabanı tasarımı — şema, modeller, veri sözlüğü (#24) | [`docs/database/`](docs/database/README.md) |
| 2 | ER diyagramları (#26) | [`docs/diagrams/er-diagrams/`](docs/diagrams/er-diagrams/) |
| 2 | Teknoloji yığını (#26) | [`docs/architecture/technology_stack.md`](docs/architecture/technology_stack.md) |
| 3 | H3-01 Kontrollü Django/DRF fixture ve 38 senaryoluk veri kümesi (#27) | [`benchmarks/drf_fixtures/`](benchmarks/drf_fixtures/README.md) |
| 3 | PyGoat ayrım ve inceleme notu (#27) | [`benchmarks/pygoat/`](benchmarks/pygoat/README.md) |
| 3 | H3-02 EDA notebook ve veri kalitesi raporları (#28) | [`experiments/h3_02_eda/`](experiments/h3_02_eda/README.md) |
| 3 | H3-03 Bağımsız test kümesi ve ground truth (#29) | [`benchmarks/reference_cases/`](benchmarks/reference_cases/README.md) |
| 3 | H3-04 Kural tabanlı Pytest üretim baseline'ı (#30) | [`agent/test_generation/rule_based/`](agent/test_generation/rule_based/README.md), [`experiments/h3_04_rule_based_baseline/`](experiments/h3_04_rule_based_baseline/README.md) |
| 1–3 | Bağımsız denetim ve düzeltme kaydı | [`docs/audit/hafta1-3_denetim_duzeltme.md`](docs/audit/hafta1-3_denetim_duzeltme.md) |

### Doğrulama komutları (Hafta 3)

Tüm komutlar depo kökünden çalıştırılır:

```bash
# H3-01 kontrollü fixture ve senaryo eşleşmesi
(cd benchmarks/drf_fixtures && python scripts/validate_scenarios.py && cd sample_app && pytest -q)
# H3-03 ground truth, ayrım ve sabitleme
(cd benchmarks/reference_cases && python scripts/check_references.py && pytest -q)
# H3-02 EDA testleri
(cd experiments/h3_02_eda && pytest -q)
# H3-04 üretici testleri ve uçtan uca üretim/çalıştırma
(cd agent/test_generation/rule_based && pytest -q)
python -m agent.test_generation.rule_based all
```

Bağımlılıklar: ilgili dizinlerdeki `requirements.txt` dosyaları.

## Ekip

**Fırat Üniversitesi — Yapay Zekâ ve Veri Mühendisliği**

- Reyyan Erva Gökkaya
- Merve Çaloğlu

Geliştirme süreci ortak GitHub deposu, branch tabanlı çalışma düzeni, Issues ve Pull Requests aracılığıyla yürütülecektir.

## Güvenlik ve Kullanım Notları

Bu proje eğitim ve araştırma amaçlı geliştirilmektedir.

PyGoat gibi kasıtlı güvenlik açıkları içeren uygulamalar yalnızca yetkilendirilmiş ve izole test ortamlarında çalıştırılmalıdır.

Gerçek sistemlere izinsiz güvenlik testi uygulanmamalıdır. API anahtarları, kimlik bilgileri ve diğer gizli yapılandırmalar GitHub deposuna eklenmemelidir.

Üretilen test kodları güvenilir kabul edilmeden önce doğrulanmalı ve uygun kaynak kısıtlamaları altında çalıştırılmalıdır.

---

**Django AI Test Agent** — Kaynak kod analizinden otomatik test üretimine ve güvenlik değerlendirmesine uzanan modüler bir yazılım mühendisliği çalışması.
