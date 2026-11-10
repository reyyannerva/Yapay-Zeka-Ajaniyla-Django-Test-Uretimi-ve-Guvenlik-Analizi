# H3-02 | EDA ve Veri Kalitesi Analizi — Özet Rapor

> Bu dosya `H3_02_EDA_Veri_Kalitesi.ipynb` tarafından `scenario_eda.report.render_summary` ile otomatik üretilir. Tüm sayılar kanonik veri kümesinden hesaplanmıştır; elle düzenlemeyin. İlgili issue: #28 · İsterler: İST-03, İST-13, İST-15, İST-16.

## 1. Veri kümesine genel bakış

- Kanonik kaynak: `benchmarks/drf_fixtures/scenarios/scenarios.json` — `h3-01-drf-controlled` v1.0.0 (hedef: `benchmarks/drf_fixtures/sample_app`).
- Türetilmiş kopya: `scenarios.csv` (yalnızca tutarlılık kontrolü için okunur); şema: `scenarios.schema.json`.
- Toplam **38** senaryo; **15** pozitif (%39.5), **23** negatif (%60.5); **3** bilerek-hatalı senaryo (negatiflerin alt kümesi).
- Kaynak: tüm kayıtlar kontrollü Django/DRF fixture kaynağına aittir; depoda PyGoat senaryo kaydı sayısı **0**.

## 2. Yöntem

1. **Yapısal doğrulama:** kanonik JSON Schema (Draft 2020-12) ile; H3-01 `validate_scenarios.py` ayrıca çalıştırılıp sonucu notebook'ta karşılaştırılır.
2. **Semantik doğrulama:** şemadan okunan zorunlu alan/enum tanımlarıyla alan düzeyi kontroller, yinelenen kimlik/içerik ve etiket–durum kodu tutarlılığı.
3. **Referans bütünlüğü (statik):** `fixture_ref` değerleri `users.json`/`articles.json` ile; endpoint'ler `config/urls.py` + `catalog/urls.py` metninden çıkarılan rota desenleriyle eşlenir. Rol semantiği kullanıcı adından değil fixture verisinden (`is_staff`, `owner`) doğrulanır.
4. **Django URL çözümlemesi:** Django URL çözümlemesi yapıldı (django.urls.resolve; HTTP isteği çalıştırılmadı). Davranışsal (çalışma zamanı) doğrulama bu analizin kapsamında değildir; H3-01'in `pytest` senaryo↔uygulama testleriyle yapılır.
5. **Durum kodu incelemesi:** hedef uygulamanın yapılandırmasına dayanan sezgisel kurallar; çıktılar kesin hata değil, inceleme önerisidir. Evrensel HTTP varsayımı (ör. her DELETE → 204) kullanılmaz.
6. **Kapsam modeli:** alan modeline göre açıkça listelenen (endpoint türü × metot × koşul) hücreleri; öncelikler ve %10 düşük temsil eşiği proje-özgü, yapılandırılabilir sezgisel değerlerdir.

Çalıştırılan kontroller:

| Katman | Kontrol | Durum | İncelenen kayıt | Bulgu |
|---|---|---|---|---|
| JSON Schema | JSON Schema doğrulaması (Draft 2020-12) | Çalıştırıldı | 38 | 0 |
| Semantik | Eksik/null zorunlu alan, boş metin, geçersiz enum/tip, kimlik biçimi, hata açıklaması | Çalıştırıldı | 38 | 0 |
| Semantik | Yinelenen senaryo kimliği | Çalıştırıldı | 38 | 0 |
| Semantik | Aynı isteği tanımlayan yinelenen içerik | Çalıştırıldı | 38 | 0 |
| Semantik | Pozitif/negatif etiket – durum kodu – bilerek-hata tutarlılığı | Çalıştırıldı | 38 | 0 |
| Referans bütünlüğü (statik) | Fixture kullanıcı/makale, rol semantiği, endpoint çözümleme, güvensiz uç işareti | Çalıştırıldı | 38 | 5 |
| Django URL çözümlemesi | View metot desteği ile 405 beklentisi | Çalıştırıldı | 38 | 0 |
| Durum kodu incelemesi (sezgisel) | Durum kodu makullüğü (proje-özgü sezgisel kurallar) | Çalıştırıldı | 38 | 0 |
| JSON/CSV tutarlılığı | Türetilmiş CSV ↔ kanonik JSON hücre karşılaştırması | Çalıştırıldı | 38 | 0 |

