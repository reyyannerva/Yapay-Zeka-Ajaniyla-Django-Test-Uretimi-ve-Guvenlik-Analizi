# H5-04 — Dev kümesi üretim deneyi karşılaştırması (otomatik üretilmiştir)

Issue #42 · manifest sürüm 1.0.0 · dev kümesi 20 senaryo · ortam yüklendi: True.

Bu deney güvenlik tespiti metriği (TP/FP/TN/FN, F1) ÜRETMEZ: geliştirme kümesinde bilinen açık yoktur. Odak üretim kalitesi (sözdizimi/toplanma) ve çalıştırılabilirliktir (PASS/FAIL/ERROR/TIMEOUT).

| Metrik | llm | rule_based |
|---|---|---|
| Senaryo | 20 | 20 |
| Sözdizimi geçerli | 20/20 | 20/20 |
| Toplanabilir | 20/20 | 20/20 |
| İlk geçişte çalıştırılabilir | 1.0000 | 1.0000 |
| PASS | 20 | 20 |
| FAIL | 0 | 0 |
| ERROR (teknik) | 0 | 0 |
| NOT_RUN | 0 | 0 |
| Güvenlik F1 | Ölçülemedi | Ölçülemedi |

## Senaryo düzeyi sonuçlar

| Senaryo | Yöntem | llm | rule_based |
|---|---|---|---|
| SC-AUT-001 | POST | PASS | PASS |
| SC-AUT-005 | POST | PASS | PASS |
| SC-AUZ-004 | POST | PASS | PASS |
| SC-CRT-001 | POST | PASS | PASS |
| SC-CRT-002 | POST | PASS | PASS |
| SC-INP-001 | POST | PASS | PASS |
| SC-INP-002 | POST | PASS | PASS |
| SC-INP-004 | POST | PASS | PASS |
| SC-LST-001 | GET | PASS | PASS |
| SC-LST-002 | GET | PASS | PASS |
| SC-LST-003 | GET | PASS | PASS |
| SC-MNA-001 | DELETE | PASS | PASS |
| SC-MNA-002 | PUT | PASS | PASS |
| SC-PUB-001 | POST | PASS | PASS |
| SC-RET-001 | GET | PASS | PASS |
| SC-RET-002 | GET | PASS | PASS |
| SC-RET-003 | GET | PASS | PASS |
| SC-RET-004 | GET | PASS | PASS |
| SC-RET-005 | GET | PASS | PASS |
| SC-RET-006 | GET | PASS | PASS |

## HTTP yöntemi kapsamı (dev kümesi)

| Yöntem | Dev senaryo sayısı |
|---|---|
| GET | 9 |
| POST | 9 |
| PUT | 1 |
| PATCH | 0 |
| DELETE | 1 |

## 5 metot ve güvenlik açıkları için: mühürlü test kümesi (#32)

Dev kümesinde eksik metot(lar): PATCH. Gerçek güncelleme/silme işlemleri (PUT/PATCH/DELETE, 2xx/4xx) ve bilinen güvenlik açıkları mühürlü test kümesinde #32 (H3-06) ile değerlendirilir. Dev kümesinde PUT/DELETE yalnızca 405 (method-not-allowed) senaryolarında bulunur, PATCH ise yoktur; bu deney (dev kümesi, üretim + çalıştırılabilirlik) #32'yi tamamlar. Bkz. `experiments/h3_06_baseline_evaluation` (#32 / H3-06).
