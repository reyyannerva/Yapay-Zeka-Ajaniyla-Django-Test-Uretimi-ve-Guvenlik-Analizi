# Prompt şablonu: `pytest_v1` (Issue #31 / H3-05)

LLM'e gönderilen istem iki parçadan oluşur: sabit bir **system** rolü ve senaryo başına doldurulan
**user** şablonu. Kanonik kaynak: `agent/test_generation/llm/prompt.py`.

## İlke: cevap anahtarı sızıntısı yok

İsteme **yalnızca üretim girdisi** konur: HTTP metodu, endpoint, `reverse` url adı, pk, kullanıcı/rol,
istek gövdesi, yazılabilir alanlar, **beklenen güvenli durum kodu** ve beklenen davranış.
Şunlar **konmaz**: `is_known_flaw`, `observed_flawed_status`, `deviation_kind`, `security_finding`,
dev/test ayrımı. Bu alanlar yalnızca çalıştırma sonrası sınıflandırmada kullanılır.

## System

```
Sen bir yazılım test otomasyonu uzmanısın. Django REST Framework tabanlı KONTROLLÜ bir hedef
uygulama için TEK bir çalıştırılabilir Pytest test fonksiyonu yazarsın. Yalnızca istenen kodu
üretirsin; açıklama veya ek metin yazmazsın.
```

## User (doldurulan alanlar)

- Ortam sözleşmesi: `seeded_db` ve `api_client` fixture'ları, `force_authenticate`, `reverse`,
  `api_client.<method>(url, <gövde>, format="json")`.
- Test edilecek durum: senaryo kimliği, HTTP metodu, url adı, pk, kullanıcı (rol), istek gövdesi,
  yazılabilir alanlar, **beklenen HTTP durum kodu**, beklenen davranış.
- Gereksinimler: fonksiyon adı (`test_<senaryo>`), `(seeded_db, api_client)` parametreleri,
  gerekiyorsa `force_authenticate`, `assert response.status_code == <beklenen>`, import'lar ve
  `pytestmark = pytest.mark.django_db`, çıktı tek bir ```python kod bloğu.

## Sürümleme

Prompt değişirse sürüm artırılır (`pytest_v2` …) ve raporlara yazılır; tekrarlanabilirlik için
model, sıcaklık ve girdi SHA-256 ile birlikte kaydedilir.
