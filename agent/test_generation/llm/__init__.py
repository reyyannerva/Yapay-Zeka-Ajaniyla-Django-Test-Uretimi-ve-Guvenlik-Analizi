"""LLM tabanlı Pytest üretim prototipi — H3-05 / Issue #31.

Groq üzerinden açık-ağırlıklı bir dil modeli (LiteLLM ile; varsayılan gpt-oss-120b — Issue #31
"Llama 3.3 70B" dese de bu model Groq'ta erişilemediğinden) kullanarak, H3-04'ün ortak endpoint
özeti ve H3-03'ün bağımsız referans gereksinimlerinden çalıştırılabilir Pytest testleri üretir.
Kural tabanlı baseline (H3-04) ile aynı girdi sözleşmesini, sınıflandırmayı ve rapor
yapısını kullanır; böylece H3-06 karşılaştırması adildir.

Not: Bu modül gizli bilgi (API anahtarı) içermez; anahtar ortam değişkeninden/.env'den okunur.
"""

VERSION = "1.0.0"
PROMPT_VERSION = "pytest_v1"
