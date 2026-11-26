# Üç yöntem karşılaştırması: Kural tabanlı / LLM / Hibrit · H5-06 / #44

Kaynak: **H5-04 (#42)** geliştirme kümesi üretim deneyi ve **H5-05 (#43)** hibrit deney + metrik
motoru. Buradaki sayılar o deneylerin **gerçek, çalıştırılmış** çıktılarıdır; demo için kopyalanmıştır.
Metrikler doğru adlandırılmıştır ve **ölçülememiş değerler "Ölçülemedi" olarak** gösterilir — hedef
değerler gerçek sonuç gibi sunulmaz.

> **Bağlam / dürüstlük notu:** Bu sonuçlar **geliştirme/kontrollü kümeler** üzerindedir; projenin
> nihai/tarafsız performansı değildir. Güvenlik tespiti (Precision/Recall/F1) ancak **bilinen kusur
> içeren** senaryolarda ölçülebilir.

## Katman A — H5-04'ün 20 geliştirme senaryosu (GET/POST ağırlıklı, bilinen kusur: 0)

Geliştirme kümesinde bilinen güvenlik açığı olmadığından **güvenlik F1 ölçülemez**; odak üretim
kalitesi ve çalıştırılabilirliktir.

| Yöntem | Senaryo | Sözdizimi geçerli | Toplanan | İlk geçiş çalıştırılabilir | PASS/FAIL/ERROR/TIMEOUT | Güvenlik F1 |
|---|---|---|---|---|---|---|
| Kural tabanlı | 20 | 20/20 | 20/20 | 1.0000 | 20/0/0/0 | Ölçülemedi (kusur yok) |
| LLM (Groq) | 20 | 20/20 | 20/20 | 1.0000 | 20/0/0/0 | Ölçülemedi (kusur yok) |
| Hibrit | 20 | 20/20 | 20/20 | 1.0000 | 20/0/0/0 | Ölçülemedi (kusur yok) |

## Katman B — kontrollü ek geliştirme kümesi (17 senaryo, 5 HTTP metodu, bilinen kusur: 3)

Bu kümede **GET/POST/PUT/PATCH/DELETE** temsil edilir ve **3 bilinen güvenlik kusuru** vardır;
böylece güvenlik tespiti ölçülebilir.

| Yöntem | Senaryo | TP | FP | TN | FN | Precision | Recall | F1 | Sözdizimi | Çalıştırılabilir | PASS/FAIL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Kural tabanlı | 17 | 3 | 0 | 14 | 0 | 1.0000 | 1.0000 | 1.0000 | 17/17 | 17/17 | 14/3 |
| LLM (Groq) | 17 | 3 | 0 | 14 | 0 | 1.0000 | 1.0000 | 1.0000 | 17/17 | 17/17 | 14/3 |
| Hibrit | 17 | 3 | 0 | 14 | 0 | 1.0000 | 1.0000 | 1.0000 | 17/17 | 17/17 | 14/3 |

Metot kapsamı (Katman B): GET 3, POST 2, PUT 3, PATCH 6, DELETE 3.

## Okuma notları

- **Sözdizimi geçerli / Toplanan / İlk geçiş çalıştırılabilir:** üretilen testin teknik kalitesi;
  testin *çalışabilmesi* ile hedef uygulamanın testi *geçmesi* ayrı ölçülür.
- **PASS/FAIL:** Katman B'de 14 PASS (güvenli senaryolar) + 3 FAIL (bilinen kusurlar yakalandı → TP).
- **F1 = 1.0000 (Katman B):** küçük, kontrollü kümede üç kusurun da yakalanması; **nihai performans
  iddiası değildir** (örneklem küçük, kontrollü).
- Üç yöntem bu kümelerde benzer teknik sonuç verir; hibrit politikanın katkısı daha büyük/kusurlu
  kümelerde değerlendirilmelidir (H6+).

## Kaynak dosyalar (gerçek çıktı)

- H5-04: `experiments/h5_04_generation_experiment/results/` (comparison.md, metrics.csv, results.json)
- H5-05: `experiments/h5_05_hybrid_experiment/results/comparison_table.md` (ve `.csv`)
