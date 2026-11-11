# H3-06 — Baseline karşılaştırma sonuçları (otomatik üretilmiştir)

Manifest: `experiments/h3_06_baseline_evaluation/evaluation_manifest.json` (sürüm 1.0.0, SHA-256 `4020a370c2911287…`); test kümesi 18 senaryo, 3 bilinen kusur.

| Metrik | Baseline A — kural tabanlı (H3-04) | Baseline B — LLM (H3-05) |
|---|---|---|
| Sözdizimi geçerli | 18/18 | 18/18 |
| Pytest toplama | 18/18 | 18/18 |
| İlk geçişte çalıştırılabilir | 1.0000 | 1.0000 |
| TP | 2 | 2 |
| FP | 0 | 0 |
| TN | 15 | 15 |
| FN | 1 | 1 |
| Matris dışı (teknik hata, kusursuz) | 0 | 0 |
| Precision | 1.0000 | 1.0000 |
| Recall | 0.6667 | 0.6667 |
| F1 | 0.8000 | 0.8000 |
| Hedef F1 ≥ 0.80 | Karşılandı | Karşılandı |
| Hedef çalıştırılabilirlik ≥ %70 | Karşılandı | Karşılandı |

## Senaryo düzeyi sonuçlar

| Senaryo | Yöntem | Güvenli beklenti | Kusur | Baseline A — kural tabanlı (H3-04) | Baseline B — LLM (H3-05) |
|---|---|---|---|---|---|
| SC-AUT-002 | PUT | 401 | hayır | PASS → TN | PASS → TN |
| SC-AUT-003 | PATCH | 401 | hayır | PASS → TN | PASS → TN |
| SC-AUT-004 | DELETE | 401 | hayır | PASS → TN | PASS → TN |
| SC-AUZ-001 | PUT | 403 | hayır | PASS → TN | PASS → TN |
| SC-AUZ-002 | PATCH | 403 | hayır | PASS → TN | PASS → TN |
| SC-AUZ-003 | DELETE | 403 | hayır | PASS → TN | PASS → TN |
| SC-DEL-001 | DELETE | 204 | hayır | PASS → TN | PASS → TN |
| SC-DEL-002 | DELETE | 204 | hayır | PASS → TN | PASS → TN |
| SC-FLW-001 | PUT | 403 | evet (status) | FAIL → TP, gözlenen 200 | FAIL → TP, gözlenen 200 |
| SC-FLW-002 | DELETE | 403 | evet (status) | FAIL → TP, gözlenen 204 | FAIL → TP, gözlenen 204 |
| SC-FLW-003 | GET | 200 | evet (content) | PASS → FN | PASS → FN |
| SC-INP-003 | PUT | 400 | hayır | PASS → TN | PASS → TN |
| SC-NF-001 | PUT | 404 | hayır | PASS → TN | PASS → TN |
| SC-NF-002 | DELETE | 404 | hayır | PASS → TN | PASS → TN |
| SC-UPD-001 | PUT | 200 | hayır | PASS → TN | PASS → TN |
| SC-UPD-002 | PUT | 200 | hayır | PASS → TN | PASS → TN |
| SC-UPD-003 | PATCH | 200 | hayır | PASS → TN | PASS → TN |
| SC-UPD-004 | PATCH | 200 | hayır | PASS → TN | PASS → TN |

## HTTP yöntemi kapsamı

| Yöntem | Test kümesinde | Baseline A — kural tabanlı (H3-04) çalıştırılabilir | Baseline B — LLM (H3-05) çalıştırılabilir |
|---|---|---|---|
| GET | 1 | 1/1 | 1/1 |
| POST | 0 | Kapsam dışı (test kümesinde yok) | Kapsam dışı (test kümesinde yok) |
| PUT | 7 | 7/7 | 7/7 |
| PATCH | 4 | 4/4 | 4/4 |
| DELETE | 6 | 6/6 | 6/6 |

Mutasyon skoru: **Bu aşamada ölçülmedi**.
