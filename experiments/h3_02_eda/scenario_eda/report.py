"""Rapor tablolarının üretimi, dışa aktarımı ve Markdown özeti — H3-02 / Issue #28.

Tüm sayısal ifadeler ``build_report_tables`` çıktısından hesaplanır; özet metinde elle
yazılmış istatistik yoktur. Çıktılar deterministiktir (sabit sıralama, zaman damgası yok),
böylece ``tests/test_reproducibility.py`` depodaki raporların yeniden üretilebildiğini doğrular.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import coverage as cov
from . import quality as q
from .data import HTTP_METHODS, MUTATING_METHODS, AnalysisContext

# Dosya adı → tablo anahtarı (rapor dizinine yazılan CSV'ler)
REPORT_FILES = {
    "general_statistics.csv": "general_statistics",
    "method_distribution.csv": "method_distribution",
    "class_distribution.csv": "class_distribution",
    "category_distribution.csv": "category_distribution",
    "role_distribution.csv": "role_distribution",
    "status_code_distribution.csv": "status_code_distribution",
    "endpoint_distribution.csv": "endpoint_distribution",
    "cross_tabulations.csv": "cross_tabulations",
    "coverage_matrix.csv": "coverage_matrix",
    "authorization_coverage.csv": "authorization_coverage",
    "coverage_gaps.csv": "coverage_gaps",
    "data_quality_findings.csv": "data_quality_findings",
    "data_quality_checks.csv": "data_quality_checks",
    "intentional_flaws.csv": "intentional_flaws",
    "source_comparison.csv": "source_comparison",
}
SUMMARY_FILE = "eda_summary.md"


def build_report_tables(ctx: AnalysisContext) -> dict[str, pd.DataFrame]:
    df, schema = ctx.df, ctx.schema
    findings, inventory = q.run_checks(ctx)
    matrix = cov.coverage_matrix(df)
    label = cov.label_distribution(df).assign(boyut="label")
    expect = cov.expectation_distribution(df).assign(boyut="beklenti sınıfı (türetilmiş)")
    class_dist = pd.concat([label, expect], ignore_index=True)
    class_dist = class_dist[["boyut"] + [c for c in class_dist.columns if c != "boyut"]]
    return {
        "general_statistics": cov.general_statistics(df, schema, ctx.data),
        "method_distribution": cov.method_distribution(df),
        "class_distribution": class_dist,
        "category_distribution": cov.category_distribution(df, schema),
        "role_distribution": cov.role_distribution(df, schema, ctx.users),
        "status_code_distribution": cov.status_distribution(df, schema),
        "endpoint_distribution": cov.endpoint_distribution(df),
        "cross_tabulations": cov.crosstabs_long(cov.standard_crosstabs(df, schema)),
        "coverage_matrix": matrix,
        "authorization_coverage": cov.authorization_coverage(matrix),
        "coverage_gaps": cov.coverage_gaps(df, matrix, schema, ctx.users, ctx.articles, ctx.data),
        "data_quality_findings": findings,
        "data_quality_checks": inventory,
        "intentional_flaws": cov.intentional_flaws(df, ctx.scenarios),
        "source_comparison": cov.source_comparison(df, ctx.pygoat, ctx.data),
    }


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def export_reports(ctx: AnalysisContext, tables: dict[str, pd.DataFrame], out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fname, key in REPORT_FILES.items():
        write_csv(tables[key], out_dir / fname)
        written.append(out_dir / fname)
    (out_dir / SUMMARY_FILE).write_text(render_summary(ctx, tables), encoding="utf-8")
    written.append(out_dir / SUMMARY_FILE)
    return written


# --------------------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------------------
def md_table(df: pd.DataFrame, columns: list[str] | None = None, headers: list[str] | None = None) -> str:
    """Ek bağımlılık (tabulate) gerektirmeyen Markdown tablo üreticisi."""
    cols = columns or list(df.columns)
    head = headers or cols

    def cell(v) -> str:
        if v is None or (not isinstance(v, str) and pd.isna(v)):
            return "—"
        return str(v).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(cell(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def _count(df: pd.DataFrame, col: str, val) -> int:
    return int((df[col] == val).sum()) if len(df) else 0


def render_summary(ctx: AnalysisContext, t: dict[str, pd.DataFrame]) -> str:
    df = ctx.df
    n = len(df)
    pos, neg = _count(df, "label", "positive"), _count(df, "label", "negative")
    flaws = int((df["is_intentional_flaw"] == True).sum())  # noqa: E712
    md = t["method_distribution"]
    present_methods = md[md["senaryo_sayisi"] > 0]["deger"].tolist()
    absent_methods = md[md["senaryo_sayisi"] == 0]["deger"].tolist()
    least = md.sort_values(["senaryo_sayisi", "deger"]).iloc[0]
    most = md.sort_values(["senaryo_sayisi", "deger"], ascending=[False, True]).iloc[0]
    cat = t["category_distribution"]
    low_cats = cat[cat["temsil_durumu"] != "Temsil ediliyor"]
    status = t["status_code_distribution"]
    f = t["data_quality_findings"]
    sev_counts = {s: _count(f, "onem_derecesi", s) for s in q.SEVERITY_ORDER}
    verified_errors = sum(sev_counts[s] for s in ("Kritik", "Yüksek", "Orta", "Düşük"))
    matrix = t["coverage_matrix"]
    cell_counts = {s: _count(matrix, "durum", s) for s in cov.CELL_STATUS_ORDER}
    applicable = len(matrix) - cell_counts[cov.STATUS_NA]
    authz = t["authorization_coverage"]
    gaps = t["coverage_gaps"]
    gap_counts = {g: _count(gaps, "siniflandirma", g) for g in (cov.GAP_CONFIRMED, cov.GAP_POTENTIAL, cov.GAP_METADATA)}
    flaw_t = t["intentional_flaws"]
    src = t["source_comparison"]
    pg_records = int(src.loc[src["kaynak"] == "PyGoat", "senaryo_kaydi"].iloc[0])
    checks = t["data_quality_checks"]
    django_ok = ctx.method_support is not None

    out: list[str] = []
    w = out.append
    w("# H3-02 | EDA ve Veri Kalitesi Analizi — Özet Rapor")
    w("")
    w("> Bu dosya `H3_02_EDA_Veri_Kalitesi.ipynb` tarafından `scenario_eda.report.render_summary` ile "
      "otomatik üretilir. Tüm sayılar kanonik veri kümesinden hesaplanmıştır; elle düzenlemeyin. "
      "İlgili issue: #28 · İsterler: İST-03, İST-13, İST-15, İST-16.")
    w("")
    w("## 1. Veri kümesine genel bakış")
    w("")
    w(f"- Kanonik kaynak: `benchmarks/drf_fixtures/scenarios/scenarios.json` — `{ctx.data.get('dataset')}` "
      f"v{ctx.data.get('version')} (hedef: `{ctx.data.get('target_app')}`).")
    w("- Türetilmiş kopya: `scenarios.csv` (yalnızca tutarlılık kontrolü için okunur); şema: `scenarios.schema.json`.")
    w(f"- Toplam **{n}** senaryo; **{pos}** pozitif (%{cov._pct(pos, n)}), **{neg}** negatif (%{cov._pct(neg, n)}); "
      f"**{flaws}** bilerek-hatalı senaryo (negatiflerin alt kümesi).")
    w(f"- Kaynak: tüm kayıtlar kontrollü Django/DRF fixture kaynağına aittir; depoda PyGoat senaryo kaydı "
      f"sayısı **{pg_records}**.")
    w("")
    w("## 2. Yöntem")
    w("")
    w("1. **Yapısal doğrulama:** kanonik JSON Schema (Draft 2020-12) ile; H3-01 `validate_scenarios.py` "
      "ayrıca çalıştırılıp sonucu notebook'ta karşılaştırılır.")
    w("2. **Semantik doğrulama:** şemadan okunan zorunlu alan/enum tanımlarıyla alan düzeyi kontroller, "
      "yinelenen kimlik/içerik ve etiket–durum kodu tutarlılığı.")
    w("3. **Referans bütünlüğü (statik):** `fixture_ref` değerleri `users.json`/`articles.json` ile; endpoint'ler "
      "`config/urls.py` + `catalog/urls.py` metninden çıkarılan rota desenleriyle eşlenir. Rol semantiği "
      "kullanıcı adından değil fixture verisinden (`is_staff`, `owner`) doğrulanır.")
    w(f"4. **Django URL çözümlemesi:** {ctx.method_support_note} Davranışsal (çalışma zamanı) doğrulama "
      "bu analizin kapsamında değildir; H3-01'in `pytest` senaryo↔uygulama testleriyle yapılır.")
    w("5. **Durum kodu incelemesi:** hedef uygulamanın yapılandırmasına dayanan sezgisel kurallar; çıktılar "
      "kesin hata değil, inceleme önerisidir. Evrensel HTTP varsayımı (ör. her DELETE → 204) kullanılmaz.")
    w("6. **Kapsam modeli:** alan modeline göre açıkça listelenen (endpoint türü × metot × koşul) hücreleri; "
      f"öncelikler ve %{cov.UNDERREPRESENTED_SHARE * 100:.0f} düşük temsil eşiği proje-özgü, yapılandırılabilir "
      "sezgisel değerlerdir.")
    w("")
    w("Çalıştırılan kontroller:")
    w("")
    w(md_table(checks, ["kontrol_katmani", "kontrol", "durum", "incelenen_kayit", "bulgu_sayisi"],
               ["Katman", "Kontrol", "Durum", "İncelenen kayıt", "Bulgu"]))
    w("")
    w("## 3. Tanımlayıcı istatistikler")
    w("")
    w(md_table(t["general_statistics"], ["metrik", "deger"], ["Metrik", "Değer"]))
    w("")
    w("**HTTP metodu dağılımı** (beş metodun tamamı raporlanır):")
    w("")
    w(md_table(md, ["deger", "senaryo_sayisi", "yuzde", "pozitif", "negatif", "bilerek_guvensiz", "temsil_durumu"],
               ["Metot", "Senaryo", "%", "Pozitif", "Negatif", "Bilerek güvensiz", "Temsil"]))
    w("")
    w("**Kategori dağılımı:**")
    w("")
    w(md_table(cat, ["gorunen_ad", "deger", "senaryo_sayisi", "yuzde", "pozitif", "negatif", "bilerek_guvensiz",
                     "temsil_durumu"],
               ["Kategori", "Kod", "Senaryo", "%", "Pozitif", "Negatif", "Bilerek güvensiz", "Temsil"]))
    w("")
    w("**Beklenen HTTP durum kodu dağılımı:**")
    w("")
    w(md_table(status, ["deger", "senaryo_sayisi", "yuzde", "beklenen_basari", "beklenen_ret", "bilerek_guvensiz"],
               ["Kod", "Senaryo", "%", "Beklenen başarı", "Beklenen ret", "Bilerek güvensiz"]))
    w("")
    w("**Rol dağılımı** (etiket, fixture kimliği ve fixture'dan türetilen aktör ilişkisi ayrı boyutlardır):")
    w("")
    w(md_table(t["role_distribution"], ["boyut", "gorunen_ad", "senaryo_sayisi", "yuzde", "pozitif", "negatif"],
               ["Boyut", "Değer", "Senaryo", "%", "Pozitif", "Negatif"]))
    w("")
    w("## 4. Kapsam bulguları")
    w("")
    w(f"- Temsil edilen metotlar: {', '.join(present_methods)}"
      + (f"; **temsil edilmeyen: {', '.join(absent_methods)}**." if absent_methods else "; eksik metot yok."))
    w(f"- En çok temsil edilen metot {most['deger']} ({most['senaryo_sayisi']} senaryo), en az temsil edilen "
      f"{least['deger']} ({least['senaryo_sayisi']} senaryo, %{least['yuzde']}).")
    if len(low_cats):
        w("- Düşük temsil edilen kategoriler (yapılandırılabilir eşik): " + ", ".join(
            f"{r.gorunen_ad} ({r.senaryo_sayisi} senaryo, %{r.yuzde})" for r in low_cats.itertuples()) + ".")
    w(f"- Kapsam modeli: {len(matrix)} hücre ({applicable} uygulanabilir); "
      + ", ".join(f"{k}: {v}" for k, v in cell_counts.items()) + ".")
    w(f"- Kapsam boşlukları: {len(gaps)} kayıt — " + ", ".join(f"{k}: {v}" for k, v in gap_counts.items()) + ".")
    w("")
    w(md_table(gaps, ["bosluk_no", "siniflandirma", "oncelik", "kapsam_boyutu", "endpoint_turu", "http_metodu",
                      "kosul", "kanit"],
               ["No", "Sınıf", "Öncelik", "Boyut", "Endpoint türü", "Metot", "Koşul", "Kanıt"]))
    w("")
    w("## 5. Veri kalitesi bulguları")
    w("")
    w("Önem derecesine göre bulgu sayısı: " + ", ".join(f"{k}: {v}" for k, v in sev_counts.items()) + ".")
    w("")
    if verified_errors == 0:
        w(f"**Doğrulanmış veri hatası (Kritik/Yüksek/Orta/Düşük): 0.** JSON Schema, eksik/null alan, yinelenen "
          "kimlik, geçersiz metot/kategori/rol/durum kodu, etiket tutarlılığı, fixture/endpoint referansları"
          + (", view metot desteği" if django_ok else "") + " ve JSON↔CSV tutarlılığı kontrollerinde hata "
          "bulunmadı. Bu sonuç kapsamın eksiksiz olduğu anlamına gelmez (bkz. bölüm 4).")
    else:
        w(f"**Doğrulanmış veri hatası (Kritik/Yüksek/Orta/Düşük): {verified_errors}.** Ayrıntılar aşağıdadır.")
    w("")
    if len(f):
        w(md_table(f, ["bulgu_no", "senaryo_id", "alan", "sorun_turu", "onem_derecesi", "kanit", "onerilen_duzeltme"],
                   ["No", "Senaryo", "Alan", "Sorun türü", "Önem", "Kanıt", "Önerilen düzeltme"]))
    else:
        w("_Bulgu tablosu boş (başlıklarla birlikte `data_quality_findings.csv` olarak dışa aktarıldı)._")
    w("")
    w("## 6. Yetkilendirme değerlendirmesi (PUT / PATCH / DELETE)")
    w("")
    w(md_table(authz, ["endpoint_turu_ad", "http_metodu", "kosul_ad", "durum", "senaryo_idleri",
                       "beklenen_durum_kodlari"],
               ["Endpoint türü", "Metot", "Koşul", "Durum", "Senaryolar", "Beklenen kod"]))
    w("")
    sec = authz[(authz["endpoint_turu"] == "guvenli_nesne") & (authz["uygulanabilir"] == "Evet")]
    w(f"- Güvenli nesne ucunda {len(sec)} uygulanabilir hücrenin {_count(sec, 'durum', cov.STATUS_PRESENT)} tanesi "
      f"açıkça, {_count(sec, 'durum', cov.STATUS_INDIRECT)} tanesi dolaylı temsil ediliyor; "
      f"{_count(sec, 'durum', cov.STATUS_MISSING)} tanesi kapsanmıyor.")
    w("- Eksik hücreler kapsam boşluğudur; doğrulanmış bir güvenlik açığı olarak yorumlanmamalıdır.")
    w("")
    w("**Bilerek-hatalı senaryolar** (veri hatası değil; değerlendirme için kasıtlı):")
    w("")
    w(md_table(flaw_t, ["senaryo_id", "http_metodu", "endpoint", "view", "gozlemlenen_durum_kodu",
                        "guvenli_karsilik_idleri", "guvenli_karsilik_durum_kodlari", "aciklama_karsilik_uyumu"],
               ["Senaryo", "Metot", "Endpoint", "View", "Gözlemlenen", "Güvenli karşılık", "Karşılık kodu",
                "Açıklama uyumu"]))
    w("")
    w("## 7. PyGoat ve kontrollü fixture kaynak ayrımı")
    w("")
    w(md_table(src, ["kaynak", "depo_konumu", "senaryo_kaydi", "http_metodu", "kategori", "pozitif", "negatif",
                     "bilerek_hatali", "degerlendirme_hazirligi"],
               ["Kaynak", "Konum", "Kayıt", "Metot", "Kategori", "Pozitif", "Negatif", "Bilerek hatalı",
                "Değerlendirme hazırlığı"]))
    w("")
    if pg_records == 0:
        w("PyGoat için depoda etiketli senaryo kaydı bulunmadığından **nicel kaynak karşılaştırması yapılamaz**; "
          "kaynak karşılaştırma grafiği bu nedenle üretilmedi. Bu durum kontrollü fixture veri kümesinin bir "
          "kusuru değildir: H3-01 kapsamı PyGoat'ı ayrı bir değerlendirme hedefi olarak belgelemekle sınırlıdır.")
    w("")
    w("## 8. Öneriler (öncelik sırasıyla)")
    w("")
    recs = gaps[gaps["siniflandirma"] != cov.GAP_METADATA]
    for k, r in enumerate(recs.itertuples(), 1):
        w(f"{k}. [{r.oncelik}] ({r.bosluk_no}) {r.oneri}")
    k = len(recs)
    for r in f[f["sorun_turu"] == "ROL_DOGRULANAMIYOR"].groupby("sorun_turu"):
        ids = ", ".join(r[1]["senaryo_id"].dropna())
        k += 1
        w(f"{k}. [Düşük] `owner` rolünün nesnesiz veya mevcut olmayan kaynak içeren senaryolardaki anlamını "
          f"belgeleyin ({ids}).")
    for r in gaps[gaps["siniflandirma"] == cov.GAP_METADATA].itertuples():
        k += 1
        w(f"{k}. [{r.oncelik}] ({r.bosluk_no}) {r.oneri}")
    w("")
    w("Önerilen tüm yeni senaryoların beklenen durum kodları, eklenmeden önce H3-01 senaryo↔uygulama testi "
      "(`pytest`) ile hedef uygulamaya karşı doğrulanmalıdır. Bu analiz kaynak veri kümesini değiştirmez.")
    w("")
    w("## 9. Sınırlılıklar")
    w("")
    w("- Referans ve rota kontrolleri statiktir; Django URL çözümlemesi HTTP isteği çalıştırmaz. Beklenen "
      "durum kodlarının gerçek davranışla eşleşmesi H3-01 `pytest` paketinin kapsamındadır.")
    w("- Kimlik doğrulama durumu ve sahiplik açık alanlar değildir; fixture verisinden türetilmiştir.")
    w("- Kapsam modeli, öncelikler ve düşük temsil eşiği proje-özgü sezgisel tercihlerdir.")
    w("- Veri kümesi küçük (" + str(n) + " kayıt) ve tek kaynaklıdır; oranlar istatistiksel genelleme için "
      "kullanılmamalıdır.")
    w("- PyGoat senaryo kaydı olmadığından kaynaklar arası nicel karşılaştırma yapılamamıştır.")
    w("")
    w("## 10. Yeniden üretim")
    w("")
    w("```bash")
    w("pip install -r experiments/h3_02_eda/requirements.txt")
    w("jupyter nbconvert --to notebook --execute --inplace \\")
    w("  experiments/h3_02_eda/H3_02_EDA_Veri_Kalitesi.ipynb")
    w("python -m pytest experiments/h3_02_eda/tests -q")
    w("```")
    w("")
    w("Google Colab adımları için `experiments/h3_02_eda/README.md` dosyasına bakın.")
    w("")
    return "\n".join(out)


def quick_facts(tables: dict[str, pd.DataFrame]) -> dict:
    """Notebook'un sonuç bölümünde kullanılan sayısal özet (yalnızca tablolardan)."""
    md = tables["method_distribution"]
    f = tables["data_quality_findings"]
    return {
        "metot_sayilari": dict(zip(md["deger"], md["senaryo_sayisi"])),
        "eksik_metotlar": md[md["senaryo_sayisi"] == 0]["deger"].tolist(),
        "bulgu_sayisi": len(f),
        "dogrulanmis_hata": int(f["onem_derecesi"].isin(["Kritik", "Yüksek", "Orta", "Düşük"]).sum()) if len(f) else 0,
        "bosluk_sayisi": len(tables["coverage_gaps"]),
        "mutasyon_metotlari": list(MUTATING_METHODS),
        "tum_metotlar": list(HTTP_METHODS),
    }
