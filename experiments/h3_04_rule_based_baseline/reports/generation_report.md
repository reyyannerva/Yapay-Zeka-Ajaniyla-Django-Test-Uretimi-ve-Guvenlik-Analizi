# H3-04 | Kural Tabanlı Pytest Üretim Raporu

> Otomatik üretilmiştir (`python -m agent.test_generation.rule_based all`). LLM kullanılmamıştır. Beklenen durum kodları `ground_truth.json` → `secure_status` alanından alınmıştır.

- Endpoint özeti kaynağı: `manual_fixture_metadata` (AST entegrasyonu: yok).
- Yeniden üretim sonucu birebir aynı: **evet**.

## Senaryo durumları

| Durum | Açıklama | Senaryo |
|---|---|---|
| GENERATED | Üretildi | 38 |
| UNSUPPORTED | Desteklenmiyor | 0 |
| INVALID_INPUT | Geçersiz girdi | 0 |
| MISSING_REFERENCE | Referans eksik | 0 |
| GENERATION_ERROR | Üretim hatası | 0 |

## Üretilen testlerin dağılımı

| HTTP metodu | Test |
|---|---|
| GET | 10 |
| POST | 9 |
| PUT | 8 |
| PATCH | 4 |
| DELETE | 7 |

| Beklenen durum kodu (referans) | Test |
|---|---|
| 200 | 12 |
| 201 | 2 |
| 204 | 2 |
| 400 | 4 |
| 401 | 5 |
| 403 | 6 |
| 404 | 5 |
| 405 | 2 |

| Rol | Test |
|---|---|
| admin | 5 |
| anonymous | 10 |
| owner | 11 |
| user | 12 |

| Yan etki kuralı | Test |
|---|---|
| count_plus_one | 2 |
| count_unchanged | 6 |
| none | 13 |
| partial_update_applied | 2 |
| resource_deleted | 2 |
| resource_still_absent | 2 |
| resource_unchanged | 9 |
| update_applied | 2 |

## Senaryo → test izlenebilirliği

