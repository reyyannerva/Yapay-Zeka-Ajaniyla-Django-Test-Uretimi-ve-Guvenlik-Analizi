# H3-05 | LLM Üretilmiş Testlerin Çalıştırma Raporu

> Kontrollü fixture ortamında (`benchmarks/drf_fixtures/sample_app`) çalıştırıldı. Model: `groq/openai/gpt-oss-120b`.
> Sınıflandırma H3-04 ile uyumludur. Bilinen kusuru tespit eden başarısız testler beklenen sonuçtur.

## Sınıflandırma
| Sınıf | Adet |
|---|---|
| PASSED | 35 |
| KNOWN_FLAW_DETECTED | 2 |
| KNOWN_FLAW_NOT_DETECTED | 1 |
| APPLICATION_MISMATCH | 0 |
| GENERATION_ERROR | 0 |
| NOT_RUN | 0 |

## Senaryo → sonuç
| Senaryo | Sınıf | Pytest | Açıklama |
|---|---|---|---|
| SC-LST-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-LST-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-LST-003 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-RET-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-RET-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-RET-003 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-RET-004 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-RET-005 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-RET-006 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUT-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUT-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUT-003 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUT-004 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUT-005 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-CRT-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-CRT-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-INP-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-INP-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-INP-003 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-INP-004 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUZ-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUZ-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUZ-003 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-AUZ-004 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-UPD-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-UPD-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-UPD-003 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-UPD-004 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-DEL-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-DEL-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-NF-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-NF-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-MNA-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-MNA-002 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-PUB-001 | PASSED | passed | uygulama güvenli beklentiyle uyumlu |
| SC-FLW-001 | KNOWN_FLAW_DETECTED | failed | güvensiz uç güvenli beklentiden sapıyor (kusur yakalandı) |
| SC-FLW-002 | KNOWN_FLAW_DETECTED | failed | güvensiz uç güvenli beklentiden sapıyor (kusur yakalandı) |
| SC-FLW-003 | KNOWN_FLAW_NOT_DETECTED | passed | güvenli durum geçti; kusur (içerik düzeyi) durum koduyla yakalanmaz |
