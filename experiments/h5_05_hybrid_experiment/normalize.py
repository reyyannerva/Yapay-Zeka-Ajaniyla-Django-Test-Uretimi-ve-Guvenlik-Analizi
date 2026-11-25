"""Aday testleri anlamsal imzaya indirgeme — H5-05 / Issue #43.

Bir aday (kural tabanlı veya LLM) tek-senaryo test modülüdür. ``signature`` modülü AST üzerinden
çözümler ve şu alanları çıkarır (kod ÇALIŞTIRILMAZ):

* ``http_method``: ``api_client.<get|post|put|patch|delete>(...)`` çağrısı
* ``endpoint``: ``reverse('ad', kwargs={...})`` → endpoint özetindeki yol şablonu ile somut yol; ya da
  doğrudan metin URL
* ``auth``/``actor``: ``force_authenticate(user=User.objects.get(username='x'))`` (değişken üzerinden de)
* ``payload``: istek gövdesi (sözlük sabiti veya aynı fonksiyondaki atama)
* ``preconditions``: kullanılan fixture'lar (``seeded_db`` vb.)
* ``expected_status``: ``assert response.status_code == N``
* ``assertion_kinds``: status / route / side_effect / body

İmza, yinelenen ve çelişen adayları belirlemek için kullanılır; ground truth etiketlerine dokunmaz.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field

HTTP_CALLS = ("get", "post", "put", "patch", "delete")


@dataclass
class Signature:
    parse_ok: bool
    test_functions: list[str] = field(default_factory=list)
    http_method: str | None = None
    endpoint: str | None = None
    route_name: str | None = None
    auth: str | None = None             # "authenticated" | "anonymous"
    actor: str | None = None            # kullanıcı adı (biliniyorsa)
    payload: object = None
    preconditions: list[str] = field(default_factory=list)
    expected_status: int | None = None
    assertion_kinds: list[str] = field(default_factory=list)
    request_count: int = 0
    error: str | None = None

    def key(self) -> tuple:
        """Yineleme anahtarı: aynı istek + aynı beklenti → aynı test niyeti."""
        return (self.http_method, self.endpoint, self.auth, self.actor, self.expected_status)

    def to_json(self) -> dict:
        d = asdict(self)
        d["key_sha256"] = hashlib.sha256(json.dumps(list(self.key()), ensure_ascii=False).encode()).hexdigest()
        return d


def _literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None


def _str_const(node) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _username_from(node, assigns: dict[str, ast.AST]) -> str | None:
    if isinstance(node, ast.Name) and node.id in assigns:
        node = assigns[node.id]
    if isinstance(node, ast.Call):
        for kw in node.keywords:
            if kw.arg == "username":
                return _str_const(kw.value)
        for a in node.args:
            s = _str_const(a)
            if s:
                return s
    return None


def _resolve_reverse(call: ast.Call, routes: dict[str, str]) -> tuple[str | None, str | None]:
    name = _str_const(call.args[0]) if call.args else None
    kwargs = {}
    for kw in call.keywords:
        if kw.arg == "kwargs":
            kwargs = _literal(kw.value) or {}
        elif kw.arg == "args":
            args = _literal(kw.value) or []
            kwargs = {"pk": args[0]} if args else {}
    tpl = routes.get(name or "")
    if tpl is None:
        return name, None
    path = tpl
    for k, v in kwargs.items():
        path = path.replace("{" + str(k) + "}", str(v))
    return name, (None if "{" in path else path)


def signature(source: str, routes: dict[str, str]) -> Signature:
    """``routes``: endpoint özetinden ``url_name → yol şablonu`` eşlemesi."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return Signature(parse_ok=False, error=f"SyntaxError: {exc.msg} (satır {exc.lineno})")
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and n.name.startswith("test_")]
    sig = Signature(parse_ok=True, test_functions=[f.name for f in funcs])
    if not funcs:
        sig.error = "test fonksiyonu yok"
        return sig
    kinds: set[str] = set()
    for fn in funcs:
        sig.preconditions = sorted({a.arg for a in fn.args.args} | set(sig.preconditions))
        assigns: dict[str, ast.AST] = {}
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                assigns[node.targets[0].id] = node.value
        auth_seen = False
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            attr = node.func.attr
            if attr == "force_authenticate":
                user = next((kw.value for kw in node.keywords if kw.arg == "user"), node.args[0] if node.args else None)
                if not (isinstance(user, ast.Constant) and user.value is None):
                    auth_seen = True
                    sig.actor = sig.actor or _username_from(user, assigns)
            elif attr == "login" or attr == "credentials":
                auth_seen = True
            elif attr in HTTP_CALLS and isinstance(node.func.value, ast.Name) and "client" in node.func.value.id:
                sig.request_count += 1
                if sig.http_method is None:
                    sig.http_method = attr.upper()
                    url = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "path"), None)
                    if isinstance(url, ast.Name) and url.id in assigns:
                        url = assigns[url.id]
                    if isinstance(url, ast.Call) and getattr(url.func, "id", getattr(url.func, "attr", None)) == "reverse":
                        sig.route_name, sig.endpoint = _resolve_reverse(url, routes)
                    elif _str_const(url):
                        sig.endpoint = _str_const(url)
                    body = node.args[1] if len(node.args) > 1 else next(
                        (k.value for k in node.keywords if k.arg == "data"), None)
                    if isinstance(body, ast.Name) and body.id in assigns:
                        body = assigns[body.id]
                    sig.payload = _literal(body) if body is not None else None
        sig.auth = "authenticated" if auth_seen else "anonymous"
        derived = _response_derived(fn)
        for node in ast.walk(fn):
            if not isinstance(node, ast.Assert):
                continue
            text = ast.unparse(node.test)
            if "status_code" in text:
                kinds.add("status")
                t = node.test
                if sig.expected_status is None and isinstance(t, ast.Compare) and len(t.ops) == 1 \
                        and isinstance(t.ops[0], ast.Eq):
                    for side in (t.left, t.comparators[0]):
                        v = _literal(side)
                        if isinstance(v, int):
                            sig.expected_status = v
            elif "url ==" in text or "route" in text:
                kinds.add("route")
            elif any(s in text for s in ("count", "before", "after", "snapshot", "exists")):
                kinds.add("side_effect")
            elif any(s in text for s in ("data", "json", "content")) or \
                    any(isinstance(n, ast.Name) and n.id in derived for n in ast.walk(node.test)):
                kinds.add("body")
            else:
                kinds.add("other")
    sig.assertion_kinds = sorted(kinds)
    return sig


def _response_derived(fn) -> set[str]:
    """``response`` nesnesinden türeyen yerel adlar (atama ve for döngüsü hedefleri), sabit noktaya kadar."""
    names = {"response"}
    changed = True
    while changed:
        changed = False
        for node in ast.walk(fn):
            pairs = []
            if isinstance(node, ast.Assign):
                pairs = [(t, node.value) for t in node.targets]
            elif isinstance(node, (ast.For, ast.comprehension)):
                pairs = [(node.target, node.iter)]
            for target, value in pairs:
                if any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(value)):
                    for t in ast.walk(target):
                        if isinstance(t, ast.Name) and t.id not in names:
                            names.add(t.id)
                            changed = True
    names.discard("response")
    return names


def routes_from_endpoint_summary(summary: dict) -> dict[str, str]:
    return {e["url_name"]: e["path"] for e in summary["endpoints"]}
