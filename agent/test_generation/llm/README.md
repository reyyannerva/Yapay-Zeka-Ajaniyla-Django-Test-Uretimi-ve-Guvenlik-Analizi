# LLM Tabanlı Pytest Üretimi (Issue #31 / H3-05)

Groq üzerinden **açık-ağırlıklı bir dil modeli** (LiteLLM ile) kullanarak Django/DRF endpoint özeti
ve bağımsız referans gereksinimlerinden çalıştırılabilir Pytest testleri üreten ilk LLM prototipi.

> **Model notu:** Issue #31 "Llama 3.3 70B" belirtir; ancak bu model Groq kataloğunda erişilemediğinden
> (model_not_found; hesapta Llama sohbet modeli listelenmiyor) açık-ağırlıklı **`openai/gpt-oss-120b`**
> kullanılmıştır. Öneri formu zaten "Groq üzerinden açık ağırlıklı bir dil modeli" der (model adı
> bağlamaz) ve kod LiteLLM ile model-bağımsızdır; model `.env`/`--model` ile değiştirilebilir.

Kural tabanlı baseline (`agent/test_generation/rule_based/`, #30) ile **aynı girdi sözleşmesini,
sınıflandırmayı ve rapor yapısını** kullanır; böylece H3-06 karşılaştırması adildir.

## Girdiler (ortak)

- `experiments/h3_04_rule_based_baseline/endpoint_summary.json` — H3-04 ortak endpoint özeti
- `benchmarks/reference_cases/ground_truth.json` — H3-03 bağımsız referans (beklenen güvenli durum)
- `benchmarks/drf_fixtures/scenarios/scenarios.json` — H3-01 senaryolar

## Modüller

| Dosya | Görev |
|---|---|
| `loaders.py` | Girdileri yükler, senaryo+referans+endpoint → `Case` |
| `prompt.py` | `pytest_v1` prompt şablonu (yalnızca üretim girdisi; cevap anahtarı yok) |
| `client.py` | LiteLLM/Groq sarmalayıcı (anahtar .env'den, hata sınıflandırma, token/süre) |
| `extract.py` / `validation.py` | Kod ayıklama / `ast.parse` sözdizimi kontrolü |
| `generator.py` | Üretim orkestrasyonu (prompt→çağrı→ayıkla→doğrula→yaz) |
| `runner.py` | Üretilen testleri çalıştırır, H3-04 taksonomisiyle sınıflandırır |
| `reporting.py` | Üretim ve çalıştırma raporları (JSON+MD) |

## Veri bütünlüğü

- İsteme **yalnızca üretim girdisi** verilir (metot, endpoint, rol, girdi, beklenen güvenli
  durum/davranış). **Cevap anahtarı meta** (is_known_flaw, gözlenen güvensiz kod, dev/test ayrımı)
  prompt'a **konmaz**; yalnızca sınıflandırmada kullanılır (bkz. `tests/test_loaders_prompt.py`).
- API anahtarı koda/log/repoya yazılmaz; `.env`'den okunur, mesajlardan temizlenir.
- Çalıştırılmamış test "başarılı" raporlanmaz; metrik uydurulmaz.

## Çalıştırma (depo kökünden)

```bash
pip install -r experiments/h3_05_llm_baseline/requirements.txt
# Anahtar: experiments/h3_05_llm_baseline/.env içine GROQ_API_KEY=... (bkz. .env.example)

python -m agent.test_generation.llm all        # üret + çalıştır + raporla
python -m agent.test_generation.llm generate   # yalnızca üret
python -m agent.test_generation.llm run         # mevcut üretilmişleri çalıştır + sınıflandır
```

Seçenekler: `--model`, `--temperature`, `--max-tokens`, `--only SC-...`, `--limit N`,
`--endpoints/--ground-truth/--scenarios/--out/--reports/--env`.

## Modül birim testleri (ağ/anahtar gerekmez)

```bash
cd agent/test_generation/llm && python -m pytest -q
```
