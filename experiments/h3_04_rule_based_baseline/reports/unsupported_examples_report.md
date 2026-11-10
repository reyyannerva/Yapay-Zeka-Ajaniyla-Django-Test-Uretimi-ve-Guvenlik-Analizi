# H3-04 | Desteklenmeyen ve Geçersiz Girdi Örnekleri

> Otomatik üretilmiştir (`python -m agent.test_generation.rule_based examples`). Örnekler **sentetiktir** ve yalnızca üreticinin bu durumları sessizce atlamadığını, gerekçeli tanı ürettiğini gösterir.

Toplam **21** örnek; beklenen durum ve tanı koduyla uyumlu: **21**.

| Örnek | Açıklama | Beklenen | Gerçekleşen | Tanı kodları | Ayrıntı | Uyum |
|---|---|---|---|---|---|---|
| EX-00 | Temel örnek (değişiklik yok) — üretilmeli | GENERATED / - | GENERATED | — | — | ✓ |
| EX-01 | Geçersiz HTTP metodu (FETCH) | INVALID_INPUT / UNKNOWN_METHOD | INVALID_INPUT | UNKNOWN_METHOD | Geçersiz HTTP metodu (http_method='FETCH') | ✓ |
| EX-02 | Geçerli ancak desteklenmeyen HTTP metodu (HEAD) | UNSUPPORTED / UNSUPPORTED_METHOD | UNSUPPORTED | UNSUPPORTED_METHOD | Bu baseline yalnızca GET, POST, PUT, PATCH, DELETE metotlarını destekler (http_method=HEAD) | ✓ |
| EX-03 | Desteklenmeyen beklenen durum kodu (418) | INVALID_INPUT / INVALID_STATUS | INVALID_INPUT | INVALID_STATUS | Referanstaki beklenen durum kodu geçersiz veya desteklenmiyor (secure_status=418; desteklenen=[200, 201, 204, 400, 401, 403, 404, 405]) | ✓ |
| EX-04 | Çözümlenemeyen endpoint (/api/comments/1/) | INVALID_INPUT / UNRESOLVED_ROUTE | INVALID_INPUT | UNRESOLVED_ROUTE | Endpoint yolu endpoint özetindeki hiçbir şablona uymuyor (endpoint=/api/comments/1/; şablonlar=['/api/articles/', '/api/articles/{pk}/', '/api/articles/{pk}/publish/', '/api/insecure/articles/', '/api/insecure/articles/{pk}/']) | ✓ |
| EX-05 | Senaryo var, bağımsız referans (ground truth) yok | MISSING_REFERENCE / MISSING_REFERENCE | MISSING_REFERENCE | MISSING_REFERENCE | Senaryo için bağımsız referans (ground truth) kaydı yok; beklenen sonuç uydurulmaz, test üretilmez  | ✓ |
| EX-06 | Referans var, senaryonun istek verisi yok | MISSING_REFERENCE / MISSING_SCENARIO_DATA | MISSING_REFERENCE | MISSING_SCENARIO_DATA | Ground truth kaydının istek verisi (endpoint, girdi, fixture) bulunamadı scenarios.json içinde bu kimlik yok | ✓ |
| EX-07 | Fixture'da olmayan kullanıcı (dave) | INVALID_INPUT / MISSING_FIXTURE_USER | INVALID_INPUT | MISSING_FIXTURE_USER | Fixture kullanıcısı bulunamadı (user='dave'; mevcut=['admin', 'alice', 'bob', 'carol']) | ✓ |
| EX-08 | owner rolü, kaynağın sahibi olmayan kullanıcıyla (carol → makale 1) | INVALID_INPUT / ROLE_MISMATCH | INVALID_INPUT | ROLE_MISMATCH | Rol etiketi fixture verisiyle çelişiyor (owner rolü, kaynağın sahibi olmayan kullanıcıyla (carol, kaynak 1)) | ✓ |
| EX-09 | Detay ucunda route parametresi için fixture referansı yok | INVALID_INPUT / MISSING_ROUTE_PARAM | INVALID_INPUT | MISSING_ROUTE_PARAM | 'pk' route parametresi için fixture kaynak referansı yok | ✓ |
| EX-10 | Endpoint'teki pk ile fixture referansı çelişiyor | INVALID_INPUT / ROUTE_PARAM_MISMATCH | INVALID_INPUT | ROUTE_PARAM_MISMATCH | Endpoint'teki parametre fixture referansıyla uyuşmuyor (pk=1, fixture_ref.article=2) | ✓ |
| EX-11 | İstek gövdesi nesne değil (liste) | INVALID_INPUT / INVALID_PAYLOAD | INVALID_INPUT | INVALID_PAYLOAD | request_input bir JSON nesnesi veya null olmalı (tip=list) | ✓ |
| EX-12 | Desteklenmiyor olarak işaretli endpoint (dinamik rota) | UNSUPPORTED / UNSUPPORTED_ENDPOINT | UNSUPPORTED | UNSUPPORTED_ENDPOINT | Endpoint desteklenmiyor olarak işaretli (Dinamik rota ve özel izin sınıfı (DynamicPermission) ilk baseline kapsamı dışında) | ✓ |
| EX-13 | DRF dışı Django fonksiyon view'ı | UNSUPPORTED / UNSUPPORTED_VIEW | UNSUPPORTED | UNSUPPORTED_VIEW | View türü bu baseline tarafından desteklenmiyor (yalnızca DRF ViewSet/APIView/GenericAPIView) (view=synthetic.views.legacy_article (DjangoFunctionView)) | ✓ |
| EX-14 | Aynı yolu karşılayan iki endpoint şablonu (belirsiz eşleşme) | INVALID_INPUT / AMBIGUOUS_ENDPOINT | INVALID_INPUT | AMBIGUOUS_ENDPOINT | Endpoint yolu birden fazla şablona uyuyor (EP-ARTICLE-DETAIL, EP-SYN-DUPLICATE) | ✓ |
| EX-15 | Desteklenmeyen kimlik doğrulama mekanizması (JWT) | UNSUPPORTED / UNSUPPORTED_AUTH | UNSUPPORTED | UNSUPPORTED_AUTH | Kimlik doğrulama mekanizması desteklenmiyor (mekanizmalar=['JWTAuthentication']) | ✓ |
| EX-16 | Ground truth ile senaryo verisi metotta çelişiyor | INVALID_INPUT / REFERENCE_CONFLICT | INVALID_INPUT | REFERENCE_CONFLICT | Ground truth ile senaryo verisi çelişiyor http_method: ground_truth='PUT', scenarios='PATCH' | ✓ |
| EX-17 | Bilinmeyen kullanıcı rolü (superuser) | INVALID_INPUT / UNKNOWN_ROLE | INVALID_INPUT | UNKNOWN_ROLE | Bilinmeyen kullanıcı rolü (user_role='superuser') | ✓ |
| EX-18 | owner rolü, koleksiyon ucunda (sahiplik doğrulanamaz) — uyarıyla üretilir | GENERATED / OWNERSHIP_UNVERIFIABLE | GENERATED | OWNERSHIP_UNVERIFIABLE | owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi (hedef nesne yok (koleksiyon ucu)) | ✓ |
| EX-19 | Endpoint özeti geçersiz JSON | INVALID_INPUT / INVALID_JSON | INVALID_INPUT | INVALID_JSON | satır 1: Expecting value | ✓ |
| EX-20 | Endpoint özetinde zorunlu alan eksik (url_name) | INVALID_INPUT / SCHEMA_VIOLATION | INVALID_INPUT | SCHEMA_VIOLATION | endpoint özeti: şema ihlali (endpoints/1) 'url_name' is a required property | ✓ |
