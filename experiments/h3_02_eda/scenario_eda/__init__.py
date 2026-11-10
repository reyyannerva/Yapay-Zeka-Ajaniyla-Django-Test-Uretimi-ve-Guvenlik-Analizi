"""H3-02 / Issue #28 — Senaryo veri kümesi EDA ve veri kalitesi analiz paketi.

Modüller:
    data      Girdi dosyalarının bulunması, yüklenmesi, URL rotalarının statik çözümlemesi,
              (isteğe bağlı) Django URL çözümlemesi ve kayıt düzeyi zenginleştirme.
    quality   Yeniden kullanılabilir, test edilebilir veri kalitesi kontrolleri.
    coverage  Dağılım tabloları, çapraz tablolar, kapsam modeli ve kapsam boşlukları.
    report    Rapor tablolarının üretimi, dışa aktarımı ve Markdown özetinin oluşturulması.
    plots     Rapor grafikleri (yalnızca bu modül matplotlib ister).

Kanonik veri kaynağı ``benchmarks/drf_fixtures/scenarios/scenarios.json`` dosyasıdır; bu paket
kaynak veriyi hiçbir koşulda değiştirmez.
"""
from .data import (  # noqa: F401
    HTTP_METHODS,
    AnalysisContext,
    DatasetPaths,
    find_repo_root,
    load_context,
)

__all__ = [
    "HTTP_METHODS",
    "AnalysisContext",
    "DatasetPaths",
    "find_repo_root",
    "load_context",
]
