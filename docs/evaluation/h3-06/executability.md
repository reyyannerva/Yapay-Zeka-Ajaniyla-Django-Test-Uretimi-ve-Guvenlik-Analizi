# H3-06 — Sözdizimi, Toplanabilirlik ve İlk Geçişte Çalıştırılabilirlik

Değerlendirilen çıktı: her iki yöntemin **ilk üretim çıktısı**; otomatik düzeltme, yeniden üretme veya elle
düzenleme yapılmamıştır (H3-05 `_complete_with_retry` yalnızca kota/zaman aşımı/bağlantı hatalarında aynı
istemi yeniden gönderir, kod onarmaz).

| Aşama | Baseline A — kural tabanlı | Baseline B — LLM |
|---|---|---|
| Artefakt bulundu | 18/18 | 18/18 |
| Python sözdizimi geçerli (`ast.parse`) | 18/18 | 18/18 |
| Güvenlik ön kontrolü (dış ağ/süreç yok) | 18/18 | 18/18 |
| Pytest tarafından toplandı | 18/18 | 18/18 |
| PASS | 16 | 16 |
| FAIL (doğrulama başarısız) | 2 | 2 |
| ERROR (teknik) | 0 | 0 |
| **İlk geçişte çalıştırılabilir (PASS + FAIL)** | **18/18 = %100** | **18/18 = %100** |
| Hedef ≥ %70 | Karşılandı | Karşılandı |

FAIL sonuçlarının ikisi de bilinen kusurları (SC-FLW-001/002) yakalayan **geçerli** testlerdir; üretim
hatası değildir ve çalıştırılabilir sayılır (Issue #32 gereği).

## Yöntem bazında

| Yöntem | Test kümesinde | A çalıştırılabilir | B çalıştırılabilir |
|---|---|---|---|
| GET | 1 | 1/1 | 1/1 |
| POST | 0 | Kapsam dışı | Kapsam dışı |
| PUT | 7 | 7/7 | 7/7 |
| PATCH | 4 | 4/4 | 4/4 |
| DELETE | 6 | 6/6 | 6/6 |

## Desteklenmeyen / üretilemeyen senaryolar

* H3-04: 38/38 senaryo `GENERATED`; `UNSUPPORTED` = 0. Desteklenmeyen uç türleri (dinamik rota, özel izin
  sınıfı) yalnızca H3-04 sentetik örneklerinde (`examples/unsupported_cases.json`) gösterilmiştir; test
  kümesinde yoktur.
* H3-05: 38/38 `GENERATED`; `INVALID_SYNTAX`, `EMPTY_OUTPUT`, `LLM_ERROR` = 0 (son çalıştırma). Önceki
  denemelerde `model_not_found` (Llama 3.3 70B) ve TPM kota hataları yaşanmış, `error_analysis.md`'de
  belgelenmiştir; bunlar ilk geçiş kod kalitesini değil erişimi etkiler.

## Değerlendirici doğrulaması

Hattın teknik hata türlerini doğru ayırdığı sentetik test modülleriyle sınanmıştır (sonuçlara katılmaz):
sözdizimi hatası, toplanamayan modül, test içermeyen modül, eksik fixture, `NoReverseMatch`, zaman aşımı,
dış ağ erişimi, eksik/yinelenen artefakt, ortam hatası (`agent/evaluation/tests/test_execution.py`).
