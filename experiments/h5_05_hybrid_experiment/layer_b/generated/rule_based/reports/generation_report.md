# H3-04 | Kural Tabanlı Pytest Üretim Raporu

> Otomatik üretilmiştir (`python -m agent.test_generation.rule_based all`). LLM kullanılmamıştır. Beklenen durum kodları `ground_truth.json` → `secure_status` alanından alınmıştır.

- Endpoint özeti kaynağı: `manual_fixture_metadata` (AST entegrasyonu: yok).
- Yeniden üretim sonucu birebir aynı: **evet**.

## Senaryo durumları

| Durum | Açıklama | Senaryo |
|---|---|---|
| GENERATED | Üretildi | 17 |
| UNSUPPORTED | Desteklenmiyor | 0 |
| INVALID_INPUT | Geçersiz girdi | 0 |
| MISSING_REFERENCE | Referans eksik | 0 |
| GENERATION_ERROR | Üretim hatası | 0 |

## Üretilen testlerin dağılımı

| HTTP metodu | Test |
|---|---|
| GET | 3 |
| POST | 2 |
| PUT | 3 |
| PATCH | 6 |
| DELETE | 3 |

| Beklenen durum kodu (referans) | Test |
|---|---|
| 200 | 6 |
| 201 | 1 |
| 204 | 1 |
| 400 | 1 |
| 401 | 2 |
| 403 | 6 |
| 404 | 0 |
| 405 | 0 |

| Rol | Test |
|---|---|
| admin | 1 |
| anonymous | 2 |
| owner | 5 |
| user | 9 |

| Yan etki kuralı | Test |
|---|---|
| count_plus_one | 1 |
| count_unchanged | 1 |
| none | 3 |
| partial_update_applied | 3 |
| resource_deleted | 1 |
| resource_unchanged | 7 |
| update_applied | 1 |

## Senaryo → test izlenebilirliği

| Senaryo | Durum | Metot | Endpoint | Rol (fixture) | Beklenen | Yan etki | Test |
|---|---|---|---|---|---|---|---|
| SC-TKC-001 | GENERATED | POST | /api/tasks/ | user (mehmet) | 201 | count_plus_one | test_post_generated.py::test_sc_tkc_001_post_user_201 |
| SC-TKC-002 | GENERATED | POST | /api/tasks/ | user (mehmet) | 400 | count_unchanged | test_post_generated.py::test_sc_tkc_002_post_user_400 |
| SC-TKD-001 | GENERATED | DELETE | /api/tasks/1/ | owner (ayse) | 204 | resource_deleted | test_delete_generated.py::test_sc_tkd_001_delete_owner_204 |
| SC-TKD-002 | GENERATED | DELETE | /api/tasks/1/ | user (mehmet) | 403 | resource_unchanged | test_delete_generated.py::test_sc_tkd_002_delete_user_403 |
| SC-TKL-001 | GENERATED | GET | /api/tasks/ | user (mehmet) | 200 | none | test_get_generated.py::test_sc_tkl_001_get_user_200 |
| SC-TKL-002 | GENERATED | GET | /api/tasks/ | anonymous (anonim) | 401 | none | test_get_generated.py::test_sc_tkl_002_get_anonymous_401 |
| SC-TKP-001 | GENERATED | PATCH | /api/tasks/1/ | owner (ayse) | 200 | partial_update_applied | test_patch_generated.py::test_sc_tkp_001_patch_owner_200 |
| SC-TKP-002 | GENERATED | PATCH | /api/tasks/1/ | user (mehmet) | 403 | resource_unchanged | test_patch_generated.py::test_sc_tkp_002_patch_user_403 |
| SC-TKP-003 | GENERATED | PATCH | /api/tasks/1/ | anonymous (anonim) | 401 | resource_unchanged | test_patch_generated.py::test_sc_tkp_003_patch_anonymous_401 |
| SC-TKP-004 | GENERATED | PATCH | /api/tasks/2/ | admin (yonetici) | 200 | partial_update_applied | test_patch_generated.py::test_sc_tkp_004_patch_admin_200 |
| SC-TKU-001 | GENERATED | PUT | /api/tasks/1/ | owner (ayse) | 200 | update_applied | test_put_generated.py::test_sc_tku_001_put_owner_200 |
| SC-TKU-002 | GENERATED | PUT | /api/tasks/1/ | user (mehmet) | 403 | resource_unchanged | test_put_generated.py::test_sc_tku_002_put_user_403 |
| SC-TKX-001 | GENERATED | PUT | /api/legacy/tasks/1/ | user (mehmet) | 403 | resource_unchanged | test_put_generated.py::test_sc_tkx_001_put_user_403 |
| SC-TKX-002 | GENERATED | PATCH | /api/legacy/tasks/1/ | user (mehmet) | 403 | resource_unchanged | test_patch_generated.py::test_sc_tkx_002_patch_user_403 |
| SC-TKX-003 | GENERATED | DELETE | /api/legacy/tasks/1/ | user (mehmet) | 403 | resource_unchanged | test_delete_generated.py::test_sc_tkx_003_delete_user_403 |
| SC-TKX-004 | GENERATED | PATCH | /api/legacy/tasks/1/ | owner (ayse) | 200 | partial_update_applied | test_patch_generated.py::test_sc_tkx_004_patch_owner_200 |
| SC-TKX-005 | GENERATED | GET | /api/legacy/tasks/1/ | owner (ayse) | 200 | none | test_get_generated.py::test_sc_tkx_005_get_owner_200 |

