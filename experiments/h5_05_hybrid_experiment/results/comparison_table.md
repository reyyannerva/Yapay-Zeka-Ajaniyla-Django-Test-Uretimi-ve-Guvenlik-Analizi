# H5-05 karşılaştırma tablosu (geliştirme kümesi — nihai performans DEĞİLDİR)

## Katman A — H5-04'ün 20 geliştirme senaryosu

HTTP metotları: {'GET': 9, 'POST': 9, 'PUT': 1, 'PATCH': 0, 'DELETE': 1} · bilinen kusur: 0 · karşılaştırılabilirlik: evet (aynı senaryolar ve aynı girdi özetleri)

| Yöntem | Denendi | Senaryo | TP | FP | TN | FN | Hariç | Precision | Recall | F1 | Sözdizimi geçerli | Toplanan | İlk geçiş çalıştırılabilir (pay/payda) | Oran | Test düzeyi | PASS/FAIL/ERROR/TIMEOUT/NOT_RUN | F1 ≥ 0.80 | Çalıştırılabilirlik ≥ %70 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rule_based | True | 20 | 0 | 0 | 20 | 0 | 0 | Ölçülemedi | Ölçülemedi | Ölçülemedi | 20/20 | 20/20 | 20/20 | 1.0000 | 20/20 | 20/0/0/0/0 | Ölçülemedi | Karşılandı |
| llm | True | 20 | 0 | 0 | 20 | 0 | 0 | Ölçülemedi | Ölçülemedi | Ölçülemedi | 20/20 | 20/20 | 20/20 | 1.0000 | 20/20 | 20/0/0/0/0 | Ölçülemedi | Karşılandı |
| hybrid | True | 20 | 0 | 0 | 20 | 0 | 0 | Ölçülemedi | Ölçülemedi | Ölçülemedi | 20/20 | 20/20 | 20/20 | 1.0000 | 21/21 | 20/0/0/0/0 | Ölçülemedi | Karşılandı |

## Katman B — kontrollü ek geliştirme kümesi (17 senaryo, 5 HTTP metodu)

HTTP metotları: {'GET': 3, 'POST': 2, 'PUT': 3, 'PATCH': 6, 'DELETE': 3} · bilinen kusur: 3 · karşılaştırılabilirlik: evet (aynı senaryolar ve aynı girdi özetleri)

| Yöntem | Denendi | Senaryo | TP | FP | TN | FN | Hariç | Precision | Recall | F1 | Sözdizimi geçerli | Toplanan | İlk geçiş çalıştırılabilir (pay/payda) | Oran | Test düzeyi | PASS/FAIL/ERROR/TIMEOUT/NOT_RUN | F1 ≥ 0.80 | Çalıştırılabilirlik ≥ %70 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rule_based | True | 17 | 3 | 0 | 14 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 17/17 | 17/17 | 17/17 | 1.0000 | 17/17 | 14/3/0/0/0 | Karşılandı | Karşılandı |
| llm | True | 17 | 3 | 0 | 14 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 17/17 | 17/17 | 17/17 | 1.0000 | 17/17 | 14/3/0/0/0 | Karşılandı | Karşılandı |
| hybrid | True | 17 | 3 | 0 | 14 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 17/17 | 17/17 | 17/17 | 1.0000 | 17/17 | 14/3/0/0/0 | Karşılandı | Karşılandı |
