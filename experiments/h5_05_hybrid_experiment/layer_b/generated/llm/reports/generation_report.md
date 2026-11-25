# H3-05 | LLM Tabanlı Pytest Üretim Raporu

> Üretici: `agent.test_generation.llm` v1.0.0 · Prompt: `pytest_v1` · Model: `groq/openai/gpt-oss-120b`.
> Beklenen durum kodları bağımsız referanstan (`ground_truth.json` → `secure_status`) alınmıştır.
> Cevap anahtarı meta (is_known_flaw, gözlenen kod, dev/test ayrımı) prompt'a konulmamıştır.

## Üretim durumları
| Durum | Adet |
|---|---|
| GENERATED | 17 |
| INVALID_SYNTAX | 0 |
| EMPTY_OUTPUT | 0 |
| LLM_ERROR | 0 |

## Üretilen testlerin metot dağılımı (GENERATED)
| HTTP metodu | Adet |
|---|---|
| GET | 3 |
| POST | 2 |
| PUT | 3 |
| PATCH | 6 |
| DELETE | 3 |

## Kaynak tüketimi (İST-12)
| Ölçüt | Adet |
|---|---|
| Prompt token | 11568 |
| Completion token | 4146 |
| Toplam token | 15714 |
| Toplam süre (ms) | 16327 |
| Ortalama süre (ms) | 960 |

## Senaryo → üretim izlenebilirliği
| Senaryo | Durum | Metot | Token (p/c) | Süre (ms) | Not |
|---|---|---|---|---|---|
| SC-TKL-001 | GENERATED | GET | 672/325 | 2246 |  |
| SC-TKL-002 | GENERATED | GET | 677/226 | 874 |  |
| SC-TKC-001 | GENERATED | POST | 689/250 | 943 |  |
| SC-TKC-002 | GENERATED | POST | 676/257 | 853 |  |
| SC-TKU-001 | GENERATED | PUT | 693/249 | 844 |  |
| SC-TKU-002 | GENERATED | PUT | 689/232 | 873 |  |
| SC-TKP-001 | GENERATED | PATCH | 684/219 | 870 |  |
| SC-TKP-002 | GENERATED | PATCH | 677/221 | 719 |  |
| SC-TKP-003 | GENERATED | PATCH | 680/278 | 1031 |  |
| SC-TKP-004 | GENERATED | PATCH | 680/233 | 740 |  |
| SC-TKD-001 | GENERATED | DELETE | 670/219 | 715 |  |
| SC-TKD-002 | GENERATED | DELETE | 674/205 | 892 |  |
| SC-TKX-001 | GENERATED | PUT | 693/226 | 848 |  |
| SC-TKX-002 | GENERATED | PATCH | 681/324 | 1255 |  |
| SC-TKX-003 | GENERATED | DELETE | 678/216 | 846 |  |
| SC-TKX-004 | GENERATED | PATCH | 681/228 | 861 |  |
| SC-TKX-005 | GENERATED | GET | 674/238 | 917 |  |