| Senaryo | Durum | Metot | Endpoint | Rol (fixture) | Beklenen | Yan etki | Test |
|---|---|---|---|---|---|---|---|
| SC-AUT-001 | GENERATED | POST | /api/articles/ | anonymous (anonim) | 401 | count_unchanged | test_post_generated.py::test_sc_aut_001_post_anonymous_401 |
| SC-AUT-002 | GENERATED | PUT | /api/articles/1/ | anonymous (anonim) | 401 | resource_unchanged | test_put_generated.py::test_sc_aut_002_put_anonymous_401 |
| SC-AUT-003 | GENERATED | PATCH | /api/articles/1/ | anonymous (anonim) | 401 | resource_unchanged | test_patch_generated.py::test_sc_aut_003_patch_anonymous_401 |
| SC-AUT-004 | GENERATED | DELETE | /api/articles/1/ | anonymous (anonim) | 401 | resource_unchanged | test_delete_generated.py::test_sc_aut_004_delete_anonymous_401 |
| SC-AUT-005 | GENERATED | POST | /api/articles/2/publish/ | anonymous (anonim) | 401 | none | test_post_generated.py::test_sc_aut_005_post_anonymous_401 |
| SC-AUZ-001 | GENERATED | PUT | /api/articles/1/ | user (carol) | 403 | resource_unchanged | test_put_generated.py::test_sc_auz_001_put_user_403 |
| SC-AUZ-002 | GENERATED | PATCH | /api/articles/1/ | user (carol) | 403 | resource_unchanged | test_patch_generated.py::test_sc_auz_002_patch_user_403 |
| SC-AUZ-003 | GENERATED | DELETE | /api/articles/1/ | user (carol) | 403 | resource_unchanged | test_delete_generated.py::test_sc_auz_003_delete_user_403 |
| SC-AUZ-004 | GENERATED | POST | /api/articles/2/publish/ | user (carol) | 403 | none | test_post_generated.py::test_sc_auz_004_post_user_403 |
| SC-CRT-001 | GENERATED | POST | /api/articles/ | user (carol) | 201 | count_plus_one | test_post_generated.py::test_sc_crt_001_post_user_201 |
| SC-CRT-002 | GENERATED | POST | /api/articles/ | owner (alice) | 201 | count_plus_one | test_post_generated.py::test_sc_crt_002_post_owner_201 |
| SC-DEL-001 | GENERATED | DELETE | /api/articles/1/ | owner (alice) | 204 | resource_deleted | test_delete_generated.py::test_sc_del_001_delete_owner_204 |
| SC-DEL-002 | GENERATED | DELETE | /api/articles/3/ | admin (admin) | 204 | resource_deleted | test_delete_generated.py::test_sc_del_002_delete_admin_204 |
| SC-FLW-001 | GENERATED | PUT | /api/insecure/articles/1/ | user (carol) | 403 | resource_unchanged | test_put_generated.py::test_sc_flw_001_put_user_403 |
| SC-FLW-002 | GENERATED | DELETE | /api/insecure/articles/3/ | user (carol) | 403 | resource_unchanged | test_delete_generated.py::test_sc_flw_002_delete_user_403 |
| SC-FLW-003 | GENERATED | GET | /api/insecure/articles/ | anonymous (anonim) | 200 | none | test_get_generated.py::test_sc_flw_003_get_anonymous_200 |
| SC-INP-001 | GENERATED | POST | /api/articles/ | user (carol) | 400 | count_unchanged | test_post_generated.py::test_sc_inp_001_post_user_400 |
| SC-INP-002 | GENERATED | POST | /api/articles/ | user (carol) | 400 | count_unchanged | test_post_generated.py::test_sc_inp_002_post_user_400 |
| SC-INP-003 | GENERATED | PUT | /api/articles/1/ | owner (alice) | 400 | resource_unchanged | test_put_generated.py::test_sc_inp_003_put_owner_400 |
| SC-INP-004 | GENERATED | POST | /api/articles/ | user (carol) | 400 | count_unchanged | test_post_generated.py::test_sc_inp_004_post_user_400 |
| SC-LST-001 | GENERATED | GET | /api/articles/ | anonymous (anonim) | 200 | none | test_get_generated.py::test_sc_lst_001_get_anonymous_200 |
| SC-LST-002 | GENERATED | GET | /api/articles/ | user (carol) | 200 | none | test_get_generated.py::test_sc_lst_002_get_user_200 |
| SC-LST-003 | GENERATED | GET | /api/articles/ | admin (admin) | 200 | none | test_get_generated.py::test_sc_lst_003_get_admin_200 |
| SC-MNA-001 | GENERATED | DELETE | /api/articles/ | owner (alice) | 405 | count_unchanged | test_delete_generated.py::test_sc_mna_001_delete_owner_405 |
| SC-MNA-002 | GENERATED | PUT | /api/articles/ | owner (alice) | 405 | count_unchanged | test_put_generated.py::test_sc_mna_002_put_owner_405 |
| SC-NF-001 | GENERATED | PUT | /api/articles/999/ | owner (alice) | 404 | resource_still_absent | test_put_generated.py::test_sc_nf_001_put_owner_404 |
| SC-NF-002 | GENERATED | DELETE | /api/articles/999/ | owner (alice) | 404 | resource_still_absent | test_delete_generated.py::test_sc_nf_002_delete_owner_404 |
| SC-PUB-001 | GENERATED | POST | /api/articles/2/publish/ | owner (alice) | 200 | none | test_post_generated.py::test_sc_pub_001_post_owner_200 |
| SC-RET-001 | GENERATED | GET | /api/articles/1/ | anonymous (anonim) | 200 | none | test_get_generated.py::test_sc_ret_001_get_anonymous_200 |
| SC-RET-002 | GENERATED | GET | /api/articles/2/ | anonymous (anonim) | 404 | none | test_get_generated.py::test_sc_ret_002_get_anonymous_404 |
| SC-RET-003 | GENERATED | GET | /api/articles/2/ | owner (alice) | 200 | none | test_get_generated.py::test_sc_ret_003_get_owner_200 |
| SC-RET-004 | GENERATED | GET | /api/articles/2/ | admin (admin) | 200 | none | test_get_generated.py::test_sc_ret_004_get_admin_200 |
| SC-RET-005 | GENERATED | GET | /api/articles/2/ | user (carol) | 404 | none | test_get_generated.py::test_sc_ret_005_get_user_404 |
| SC-RET-006 | GENERATED | GET | /api/articles/999/ | anonymous (anonim) | 404 | none | test_get_generated.py::test_sc_ret_006_get_anonymous_404 |
| SC-UPD-001 | GENERATED | PUT | /api/articles/1/ | owner (alice) | 200 | update_applied | test_put_generated.py::test_sc_upd_001_put_owner_200 |
| SC-UPD-002 | GENERATED | PUT | /api/articles/3/ | admin (admin) | 200 | update_applied | test_put_generated.py::test_sc_upd_002_put_admin_200 |
| SC-UPD-003 | GENERATED | PATCH | /api/articles/1/ | owner (alice) | 200 | partial_update_applied | test_patch_generated.py::test_sc_upd_003_patch_owner_200 |
| SC-UPD-004 | GENERATED | PATCH | /api/articles/3/ | admin (admin) | 200 | partial_update_applied | test_patch_generated.py::test_sc_upd_004_patch_admin_200 |

