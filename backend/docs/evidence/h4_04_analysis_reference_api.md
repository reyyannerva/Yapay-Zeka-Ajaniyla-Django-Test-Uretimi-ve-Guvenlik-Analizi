# H4-04 | Analiz Çalışması ve Referans Gereksinim API'leri — Kanıt (Issue #36)

AnalysisRun oluşturma/listeleme/detay ve kaynak koddan bağımsız referans gereksinim JSON CRUD
uç noktaları. Kaynak: [`core/api/`](../../core/api/). Sahiplik H4-02 (#34), referans doğrulaması
H4-01 (#33) serializer'ı, ilerleme H4-01 `progress.py` ile. Davranışlar otomatik testlerle
doğrulanmıştır: `core/tests/test_analysis_api.py` (12), `core/tests/test_requirement_api.py` (13).

## Uç noktalar (`/api/`)

| Metot + yol | Açıklama | Yetki |
|---|---|---|
| `POST /api/analysis-runs/` | Analiz oluştur (durum `QUEUED`; gerçek işlem başlatılmaz) | Sahip |
| `GET  /api/analysis-runs/` | Kullanıcının analizleri | Sahip |
| `GET  /api/analysis-runs/{id}/` | Analiz detayı (+ `progress`, `requirements_snapshot`) | Sahip |
| `GET/POST/PUT/PATCH/DELETE /api/reference-requirements/[{id}/]` | Referans gereksinim JSON CRUD | Sahip |

## AnalysisRun — örnekler

**Oluşturma (kural tabanlı)**
```
POST /api/analysis-runs/   {"project": 1, "method": "RULE_BASED"}
201   {"id": 5, "project": 1, "status": "QUEUED", "method": "RULE_BASED", "llm_provider": null,
       "llm_model": null, "celery_task_id": null, "requirements_snapshot": [...], "progress": {...},
       "created_at": "...", "started_at": null, "finished_at": null}
```
- LLM yöntemlerinde `llm_provider` + `llm_model` zorunlu (eksikse 400); `RULE_BASED`'de verilmez (verilirse 400).
- Proje başına **tek aktif analiz**: ikinci aktif istek → 400.
- Başkasının / var olmayan proje kimliği → 400 (varlık ifşa edilmez).
- Oluşturulurken aktif referans gereksinimlerin anlık görüntüsü `requirements_snapshot`'a yazılır
  (her analiz kendi referans kümesini taşır; farklı analizler karışmaz).

**Detay — ilerleme yanıltıcı değildir**
```
GET /api/analysis-runs/5/
200   {... "progress": {"total": 0, "completed": 0, "running": 0, "pending": 0, "percent": null, ...}}
```
Henüz yürütme kaydı yoksa `percent: null` döner (yanıltıcı %0 üretilmez). İlerleme her sorguda
`TestExecution` kayıtlarından türetilir (sayaç saklanmaz).

## ReferenceRequirement — örnekler

**Oluşturma (ACCESS_RULE)**
```
POST /api/reference-requirements/
{
  "project": 1, "requirement_code": "ACC-1", "category": "ACCESS_RULE",
  "title": "Sipariş silme", "expected_result": "anonim 401, staff 204",
  "specification": {"schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": "DELETE",
                    "expected_status_by_role": {"anonymous": 401, "staff": 204}}
}
201   {"id": 9, "revision": 1, ...}
```
- `specification.method` yalnızca **GET/POST/PUT/PATCH/DELETE**; diğeri (ör. `HEAD`) → 400.
- `specification` JSON nesnesi değilse, zorunlu alan eksikse → 400.
- `(project, requirement_code)` benzersizdir; tekrar → 400.
- **PUT/PATCH** güncelleme → 200 ve `revision` artar; **DELETE** → 204.
- Başkasına ait / var olmayan proje kimliği → 400; başkasının kaydı → 404.

## Veri bütünlüğü ve güvenlik

- Referans gereksinimler **kullanıcının bağımsız beklentileridir**; yüklenen projenin mevcut davranışı
  veya LLM çıktısı otomatik ground truth kabul edilmez (H3-03 ilkesiyle uyumlu).
- Sahiplik H4-02 `OwnedQuerysetMixin`/`IsProjectOwner` ile: queryset kullanıcıya göre filtrelendiğinden
  başkasının kaydı **404**; proje alanı sahibin projelerine sınırlı olduğundan yetkisiz proje **400**.
- Kimliği doğrulanmamış istek → **401**. Bu aşamada gerçek AST/LLM/Docker başlatılmaz.
