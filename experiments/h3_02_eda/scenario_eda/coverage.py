"""Dağılım, çapraz tablo ve kapsam analizi — H3-02 / Issue #28.

Kapsam modeli (``COVERAGE_MODEL``) körlemesine bir Kartezyen çarpım DEĞİLDİR: hedef
uygulamanın gerçek alan modeline (urls.py rotaları, views.py/permissions.py/insecure.py
kuralları) göre anlamlı (endpoint türü, HTTP metodu, koşul) hücreleri açıkça listeler.
Öncelikler ve "düşük temsil" eşiği proje-özgü, YAPILANDIRILABİLİR sezgisel değerlerdir;
evrensel bir kapsam standardı iddia edilmez.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .data import (
    ENDPOINT_KIND_LABELS,
    EXPECTATION_FLAW,
    EXPECTATION_ORDER,
    EXPECTATION_REJECTION,
    EXPECTATION_SUCCESS,
    HTTP_METHODS,
    MUTATING_METHODS,
)

CATEGORY_LABELS = {
    "AUTHENTICATION": "Kimlik doğrulama",
    "AUTHORIZATION": "Yetkilendirme",
    "INPUT_VALIDATION": "Girdi doğrulama",
    "HTTP_BEHAVIOR": "HTTP davranışı",
    "SECURITY_CONFIGURATION": "Güvenlik yapılandırması",
}
ROLE_LABELS = {
    "anonymous": "Anonim (anonymous)",
    "user": "Kullanıcı (user)",
    "owner": "Kaynak sahibi (owner)",
    "admin": "Yönetici (admin)",
}
RELATION_LABELS = {
    "anonim": "Anonim",
    "kimligi_dogrulanmis": "Kimliği doğrulanmış (nesnesiz)",
    "kaynak_sahibi": "Kaynak sahibi",
    "sahip_olmayan": "Sahip olmayan kullanıcı",
    "yonetici": "Yönetici",
    "belirlenemez": "Belirlenemez",
}
CONDITION_LABELS = {
    **RELATION_LABELS,
    "kaynak_yok": "Mevcut olmayan kaynak",
    "gecersiz_girdi": "Geçersiz girdi",
    "metot_desteklenmiyor": "Desteklenmeyen metot",
}
CONDITION_ORDER = ["anonim", "kimligi_dogrulanmis", "kaynak_sahibi", "sahip_olmayan", "yonetici",
                   "kaynak_yok", "gecersiz_girdi", "metot_desteklenmiyor", "belirlenemez"]
KIND_ORDER = ["guvenli_koleksiyon", "guvenli_nesne", "guvenli_nesne_aksiyonu",
              "guvensiz_koleksiyon", "guvensiz_nesne", "cozumlenemedi"]

# Proje-özgü sezgisel eşik: bir değerin payı bunun altındaysa "düşük temsil" olarak işaretlenir.
UNDERREPRESENTED_SHARE = 0.10

STATUS_PRESENT = "Açıkça mevcut"
STATUS_INDIRECT = "Dolaylı temsil"
STATUS_MISSING = "Kapsanmıyor"
STATUS_NA = "Uygulanamaz"
CELL_STATUS_ORDER = [STATUS_PRESENT, STATUS_INDIRECT, STATUS_MISSING, STATUS_NA]

GAP_CONFIRMED = "Doğrulanmış eksik"
GAP_POTENTIAL = "Olası eksik"
GAP_METADATA = "Yetersiz meta veri"
PRIORITY_ORDER = ["Yüksek", "Orta", "Düşük"]


# --------------------------------------------------------------------------------------
# Dağılımlar
# --------------------------------------------------------------------------------------
def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


def distribution(df: pd.DataFrame, col: str, order: list | None = None,
                 labels: dict | None = None, min_share: float = UNDERREPRESENTED_SHARE) -> pd.DataFrame:
    """Değer sayısı, yüzde ve beklenti sınıfı kırılımı; ``order`` içindeki sıfır değerler dâhil."""
    total = len(df)
    values = list(order) if order is not None else []
    extra = [v for v in df[col].dropna().unique().tolist() if v not in values] if total else []
    values += sorted(extra, key=str)
    rows = []
    for v in values:
        sub = df[df[col] == v] if total else df
        n = len(sub)
        rows.append({
            "deger": v,
            "gorunen_ad": (labels or {}).get(v, str(v)),
            "senaryo_sayisi": n,
            "yuzde": _pct(n, total),
            "pozitif": int((sub["label"] == "positive").sum()) if n else 0,
            "negatif": int((sub["label"] == "negative").sum()) if n else 0,
            "beklenen_basari": int((sub["expectation_class"] == EXPECTATION_SUCCESS).sum()) if n else 0,
            "beklenen_ret": int((sub["expectation_class"] == EXPECTATION_REJECTION).sum()) if n else 0,
            "bilerek_guvensiz": int((sub["expectation_class"] == EXPECTATION_FLAW).sum()) if n else 0,
            "temsil_durumu": ("Temsil edilmiyor" if n == 0 else
                              ("Düşük temsil (eşik %{:.0f})".format(min_share * 100)
                               if total and n / total < min_share else "Temsil ediliyor")),
        })
    return pd.DataFrame(rows)


def schema_enum(schema: dict, field: str) -> list:
    return list(schema["$defs"]["scenario"]["properties"][field]["enum"])


def method_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Beş HTTP metodunun tamamı (sıfır kayıtlı olsa bile) raporlanır."""
    return distribution(df, "http_method", list(HTTP_METHODS))


