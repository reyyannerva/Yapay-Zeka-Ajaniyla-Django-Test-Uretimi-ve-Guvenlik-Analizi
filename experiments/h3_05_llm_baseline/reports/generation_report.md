# H3-05 | LLM Tabanlı Pytest Üretim Raporu

> Üretici: `agent.test_generation.llm` v1.0.0 · Prompt: `pytest_v1` · Model: `groq/openai/gpt-oss-120b`.
> Beklenen durum kodları bağımsız referanstan (`ground_truth.json` → `secure_status`) alınmıştır.
> Cevap anahtarı meta (is_known_flaw, gözlenen kod, dev/test ayrımı) prompt'a konulmamıştır.

## Üretim durumları
| Durum | Adet |
|---|---|
| GENERATED | 38 |
| INVALID_SYNTAX | 0 |
| EMPTY_OUTPUT | 0 |
| LLM_ERROR | 0 |

## Üretilen testlerin metot dağılımı (GENERATED)
| HTTP metodu | Adet |
|---|---|
| GET | 10 |
| POST | 9 |
| PUT | 8 |
| PATCH | 4 |
| DELETE | 7 |

## Kaynak tüketimi (İST-12)
| Ölçüt | Adet |
|---|---|
| Prompt token | 25638 |
| Completion token | 9422 |
| Toplam token | 35060 |
| Toplam süre (ms) | 63320 |
| Ortalama süre (ms) | 1666 |

## Senaryo → üretim izlenebilirliği
| Senaryo | Durum | Metot | Token (p/c) | Süre (ms) | Not |
|---|---|---|---|---|---|
| SC-LST-001 | GENERATED | GET | 677/358 | 2446 |  |
| SC-LST-002 | GENERATED | GET | 680/294 | 1275 |  |
| SC-LST-003 | GENERATED | GET | 667/296 | 1630 |  |
| SC-RET-001 | GENERATED | GET | 672/200 | 1407 |  |
| SC-RET-002 | GENERATED | GET | 678/187 | 1323 |  |
| SC-RET-003 | GENERATED | GET | 673/218 | 1110 |  |
| SC-RET-004 | GENERATED | GET | 673/202 | 1636 |  |
| SC-RET-005 | GENERATED | GET | 681/193 | 1348 |  |
| SC-RET-006 | GENERATED | GET | 671/202 | 1471 |  |
| SC-AUT-001 | GENERATED | POST | 687/349 | 3322 |  |
| SC-AUT-002 | GENERATED | PUT | 684/183 | 1345 |  |
| SC-AUT-003 | GENERATED | PATCH | 678/186 | 1303 |  |
| SC-AUT-004 | GENERATED | DELETE | 670/249 | 1285 |  |
| SC-AUT-005 | GENERATED | POST | 614/176 | 1458 |  |
| SC-CRT-001 | GENERATED | POST | 695/254 | 1838 |  |
| SC-CRT-002 | GENERATED | POST | 681/231 | 1240 |  |
| SC-INP-001 | GENERATED | POST | 676/360 | 2220 |  |
| SC-INP-002 | GENERATED | POST | 683/251 | 1492 |  |
| SC-INP-003 | GENERATED | PUT | 677/201 | 1216 |  |
| SC-INP-004 | GENERATED | POST | 712/287 | 1068 |  |
| SC-AUZ-001 | GENERATED | PUT | 693/236 | 1590 |  |
| SC-AUZ-002 | GENERATED | PATCH | 687/227 | 1322 |  |
| SC-AUZ-003 | GENERATED | DELETE | 677/216 | 1117 |  |
| SC-AUZ-004 | GENERATED | POST | 622/261 | 1290 |  |
| SC-UPD-001 | GENERATED | PUT | 686/234 | 1813 |  |
| SC-UPD-002 | GENERATED | PUT | 686/250 | 1237 |  |
| SC-UPD-003 | GENERATED | PATCH | 679/229 | 2397 |  |
| SC-UPD-004 | GENERATED | PATCH | 679/234 | 1440 |  |
| SC-DEL-001 | GENERATED | DELETE | 672/217 | 1654 |  |
| SC-DEL-002 | GENERATED | DELETE | 672/223 | 1383 |  |
| SC-NF-001 | GENERATED | PUT | 693/215 | 1090 |  |
| SC-NF-002 | GENERATED | DELETE | 677/225 | 1344 |  |
| SC-MNA-001 | GENERATED | DELETE | 672/325 | 2318 |  |
| SC-MNA-002 | GENERATED | PUT | 676/371 | 1936 |  |
| SC-PUB-001 | GENERATED | POST | 620/259 | 1827 |  |
| SC-FLW-001 | GENERATED | PUT | 703/230 | 1184 |  |
| SC-FLW-002 | GENERATED | DELETE | 687/240 | 1250 |  |
| SC-FLW-003 | GENERATED | GET | 628/353 | 5695 |  |
