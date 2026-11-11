"""Baseline artefaktlarını senaryo düzeyinde, karşılaştırılabilir biçime getirme — H3-06 / Issue #32.

İki baseline farklı dosya düzeni kullanır (H3-04: HTTP yöntemi başına bir modül; H3-05: senaryo başına bir
modül). Adil karşılaştırma için her ikisi de aynı yapıya indirgenir: senaryo başına **tek fonksiyonlu**, tek
başına çalıştırılabilir bir test modülü (``Artifact.source``) ve onun ihtiyaç duyduğu destek dosyaları.

* Test kodunda hiçbir değişiklik yapılmaz (onarım yok). H3-04 için modül başlığı (importlar, ``pytestmark``)
  ile senaryonun fonksiyonu kaynaktan aynen kopyalanır; H3-05 için ham model yanıtından H3-05'in kendi
  ``extract_code`` işleviyle ayıklanan kod kullanılır (ilk geçiş çıktısı).
* Senaryo kimliği ile eşleşen artefakt yoksa ``NO_ARTIFACT``; birden fazla ise ``DUPLICATE_ARTIFACT``.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import manifest as mf

SAFE_HOSTS = ("testserver", "localhost", "127.0.0.1")
FORBIDDEN_MODULES = ("requests", "httpx", "urllib", "urllib3", "aiohttp", "socket", "http.client",
                     "subprocess", "ftplib", "smtplib", "paramiko")
_URL = re.compile(r"^(?:https?|ftp)://([^/:?#]+)", re.IGNORECASE)


@dataclass
class Artifact:
    scenario_id: str
    baseline: str
    origin: str                      # depo içi kaynak yol (izlenebilirlik)
    source: str                      # çalıştırılacak tek-senaryo modülü
    function: str | None             # beklenen test fonksiyonu adı
    support_files: dict[str, Path] = field(default_factory=dict)
    generation_status: str = "GENERATED"
    notes: list[str] = field(default_factory=list)


def sid_token(scenario_id: str) -> str:
    return scenario_id.lower().replace("-", "_")


def syntax_error(source: str) -> str | None:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        return f"SyntaxError: {exc.msg} (satır {exc.lineno})"
    return None


def safety_violations(source: str) -> list[str]:
    """Kontrollü hedef dışında ağ/süreç erişimi içeren testleri çalıştırmadan önce tespit eder."""
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for n in names:
            if any(n == m or n.startswith(m + ".") for m in FORBIDDEN_MODULES):
                found.append(f"yasaklı içe aktarma: {n}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            m = _URL.match(node.value.strip())
            if m and m.group(1).lower() not in SAFE_HOSTS:
                found.append(f"dış hedef URL: {node.value.strip()[:80]}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and \
                node.func.attr in ("system", "popen", "execv", "execve", "spawnv"):
            found.append(f"süreç çalıştırma: os.{node.func.attr}")
    return found


# --------------------------------------------------------------------------- H3-04 (kural tabanlı)

def _module_header(tree: ast.Module, source: str) -> str:
    """İlk test fonksiyonuna kadarki modül düzeyi ifadeler (docstring hariç importlar, pytestmark)."""
    lines = source.splitlines()
    parts = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            break
        if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            continue  # modül docstring'i
        parts.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
    return "\n".join(parts)


def rule_based_artifacts(scenario_ids: list[str], base: Path = mf.H304) -> dict[str, list[Artifact]]:
    gen_dir = base / "generated_tests"
    report = mf.load_json(base / "reports" / "generation_report.json")
    status = {s["scenario_id"]: s for s in report["scenarios"]}
    support = {"conftest.py": gen_dir / "conftest.py", "h304_support.py": gen_dir / "h304_support.py"}
    out: dict[str, list[Artifact]] = {sid: [] for sid in scenario_ids}
    modules: dict[Path, tuple[str, ast.Module | None, str | None]] = {}
    for path in sorted(gen_dir.glob("test_*_generated.py")):
        src = path.read_text(encoding="utf-8")
        err = syntax_error(src)
        modules[path] = (src, None if err else ast.parse(src), err)
    for sid in scenario_ids:
        rec = status.get(sid)
        if rec is None or rec.get("status") != "GENERATED":
            continue  # NO_ARTIFACT (üretilmedi/desteklenmedi)
        prefix = f"test_{sid_token(sid)}_"
        for path, (src, tree, err) in modules.items():
            if tree is None:
                if prefix in src:
                    out[sid].append(Artifact(sid, "rule_based", mf.rel(path), src, rec.get("test_name"),
                                             dict(support), notes=[err]))
                continue
            header = _module_header(tree, src)
            lines = src.splitlines()
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(prefix):
                    start = min([d.lineno for d in node.decorator_list] + [node.lineno])
                    body = "\n".join(lines[start - 1:node.end_lineno])
                    out[sid].append(Artifact(sid, "rule_based", f"{mf.rel(path)}::{node.name}",
                                             f"{header}\n\n\n{body}\n", node.name, dict(support)))
    return out


# --------------------------------------------------------------------------- H3-05 (LLM)

def llm_artifacts(scenario_ids: list[str], base: Path = mf.H305) -> dict[str, list[Artifact]]:
    from agent.test_generation.llm.extract import extract_code

    report = mf.load_json(base / "reports" / "generation_report.json")
    by_sid: dict[str, list[dict]] = {}
    for r in report["records"]:
        by_sid.setdefault(r["scenario_id"], []).append(r)
    support = {"conftest.py": base / "generated_tests" / "conftest.py"}
    out: dict[str, list[Artifact]] = {sid: [] for sid in scenario_ids}
    for sid in scenario_ids:
        for r in by_sid.get(sid, []):
            raw_path = base / "raw_responses" / f"{sid}.txt"
            if not raw_path.exists():
                continue  # ham yanıt yoksa artefakt doğrulanamaz → NO_ARTIFACT
            code = extract_code(raw_path.read_text(encoding="utf-8"))
            if not code.strip():
                continue  # boş model çıktısı → NO_ARTIFACT
            out[sid].append(Artifact(sid, "llm", mf.rel(raw_path), code.rstrip("\n") + "\n",
                                     r.get("test_name") or f"test_{sid_token(sid)}", dict(support),
                                     generation_status=r.get("status", "UNKNOWN")))
    return out


ADAPTERS = {"rule_based": rule_based_artifacts, "llm": llm_artifacts}