## 3. Tanımlayıcı istatistikler

| Metrik | Değer |
|---|---|
| Veri kümesi | h3-01-drf-controlled v1.0.0 |
| Toplam senaryo | 38 |
| Benzersiz senaryo kimliği | 38 |
| Yinelenen kimlik (birden fazla kullanılan kimlik sayısı) | 0 |
| Pozitif senaryo | 15 (%39.5) |
| Negatif senaryo | 23 (%60.5) |
| Negatif/pozitif oranı | 1.53 |
| Azınlık sınıf payı | %39.5 |
| Bilerek-hatalı (is_intentional_flaw) senaryo | 3 |
| Temsil edilen kategori / şemada tanımlı | 5 / 5 |
| Temsil edilen HTTP metodu / kapsam (GET, POST, PUT, PATCH, DELETE) | 5 / 5 |
| Temsil edilen user_role / şemada tanımlı | 4 / 4 |
| Farklı fixture kimliği (istek yapan) | 3 |
| Temsil edilen durum kodu / şemada tanımlı | 8 / 8 |
| Farklı endpoint türü | 5 |
| Farklı endpoint deseni (rota) | 5 |
| Farklı somut endpoint | 9 |

**HTTP metodu dağılımı** (beş metodun tamamı raporlanır):

| Metot | Senaryo | % | Pozitif | Negatif | Bilerek güvensiz | Temsil |
|---|---|---|---|---|---|---|
| GET | 10 | 26.3 | 6 | 4 | 1 | Temsil ediliyor |
| POST | 9 | 23.7 | 3 | 6 | 0 | Temsil ediliyor |
| PUT | 8 | 21.1 | 2 | 6 | 1 | Temsil ediliyor |
| PATCH | 4 | 10.5 | 2 | 2 | 0 | Temsil ediliyor |
| DELETE | 7 | 18.4 | 2 | 5 | 1 | Temsil ediliyor |

**Kategori dağılımı:**

| Kategori | Kod | Senaryo | % | Pozitif | Negatif | Bilerek güvensiz | Temsil |
|---|---|---|---|---|---|---|---|
| Kimlik doğrulama | AUTHENTICATION | 5 | 13.2 | 0 | 5 | 0 | Temsil ediliyor |
| Yetkilendirme | AUTHORIZATION | 9 | 23.7 | 1 | 8 | 2 | Temsil ediliyor |
| Girdi doğrulama | INPUT_VALIDATION | 4 | 10.5 | 0 | 4 | 0 | Temsil ediliyor |
| HTTP davranışı | HTTP_BEHAVIOR | 19 | 50.0 | 14 | 5 | 0 | Temsil ediliyor |
| Güvenlik yapılandırması | SECURITY_CONFIGURATION | 1 | 2.6 | 0 | 1 | 1 | Düşük temsil (eşik %10) |

**Beklenen HTTP durum kodu dağılımı:**

| Kod | Senaryo | % | Beklenen başarı | Beklenen ret | Bilerek güvensiz |
|---|---|---|---|---|---|
| 200 | 13 | 34.2 | 11 | 0 | 2 |
| 201 | 2 | 5.3 | 2 | 0 | 0 |
| 204 | 3 | 7.9 | 2 | 0 | 1 |
| 400 | 4 | 10.5 | 0 | 4 | 0 |
| 401 | 5 | 13.2 | 0 | 5 | 0 |
| 403 | 4 | 10.5 | 0 | 4 | 0 |
| 404 | 5 | 13.2 | 0 | 5 | 0 |
| 405 | 2 | 5.3 | 0 | 2 | 0 |

