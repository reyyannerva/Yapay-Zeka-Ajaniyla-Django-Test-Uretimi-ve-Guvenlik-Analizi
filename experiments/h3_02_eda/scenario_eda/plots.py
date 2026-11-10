"""Rapor grafikleri — H3-02 / Issue #28.

Tüm grafikler gerçek veri kümesinden üretilen tablolardan çizilir. Tasarım kuralları:
* Açık (beyaz) yüzey, ölçülü ve sabit sıralı renk paleti; sınıf renkleri her grafikte aynıdır.
* Eksenler sıfırdan başlar (kesik eksen yok); tüm etiketler Türkçedir.
* Isı haritalarında tek tonlu sıralı ölçek kullanılır; sıfır hücreler beyaz kalır ve "0" yazılır,
  böylece kapsam boşlukları görünür olur.
* Durum (kapsam) renkleri yalnızca metin etiketiyle birlikte kullanılır; anlam yalnızca renge
  bırakılmaz.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

from . import coverage as cov  # noqa: E402
from .data import EXPECTATION_FLAW, EXPECTATION_REJECTION, EXPECTATION_SUCCESS  # noqa: E402

SURFACE = "#ffffff"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#8a8984"
GRID = "#e6e5e1"

CLASS_COLORS = {  # sabit sıralı kategorik yuvalar 1–3
    EXPECTATION_SUCCESS: "#2a78d6",
    EXPECTATION_REJECTION: "#eb6834",
    EXPECTATION_FLAW: "#1baf7a",
}
SEQ_CMAP = LinearSegmentedColormap.from_list(
    "h302_blue", ["#ffffff", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
CELL_COLORS = {
    cov.STATUS_PRESENT: ("#0ca30c", "#ffffff"),
    cov.STATUS_INDIRECT: ("#fab219", INK),
    cov.STATUS_MISSING: ("#d03b3b", "#ffffff"),
    cov.STATUS_NA: ("#f0efec", INK_2),
    "Modelde tanımlı değil": ("#ffffff", INK_MUTED),
}
SEVERITY_COLORS = {"Kritik": "#d03b3b", "Yüksek": "#ec835a", "Orta": "#fab219", "Düşük": "#86b6ef",
                   "Bilgi": "#b9b8b2"}
DPI = 200


def setup_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12.5, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlepad": 12, "axes.labelsize": 10, "axes.labelcolor": INK_2,
        "axes.edgecolor": GRID, "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK, "legend.frameon": False,
        "legend.fontsize": 9, "figure.dpi": 100,
    })


def save(fig, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", metadata={"Software": None})
    return path


def _note(ax, text: str, offset_pt: float = -46) -> None:
    """Eksenin altına, x ekseni etiketiyle çakışmayan sabit nokta ofsetinde açıklama notu."""
    ax.annotate(text, xy=(0, 0), xycoords="axes fraction", xytext=(0, offset_pt),
                textcoords="offset points", fontsize=8.5, color=INK_2, ha="left", va="top",
                annotation_clip=False)


def _class_legend(ax, ncol=3):
    handles = [Patch(facecolor=c, label=k) for k, c in CLASS_COLORS.items()]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=ncol, borderaxespad=0.2,
              handlelength=1.2, columnspacing=1.4)


def stacked_class_barh(ax, dist: pd.DataFrame, label_col: str = "gorunen_ad", total: int | None = None,
                       show_legend: bool = True) -> None:
    """Beklenti sınıfına göre yığılmış yatay çubuk; çubuk sonunda 'n (%x)' etiketi."""
    d = dist.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(d))
    left = np.zeros(len(d))
    cols = {EXPECTATION_SUCCESS: "beklenen_basari", EXPECTATION_REJECTION: "beklenen_ret",
            EXPECTATION_FLAW: "bilerek_guvensiz"}
    for cls, col in cols.items():
        vals = d[col].to_numpy(dtype=float)
        ax.barh(y, vals, left=left, color=CLASS_COLORS[cls], edgecolor=SURFACE, linewidth=1.5, height=0.62)
        left += vals
    tot = total if total is not None else int(dist["senaryo_sayisi"].sum())
    xmax = max(float(d["senaryo_sayisi"].max()), 1.0)
    for yi, (n, pct) in enumerate(zip(d["senaryo_sayisi"], d["yuzde"])):
        ax.text(n + xmax * 0.015, yi, f"{n}  (%{pct:.1f})", va="center", ha="left", fontsize=9, color=INK)
    ax.set_yticks(y, d[label_col].astype(str))
    ax.set_xlim(0, xmax * 1.22)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Senaryo sayısı (toplam {tot})")
    if show_legend:
        _class_legend(ax)


def fig_methods(dist: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    stacked_class_barh(ax, dist)
    ax.set_title("HTTP metotlarına göre senaryo dağılımı", pad=34)
    ax.set_ylabel("HTTP metodu")
    zero = dist[dist["senaryo_sayisi"] == 0]["deger"].tolist()
    note = ("Temsil edilmeyen metot: " + ", ".join(zero)) if zero else "Beş metodun tamamı temsil ediliyor."
    _note(ax, note)
    return save(fig, path), fig


def fig_classes(class_dist: pd.DataFrame, path: Path):
    lab = class_dist[class_dist["boyut"] == "label"]
    fig, ax = plt.subplots(figsize=(8.5, 2.9))
    stacked_class_barh(ax, lab)
    ax.set_title("Pozitif / negatif senaryo dağılımı", pad=34)
    ax.set_ylabel("Etiket (label)")
    pos = int(lab.loc[lab["deger"] == "positive", "senaryo_sayisi"].iloc[0])
    neg = int(lab.loc[lab["deger"] == "negative", "senaryo_sayisi"].iloc[0])
    ratio = f"{neg / pos:.2f}" if pos else "tanımsız"
    _note(ax, f"Negatif/pozitif oranı: {ratio}. Bilerek güvensiz davranışlar negatif etiketin alt kümesidir.")
    return save(fig, path), fig


def fig_categories(dist: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    stacked_class_barh(ax, dist)
    ax.set_title("Senaryo kategorilerine göre dağılım", pad=34)
    ax.set_ylabel("Kategori")
    return save(fig, path), fig


def fig_roles(role_dist: pd.DataFrame, path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), gridspec_kw={"wspace": 0.55})
    a = role_dist[role_dist["boyut"] == "user_role (etiket)"]
    b = role_dist[role_dist["boyut"].str.startswith("aktör")]
    b = b[(b["senaryo_sayisi"] > 0) | (b["deger"] != "belirlenemez")]
    stacked_class_barh(axes[0], a)
    axes[0].set_title("Veri kümesi rol etiketi (user_role)", pad=34)
    stacked_class_barh(axes[1], b, show_legend=False)
    axes[1].set_title("Fixture'dan türetilen aktör–kaynak ilişkisi", pad=34)
    _note(axes[0], "Sağ panel kullanıcı adından değil users.json (is_staff) ve articles.json (owner) "
          "kayıtlarından türetilmiştir; 'Belirlenemez' = hedef nesne fixture'da yok.")
    return save(fig, path), fig


def fig_status(dist: pd.DataFrame, path: Path):
    d = dist.copy()
    d["gorunen_ad"] = d["deger"].astype(str)
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    stacked_class_barh(ax, d)
    ax.set_title("Beklenen HTTP durum kodu dağılımı", pad=34)
    ax.set_ylabel("Beklenen durum kodu")
    return save(fig, path), fig


def heatmap(ax, ct: pd.DataFrame, xlabels: list[str], ylabels: list[str]) -> None:
    data = ct.to_numpy()
    vmax = max(int(data.max()), 1)
    ax.imshow(data, cmap=SEQ_CMAP, vmin=0, vmax=vmax, aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = int(data[i, j])
            color = "#ffffff" if v > vmax * 0.55 else (INK_MUTED if v == 0 else INK)
            ax.text(j, i, str(v), ha="center", va="center", fontsize=10, color=color,
                    fontweight="bold" if v else "normal")
    ax.set_xticks(range(len(xlabels)), xlabels, rotation=0)
    ax.set_yticks(range(len(ylabels)), ylabels)
    ax.set_xticks(np.arange(-0.5, data.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, data.shape[0]), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def _wrap(s: str, width: int = 14) -> str:
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > width and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    return "\n".join(lines)


def fig_method_category(ct: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    heatmap(ax, ct, [_wrap(cov.CATEGORY_LABELS.get(c, c)) for c in ct.columns], list(ct.index))
    ax.set_title("HTTP metodu × kategori kapsam ısı haritası (senaryo sayısı)")
    ax.set_xlabel("Kategori")
    ax.set_ylabel("HTTP metodu")
    return save(fig, path), fig


def fig_method_role(ct_role: pd.DataFrame, ct_rel: pd.DataFrame, path: Path):
    ct_rel = ct_rel.loc[:, (ct_rel.sum(axis=0) > 0) | (ct_rel.columns != "belirlenemez")]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.4), gridspec_kw={"width_ratios": [4, 6], "wspace": 0.25})
    heatmap(axes[0], ct_role, [_wrap(cov.ROLE_LABELS.get(c, c), 12) for c in ct_role.columns], list(ct_role.index))
    axes[0].set_title("HTTP metodu × rol etiketi (user_role)")
    axes[0].set_xlabel("Rol etiketi")
    axes[0].set_ylabel("HTTP metodu")
    heatmap(axes[1], ct_rel, [_wrap(cov.RELATION_LABELS.get(c, c), 12) for c in ct_rel.columns], list(ct_rel.index))
    axes[1].set_title("HTTP metodu × aktör–kaynak ilişkisi (fixture'dan)")
    axes[1].set_xlabel("Aktör–kaynak ilişkisi")
    return save(fig, path), fig


AUTHZ_CONDITIONS = ["anonim", "kaynak_sahibi", "sahip_olmayan", "yonetici", "kaynak_yok", "gecersiz_girdi"]


def fig_authorization(authz: pd.DataFrame, path: Path):
    rows = [(k, m) for k in ("guvenli_nesne", "guvensiz_nesne") for m in ("PUT", "PATCH", "DELETE")]
    fig, ax = plt.subplots(figsize=(13.5, 5.6))
    for i, (kind, method) in enumerate(rows):
        for j, cond in enumerate(AUTHZ_CONDITIONS):
            hit = authz[(authz["endpoint_turu"] == kind) & (authz["http_metodu"] == method) & (authz["kosul"] == cond)]
            if hit.empty:
                status, text = "Modelde tanımlı değil", "—"
            else:
                r = hit.iloc[0]
                status = r["durum"]
                if status == cov.STATUS_PRESENT:
                    text = r["senaryo_idleri"].replace(";", "\n") + f"\n→ {r['beklenen_durum_kodlari']}"
                elif status == cov.STATUS_INDIRECT:
                    text = "Dolaylı\n(PUT/PATCH\nortak yol)"
                elif status == cov.STATUS_MISSING:
                    text = "Kapsanmıyor"
                else:
                    text = "Uygulanamaz"
            fc, tc = CELL_COLORS[status]
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=fc, edgecolor=SURFACE, linewidth=3))
            ax.text(j + 0.5, i + 0.5, text, ha="center", va="center", fontsize=8.6, color=tc,
                    fontweight="bold" if status == cov.STATUS_PRESENT else "normal")
    ax.set_xlim(0, len(AUTHZ_CONDITIONS))
    ax.set_ylim(len(rows), 0)
    ax.set_xticks(np.arange(len(AUTHZ_CONDITIONS)) + 0.5,
                  [_wrap(cov.CONDITION_LABELS[c], 13) for c in AUTHZ_CONDITIONS])
    ax.set_yticks(np.arange(len(rows)) + 0.5,
                  [f"{'Güvenli' if k == 'guvenli_nesne' else 'Bilerek güvensiz'} · {m}" for k, m in rows])
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.axhline(3, color=INK_2, linewidth=1.2)
    ax.set_title("PUT / PATCH / DELETE yetkilendirme kapsam matrisi (nesne uçları)", pad=44)
    handles = [Patch(facecolor=CELL_COLORS[s][0], edgecolor=GRID, label=s) for s in
               (cov.STATUS_PRESENT, cov.STATUS_INDIRECT, cov.STATUS_MISSING, cov.STATUS_NA, "Modelde tanımlı değil")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -0.02), ncol=5, handlelength=1.2)
    _note(ax, "Hücre metni: senaryo kimlikleri → beklenen durum kodu. Eksik hücre kapsam boşluğudur; "
          "doğrulanmış güvenlik açığı anlamına gelmez.", offset_pt=-34)
    return save(fig, path), fig


def fig_findings(findings: pd.DataFrame, path: Path):
    n_types = findings["sorun_turu"].nunique() if not findings.empty else 1
    fig, ax = plt.subplots(figsize=(9, 1.6 + 0.55 * n_types))
    if findings.empty:
        ax.axis("off")
        ax.text(0.5, 0.5, "Doğrulanmış veri kalitesi bulgusu yok (0 kayıt)", ha="center", va="center",
                fontsize=12, color=INK_2)
        ax.set_title("Veri kalitesi bulguları (sorun türü × önem derecesi)")
        return save(fig, path), fig
    ct = pd.crosstab(findings["sorun_turu"], findings["onem_derecesi"])
    sev = [s for s in SEVERITY_COLORS if s in ct.columns]
    ct = ct[sev].loc[ct.sum(axis=1).sort_values().index]
    left = np.zeros(len(ct))
    y = np.arange(len(ct))
    for s in sev:
        vals = ct[s].to_numpy(dtype=float)
        ax.barh(y, vals, left=left, color=SEVERITY_COLORS[s], edgecolor=SURFACE, linewidth=1.5, height=0.4, label=s)
        left += vals
    for yi, v in enumerate(ct.sum(axis=1)):
        ax.text(v + 0.05, yi, str(int(v)), va="center", fontsize=9)
    ax.set_yticks(y, ct.index)
    ax.set_xlim(0, max(left.max(), 1) * 1.2)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Bulgu sayısı")
    ax.set_title("Veri kalitesi bulguları (sorun türü × önem derecesi)", pad=30)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(sev), title=None)
    counts = findings["onem_derecesi"].value_counts()
    note = " · ".join(f"{s}: {int(counts.get(s, 0))}" for s in SEVERITY_COLORS)
    _note(ax, "Önem dağılımı — " + note)
    return save(fig, path), fig


def fig_coverage_cells(matrix: pd.DataFrame, path: Path):
    kinds = [k for k in cov.KIND_ORDER if k in set(matrix["endpoint_turu"])]
    ct = pd.crosstab(matrix["endpoint_turu"], matrix["durum"]).reindex(index=kinds, columns=cov.CELL_STATUS_ORDER,
                                                                         fill_value=0)
    ct = ct.iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    left = np.zeros(len(ct))
    y = np.arange(len(ct))
    for s in cov.CELL_STATUS_ORDER:
        vals = ct[s].to_numpy(dtype=float)
        ax.barh(y, vals, left=left, color=CELL_COLORS[s][0], edgecolor=SURFACE, linewidth=1.5, height=0.6, label=s)
        for yi, (lv, v) in enumerate(zip(left, vals)):
            if v:
                ax.text(lv + v / 2, yi, str(int(v)), ha="center", va="center", fontsize=8.5, color=CELL_COLORS[s][1])
        left += vals
    ax.set_yticks(y, [cov.ENDPOINT_KIND_LABELS.get(k, k) for k in ct.index])
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(0, left.max() * 1.05)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Kapsam modeli hücre sayısı (endpoint türü × metot × koşul)")
    ax.set_title("Kapsam modeli hücre durumu (endpoint türüne göre)", pad=30)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4)
    return save(fig, path), fig


FIGURE_FILES = {
    "01_http_metot_dagilimi.png": "HTTP metodu dağılımı",
    "02_pozitif_negatif_dagilimi.png": "Pozitif/negatif dağılımı",
    "03_kategori_dagilimi.png": "Kategori dağılımı",
    "04_rol_dagilimi.png": "Rol ve aktör ilişkisi dağılımı",
    "05_durum_kodu_dagilimi.png": "Beklenen durum kodu dağılımı",
    "06_metot_kategori_isi_haritasi.png": "Metot × kategori ısı haritası",
    "07_metot_rol_isi_haritasi.png": "Metot × rol ısı haritası",
    "08_put_patch_delete_yetkilendirme_kapsami.png": "PUT/PATCH/DELETE yetkilendirme matrisi",
    "09_veri_kalitesi_bulgulari.png": "Veri kalitesi bulguları",
    "10_kapsam_modeli_hucre_durumu.png": "Kapsam modeli hücre durumu",
}


def render_all(ctx, tables: dict[str, pd.DataFrame], out_dir: Path, close: bool = True) -> dict[str, Path]:
    """Tüm rapor grafiklerini üretir. Kaynak karşılaştırma grafiği yalnızca PyGoat kaydı varsa çizilir."""
    setup_style()
    out_dir = Path(out_dir)
    tabs = cov.standard_crosstabs(ctx.df, ctx.schema)
    jobs = [
        ("01_http_metot_dagilimi.png", lambda p: fig_methods(tables["method_distribution"], p)),
        ("02_pozitif_negatif_dagilimi.png", lambda p: fig_classes(tables["class_distribution"], p)),
        ("03_kategori_dagilimi.png", lambda p: fig_categories(tables["category_distribution"], p)),
        ("04_rol_dagilimi.png", lambda p: fig_roles(tables["role_distribution"], p)),
        ("05_durum_kodu_dagilimi.png", lambda p: fig_status(tables["status_code_distribution"], p)),
        ("06_metot_kategori_isi_haritasi.png", lambda p: fig_method_category(tabs["metot_x_kategori"], p)),
        ("07_metot_rol_isi_haritasi.png",
         lambda p: fig_method_role(tabs["metot_x_rol"], tabs["metot_x_aktor_iliskisi"], p)),
        ("08_put_patch_delete_yetkilendirme_kapsami.png",
         lambda p: fig_authorization(tables["authorization_coverage"], p)),
        ("09_veri_kalitesi_bulgulari.png", lambda p: fig_findings(tables["data_quality_findings"], p)),
        ("10_kapsam_modeli_hucre_durumu.png", lambda p: fig_coverage_cells(tables["coverage_matrix"], p)),
    ]
    out: dict[str, Path] = {}
    for name, job in jobs:
        path, fig = job(out_dir / name)
        out[name] = path
        if close:
            plt.close(fig)
    return out

