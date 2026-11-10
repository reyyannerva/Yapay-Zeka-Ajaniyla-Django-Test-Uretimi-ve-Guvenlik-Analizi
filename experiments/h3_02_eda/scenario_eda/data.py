"""Girdi bulma, yükleme, statik rota çözümlemesi ve kayıt zenginleştirme — H3-02 / Issue #28.

Bu modül H3-01 (Issue #27) çıktılarını *okur*; hiçbir kaynak dosyayı değiştirmez.

Önemli ayrımlar:
* ``user_role`` (veri kümesindeki etiket) ile ``fixture_ref.user`` (fixture kimliği: admin, alice,
  bob, carol) aynı şey değildir. Aktör–kaynak ilişkisi (sahip / sahip olmayan / yönetici)
  kullanıcı adından DEĞİL, ``users.json`` (is_staff) ve ``articles.json`` (owner) fixture
  kayıtlarından türetilir.
* Rota çözümlemesi iki katmanlıdır: (1) ``urls.py`` dosyalarının metin tabanlı statik
  çözümlemesi (her zaman), (2) Django yüklüyse ayrı bir alt süreçte ``django.urls.resolve``
  ile view sınıfı ve desteklenen metotların belirlenmesi. İkinci katman HTTP isteği
  ÇALIŞTIRMAZ; davranışsal (çalışma zamanı) doğrulama H3-01'in pytest paketindedir.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

HTTP_METHODS: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE")
MUTATING_METHODS: tuple[str, ...] = ("PUT", "PATCH", "DELETE")

REL_DRF = Path("benchmarks") / "drf_fixtures"
REL_SCENARIOS_JSON = REL_DRF / "scenarios" / "scenarios.json"
ENV_REPO_ROOT = "H302_REPO_ROOT"

CONTROLLED_SOURCE = "Kontrollü Django/DRF fixture"
PYGOAT_SOURCE = "PyGoat"

# Kayıt düzeyi türetilmiş sınıflar (Türkçe görünen değerler)
EXPECTATION_SUCCESS = "Beklenen başarı"
EXPECTATION_REJECTION = "Beklenen ret"
EXPECTATION_FLAW = "Bilerek güvensiz davranış"
EXPECTATION_INCONSISTENT = "Tutarsız / doğrulanamayan"
EXPECTATION_ORDER = (EXPECTATION_SUCCESS, EXPECTATION_REJECTION, EXPECTATION_FLAW, EXPECTATION_INCONSISTENT)


# --------------------------------------------------------------------------------------
# Yol çözümleme
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class DatasetPaths:
    """H3-01 teslimatlarının depo içindeki konumları (depo köküne göre)."""

    repo_root: Path

    @property
    def drf_dir(self) -> Path:
        return self.repo_root / REL_DRF

    @property
    def scenarios_json(self) -> Path:
        return self.drf_dir / "scenarios" / "scenarios.json"

    @property
    def scenarios_csv(self) -> Path:
        return self.drf_dir / "scenarios" / "scenarios.csv"

    @property
    def schema_json(self) -> Path:
        return self.drf_dir / "scenarios" / "scenarios.schema.json"

    @property
    def validator_script(self) -> Path:
        return self.drf_dir / "scripts" / "validate_scenarios.py"

    @property
    def export_script(self) -> Path:
        return self.drf_dir / "scripts" / "export_scenarios_csv.py"

    @property
    def sample_app(self) -> Path:
        return self.drf_dir / "sample_app"

    @property
    def users_fixture(self) -> Path:
        return self.sample_app / "catalog" / "fixtures" / "users.json"

    @property
    def articles_fixture(self) -> Path:
        return self.sample_app / "catalog" / "fixtures" / "articles.json"

    @property
    def catalog_urls(self) -> Path:
        return self.sample_app / "catalog" / "urls.py"

    @property
    def config_urls(self) -> Path:
        return self.sample_app / "config" / "urls.py"

    @property
    def pygoat_dir(self) -> Path:
        return self.repo_root / "benchmarks" / "pygoat"

    def required_files(self) -> dict[str, Path]:
        return {
            "Kanonik senaryo JSON": self.scenarios_json,
            "Türetilmiş senaryo CSV": self.scenarios_csv,
            "JSON Schema": self.schema_json,
            "Kullanıcı fixture'ı": self.users_fixture,
            "Makale fixture'ı": self.articles_fixture,
            "catalog/urls.py": self.catalog_urls,
            "config/urls.py": self.config_urls,
        }

    def check_required(self) -> None:
        missing = {k: v for k, v in self.required_files().items() if not v.is_file()}
        if missing:
            lines = "\n".join(f"  - {k}: {v}" for k, v in missing.items())
            raise FileNotFoundError(
                "Gerekli H3-01 girdi dosyaları bulunamadı:\n" + lines +
                "\nDepo kökünü doğrulayın veya H302_REPO_ROOT ortam değişkenini ayarlayın."
            )


def find_repo_root(start: Path | str | None = None) -> Path:
    """Depo kökünü bulur.

    Sıra: (1) ``H302_REPO_ROOT`` ortam değişkeni, (2) ``start`` (varsayılan: çalışma dizini)
    ve üst dizinleri. Kök, ``benchmarks/drf_fixtures/scenarios/scenarios.json`` dosyasını
    içeren dizindir. Bulunamazsa açıklayıcı bir ``FileNotFoundError`` yükseltilir.
    """
    env = os.environ.get(ENV_REPO_ROOT)
    if env:
        root = Path(env).expanduser().resolve()
        if (root / REL_SCENARIOS_JSON).is_file():
            return root
        raise FileNotFoundError(
            f"{ENV_REPO_ROOT}={root} ayarlı ancak {REL_SCENARIOS_JSON} bu dizinde yok."
        )
    here = Path(start or Path.cwd()).expanduser().resolve()
    for candidate in (here, *here.parents):
        if (candidate / REL_SCENARIOS_JSON).is_file():
            return candidate
    raise FileNotFoundError(
        f"{REL_SCENARIOS_JSON} dosyası '{here}' ve üst dizinlerinde bulunamadı. Notebook'u depo "
        f"içinden çalıştırın veya {ENV_REPO_ROOT} ortam değişkenini depo köküne ayarlayın "
        "(Colab için README'deki kurulum hücresine bakın)."
    )


# --------------------------------------------------------------------------------------
# Statik URL rota çözümlemesi
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Route:
    """``urls.py`` dosyalarından statik olarak çıkarılan bir rota."""

    pattern: str          # ör. "/api/articles/<int:pk>/publish/"
    view_name: str        # ör. "ArticlePublishView"
    view_module: str      # ör. "views" veya "insecure"
    origin: str           # "path" veya "router"
    shape: str            # "koleksiyon" | "nesne" | "nesne_aksiyonu"

    @property
    def insecure(self) -> bool:
        return self.view_module == "insecure"

    @property
    def kind(self) -> str:
        return f"{'guvensiz' if self.insecure else 'guvenli'}_{self.shape}"

    @property
    def regex(self) -> re.Pattern[str]:
        parts = re.split(r"(<int:pk>|<pk>)", self.pattern)
        conv = {"<int:pk>": r"(?P<pk>\d+)", "<pk>": r"(?P<pk>[^/.]+)"}
        return re.compile("^" + "".join(conv.get(p, re.escape(p)) for p in parts) + "$")


ENDPOINT_KIND_LABELS = {
    "guvenli_koleksiyon": "Güvenli koleksiyon",
    "guvenli_nesne": "Güvenli nesne (detay)",
    "guvenli_nesne_aksiyonu": "Güvenli nesne aksiyonu",
    "guvensiz_koleksiyon": "Bilerek güvensiz koleksiyon",
    "guvensiz_nesne": "Bilerek güvensiz nesne (detay)",
    "cozumlenemedi": "Çözümlenemedi",
}

_PATH_RX = re.compile(r"""path\(\s*r?["']([^"']*)["']\s*,\s*(\w+)\.as_view\(""")
_INCLUDE_RX = re.compile(r"""path\(\s*r?["']([^"']*)["']\s*,\s*include\(\s*["']catalog\.urls["']""")
_ROUTER_RX = re.compile(r"""router\.register\(\s*r?["']([^"']+)["']\s*,\s*(\w+)""")
_IMPORT_RX = re.compile(r"""from\s+\.(\w+)\s+import\s+(\([^)]*\)|[^\n]+)""")


def _shape(pattern: str) -> str:
    if "<" not in pattern:
        return "koleksiyon"
    tail = pattern.split(">", 1)[1].strip("/")
    return "nesne_aksiyonu" if tail else "nesne"


def parse_routes(config_urls_text: str, catalog_urls_text: str) -> list[Route]:
    """config/urls.py + catalog/urls.py metinlerinden rota listesi çıkarır (statik).

    Desteklenen yapılar: ``path("...", View.as_view())``, ``SimpleRouter.register`` (liste +
    ``<pk>`` detay rotası) ve ``path("api/", include("catalog.urls"))`` öneki.
    """
    inc = _INCLUDE_RX.search(config_urls_text)
    prefix = "/" + (inc.group(1) if inc else "")
    modules: dict[str, str] = {}
    for module, names in _IMPORT_RX.findall(catalog_urls_text):
        for name in re.split(r"[\s,()]+", names.strip()):
            if name:
                modules[name] = module
    routes: list[Route] = []
    for pat, view in _PATH_RX.findall(catalog_urls_text):
        p = prefix + pat
        routes.append(Route(p, view, modules.get(view, "?"), "path", _shape(p)))
    trailing = "trailing_slash=False" not in catalog_urls_text
    slash = "/" if trailing else ""
    for reg_prefix, view in _ROUTER_RX.findall(catalog_urls_text):
        base = prefix + reg_prefix.strip("^$").rstrip("/")
        for p in (base + slash, base + "/<pk>" + slash):
            routes.append(Route(p, view, modules.get(view, "?"), "router", _shape(p)))
    return routes


def resolve_route(endpoint: Any, routes: list[Route]) -> tuple[Route | None, str | None]:
    """Somut endpoint'i (ör. /api/articles/3/) rota desenine eşler; (rota, pk) döndürür."""
    if not isinstance(endpoint, str):
        return None, None
    path = endpoint.split("?", 1)[0]
    # Belirli (sabit metinli) desenler önce denenir.
    for r in sorted(routes, key=lambda r: (r.pattern.count("<"), -len(r.pattern))):
        m = r.regex.match(path)
        if m:
            return r, m.groupdict().get("pk")
    return None, None


# --------------------------------------------------------------------------------------
# İsteğe bağlı Django URL çözümlemesi (HTTP isteği çalıştırmaz)
# --------------------------------------------------------------------------------------
_DJANGO_PROBE = r'''
import json, os, sys
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.urls import resolve, Resolver404
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
out = {}
for ep in json.loads(sys.stdin.read()):
    try:
        m = resolve(ep)
    except Resolver404:
        out[ep] = None
        continue
    func = m.func
    cls = getattr(func, "cls", None) or getattr(func, "view_class", None)
    actions = getattr(func, "actions", None)
    if actions:
        allowed = sorted(k.upper() for k in actions)
    else:
        allowed = sorted(h.upper() for h in cls.http_method_names
                         if h not in ("options", "head", "trace") and hasattr(cls, h))
    if issubclass(cls, ViewSetMixin):
        vt = "ViewSet"
    elif issubclass(cls, GenericAPIView):
        vt = "Generic APIView"
    elif issubclass(cls, APIView):
        vt = "APIView"
    else:
        vt = "Django view"
    out[ep] = {"view": cls.__module__ + "." + cls.__name__, "view_type": vt,
               "url_name": m.url_name, "allowed_methods": allowed}
print(json.dumps(out, sort_keys=True))
'''


def django_method_support(sample_app: Path, endpoints: list[str]) -> tuple[dict | None, str]:
    """Django ile endpoint → (view, view türü, izinli metotlar) eşlemesi; ayrı alt süreçte.

    Django/DRF kurulu değilse ``(None, açıklama)`` döner; analiz statik katmanla sürer.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _DJANGO_PROBE],
            cwd=sample_app, input=json.dumps(sorted(set(endpoints))),
            capture_output=True, text=True, timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:  # pragma: no cover - ortam bağımlı
        return None, f"Django URL çözümlemesi çalıştırılamadı: {exc}"
    if proc.returncode != 0:
        last = (proc.stderr.strip().splitlines() or ["bilinmeyen hata"])[-1]
        return None, ("Django URL çözümlemesi atlandı (Django/DRF kurulu değil veya ayarlar "
                      f"yüklenemedi): {last}")
    return json.loads(proc.stdout), ("Django URL çözümlemesi yapıldı (django.urls.resolve; "
                                     "HTTP isteği çalıştırılmadı).")


# --------------------------------------------------------------------------------------
# PyGoat envanteri
# --------------------------------------------------------------------------------------
DATA_SUFFIXES = {".json", ".csv", ".yaml", ".yml", ".jsonl"}


def pygoat_inventory(pygoat_dir: Path) -> dict[str, Any]:
    """benchmarks/pygoat/ altında gerçek senaryo kaydı olup olmadığını envanterler."""
    files = sorted(p for p in pygoat_dir.rglob("*") if p.is_file()) if pygoat_dir.is_dir() else []
    data_files = [p for p in files if p.suffix.lower() in DATA_SUFFIXES]
    records = 0
    for p in data_files:
        if p.suffix.lower() == ".json":
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(obj, dict) and isinstance(obj.get("scenarios"), list):
                records += len(obj["scenarios"])
            elif isinstance(obj, list):
                records += len(obj)
        elif p.suffix.lower() == ".csv":
            lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
            records += max(len(lines) - 1, 0)
    return {
        "dir_exists": pygoat_dir.is_dir(),
        "files": [p.relative_to(pygoat_dir).as_posix() for p in files],
        "data_files": [p.relative_to(pygoat_dir).as_posix() for p in data_files],
        "scenario_records": records,
        "has_readme": (pygoat_dir / "README.md").is_file(),
    }


# --------------------------------------------------------------------------------------
# Kayıt zenginleştirme
# --------------------------------------------------------------------------------------
def _fixture_index(fixture: list[dict], key: str) -> dict:
    return {(row["fields"][key] if key != "pk" else row["pk"]): row for row in fixture}


def actor_relation(user: Any, article: Any, users_by_name: dict, articles_by_pk: dict) -> str:
    """Aktörün kaynakla ilişkisini FIXTURE kayıtlarından türetir (kullanıcı adından değil)."""
    if user is None:
        return "anonim"
    urow = users_by_name.get(user)
    if urow is None:
        return "belirlenemez"
    if urow["fields"].get("is_staff"):
        return "yonetici"
    if article is None:
        return "kimligi_dogrulanmis"
    arow = articles_by_pk.get(article)
    if arow is None:
        return "belirlenemez"
    return "kaynak_sahibi" if arow["fields"].get("owner") == urow["pk"] else "sahip_olmayan"


def expectation_class(label: Any, status: Any, is_flaw: Any) -> str:
    """Pozitif/negatif etiketini durum koduyla birlikte yorumlar.

    Veri kümesindeki kullanım (H3-01 README + kayıtlar): ``positive`` = güvenli uçta beklenen
    başarılı davranış (2xx); ``negative`` = beklenen ret (4xx) VEYA bilerek güvensiz uçta
    gözlemlenen hatalı davranış (``is_intentional_flaw: true``).
    """
    if is_flaw is True:
        return EXPECTATION_FLAW
    if not isinstance(status, int) or isinstance(status, bool):
        return EXPECTATION_INCONSISTENT
    if label == "positive" and 200 <= status < 300:
        return EXPECTATION_SUCCESS
    if label == "negative" and 400 <= status < 500:
        return EXPECTATION_REJECTION
    return EXPECTATION_INCONSISTENT


def annotate_scenarios(
    scenarios: list[dict],
    users: list[dict],
    articles: list[dict],
    routes: list[Route],
    method_support: dict | None = None,
    source: str = CONTROLLED_SOURCE,
) -> pd.DataFrame:
    """Senaryoları düzleştirir ve türetilmiş analiz sütunları ekler. Kaynağı değiştirmez.

    Bozuk kayıtlarda (eksik alan vb.) hata vermez; eksik değerler NA olarak kalır.
    """
    users_by_name = _fixture_index(users, "username")
    articles_by_pk = _fixture_index(articles, "pk")
    rows = []
    for idx, s in enumerate(scenarios):
        fx = s.get("fixture_ref") if isinstance(s.get("fixture_ref"), dict) else {}
        user, article = fx.get("user"), fx.get("article")
        method = s.get("http_method")
        status = s.get("expected_http_status")
        route, pk = resolve_route(s.get("endpoint"), routes)
        support = (method_support or {}).get(s.get("endpoint")) if method_support else None
        if support:
            method_supported: bool | None = method in support["allowed_methods"]
        else:
            method_supported = None
        relation = actor_relation(user, article, users_by_name, articles_by_pk)
        if article is None:
            resource_state = "Koleksiyon (nesne yok)"
        elif article not in articles_by_pk:
            resource_state = "Mevcut değil"
        else:
            resource_state = "Yayında" if articles_by_pk[article]["fields"].get("is_published") else "Taslak"
        if method_supported is False or (method_supported is None and status == 405):
            condition = "metot_desteklenmiyor"
        elif resource_state == "Mevcut değil":
            condition = "kaynak_yok"
        elif s.get("category") == "INPUT_VALIDATION":
            condition = "gecersiz_girdi"
        else:
            condition = relation
        rows.append({
            "kayit_sirasi": idx,
            "id": s.get("id"),
            "category": s.get("category"),
            "http_method": method,
            "endpoint": s.get("endpoint"),
            "user_role": s.get("user_role"),
            "expected_http_status": status,
            "label": s.get("label"),
            "is_intentional_flaw": s.get("is_intentional_flaw"),
            "fixture_user": user,
            "fixture_article": article,
            "has_request_input": bool(s.get("request_input")),
            "requirement_refs": ";".join(s.get("requirement_refs") or []),
            "source": source,
            "endpoint_pattern": route.pattern if route else None,
            "endpoint_kind": route.kind if route else "cozumlenemedi",
            "endpoint_pk": pk,
            "view_type": support["view_type"] if support else None,
            "view": support["view"] if support else (route.view_name if route else None),
            "method_supported": method_supported,
            "auth_state": "anonim" if user is None else "kimligi_dogrulanmis",
            "actor_relation": relation,
            "resource_state": resource_state,
            "condition": condition,
            "expectation_class": expectation_class(s.get("label"), status, s.get("is_intentional_flaw")),
            "status_class": (f"{status // 100}xx" if isinstance(status, int) and not isinstance(status, bool)
                             else "geçersiz"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["fixture_article"] = df["fixture_article"].astype("Int64")
    return df


# --------------------------------------------------------------------------------------
# Bağlam
# --------------------------------------------------------------------------------------
@dataclass
class AnalysisContext:
    paths: DatasetPaths
    data: dict
    schema: dict
    scenarios: list[dict]
    users: list[dict]
    articles: list[dict]
    routes: list[Route]
    csv_df: pd.DataFrame
    method_support: dict | None
    method_support_note: str
    pygoat: dict
    df: pd.DataFrame = field(default_factory=pd.DataFrame)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"{path} geçerli bir JSON değil: {exc}") from exc


def load_context(repo_root: Path | str, use_django: bool = True) -> AnalysisContext:
    """Tüm girdileri yükler ve zenginleştirilmiş senaryo tablosunu hazırlar."""
    paths = DatasetPaths(Path(repo_root).resolve())
    paths.check_required()
    data = _read_json(paths.scenarios_json)
    schema = _read_json(paths.schema_json)
    scenarios = data.get("scenarios", []) if isinstance(data, dict) else []
    users = _read_json(paths.users_fixture)
    articles = _read_json(paths.articles_fixture)
    routes = parse_routes(paths.config_urls.read_text(encoding="utf-8"),
                          paths.catalog_urls.read_text(encoding="utf-8"))
    csv_df = pd.read_csv(paths.scenarios_csv, dtype=str, keep_default_na=False, encoding="utf-8")
    if use_django:
        endpoints = [s["endpoint"] for s in scenarios if isinstance(s.get("endpoint"), str)]
        method_support, note = django_method_support(paths.sample_app, endpoints)
    else:
        method_support, note = None, "Django URL çözümlemesi kullanıcı tarafından devre dışı bırakıldı."
    ctx = AnalysisContext(
        paths=paths, data=data, schema=schema, scenarios=scenarios, users=users,
        articles=articles, routes=routes, csv_df=csv_df, method_support=method_support,
        method_support_note=note, pygoat=pygoat_inventory(paths.pygoat_dir),
    )
    ctx.df = annotate_scenarios(scenarios, users, articles, routes, method_support)
    return ctx
