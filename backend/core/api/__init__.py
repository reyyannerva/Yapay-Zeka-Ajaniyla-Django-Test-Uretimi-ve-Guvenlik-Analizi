"""Analiz çalışması ve referans gereksinim API'leri — H4-04 / Issue #36.

AnalysisRun oluşturma/listeleme/detay ve kaynak koddan bağımsız referans gereksinim JSON CRUD
uç noktaları. Sahiplik H4-02 (#34) izin altyapısıyla, referans doğrulaması H4-01 (#33)
serializer'ıyla, analiz ilerlemesi H4-01 `progress.py` ile sağlanır. Bu aşamada gerçek
AST/LLM/Docker işlemi başlatılmaz; yalnızca kayıt oluşturulur.
"""
