# Bağımsız Test Kümesi ve Ground Truth Referansları (H3-03 / Issue #29)

#27'nin senaryo veri kümesi üzerine kurulu; AI test ajanının çıktılarının **tarafsız**
değerlendirilebilmesi için geliştirme verisinden ayrılmış **bağımsız test kümesi** ve
model/uygulama çıktısından **bağımsız** doğrulanmış **ground truth** (altın etiket) referansları.

## Dizin yapısı

```
benchmarks/reference_cases/
├── split.json              Aile + dev/test ataması (sabit)
├── split.md                Ayrım yöntemi, sızıntı önlemi, etiket anlamları, güvenlik bulguları
├── test_set.json           Bağımsız test kümesi (18 senaryo ID'si, sabitlenmiş)
├── ground_truth.json       38 senaryo için altın etiketler (kanonik)
├── ground_truth.schema.json
├── ground_truth.csv        JSON'dan türetilmiş (okunurluk/EDA)
├── INTEGRITY.txt           test_set.json + ground_truth.json SHA-256 özetleri
├── scripts/
│   ├── check_references.py      Şema + eşleşme + ayrım + sızıntı + sabitleme doğrulaması
│   └── export_ground_truth_csv.py
├── pytest.ini, conftest.py
└── tests/
    └── test_ground_truth_crosscheck.py   Ground truth ↔ uygulama bağımsızlık/hata kanıtı
```

## Doğrulama

```bash
# 1) Referans + ayrım + bütünlük doğrulaması
cd benchmarks/reference_cases
python scripts/check_references.py

# 2) Ground truth ↔ kontrollü uygulama çapraz-kontrolü (sample_app ortamını kullanır)
pytest -q            # 38 kayıt: hatasızlar uygulama=altın; hatalılar uygulamadan sapar

# 3) CSV'yi yeniden üret (opsiyonel)
python scripts/export_ground_truth_csv.py
```

> Çapraz-kontrol, `benchmarks/drf_fixtures/sample_app` uygulamasını `pythonpath` üzerinden kullanır;
> ek kurulum gerektirmez (aynı sanal ortam: Django + DRF + pytest-django).

## İlkeler

- Ground truth **model çıktısından ve uygulamanın hatalı davranışından bağımsızdır**; bilerek-hatalı
  senaryolarda güvenli beklenti ile gözlemlenen güvensiz davranış **ayrı alanlarda** tutulur.
- Dev/test ayrımı **aile bazlıdır**; aileler bölünmez (veri sızıntısı önlemi).
- Bağımsız test kümesi ve altın etiketler **SHA-256 ile sabitlenir**.
- Ayrıntı: [`split.md`](split.md). Kaynak senaryolar: `../drf_fixtures/scenarios/`.