def category_distribution(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    return distribution(df, "category", schema_enum(schema, "category"), CATEGORY_LABELS)


def status_distribution(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    return distribution(df, "expected_http_status", schema_enum(schema, "expected_http_status"))


def role_distribution(df: pd.DataFrame, schema: dict, users: list[dict]) -> pd.DataFrame:
    """Üç ayrı boyut: veri kümesi rol etiketi, fixture kimliği, fixture'dan türetilen aktör ilişkisi."""
    usernames = [u["fields"]["username"] for u in users]
    tmp = df.assign(fixture_identity=df["fixture_user"].fillna("(kimlik yok / anonim)"))
    parts = [
        distribution(df, "user_role", schema_enum(schema, "user_role"), ROLE_LABELS).assign(boyut="user_role (etiket)"),
        distribution(tmp, "fixture_identity", usernames + ["(kimlik yok / anonim)"]).assign(boyut="fixture kimliği"),
        distribution(df, "actor_relation", [k for k in RELATION_LABELS], RELATION_LABELS)
        .assign(boyut="aktör–kaynak ilişkisi (fixture'dan türetilmiş)"),
    ]
    out = pd.concat(parts, ignore_index=True)
    return out[["boyut"] + [c for c in out.columns if c != "boyut"]]


def expectation_distribution(df: pd.DataFrame) -> pd.DataFrame:
    return distribution(df, "expectation_class", list(EXPECTATION_ORDER))


def label_distribution(df: pd.DataFrame) -> pd.DataFrame:
    return distribution(df, "label", ["positive", "negative"], {"positive": "Pozitif", "negative": "Negatif"})


def crosstab(df: pd.DataFrame, row: str, col: str, row_order: list | None = None,
             col_order: list | None = None) -> pd.DataFrame:
    """Sıfır hücreleri koruyan çapraz tablo."""
    ct = pd.crosstab(df[row], df[col]) if len(df) else pd.DataFrame()
    rows = list(row_order) if row_order is not None else sorted(ct.index.tolist(), key=str)
    cols = list(col_order) if col_order is not None else sorted(ct.columns.tolist(), key=str)
    rows += [r for r in ct.index if r not in rows]
    cols += [c for c in ct.columns if c not in cols]
    return ct.reindex(index=rows, columns=cols, fill_value=0).astype(int)


def standard_crosstabs(df: pd.DataFrame, schema: dict) -> dict[str, pd.DataFrame]:
    m = list(HTTP_METHODS)
    cats = schema_enum(schema, "category")
    roles = schema_enum(schema, "user_role")
    codes = schema_enum(schema, "expected_http_status")
    return {
        "metot_x_kategori": crosstab(df, "http_method", "category", m, cats),
        "metot_x_rol": crosstab(df, "http_method", "user_role", m, roles),
        "metot_x_aktor_iliskisi": crosstab(df, "http_method", "actor_relation", m,
                                           [c for c in RELATION_LABELS]),
        "metot_x_durum_kodu": crosstab(df, "http_method", "expected_http_status", m, codes),
        "metot_x_beklenti_sinifi": crosstab(df, "http_method", "expectation_class", m, list(EXPECTATION_ORDER)),
        "metot_x_endpoint_turu": crosstab(df, "http_method", "endpoint_kind", m, KIND_ORDER[:-1]),
        "kategori_x_beklenti_sinifi": crosstab(df, "category", "expectation_class", cats, list(EXPECTATION_ORDER)),
        "durum_kodu_x_rol": crosstab(df, "expected_http_status", "user_role", codes, roles),
        "durum_kodu_x_kategori": crosstab(df, "expected_http_status", "category", codes, cats),
        "durum_kodu_x_aktor_iliskisi": crosstab(df, "expected_http_status", "actor_relation", codes,
                                                [c for c in RELATION_LABELS]),
    }


def crosstabs_long(tabs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, ct in tabs.items():
        for r in ct.index:
            for c in ct.columns:
                rows.append({"tablo": name, "satir": r, "sutun": c, "senaryo_sayisi": int(ct.loc[r, c])})
    return pd.DataFrame(rows, columns=["tablo", "satir", "sutun", "senaryo_sayisi"])


def endpoint_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Endpoint deseni (rota) düzeyinde senaryo sayıları ve kullanılan metotlar."""
    rows = []
    for (kind, pattern), sub in df.groupby(["endpoint_kind", "endpoint_pattern"], dropna=False, sort=False):
        rows.append({
            "endpoint_turu": kind,
            "endpoint_turu_ad": ENDPOINT_KIND_LABELS.get(kind, kind),
            "endpoint_deseni": pattern,
            "view": sub["view"].dropna().iloc[0] if sub["view"].notna().any() else None,
            "view_turu": sub["view_type"].dropna().iloc[0] if sub["view_type"].notna().any() else None,
            "senaryo_sayisi": len(sub),
            "yuzde": _pct(len(sub), len(df)),
            "metotlar": ";".join(m for m in HTTP_METHODS if m in set(sub["http_method"])),
            "somut_endpointler": ";".join(sorted(sub["endpoint"].dropna().unique())),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_k"] = out["endpoint_turu"].map({k: i for i, k in enumerate(KIND_ORDER)}).fillna(99)
    return out.sort_values(["_k", "endpoint_deseni"]).drop(columns="_k").reset_index(drop=True)


def general_statistics(df: pd.DataFrame, schema: dict, data: dict) -> pd.DataFrame:
    n = len(df)
    ids = df["id"].dropna()
    dup_ids = int((ids.value_counts() > 1).sum())
    pos = int((df["label"] == "positive").sum())
    neg = int((df["label"] == "negative").sum())
    flaws = int((df["is_intentional_flaw"] == True).sum())  # noqa: E712
    minority = min(pos, neg)
    rows = [
        ("Veri kümesi", f"{data.get('dataset')} v{data.get('version')}"),
        ("Toplam senaryo", n),
        ("Benzersiz senaryo kimliği", int(ids.nunique())),
        ("Yinelenen kimlik (birden fazla kullanılan kimlik sayısı)", dup_ids),
        ("Pozitif senaryo", f"{pos} (%{_pct(pos, n)})"),
        ("Negatif senaryo", f"{neg} (%{_pct(neg, n)})"),
        ("Negatif/pozitif oranı", round(neg / pos, 2) if pos else "tanımsız"),
        ("Azınlık sınıf payı", f"%{_pct(minority, n)}"),
        ("Bilerek-hatalı (is_intentional_flaw) senaryo", flaws),
        ("Temsil edilen kategori / şemada tanımlı", f"{df['category'].nunique()} / {len(schema_enum(schema, 'category'))}"),
        ("Temsil edilen HTTP metodu / kapsam (GET, POST, PUT, PATCH, DELETE)",
         f"{df.loc[df['http_method'].isin(HTTP_METHODS), 'http_method'].nunique()} / {len(HTTP_METHODS)}"),
        ("Temsil edilen user_role / şemada tanımlı", f"{df['user_role'].nunique()} / {len(schema_enum(schema, 'user_role'))}"),
        ("Farklı fixture kimliği (istek yapan)", int(df["fixture_user"].dropna().nunique())),
        ("Temsil edilen durum kodu / şemada tanımlı",
         f"{df['expected_http_status'].nunique()} / {len(schema_enum(schema, 'expected_http_status'))}"),
        ("Farklı endpoint türü", int(df["endpoint_kind"].nunique())),
        ("Farklı endpoint deseni (rota)", int(df["endpoint_pattern"].dropna().nunique())),
        ("Farklı somut endpoint", int(df["endpoint"].nunique())),
    ]
    return pd.DataFrame(rows, columns=["metrik", "deger"]).astype({"deger": str})


# --------------------------------------------------------------------------------------
# Kapsam modeli
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Cell:
    kind: str
    method: str
    condition: str
    priority: str          # "Yüksek" | "Orta" | "Düşük" | "-" (uygulanamaz)
    applicable: bool
    rationale: str


def _cells(kind, methods, conditions, priority, rationale, applicable=True):
    return [Cell(kind, m, c, priority if applicable else "-", applicable, rationale)
            for m in methods for c in conditions]


COVERAGE_MODEL: list[Cell] = [
    # Güvenli koleksiyon: /api/articles/  (ArticleViewSet list/create)
    *_cells("guvenli_koleksiyon", ["GET"], ["anonim", "kimligi_dogrulanmis", "yonetici"], "Orta",
            "Liste görünürlüğü get_queryset'e göre role bağlıdır (views.py)."),
    *_cells("guvenli_koleksiyon", ["POST"], ["anonim"], "Yüksek",
            "Kimlik doğrulamasız oluşturma reddedilmeli (permissions.has_permission)."),
    *_cells("guvenli_koleksiyon", ["POST"], ["kimligi_dogrulanmis", "gecersiz_girdi"], "Yüksek",
            "Geçerli oluşturma ve serializer girdi doğrulaması (serializers.py)."),
    *_cells("guvenli_koleksiyon", ["POST"], ["yonetici"], "Düşük",
            "Yönetici oluşturma davranışı kimliği doğrulanmış kullanıcıyla aynı kural yolundadır."),
    *_cells("guvenli_koleksiyon", ["PUT", "PATCH", "DELETE"], ["metot_desteklenmiyor"], "Düşük",
            "Koleksiyon rotasında desteklenmeyen metot (router list rotası yalnızca GET/POST)."),
    *_cells("guvenli_koleksiyon", ["GET"], ["gecersiz_girdi"], "-",
            "GET isteği gövde doğrulaması içermez.", applicable=False),
    # Güvenli nesne: /api/articles/<pk>/  (ArticleViewSet retrieve/update/partial_update/destroy)
    *_cells("guvenli_nesne", ["GET"], ["anonim", "kaynak_sahibi", "sahip_olmayan", "yonetici", "kaynak_yok"],
            "Orta", "Nesne görünürlüğü (yayında/taslak) ve mevcut olmayan kaynak."),
    *_cells("guvenli_nesne", ["PUT", "PATCH"],
            ["anonim", "kaynak_sahibi", "sahip_olmayan", "yonetici", "kaynak_yok", "gecersiz_girdi"], "Yüksek",
            "Güncelleme: kimlik doğrulama (401), nesne düzeyi sahiplik (403), yönetici, 404 ve girdi doğrulama."),
    *_cells("guvenli_nesne", ["DELETE"], ["anonim", "kaynak_sahibi", "sahip_olmayan", "yonetici", "kaynak_yok"],
            "Yüksek", "Silme: kimlik doğrulama, nesne düzeyi sahiplik, yönetici ve 404."),
    *_cells("guvenli_nesne", ["DELETE"], ["gecersiz_girdi"], "-",
            "DELETE isteğinde serializer girdi doğrulaması çalışmaz.", applicable=False),
    *_cells("guvenli_nesne", ["GET"], ["gecersiz_girdi"], "-",
            "GET isteği gövde doğrulaması içermez.", applicable=False),
    *_cells("guvenli_nesne", ["POST"], ["metot_desteklenmiyor"], "Düşük",
            "Detay rotasında POST desteklenmez (router detail rotası)."),
    # Güvenli nesne aksiyonu: /api/articles/<pk>/publish/  (ArticlePublishView, APIView)
    *_cells("guvenli_nesne_aksiyonu", ["POST"], ["anonim", "kaynak_sahibi", "sahip_olmayan", "yonetici"], "Orta",
            "Yayınlama: IsAuthenticated + sahip/yönetici kontrolü (views.ArticlePublishView)."),
    *_cells("guvenli_nesne_aksiyonu", ["POST"], ["kaynak_yok"], "Düşük",
            "get_object_or_404 ile mevcut olmayan kaynak."),
    *_cells("guvenli_nesne_aksiyonu", ["GET"], ["metot_desteklenmiyor"], "Düşük",
            "APIView yalnızca post() tanımlar."),
    *_cells("guvenli_nesne_aksiyonu", ["POST"], ["gecersiz_girdi"], "-",
            "publish ucu istek gövdesi okumaz.", applicable=False),
    # Bilerek güvensiz uçlar (insecure.py)
    *_cells("guvensiz_koleksiyon", ["GET"], ["anonim"], "Orta",
            "InsecureArticleList: AllowAny + filtrelenmemiş queryset → taslak ifşası."),
    *_cells("guvensiz_nesne", ["GET"], ["sahip_olmayan"], "Orta",
            "InsecureArticleDetail queryset'i filtrelenmez → başkasının taslağı okunabilir (kaynak kodu)."),
    *_cells("guvensiz_nesne", ["PUT", "PATCH", "DELETE"], ["sahip_olmayan"], "Yüksek",
            "BOLA/IDOR: nesne düzeyi sahiplik kontrolü yok (insecure.py)."),
    *_cells("guvensiz_nesne", ["PUT", "PATCH", "DELETE"], ["anonim"], "Düşük",
            "Güvensiz uçta da IsAuthenticated kontrolünün çalıştığını doğrulayan kontrol senaryosu."),
]


def coverage_matrix(df: pd.DataFrame, model: list[Cell] = COVERAGE_MODEL) -> pd.DataFrame:
    """Kapsam modelindeki her hücre için durum ve kanıt (senaryo kimlikleri)."""
    rows = []
    present: dict[tuple, pd.DataFrame] = {}
    for cell in model:
        sub = df[(df["endpoint_kind"] == cell.kind) & (df["http_method"] == cell.method)
                 & (df["condition"] == cell.condition)]
        present[(cell.kind, cell.method, cell.condition)] = sub
    for cell in model:
        sub = present[(cell.kind, cell.method, cell.condition)]
        indirect = ""
        if not cell.applicable:
            status = STATUS_NA
        elif len(sub):
            status = STATUS_PRESENT
        else:
            status = STATUS_MISSING
            sibling = {"PUT": "PATCH", "PATCH": "PUT"}.get(cell.method)
            # 405 hücreleri router eşlemesine bağlıdır; ortak update yolu gerekçesi geçerli değildir.
            if sibling and cell.condition != "metot_desteklenmiyor":
                sib = present.get((cell.kind, sibling, cell.condition))
                if sib is not None and len(sib):
                    status = STATUS_INDIRECT
                    indirect = (f"{sibling} için {', '.join(sib['id'])} mevcut; DRF'te PUT ve PATCH aynı "
                                "UpdateModelMixin.update yolunu (partial bayrağıyla) kullanır. "
                                "Açık senaryo hâlâ önerilir.")
        rows.append({
            "endpoint_turu": cell.kind,
            "endpoint_turu_ad": ENDPOINT_KIND_LABELS.get(cell.kind, cell.kind),
            "http_metodu": cell.method,
            "kosul": cell.condition,
            "kosul_ad": CONDITION_LABELS.get(cell.condition, cell.condition),
            "uygulanabilir": "Evet" if cell.applicable else "Hayır",
            "oncelik": cell.priority,
            "gerekce": cell.rationale,
            "durum": status,
            "senaryo_sayisi": len(sub),
            "senaryo_idleri": ";".join(sub["id"]),
            "beklenen_durum_kodlari": ";".join(str(x) for x in sorted(sub["expected_http_status"].unique())),
            "kaynak_gorunurlugu": ";".join(sorted(sub["resource_state"].unique())),
            "dolayli_kanit": indirect,
        })
    return pd.DataFrame(rows)


def unmodelled_scenarios(df: pd.DataFrame, model: list[Cell] = COVERAGE_MODEL) -> pd.DataFrame:
    keys = {(c.kind, c.method, c.condition) for c in model}
    mask = [(k, m, c) not in keys for k, m, c in zip(df["endpoint_kind"], df["http_method"], df["condition"])]
    return df.loc[mask, ["id", "endpoint_kind", "http_method", "condition", "expected_http_status"]]


def authorization_coverage(matrix: pd.DataFrame) -> pd.DataFrame:
    """PUT/PATCH/DELETE için nesne uçlarındaki (güvenli + bilerek güvensiz) yetkilendirme matrisi."""
    sub = matrix[matrix["http_metodu"].isin(MUTATING_METHODS)
                 & matrix["endpoint_turu"].isin(["guvenli_nesne", "guvensiz_nesne"])].copy()
    sub["_m"] = sub["http_metodu"].map({m: i for i, m in enumerate(HTTP_METHODS)})
    sub["_k"] = sub["endpoint_turu"].map({k: i for i, k in enumerate(KIND_ORDER)})
    sub["_c"] = sub["kosul"].map({c: i for i, c in enumerate(CONDITION_ORDER)})
    return sub.sort_values(["_k", "_m", "_c"]).drop(columns=["_m", "_k", "_c"]).reset_index(drop=True)


# --------------------------------------------------------------------------------------
# Kapsam boşlukları
# --------------------------------------------------------------------------------------
_RECOMMEND = {
    ("guvenli_nesne", "kaynak_yok"): "Mevcut olmayan kaynak (ör. /api/articles/999/) için {m} senaryosu ekleyin; beklenen durum kodu H3-01 senaryo↔uygulama testiyle doğrulanmalıdır.",
    ("guvenli_nesne", "gecersiz_girdi"): "Kaynak sahibi tarafından geçersiz girdiyle {m} senaryosu ekleyin (ör. boş başlık); kısmi doğrulama (partial=True) davranışı ayrıca belgelenmeli.",
    ("guvensiz_nesne", "sahip_olmayan"): "Bilerek güvensiz uçta sahip olmayan kullanıcı ile {m} (BOLA/IDOR) senaryosu ekleyin ve güvenli uçtaki karşılığıyla eşleyin.",
    ("guvensiz_nesne", "sahip_olmayan", "GET"): "Bilerek güvensiz detay ucunda sahip olmayan kullanıcının başkasının taslak kaydını okuduğu (hassas veri ifşası) bir GET senaryosu ekleyin ve güvenli detay ucundaki sahip-olmayan taslak erişimi (404) senaryosuyla eşleyin.",
    ("guvensiz_nesne", "anonim"): "Güvensiz uçta anonim {m} kontrol senaryosu ekleyin (IsAuthenticated nedeniyle 401 beklenir; doğrulanmalıdır).",
}


def coverage_gaps(df: pd.DataFrame, matrix: pd.DataFrame, schema: dict, users: list[dict],
                  articles: list[dict], data: dict) -> pd.DataFrame:
    """Veri kümesi düzeyindeki kapsam boşlukları (kayıt düzeyi kalite bulgularından ayrı)."""
    gaps: list[dict] = []

    def add(cls, prio, dim, kind, method, cond, expl, evidence, rec):
        gaps.append({"siniflandirma": cls, "oncelik": prio, "kapsam_boyutu": dim,
                     "endpoint_turu": kind, "http_metodu": method, "kosul": cond,
                     "aciklama": expl, "kanit": evidence, "oneri": rec})

    # 1) Kapsam modeli hücreleri
    for _, r in matrix.iterrows():
        if r["durum"] not in (STATUS_MISSING, STATUS_INDIRECT):
            continue
        cls = GAP_CONFIRMED if (r["durum"] == STATUS_MISSING and r["oncelik"] == "Yüksek") else GAP_POTENTIAL
        rec = _RECOMMEND.get((r["endpoint_turu"], r["kosul"], r["http_metodu"]),
                             _RECOMMEND.get((r["endpoint_turu"], r["kosul"]),
                                            r["endpoint_turu_ad"] + " ucunda {m} için '" + r["kosul_ad"]
                                            + "' koşulunu temsil eden bir senaryo eklemeyi değerlendirin."))
        evidence = r["dolayli_kanit"] or "Veri kümesinde bu (endpoint türü, metot, koşul) hücresine eşlenen kayıt yok."
        add(cls, r["oncelik"], "endpoint türü × metot × koşul", r["endpoint_turu"], r["http_metodu"], r["kosul"],
            f"{r['endpoint_turu_ad']} / {r['http_metodu']} / {r['kosul_ad']}: {r['durum'].lower()}. {r['gerekce']}",
            evidence, rec.format(m=r["http_metodu"]))

    # 2) Metot, kategori, rol ve durum kodu temsili
    for m in HTTP_METHODS:
        if not (df["http_method"] == m).any():
            add(GAP_CONFIRMED, "Yüksek", "HTTP metodu", "", m, "",
                f"{m} metodu veri kümesinde hiç temsil edilmiyor.", "0 kayıt", f"{m} senaryoları ekleyin.")
    for field, label in (("category", "kategori"), ("user_role", "user_role"), ("expected_http_status", "durum kodu")):
        for v in schema_enum(schema, field):
            if not (df[field] == v).any():
                add(GAP_POTENTIAL, "Düşük", label, "", "", str(v),
                    f"Şemada tanımlı {label} '{v}' veri kümesinde kullanılmıyor.", "0 kayıt",
                    "Gerekliyse senaryo ekleyin veya şemadaki değeri gözden geçirin.")
    for cat in schema_enum(schema, "category"):
        sub = df[df["category"] == cat]
        if len(sub) and (sub["is_intentional_flaw"] == True).all():  # noqa: E712
            add(GAP_POTENTIAL, "Orta", "kategori × beklenti sınıfı", "", "", cat,
                f"'{CATEGORY_LABELS.get(cat, cat)}' kategorisindeki tüm kayıtlar bilerek-hatalı; güvenli "
                "uçta beklenen doğru davranışı aynı kategoride temsil eden kontrol senaryosu yok.",
                ";".join(sub["id"]),
                "Bu kategoride güvenli uç için bir pozitif/kontrol senaryosu ekleyin (ör. güvenli listede "
                "taslakların gizlendiğini aynı kategoriyle etiketleyin).")

    # 3) Fixture kimliği çeşitliliği (kullanıcı adından değil fixture sahipliğinden)
    requesters = set(df["fixture_user"].dropna())
    owners = {a["fields"]["owner"] for a in articles}
    for u in users:
        name = u["fields"]["username"]
        if name not in requesters:
            role_txt = ("kaynak sahibi olduğu halde" if u["pk"] in owners else "")
            add(GAP_POTENTIAL, "Orta", "fixture kimliği", "", "", name,
                f"Fixture kullanıcısı '{name}' {role_txt} hiçbir senaryoda istek yapan kimlik değil.".replace("  ", " "),
                f"istek yapan kimlikler={sorted(requesters)}",
                f"'{name}' ile sahipler arası çapraz erişim senaryosu ekleyin (ör. bir kaynak sahibinin "
                "başka bir sahibin kaydını güncellemesi/silmesi).")
    non_owner = df[(df["actor_relation"] == "sahip_olmayan") & df["http_method"].isin(MUTATING_METHODS)
                   & (df["endpoint_kind"] == "guvenli_nesne")]
    if len(non_owner) and non_owner["fixture_user"].nunique() == 1:
        add(GAP_POTENTIAL, "Orta", "aktör çeşitliliği", "guvenli_nesne", "PUT;PATCH;DELETE", "sahip_olmayan",
            "Güvenli nesne ucundaki tüm sahip-olmayan değiştirme senaryoları tek fixture kimliğiyle "
            f"('{non_owner['fixture_user'].iloc[0]}') tanımlanmış.", ";".join(non_owner["id"]),
            "Başka kayıtların sahibi olan bir kullanıcıyla (fixture'daki sahipler: "
            + ", ".join(sorted(u["fields"]["username"] for u in users if u["pk"] in owners))
            + ") başka bir sahibin kaydı üzerinde sahip-olmayan senaryosu ekleyin.")
    if len(non_owner) and "Taslak" not in set(non_owner["resource_state"]):
        add(GAP_POTENTIAL, "Orta", "kaynak görünürlüğü", "guvenli_nesne", "PUT;PATCH;DELETE", "sahip_olmayan",
            "Sahip olmayan kullanıcının başkasının TASLAK kaydını değiştirme girişimi temsil edilmiyor. "
            "views.get_queryset taslağı sahip olmayana göstermediğinden kaynak koduna göre 403 yerine 404 "
            "beklenir (çalışma zamanında doğrulanmadı).",
            f"mevcut sahip-olmayan değiştirme senaryolarının kaynak durumu={sorted(set(non_owner['resource_state']))}",
            "Taslak kayıt (ör. makale 2 veya 4) üzerinde sahip-olmayan PUT/PATCH/DELETE senaryosu ekleyin.")

    # 4) Yetersiz meta veri
    undetermined = df[df["condition"] == "belirlenemez"]
    for _, r in undetermined.iterrows():
        add(GAP_METADATA, "Düşük", "aktör–kaynak ilişkisi", r["endpoint_kind"], r["http_method"], "belirlenemez",
            "Aktörün kaynakla ilişkisi fixture verisinden belirlenemedi.", r["id"],
            "fixture_ref değerlerini gözden geçirin.")
    add(GAP_METADATA, "Düşük", "meta veri alanları", "", "", "",
        "Kayıtlarda açık 'kimlik doğrulama durumu' ve 'sahiplik' alanları yok; bu boyutlar fixture_ref + "
        "users.json/articles.json üzerinden türetildi.", "şema alanları: " + ", ".join(
            schema["$defs"]["scenario"]["properties"].keys()),
        "Ground truth (H3-03) için 'auth_state' ve 'ownership' alanlarının açıkça eklenmesini değerlendirin.")
    add(GAP_METADATA, "Düşük", "veri kaynağı", "", "", "",
        "Kayıt düzeyinde kaynak (source) alanı yok; kaynak, veri kümesi düzeyindeki 'dataset'/'target_app' "
        "alanlarından türetildi.", f"dataset={data.get('dataset')!r}, target_app={data.get('target_app')!r}",
        "PyGoat senaryoları eklendiğinde kayıt düzeyinde 'source' alanı tanımlayın.")

    out = pd.DataFrame(gaps, columns=["siniflandirma", "oncelik", "kapsam_boyutu", "endpoint_turu", "http_metodu",
                                      "kosul", "aciklama", "kanit", "oneri"])
    cls_order = {GAP_CONFIRMED: 0, GAP_POTENTIAL: 1, GAP_METADATA: 2}
    pr_order = {p: i for i, p in enumerate(PRIORITY_ORDER)}
    out = (out.assign(_c=out["siniflandirma"].map(cls_order), _p=out["oncelik"].map(pr_order).fillna(9))
              .sort_values(["_c", "_p"], kind="mergesort").drop(columns=["_c", "_p"]).reset_index(drop=True))
    out.insert(0, "bosluk_no", [f"GAP-{k:03d}" for k in range(1, len(out) + 1)])
    return out


# --------------------------------------------------------------------------------------
# Bilerek-hatalı senaryolar ve kaynak karşılaştırması
# --------------------------------------------------------------------------------------
def intentional_flaws(df: pd.DataFrame, scenarios: list[dict]) -> pd.DataFrame:
    """Bilerek-hatalı senaryolar + güvenli uçtaki karşılıkları (aynı metot, şekil ve aktör ilişkisi)."""
    by_id = {s.get("id"): s for s in scenarios if isinstance(s, dict)}
    rows = []
    for _, r in df[df["is_intentional_flaw"] == True].iterrows():  # noqa: E712
        shape = str(r["endpoint_kind"]).replace("guvensiz_", "")
        cp = df[(df["endpoint_kind"] == f"guvenli_{shape}") & (df["http_method"] == r["http_method"])
                & (df["actor_relation"] == r["actor_relation"])
                & (df["category"] != "INPUT_VALIDATION")]
        expl = by_id.get(r["id"], {}).get("flaw_explanation", "")
        m = re.search(r"beklenen (\d{3})", expl or "")
        stated = int(m.group(1)) if m else None
        cp_codes = sorted(cp["expected_http_status"].unique().tolist())
        rows.append({
            "senaryo_id": r["id"], "http_metodu": r["http_method"], "endpoint": r["endpoint"],
            "view": r["view"], "kategori": r["category"], "user_role": r["user_role"],
            "fixture_kimligi": r["fixture_user"], "aktor_iliskisi": r["actor_relation"],
            "gozlemlenen_durum_kodu": r["expected_http_status"], "label": r["label"],
            "flaw_explanation": expl,
            "guvenli_karsilik_idleri": ";".join(cp["id"]),
            "guvenli_karsilik_durum_kodlari": ";".join(str(c) for c in cp_codes),
            "aciklamadaki_guvenli_kod": stated if stated is not None else "",
            "aciklama_karsilik_uyumu": ("Uyumlu" if stated is not None and stated in cp_codes else
                                        ("Açıklamada kod yok" if stated is None else "Uyumsuz")),
        })
    return pd.DataFrame(rows)


def source_comparison(df: pd.DataFrame, pygoat: dict, data: dict) -> pd.DataFrame:
    ctrl = {
        "kaynak": "Kontrollü Django/DRF fixture",
        "depo_konumu": "benchmarks/drf_fixtures/scenarios/scenarios.json",
        "veri_kumesi": f"{data.get('dataset')} v{data.get('version')}",
        "senaryo_kaydi": len(df),
        "http_metodu": int(df["http_method"].nunique()),
        "kategori": int(df["category"].nunique()),
        "pozitif": int((df["label"] == "positive").sum()),
        "negatif": int((df["label"] == "negative").sum()),
        "bilerek_hatali": int((df["is_intentional_flaw"] == True).sum()),  # noqa: E712
        "degerlendirme_hazirligi": "Etiketli, şema ile doğrulanmış; H3-01 senaryo↔uygulama testleriyle eşlenmiş.",
    }
    n = pygoat["scenario_records"]
    pg = {
        "kaynak": "PyGoat",
        "depo_konumu": "benchmarks/pygoat/",
        "veri_kumesi": "—",
        "senaryo_kaydi": n,
        "http_metodu": pd.NA, "kategori": pd.NA, "pozitif": pd.NA, "negatif": pd.NA, "bilerek_hatali": pd.NA,
        "degerlendirme_hazirligi": (
            "Etiketli senaryo kaydı yok; dizinde yalnızca inceleme/planlama notu var "
            f"({', '.join(pygoat['files']) or 'dosya yok'}). Nicel karşılaştırma yapılamaz; sürüm sabitleme "
            "ve ground truth H3-03'e bırakılmış." if n == 0 else
            f"{n} kayıt bulundu ({', '.join(pygoat['data_files'])}); ayrı analiz gerektirir."),
    }
    return pd.DataFrame([ctrl, pg])
