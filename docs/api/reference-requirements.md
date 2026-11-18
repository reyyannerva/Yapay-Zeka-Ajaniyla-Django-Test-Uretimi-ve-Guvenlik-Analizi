# Referans Gereksinimler

Proje başına tanımlanan, üretilen testlerin karşılaştırılacağı beklenen davranışlardır. Tüm işlemler JWT ister;
yalnızca kullanıcının kendi projelerine ait kayıtlar görünür (`GET` listesi sayfasızdır).

| Yöntem | Yol |
|---|---|
| GET, POST | `/api/reference-requirements/` |
| GET, PUT, PATCH, DELETE | `/api/reference-requirements/{id}/` |

## 1. Alanlar

| Alan | Zorunlu | Not |
|---|---|---|
| `project` | evet | Sahip olunan proje |
| `requirement_code` | evet | Proje içinde tekil |
| `category` | evet | `ROLE`, `ACCESS_RULE`, `DEPLOY_EXPECTATION` |
| `title` | evet | |
| `expected_result` | `ROLE` dışında evet | |
| `source` | hayır | `FORM`, `JSON_UPLOAD` |
| `description`, `is_active` | hayır | |
| `specification` | kategoriye göre | Aşağıdaki `oneOf` yapıları |

Salt-okunur: `id`, `revision`, `http_method` (`ACCESS_RULE` için `specification.method`'dan türetilir, diğer
kategorilerde `null`), `created_at`, `updated_at`.

## 2. `specification` yapıları (`ReferenceSpecification`, `oneOf`)

```json
// ROLE
{"schema_version": 1, "role": "staff"}

// ACCESS_RULE
{"schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": "DELETE",
 "expected_status_by_role": {"anonymous": 401, "staff": 204}}

// DEPLOY_EXPECTATION
{"schema_version": 1, "setting": "DEBUG", "expected_value": false, "check_id": "DEP-DEBUG"}
```

### HTTP yöntemi

`ACCESS_RULE.method` şemada gerçek bir enum'dur (`HttpMethodEnum`): **`GET`, `POST`, `PUT`, `PATCH`, `DELETE`**.
Kural serializer, model doğrulaması ve veritabanı CHECK kısıtıyla üç katmanda uygulanır. `HEAD`, `OPTIONS`,
`TRACE`, küçük harfli yazım (`get`) veya boş değer reddedilir:

```json
{"specification": {"method": ["\"HEAD\" geçerli bir seçim değil."]}}
```

## 3. Örnek

```bash
curl -X POST "$BASE_URL/api/reference-requirements/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" \
  -d '{"project": 1, "requirement_code": "ACC-ORDERS-DELETE", "category": "ACCESS_RULE",
       "title": "Sipariş silme", "expected_result": "anonim 401, staff 204",
       "specification": {"schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": "DELETE",
                         "expected_status_by_role": {"anonymous": 401, "staff": 204}}}'
```

Hatalar şemadaki örneklerdedir: desteklenmeyen yöntem, eksik `specification` alanları, eksik zorunlu alanlar,
eksik `expected_result` (tümü 400; örnek gövdeler gerçek yanıtlarla testte karşılaştırılır), bulunamayan kayıt 404.