## Tanılar (uyarılar ve hatalar)

| Senaryo | Kod | Önem | İleti | Ayrıntı |
|---|---|---|---|---|
| SC-CRT-002 | OWNERSHIP_UNVERIFIABLE | warning | owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi | hedef nesne yok (koleksiyon ucu) |
| SC-FLW-003 | CONTENT_ASSERTION_UNSUPPORTED | warning | Referanstaki güvenlik beklentisi içerik düzeyinde ve makine-okunur değil; yalnızca durum kodu doğrulanır, bilinen kusur bu testle tespit EDİLEMEZ | Liste yalnızca yayınlanan kayıtları döndürmeli; taslaklar gizli. |
| SC-MNA-001 | OWNERSHIP_UNVERIFIABLE | warning | owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi | hedef nesne yok (koleksiyon ucu) |
| SC-MNA-001 | METHOD_NOT_IN_OPERATIONS | warning | DELETE bu endpoint'in işlemleri arasında yok; beklenen sonuç referanstan alınır | işlemler=['GET', 'POST']; referans=405 |
| SC-MNA-002 | OWNERSHIP_UNVERIFIABLE | warning | owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi | hedef nesne yok (koleksiyon ucu) |
| SC-MNA-002 | METHOD_NOT_IN_OPERATIONS | warning | PUT bu endpoint'in işlemleri arasında yok; beklenen sonuç referanstan alınır | işlemler=['GET', 'POST']; referans=405 |
| SC-NF-001 | OWNERSHIP_UNVERIFIABLE | warning | owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi | kaynak 999 fixture'da yok |
| SC-NF-002 | OWNERSHIP_UNVERIFIABLE | warning | owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi | kaynak 999 fixture'da yok |

## Üretilen dosyalar (SHA-256)

| Dosya | SHA-256 |
|---|---|
| experiments/h3_04_rule_based_baseline/generated_tests/conftest.py | d273287a73c249766c488ed74f69372961211d0a7144d2845df2a2bc605ae68d |
| experiments/h3_04_rule_based_baseline/generated_tests/h304_support.py | 0ad749a5207ad47f4d9f228b09582b1ec52a82cf49db2e64e5dfe14d8da181c4 |
| experiments/h3_04_rule_based_baseline/generated_tests/pytest.ini | 1f9116cb78059d2a2f4943a09d400f9a8bcbae1053b6af04b6c55f39da011a66 |
| experiments/h3_04_rule_based_baseline/generated_tests/test_delete_generated.py | b74e713441360a078849b25432e89dd776c3ada14eff073617a6277cc5bd7095 |
| experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py | 95d9c3f729c0970947e7d9ff8cb64770a5e507fc1030e1fd5ce556ec97115876 |
| experiments/h3_04_rule_based_baseline/generated_tests/test_patch_generated.py | 842e728f00076bb190ab35352674c5f99647e886ad26534df75a96c98515be31 |
| experiments/h3_04_rule_based_baseline/generated_tests/test_post_generated.py | 7425d2626fe4bb1933719ed5156c1a8a8b95fc3a671a7532ae87b32be87c53da |
| experiments/h3_04_rule_based_baseline/generated_tests/test_put_generated.py | adc3ed53f74711e0283abfcc3e086836e2c4bc5a3b7a564115e5667d7e28f274 |

## Girdiler (SHA-256)

| Girdi | SHA-256 |
|---|---|
| experiments/h3_04_rule_based_baseline/endpoint_summary.json | 47fa2ed25bd95a89fe93a72f3705c74c05780c2e614c50b7bf380b77d8c4344f |
| benchmarks/reference_cases/ground_truth.json | b5114e74c63d9a60f335bd4984d9896da98d423c41ea87d618f2cca268fd737c |
| benchmarks/reference_cases/ground_truth.schema.json | 3642e429bfbee234d7a43caf27f1a8a0d9afb623dc5dd02fad1232a0e4e997ef |
| benchmarks/drf_fixtures/scenarios/scenarios.json | 6970d02ed14f5c66268b367a5cae2d02e753f60de5b8044b98ab53519237158e |
| benchmarks/drf_fixtures/scenarios/scenarios.schema.json | 8ddca198ee2356648f6859111e87e1d73353188248a8c2122af47540b0f247a1 |
| benchmarks/drf_fixtures/sample_app/catalog/fixtures/users.json | 4a976c917b4e5d7ad511bc93a239b6ea6dc0bc4122d58b603bed5ab67a1e4e62 |
| benchmarks/drf_fixtures/sample_app/catalog/fixtures/articles.json | 7d3017e8c4324818b615bc076ab0bd76400f0c3b1472ec95a4fc7d674915989d |