## Tanılar (uyarılar ve hatalar)

Tanı yok.

## Üretilen dosyalar (SHA-256)

| Dosya | SHA-256 |
|---|---|
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/conftest.py | 5a9671f9bb563e9b8fcd34bcc0a52f323697f0518c516d7c58b6ef0939368ae6 |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/h304_support.py | 0ad749a5207ad47f4d9f228b09582b1ec52a82cf49db2e64e5dfe14d8da181c4 |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/pytest.ini | 4bfe86a4b963adaf89a3f52de31700b9ea26db11b3fa9cc7cbcd56b50411b1aa |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_delete_generated.py | 221e8a58a438618dbdbcd949a3a9c80f36e159274d47e402cc3b6ce189c90dc3 |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_get_generated.py | 15b27b64d2263f673d901037e4eaf700dde09faaca11f4c38a8a4e2970e4ae38 |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_patch_generated.py | 2dbdaeccf5c606109b415bcdbb6bb41f75a283a9db020e1f4d221f197af7292a |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_post_generated.py | 1820ab610441f69eb4aaad3ce0942e3aaf15b9e045b9533deb0a0d2d35096356 |
| experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_put_generated.py | ec66cd4ca1ecff944c87a8a5842c991383c317358cc3f8eb8f184c527f360cc6 |

## Girdiler (SHA-256)

| Girdi | SHA-256 |
|---|---|
| experiments/h5_05_hybrid_experiment/layer_b/endpoint_summary.json | 9f4bd7729e95c0e17853a1b63800e307f4eca14418fac01412491600215b28ce |
| experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/reference_requirements.json | 91ae9d50ca94bb21f9027c0a0fde8602864b4035ad190046472874c240f88ed8 |
| experiments/h5_05_hybrid_experiment/layer_b/ground_truth.schema.json | 69ed5a1ce93f7ab8237149faf306b2d47f3e174e2fe0650bcf63c0c737527245 |
| experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/scenarios.json | de38304803c39cb73a0e3d4a5bac10d8174b362851f0b90a3c8317655a3205ba |
| experiments/h5_05_hybrid_experiment/layer_b/scenarios.schema.json | 960827549a92e53ffc58ad360440a307de147860a95a19d87b1f2c1aa5d4ceb0 |
| experiments/h5_05_hybrid_experiment/layer_b/target_app/tasks/fixtures/users.json | 7ab33235b998d72b04d436e5b13886fb99a04853b20543dca0bb6e2da8c884e8 |
| experiments/h5_05_hybrid_experiment/layer_b/target_app/tasks/fixtures/tasks.json | d0e1247af07bf2b61cfd157587e520aef44c9ad49fa526d97334ca2ed0df9369 |
