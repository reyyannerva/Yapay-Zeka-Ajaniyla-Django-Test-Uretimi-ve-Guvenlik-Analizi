# Veritabanı Tasarımı — Kanonik Kaynak (H2-02 #24, H2-04 #26)

Bu dizin, sistemin PostgreSQL veritabanı tasarımının **tek kanonik kaynağıdır**. Hafta 4 geliştirmesi
(H4-01 #33 — veritabanı modelleri ve migration altyapısı) bu dosyaları esas almalıdır.

| Dosya | İçerik |
|---|---|
| `database_schema.sql` | PostgreSQL 16 referans DDL: 9 uygulama tablosu, kısıtlar, indeksler (revizyon 4 ile güncel) |
| `migrations_sql/0001_initial.postgresql.sql` | Django migration'ının ürettiği gerçek DDL (`sqlmigrate core 0001`) |
| `../../backend/core/models/` | **Uygulanan** Django ORM modelleri (9 model, `AUTH_USER_MODEL`) — H4-01 (#33) |
| `django_models.py` | Yönlendirme notu; revizyon 3 referans modelleri `backend/core/models/`'a taşındı |
| `schema_changes_h4_01.md` | Revizyon 3 → 4 değişiklik kaydı, model ↔ şema eşlemesi, mimari kararlar ve kanıt |
| `data_dictionary.md` | Tablo, sütun, ilişki, durum ve bütünlük kuralları |
| `schema_validation.md` | Şema ↔ modeller ↔ veri sözlüğü ↔ ER tutarlılık kontrolü ve kabul ölçütleri |

ER diyagramları: [`../diagrams/er-diagrams/`](../diagrams/er-diagrams/) (`er_diagram_full.*`,
`er_diagram_presentation.*`, düzenlenebilir kaynak `er_diagram_source.mmd`, inceleme notu `er_diagram_review.md`).

## Geçerli revizyon: revizyon 4 (9 tablo, H4-01 ile uygulandı)

`projects`, `reference_requirements`, `analysis_runs`, `endpoints`, `generated_tests`, `test_executions`,
`security_findings`, `reports`, `llm_calls` (+ Django'nun yönettiği `auth_user` ve django-axes tabloları).

| Revizyon | Commit | Tablo | Durum |
|---|---|---|---|
| 1 | `728547c` (2026-11-04, #24) | 6 | **Geçersiz kılındı**; git geçmişinde erişilebilir: `git show 728547c:docs/database/database_schema.sql` |
| 3 | `9a4324b` (2026-11-05, "Refs #24, #26") | 9 | Revizyon 4'ün temeli |
| 4 | H4-01 / #33 (`feature/h4-01-django-models-migrations`) | 9 | **Geçerli (kanonik)**; Django migration `core.0001_initial` ile PostgreSQL 16'da uygulandı |

Revizyon 3, Figma mockup'ına (`docs/mockup/README.md`, "Kapsam notları") göre hazırlanmış ve başlangıçta
`docs/diagrams/er-diagrams/` altına "(1)" ekli dosya adlarıyla yüklenmişti. Belgelerin kendisi hedef konum
olarak `docs/database/` dizinini gösteriyordu; Hafta 1–3 denetimi (bulgu D-01) sonrasında dosyalar içerikleri
değiştirilmeden buraya taşındı (bayt düzeyinde aynı; `git rev-parse 9a4324b:<eski yol>` ile karşılaştırılabilir).

### Revizyon 3'ün kanonik olarak seçilme gerekçesi

1. #24 ve #26 kapandıktan sonra aynı yazar tarafından "Refs #24, #26" ile yapılmış, değişikliklerin tamamı
   commit mesajında listelenmiş son tasarım revizyonudur.
2. #26 teslimi olan ER diyagramları ve `er_diagram_review.md` revizyon 3'ü (9 tablo) gösterir.
3. Sistem mimarisi diyagramı (H1-02 #18) veritabanında `Endpoint` ve `LLMCallLog` varlıklarını içerir.
4. Figma ekranları 06 (endpoint'ler), 10/21/25 (raporlar) ve 24 (model seçimi) yeni tabloları gerektirir.
5. `database_schema.sql`, `django_models.py` ve `schema_validation.md` kendi içinde tutarlıdır (75 SQL kısıtı;
   `uq_analysis_runs_one_active_per_project` SQL'de kısmi tekil indeks, modelde koşullu `UniqueConstraint`).
6. `django_models.py`, Django 5.2 ile `manage.py check` (0 sorun) ve `makemigrations --dry-run` kontrolünden geçer.

### Revizyon 1 → 3 farkları (alan düzeyinde doğrulandı)

- **Yeni tablolar:** `endpoints`, `reports`, `llm_calls`.
- **Kaldırılan sütunlar (bilinçli, commit mesajında belgeli):**
  - `projects.source_repository_url`: kaynak türü `ARCHIVE` / `ALLOWED_DIRECTORY` oldu; H1-06 ve Figma'daki
    "arşiv veya izinli dizin" kapsamıyla uyumlu.
  - `analysis_runs.retry_count`: test düzeyinde `generated_tests.repair_count` (0–1) ile değiştirildi;
    İST-06 "en fazla bir otomatik düzeltme" kuralıyla uyumlu.
- **Değer kümesi değişiklikleri:** `analysis_runs.status` 6 → 9 durum (Issue #24'teki altı durum korunmuş;
  `VALIDATING`, `SCANNING`, `CANCELLED` eklendi); `test_executions.status` (`PASS`, `FAIL`, `TECHNICAL_ERROR`,
  `STOPPED`, `NOT_RUN`…); `reference_requirements.category` (`ROLE`, `ACCESS_RULE`, `DEPLOY_EXPECTATION`) ve
  yeni `source` (`FORM`, `JSON_UPLOAD`).
- **Koşullu hâle gelen kısıt:** `ck_reference_requirements_expected_result_not_blank` → `ROLE` satırlarında
  `expected_result` boş olabilir; diğer kategorilerde boş olamaz.
- Kaldırılan indeks yoktur; 6 indeks eklenmiştir.

## Sonraki işlerle uyum notları (FUTURE)

- **H4-01 (#33):** Tamamlandı — modeller `backend/core/models/`, ayrıntı `schema_changes_h4_01.md`.
- **H6-07 (#76) AST motoru → `endpoints`:** H3-04 endpoint giriş sözleşmesi (`agent/test_generation/rule_based/
  schemas/endpoint_summary.schema.json`) yol şablonunu `{pk}` + `route_params` ile, tablo ise Django biçimiyle
  (`<int:pk>`) tutar; `unsupported_reason` tabloda `DYNAMIC_ROUTE` / `CUSTOM_PERMISSION` değer kümesidir. Eşleme
  AST entegrasyonunda tanımlanmalıdır.
- **H6-03 (#47) sonuç kaydı:** H3-04 sınıfları `test_executions` alanlarına eşlenebilir: `PASSED` → `PASS`;
  `KNOWN_FLAW_DETECTED` / `APPLICATION_MISMATCH` → `FAIL` (+ `is_security_test`); `GENERATION_ERROR` →
  `ERROR` + `error_origin = TEST_CODE`; `ENVIRONMENT_ERROR` → `ERROR` + `TARGET_APP` veya `INFRASTRUCTURE`;
  H3-06 `TIMEOUT` → `TIMEOUT` (revizyon 4 değer adları).
- **Referans gereksinimler:** ürün tablosunun kategorileri (`ROLE` / `ACCESS_RULE` / `DEPLOY_EXPECTATION`)
  değerlendirme veri kümesinin (H3-01/H3-03) senaryo kategorilerinden farklı bir sınıflandırmadır; H4-04 (#36)
  API'sinde eşleme tanımlanmalıdır.