**Rol dağılımı** (etiket, fixture kimliği ve fixture'dan türetilen aktör ilişkisi ayrı boyutlardır):

| Boyut | Değer | Senaryo | % | Pozitif | Negatif |
|---|---|---|---|---|---|
| user_role (etiket) | Anonim (anonymous) | 10 | 26.3 | 2 | 8 |
| user_role (etiket) | Kullanıcı (user) | 12 | 31.6 | 2 | 10 |
| user_role (etiket) | Kaynak sahibi (owner) | 11 | 28.9 | 6 | 5 |
| user_role (etiket) | Yönetici (admin) | 5 | 13.2 | 5 | 0 |
| fixture kimliği | admin | 5 | 13.2 | 5 | 0 |
| fixture kimliği | alice | 11 | 28.9 | 6 | 5 |
| fixture kimliği | bob | 0 | 0.0 | 0 | 0 |
| fixture kimliği | carol | 12 | 31.6 | 2 | 10 |
| fixture kimliği | (kimlik yok / anonim) | 10 | 26.3 | 2 | 8 |
| aktör–kaynak ilişkisi (fixture'dan türetilmiş) | Anonim | 10 | 26.3 | 2 | 8 |
| aktör–kaynak ilişkisi (fixture'dan türetilmiş) | Kimliği doğrulanmış (nesnesiz) | 8 | 21.1 | 3 | 5 |
| aktör–kaynak ilişkisi (fixture'dan türetilmiş) | Kaynak sahibi | 6 | 15.8 | 5 | 1 |
| aktör–kaynak ilişkisi (fixture'dan türetilmiş) | Sahip olmayan kullanıcı | 7 | 18.4 | 0 | 7 |
| aktör–kaynak ilişkisi (fixture'dan türetilmiş) | Yönetici | 5 | 13.2 | 5 | 0 |
| aktör–kaynak ilişkisi (fixture'dan türetilmiş) | Belirlenemez | 2 | 5.3 | 0 | 2 |

## 4. Kapsam bulguları

- Temsil edilen metotlar: GET, POST, PUT, PATCH, DELETE; eksik metot yok.
- En çok temsil edilen metot GET (10 senaryo), en az temsil edilen PATCH (4 senaryo, %10.5).
- Düşük temsil edilen kategoriler (yapılandırılabilir eşik): Güvenlik yapılandırması (1 senaryo, %2.6).
- Kapsam modeli: 51 hücre (47 uygulanabilir); Açıkça mevcut: 34, Dolaylı temsil: 3, Kapsanmıyor: 10, Uygulanamaz: 4.
- Kapsam boşlukları: 19 kayıt — Doğrulanmış eksik: 0, Olası eksik: 17, Yetersiz meta veri: 2.

| No | Sınıf | Öncelik | Boyut | Endpoint türü | Metot | Koşul | Kanıt |
|---|---|---|---|---|---|---|---|
| GAP-001 | Olası eksik | Yüksek | endpoint türü × metot × koşul | guvenli_nesne | PATCH | kaynak_yok | PUT için SC-NF-001 mevcut; DRF'te PUT ve PATCH aynı UpdateModelMixin.update yolunu (partial bayrağıyla) kullanır. Açık senaryo hâlâ önerilir. |
| GAP-002 | Olası eksik | Yüksek | endpoint türü × metot × koşul | guvenli_nesne | PATCH | gecersiz_girdi | PUT için SC-INP-003 mevcut; DRF'te PUT ve PATCH aynı UpdateModelMixin.update yolunu (partial bayrağıyla) kullanır. Açık senaryo hâlâ önerilir. |
| GAP-003 | Olası eksik | Yüksek | endpoint türü × metot × koşul | guvensiz_nesne | PATCH | sahip_olmayan | PUT için SC-FLW-001 mevcut; DRF'te PUT ve PATCH aynı UpdateModelMixin.update yolunu (partial bayrağıyla) kullanır. Açık senaryo hâlâ önerilir. |
| GAP-004 | Olası eksik | Orta | endpoint türü × metot × koşul | guvenli_nesne_aksiyonu | POST | yonetici | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-005 | Olası eksik | Orta | endpoint türü × metot × koşul | guvensiz_nesne | GET | sahip_olmayan | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-006 | Olası eksik | Orta | kategori × beklenti sınıfı |  |  | SECURITY_CONFIGURATION | SC-FLW-003 |
| GAP-007 | Olası eksik | Orta | fixture kimliği |  |  | bob | istek yapan kimlikler=['admin', 'alice', 'carol'] |
| GAP-008 | Olası eksik | Orta | aktör çeşitliliği | guvenli_nesne | PUT;PATCH;DELETE | sahip_olmayan | SC-AUZ-001;SC-AUZ-002;SC-AUZ-003 |
| GAP-009 | Olası eksik | Orta | kaynak görünürlüğü | guvenli_nesne | PUT;PATCH;DELETE | sahip_olmayan | mevcut sahip-olmayan değiştirme senaryolarının kaynak durumu=['Yayında'] |
| GAP-010 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvenli_koleksiyon | POST | yonetici | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-011 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvenli_koleksiyon | PATCH | metot_desteklenmiyor | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-012 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvenli_nesne | POST | metot_desteklenmiyor | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-013 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvenli_nesne_aksiyonu | POST | kaynak_yok | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-014 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvenli_nesne_aksiyonu | GET | metot_desteklenmiyor | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-015 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvensiz_nesne | PUT | anonim | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-016 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvensiz_nesne | PATCH | anonim | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-017 | Olası eksik | Düşük | endpoint türü × metot × koşul | guvensiz_nesne | DELETE | anonim | Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok. |
| GAP-018 | Yetersiz meta veri | Düşük | meta veri alanları |  |  |  | şema alanları: id, category, http_method, endpoint, user_role, request_input, expected_http_status, expected_behavior, label, is_intentional_flaw, flaw_explanation, fixture_ref, requirement_refs |
| GAP-019 | Yetersiz meta veri | Düşük | veri kaynağı |  |  |  | dataset='h3-01-drf-controlled', target_app='benchmarks/drf_fixtures/sample_app' |

## 5. Veri kalitesi bulguları

Önem derecesine göre bulgu sayısı: Kritik: 0, Yüksek: 0, Orta: 0, Düşük: 0, Bilgi: 5.

**Doğrulanmış veri hatası (Kritik/Yüksek/Orta/Düşük): 0.** JSON Schema, eksik/null alan, yinelenen kimlik, geçersiz metot/kategori/rol/durum kodu, etiket tutarlılığı, fixture/endpoint referansları, view metot desteği ve JSON↔CSV tutarlılığı kontrollerinde hata bulunmadı. Bu sonuç kapsamın eksiksiz olduğu anlamına gelmez (bkz. bölüm 4).

| No | Senaryo | Alan | Sorun türü | Önem | Kanıt | Önerilen düzeltme |
|---|---|---|---|---|---|---|
| DQ-001 | SC-CRT-002 | user_role | ROL_DOGRULANAMIYOR | Bilgi | koleksiyon ucu (nesne yok); user=alice | Rolün anlamını belgeleyin (ör. 'başka kayıtların sahibi olan kullanıcı') veya bu senaryolarda 'user' rolünü kullanın. |
| DQ-002 | SC-NF-001 | user_role | ROL_DOGRULANAMIYOR | Bilgi | makale 999 fixture'da yok; user=alice | Rolün anlamını belgeleyin (ör. 'başka kayıtların sahibi olan kullanıcı') veya bu senaryolarda 'user' rolünü kullanın. |
| DQ-003 | SC-NF-002 | user_role | ROL_DOGRULANAMIYOR | Bilgi | makale 999 fixture'da yok; user=alice | Rolün anlamını belgeleyin (ör. 'başka kayıtların sahibi olan kullanıcı') veya bu senaryolarda 'user' rolünü kullanın. |
| DQ-004 | SC-MNA-001 | user_role | ROL_DOGRULANAMIYOR | Bilgi | koleksiyon ucu (nesne yok); user=alice | Rolün anlamını belgeleyin (ör. 'başka kayıtların sahibi olan kullanıcı') veya bu senaryolarda 'user' rolünü kullanın. |
| DQ-005 | SC-MNA-002 | user_role | ROL_DOGRULANAMIYOR | Bilgi | koleksiyon ucu (nesne yok); user=alice | Rolün anlamını belgeleyin (ör. 'başka kayıtların sahibi olan kullanıcı') veya bu senaryolarda 'user' rolünü kullanın. |

## 6. Yetkilendirme değerlendirmesi (PUT / PATCH / DELETE)

| Endpoint türü | Metot | Koşul | Durum | Senaryolar | Beklenen kod |
|---|---|---|---|---|---|
| Güvenli nesne (detay) | PUT | Anonim | Açıkça mevcut | SC-AUT-002 | 401 |
| Güvenli nesne (detay) | PUT | Kaynak sahibi | Açıkça mevcut | SC-UPD-001 | 200 |
| Güvenli nesne (detay) | PUT | Sahip olmayan kullanıcı | Açıkça mevcut | SC-AUZ-001 | 403 |
| Güvenli nesne (detay) | PUT | Yönetici | Açıkça mevcut | SC-UPD-002 | 200 |
| Güvenli nesne (detay) | PUT | Mevcut olmayan kaynak | Açıkça mevcut | SC-NF-001 | 404 |
| Güvenli nesne (detay) | PUT | Geçersiz girdi | Açıkça mevcut | SC-INP-003 | 400 |
| Güvenli nesne (detay) | PATCH | Anonim | Açıkça mevcut | SC-AUT-003 | 401 |
| Güvenli nesne (detay) | PATCH | Kaynak sahibi | Açıkça mevcut | SC-UPD-003 | 200 |
| Güvenli nesne (detay) | PATCH | Sahip olmayan kullanıcı | Açıkça mevcut | SC-AUZ-002 | 403 |
| Güvenli nesne (detay) | PATCH | Yönetici | Açıkça mevcut | SC-UPD-004 | 200 |
| Güvenli nesne (detay) | PATCH | Mevcut olmayan kaynak | Dolaylı temsil |  |  |
| Güvenli nesne (detay) | PATCH | Geçersiz girdi | Dolaylı temsil |  |  |
| Güvenli nesne (detay) | DELETE | Anonim | Açıkça mevcut | SC-AUT-004 | 401 |
| Güvenli nesne (detay) | DELETE | Kaynak sahibi | Açıkça mevcut | SC-DEL-001 | 204 |
| Güvenli nesne (detay) | DELETE | Sahip olmayan kullanıcı | Açıkça mevcut | SC-AUZ-003 | 403 |
| Güvenli nesne (detay) | DELETE | Yönetici | Açıkça mevcut | SC-DEL-002 | 204 |
| Güvenli nesne (detay) | DELETE | Mevcut olmayan kaynak | Açıkça mevcut | SC-NF-002 | 404 |
| Güvenli nesne (detay) | DELETE | Geçersiz girdi | Uygulanamaz |  |  |
| Bilerek güvensiz nesne (detay) | PUT | Anonim | Kapsanmıyor |  |  |
| Bilerek güvensiz nesne (detay) | PUT | Sahip olmayan kullanıcı | Açıkça mevcut | SC-FLW-001 | 200 |
| Bilerek güvensiz nesne (detay) | PATCH | Anonim | Kapsanmıyor |  |  |
| Bilerek güvensiz nesne (detay) | PATCH | Sahip olmayan kullanıcı | Dolaylı temsil |  |  |
| Bilerek güvensiz nesne (detay) | DELETE | Anonim | Kapsanmıyor |  |  |
| Bilerek güvensiz nesne (detay) | DELETE | Sahip olmayan kullanıcı | Açıkça mevcut | SC-FLW-002 | 204 |

- Güvenli nesne ucunda 17 uygulanabilir hücrenin 15 tanesi açıkça, 2 tanesi dolaylı temsil ediliyor; 0 tanesi kapsanmıyor.
- Eksik hücreler kapsam boşluğudur; doğrulanmış bir güvenlik açığı olarak yorumlanmamalıdır.

**Bilerek-hatalı senaryolar** (veri hatası değil; değerlendirme için kasıtlı):

| Senaryo | Metot | Endpoint | View | Gözlemlenen | Güvenli karşılık | Karşılık kodu | Açıklama uyumu |
|---|---|---|---|---|---|---|---|
| SC-FLW-001 | PUT | /api/insecure/articles/1/ | catalog.insecure.InsecureArticleDetail | 200 | SC-AUZ-001 | 403 | Uyumlu |
| SC-FLW-002 | DELETE | /api/insecure/articles/3/ | catalog.insecure.InsecureArticleDetail | 204 | SC-AUZ-003 | 403 | Uyumlu |
| SC-FLW-003 | GET | /api/insecure/articles/ | catalog.insecure.InsecureArticleList | 200 | SC-LST-001 | 200 | Açıklamada kod yok |

## 7. PyGoat ve kontrollü fixture kaynak ayrımı

| Kaynak | Konum | Kayıt | Metot | Kategori | Pozitif | Negatif | Bilerek hatalı | Değerlendirme hazırlığı |
|---|---|---|---|---|---|---|---|---|
| Kontrollü Django/DRF fixture | benchmarks/drf_fixtures/scenarios/scenarios.json | 38 | 5 | 5 | 15 | 23 | 3 | Etiketli, şema ile doğrulanmış; H3-01 senaryo↔uygulama testleriyle eşlenmiş. |
| PyGoat | benchmarks/pygoat/ | 0 | — | — | — | — | — | Etiketli senaryo kaydı yok; dizinde yalnızca inceleme/planlama notu var (README.md). Nicel karşılaştırma yapılamaz; sürüm sabitleme ve ground truth H3-03'e bırakılmış. |

PyGoat için depoda etiketli senaryo kaydı bulunmadığından **nicel kaynak karşılaştırması yapılamaz**; kaynak karşılaştırma grafiği bu nedenle üretilmedi. Bu durum kontrollü fixture veri kümesinin bir kusuru değildir: H3-01 kapsamı PyGoat'ı ayrı bir değerlendirme hedefi olarak belgelemekle sınırlıdır.

## 8. Öneriler (öncelik sırasıyla)

1. [Yüksek] (GAP-001) Mevcut olmayan kaynak (ör. /api/articles/999/) için PATCH senaryosu ekleyin; beklenen durum kodu H3-01 senaryo↔uygulama testiyle doğrulanmalıdır.
2. [Yüksek] (GAP-002) Kaynak sahibi tarafından geçersiz girdiyle PATCH senaryosu ekleyin (ör. boş başlık); kısmi doğrulama (partial=True) davranışı ayrıca belgelenmeli.
3. [Yüksek] (GAP-003) Bilerek güvensiz uçta sahip olmayan kullanıcı ile PATCH (BOLA/IDOR) senaryosu ekleyin ve güvenli uçtaki karşılığıyla eşleyin.
4. [Orta] (GAP-004) Güvenli nesne aksiyonu ucunda POST için 'Yönetici' koşulunu temsil eden bir senaryo eklemeyi değerlendirin.
5. [Orta] (GAP-005) Bilerek güvensiz detay ucunda sahip olmayan kullanıcının başkasının taslak kaydını okuduğu (hassas veri ifşası) bir GET senaryosu ekleyin ve güvenli detay ucundaki sahip-olmayan taslak erişimi (404) senaryosuyla eşleyin.
6. [Orta] (GAP-006) Bu kategoride güvenli uç için bir pozitif/kontrol senaryosu ekleyin (ör. güvenli listede taslakların gizlendiğini aynı kategoriyle etiketleyin).
7. [Orta] (GAP-007) 'bob' ile sahipler arası çapraz erişim senaryosu ekleyin (ör. bir kaynak sahibinin başka bir sahibin kaydını güncellemesi/silmesi).
8. [Orta] (GAP-008) Başka kayıtların sahibi olan bir kullanıcıyla (fixture'daki sahipler: alice, bob) başka bir sahibin kaydı üzerinde sahip-olmayan senaryosu ekleyin.
9. [Orta] (GAP-009) Taslak kayıt (ör. makale 2 veya 4) üzerinde sahip-olmayan PUT/PATCH/DELETE senaryosu ekleyin.
10. [Düşük] (GAP-010) Güvenli koleksiyon ucunda POST için 'Yönetici' koşulunu temsil eden bir senaryo eklemeyi değerlendirin.
11. [Düşük] (GAP-011) Güvenli koleksiyon ucunda PATCH için 'Desteklenmeyen metot' koşulunu temsil eden bir senaryo eklemeyi değerlendirin.
12. [Düşük] (GAP-012) Güvenli nesne (detay) ucunda POST için 'Desteklenmeyen metot' koşulunu temsil eden bir senaryo eklemeyi değerlendirin.
13. [Düşük] (GAP-013) Güvenli nesne aksiyonu ucunda POST için 'Mevcut olmayan kaynak' koşulunu temsil eden bir senaryo eklemeyi değerlendirin.
14. [Düşük] (GAP-014) Güvenli nesne aksiyonu ucunda GET için 'Desteklenmeyen metot' koşulunu temsil eden bir senaryo eklemeyi değerlendirin.
15. [Düşük] (GAP-015) Güvensiz uçta anonim PUT kontrol senaryosu ekleyin (IsAuthenticated nedeniyle 401 beklenir; doğrulanmalıdır).
16. [Düşük] (GAP-016) Güvensiz uçta anonim PATCH kontrol senaryosu ekleyin (IsAuthenticated nedeniyle 401 beklenir; doğrulanmalıdır).
17. [Düşük] (GAP-017) Güvensiz uçta anonim DELETE kontrol senaryosu ekleyin (IsAuthenticated nedeniyle 401 beklenir; doğrulanmalıdır).
18. [Düşük] `owner` rolünün nesnesiz veya mevcut olmayan kaynak içeren senaryolardaki anlamını belgeleyin (SC-CRT-002, SC-NF-001, SC-NF-002, SC-MNA-001, SC-MNA-002).
19. [Düşük] (GAP-018) Ground truth (H3-03) için 'auth_state' ve 'ownership' alanlarının açıkça eklenmesini değerlendirin.
20. [Düşük] (GAP-019) PyGoat senaryoları eklendiğinde kayıt düzeyinde 'source' alanı tanımlayın.

Önerilen tüm yeni senaryoların beklenen durum kodları, eklenmeden önce H3-01 senaryo↔uygulama testi (`pytest`) ile hedef uygulamaya karşı doğrulanmalıdır. Bu analiz kaynak veri kümesini değiştirmez.

## 9. Sınırlılıklar

- Referans ve rota kontrolleri statiktir; Django URL çözümlemesi HTTP isteği çalıştırmaz. Beklenen durum kodlarının gerçek davranışla eşleşmesi H3-01 `pytest` paketinin kapsamındadır.
- Kimlik doğrulama durumu ve sahiplik açık alanlar değildir; fixture verisinden türetilmiştir.
- Kapsam modeli, öncelikler ve düşük temsil eşiği proje-özgü sezgisel tercihlerdir.
- Veri kümesi küçük (38 kayıt) ve tek kaynaklıdır; oranlar istatistiksel genelleme için kullanılmamalıdır.
- PyGoat senaryo kaydı olmadığından kaynaklar arası nicel karşılaştırma yapılamamıştır.

## 10. Yeniden üretim

```bash
pip install -r experiments/h3_02_eda/requirements.txt
jupyter nbconvert --to notebook --execute --inplace \
  experiments/h3_02_eda/H3_02_EDA_Veri_Kalitesi.ipynb
python -m pytest experiments/h3_02_eda/tests -q
```

Google Colab adımları için `experiments/h3_02_eda/README.md` dosyasına bakın.
