# H3-06 — Örnek Testler ve Çıktılar

Tüm örnekler depodaki gerçek artefaktlardır; çıktılar `experiments/h3_06_baseline_evaluation/results/*/logs/`
altındaki gerçek pytest günlüklerinden alınmıştır.

## 1. TP — SC-FLW-001 (PUT, BOLA)

**Baseline B (LLM)** — `experiments/h3_05_llm_baseline/raw_responses/SC-FLW-001.txt` içinden ayıklanan kod:

```python
def test_sc_flw_001(seeded_db, api_client):
    user = User.objects.get(username="carol")
    api_client.force_authenticate(user=user)
    url = reverse("insecure-article-detail", kwargs={"pk": 1})
    payload = {"title": "Örnek Başlık", "body": "örnek içerik"}
    response = api_client.put(url, payload, format="json")
    assert response.status_code == 403
```

Çıktı (`results/llm/logs/SC-FLW-001/probe.json`): `AssertionError: assert 200 == 403` → **FAIL → TP**.

**Baseline A (kural tabanlı)** — `test_put_generated.py::test_sc_flw_001_put_user_403`: rota doğrulaması,
durum kodu doğrulaması **ve** yan etki (kaynak değişmedi) doğrulaması içerir. Çıktı:
`[H304] scenario=SC-FLW-001 check=status expected=403 observed=200` → **FAIL → TP**.

## 2. FN — SC-FLW-003 (GET, içerik sapması)

```python
def test_sc_flw_003(seeded_db, api_client):
    url = reverse("insecure-article-list")
    response = api_client.get(url, format="json")
    assert response.status_code == 200
```

Uç taslak kayıtları ifşa etse de durum kodu 200'dür; test PASS → **FN**. Baseline A aynı sonucu verir ve
docstring'inde `CONTENT_ASSERTION_UNSUPPORTED` uyarısı taşır.

## 3. TN — SC-AUT-002 (PUT, anonim, 401)

Her iki baseline `assert response.status_code == 401` doğrular; güvenli uç 401 döndürür → PASS → **TN**.
`label = negative` olmasına karşın senaryo kusursuzdur; `label` matriste kullanılmaz.

## 4. Beş HTTP yöntemi (demo için)

| Yöntem | Senaryo | Küme | A sonucu | B sonucu |
|---|---|---|---|---|
| GET | SC-FLW-003 | test | PASS (FN) | PASS (FN) |
| POST | SC-CRT-001 | **geliştirme — metrik dışı** | H3-04 raporu: PASSED | H3-05 raporu: PASSED |
| PUT | SC-FLW-001 | test | FAIL (TP) | FAIL (TP) |
| PATCH | SC-UPD-003 | test | PASS (TN) | PASS (TN) |
| DELETE | SC-FLW-002 | test | FAIL (TP) | FAIL (TP) |

POST örneği yalnızca beş yöntemin gösterimi içindir; H3-06 metriklerine katılmaz (test kümesinde POST yok).

## 5. Baseline'lar arası nitel fark

Aynı sonuçlara karşın testler aynı derinlikte değildir: Baseline A 18 testte toplam 53 doğrulama
(rota + durum + 17 yan etki) içerirken Baseline B her testte yalnızca durum kodunu doğrular (18 doğrulama).
Bu fark bu test kümesindeki kusurlarda sonucu değiştirmemiştir; ancak yan etkisi olan kusurlarda (ör. 403
dönüp yine de veriyi değiştiren bir uç) yalnızca Baseline A kusuru yakalayabilir. Bu, ölçülmüş bir metrik
değil gözlemdir.
