"""Senaryo → test planı dönüşümü (kural tabanlı karar katmanı) — H3-04 / Issue #30.

Her referans senaryosu için ya tam bir ``TestPlan`` ya da üretimi durduran açıklayıcı tanı(lar)
döndürülür. Kurallar:

* Beklenen durum kodu: yalnızca bağımsız referanstaki ``secure_status`` (sabit varsayım yok).
* Endpoint: senaryodaki somut yol, endpoint özetindeki yol şablonlarıyla eşlenir; route parametreleri
  şablondan çıkarılır ve fixture referansıyla tutarlılığı doğrulanır.
* Rol ve sahiplik: rol etiketi fixture verisiyle (``is_staff``, kaynağın sahip alanı) doğrulanır;
  kullanıcı adından anlam çıkarılmaz.
* Yan etki kontrolü: HTTP semantiğinden (işlem türü + beklenen durumun başarı/ret sınıfı) türetilir;
  hedef uygulamanın kodundan türetilmez.
"""
from __future__ import annotations

import re
from typing import Any

from .contracts import (
    BODY_METHODS,
    CODE_STATUS,
    KNOWN_HTTP_METHODS,
    ROLES,
    SUPPORTED_AUTH_MECHANISMS,
    SUPPORTED_METHODS,
    SUPPORTED_STATUSES,
    SUPPORTED_VIEW_TYPES,
    Code,
    Diagnostic,
    Endpoint,
    EndpointSummary,
    ReferenceCase,
    ScenarioOutcome,
    Severity,
    Status,
    TestPlan,
)

_PARAM_RX = {
    "int": r"\d+",
    "str": r"[^/]+",
    "slug": r"[-a-zA-Z0-9_]+",
    "uuid": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
}


def path_regex(endpoint: Endpoint) -> re.Pattern[str]:
    types = {p.name: p.type for p in endpoint.route_params}
    parts = re.split(r"(\{[a-z_][a-z0-9_]*\})", endpoint.path)
    rx = ""
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            name = part[1:-1]
            rx += f"(?P<{name}>{_PARAM_RX[types[name]]})"
        else:
            rx += re.escape(part)
    return re.compile("^" + rx + "$")


def resolve_endpoint(path: str, endpoints: tuple[Endpoint, ...]) -> list[tuple[Endpoint, dict[str, Any]]]:
    matches = []
    for ep in endpoints:
        m = path_regex(ep).match(path)
        if m:
            kwargs: dict[str, Any] = {}
            for p in ep.route_params:
                raw = m.group(p.name)
                kwargs[p.name] = int(raw) if p.type == "int" else raw
            matches.append((ep, kwargs))
    return matches


def make_test_name(case: ReferenceCase) -> str:
    sid = re.sub(r"[^a-z0-9]+", "_", str(case.scenario_id).lower()).strip("_")
    return f"test_{sid}_{case.http_method.lower()}_{case.user_role}_{case.expected_status}"


def module_for(method: str) -> str:
    return f"test_{method.lower()}_generated.py"


def _err(code: Code, msg: str, case: ReferenceCase, endpoint_id: str | None = None, detail: str = "") -> Diagnostic:
    return Diagnostic(code, Severity.ERROR, msg, scenario_id=case.scenario_id, endpoint_id=endpoint_id, detail=detail)


def _warn(code: Code, msg: str, case: ReferenceCase, endpoint_id: str | None = None, detail: str = "") -> Diagnostic:
    return Diagnostic(code, Severity.WARNING, msg, scenario_id=case.scenario_id, endpoint_id=endpoint_id, detail=detail)


def _fail(case: ReferenceCase, diags: list[Diagnostic]) -> ScenarioOutcome:
    errors = [d for d in diags if d.severity is Severity.ERROR]
    return ScenarioOutcome(case.scenario_id, CODE_STATUS[errors[0].code], None, diags)


def actor_relation(username: str | None, resource_pk: Any, users: dict[str, dict], resources: dict[Any, dict],
                   owner_field: str | None) -> str:
    if username is None:
        return "anonim"
    user = users.get(username)
    if user is None:
        return "belirlenemez"
    if user["fields"].get("is_staff"):
        return "yonetici"
    if resource_pk is None:
        return "kimligi_dogrulanmis"
    res = resources.get(resource_pk)
    if res is None or owner_field is None:
        return "belirlenemez"
    return "kaynak_sahibi" if res["fields"].get(owner_field) == user["pk"] else "sahip_olmayan"


def side_effect_rule(action: str, method: str, method_allowed: bool, expected: int, exists: bool) -> str:
    success = 200 <= expected < 300
    mutating = method in BODY_METHODS or method == "DELETE"
    if not method_allowed:
        if not mutating:
            return "none"
        return "resource_unchanged" if exists else "count_unchanged"
    if action == "create":
        return "count_plus_one" if success else "count_unchanged"
    if action in ("update", "partial_update", "destroy"):
        if not exists:
            return "resource_still_absent"
        if not success:
            return "resource_unchanged"
        return {"update": "update_applied", "partial_update": "partial_update_applied",
                "destroy": "resource_deleted"}[action]
    return "none"  # list, retrieve, custom_action


def plan_case(case: ReferenceCase, summary: EndpointSummary, users: list[dict],
              resources: list[dict]) -> ScenarioOutcome:
    diags: list[Diagnostic] = []
    # 1) Metot
    method = case.http_method
    if not isinstance(method, str) or method.upper() not in KNOWN_HTTP_METHODS or method != method.upper():
        return _fail(case, [_err(Code.UNKNOWN_METHOD, "Geçersiz HTTP metodu", case, detail=f"http_method={method!r}")])
    if method not in SUPPORTED_METHODS:
        return _fail(case, [_err(Code.UNSUPPORTED_METHOD, "Bu baseline yalnızca GET, POST, PUT, PATCH, DELETE "
                                 "metotlarını destekler", case, detail=f"http_method={method}")])
    # 2) Beklenen durum kodu (yalnızca referanstan)
    status = case.expected_status
    if not isinstance(status, int) or isinstance(status, bool) or status not in SUPPORTED_STATUSES:
        return _fail(case, [_err(Code.INVALID_STATUS, "Referanstaki beklenen durum kodu geçersiz veya "
                                 "desteklenmiyor", case, detail=f"secure_status={status!r}; desteklenen="
                                 f"{sorted(SUPPORTED_STATUSES)}")])
    if case.user_role not in ROLES:
        return _fail(case, [_err(Code.UNKNOWN_ROLE, "Bilinmeyen kullanıcı rolü", case,
                                 detail=f"user_role={case.user_role!r}")])
    # 3) Endpoint çözümleme
    if not isinstance(case.endpoint, str) or not case.endpoint:
        return _fail(case, [_err(Code.MISSING_ENDPOINT_METADATA, "Senaryoda endpoint yolu yok", case)])
    matches = resolve_endpoint(case.endpoint, summary.endpoints)
    if not matches:
        return _fail(case, [_err(Code.UNRESOLVED_ROUTE, "Endpoint yolu endpoint özetindeki hiçbir şablona "
                                 "uymuyor", case, detail=f"endpoint={case.endpoint}; şablonlar="
                                 f"{[e.path for e in summary.endpoints]}")])
    if len(matches) > 1:
        return _fail(case, [_err(Code.AMBIGUOUS_ENDPOINT, "Endpoint yolu birden fazla şablona uyuyor", case,
                                 detail=", ".join(m[0].endpoint_id for m in matches))])
    ep, kwargs = matches[0]
    if not ep.supported:
        return _fail(case, [_err(Code.UNSUPPORTED_ENDPOINT, "Endpoint desteklenmiyor olarak işaretli", case,
                                 ep.endpoint_id, ep.unsupported_reason or "")])
    if ep.view_type not in SUPPORTED_VIEW_TYPES:
        return _fail(case, [_err(Code.UNSUPPORTED_VIEW, "View türü bu baseline tarafından desteklenmiyor "
                                 "(yalnızca DRF ViewSet/APIView/GenericAPIView)", case, ep.endpoint_id,
                                 f"view={ep.view_module}.{ep.view_name} ({ep.view_type})")])
    if case.fixture_user is not None:
        bad = [m for m in summary.auth_mechanisms if m not in SUPPORTED_AUTH_MECHANISMS]
        if bad:
            return _fail(case, [_err(Code.UNSUPPORTED_AUTH, "Kimlik doğrulama mekanizması desteklenmiyor", case,
                                     ep.endpoint_id, f"mekanizmalar={bad}")])
    # 4) Route parametresi ↔ fixture referansı
    for p in ep.route_params:
        if p.source == "fixture_ref.article":
            if case.fixture_resource is None:
                return _fail(case, [_err(Code.MISSING_ROUTE_PARAM, f"'{p.name}' route parametresi için fixture "
                                         "kaynak referansı yok", case, ep.endpoint_id)])
            if case.fixture_resource != kwargs[p.name]:
                return _fail(case, [_err(Code.ROUTE_PARAM_MISMATCH, "Endpoint'teki parametre fixture "
                                         "referansıyla uyuşmuyor", case, ep.endpoint_id,
                                         f"{p.name}={kwargs[p.name]!r}, fixture_ref.article={case.fixture_resource!r}")])
    if not ep.route_params and case.fixture_resource is not None:
        diags.append(_warn(Code.ROUTE_PARAM_MISMATCH, "Koleksiyon ucunda kaynak referansı verilmiş; yok sayıldı",
                           case, ep.endpoint_id, f"fixture_ref.article={case.fixture_resource!r}"))
    # 5) Kullanıcı ve sahiplik (fixture verisinden)
    model_label = ep.model.lower()
    users_by_name = {u["fields"]["username"]: u for u in users}
    res_by_pk = {r["pk"]: r for r in resources if str(r.get("model", "")).lower() == model_label}
    username = case.fixture_user
    if username is not None and username not in users_by_name:
        return _fail(case, [_err(Code.MISSING_FIXTURE_USER, "Fixture kullanıcısı bulunamadı", case, ep.endpoint_id,
                                 f"user={username!r}; mevcut={sorted(users_by_name)}")])
    lookup = kwargs.get(ep.route_params[0].name) if ep.route_params else None
    relation = actor_relation(username, lookup, users_by_name, res_by_pk, ep.owner_field)
    role = case.user_role
    mismatch = None
    if (role == "anonymous") != (username is None):
        mismatch = f"user_role={role}, fixture_ref.user={username!r}"
    elif role == "admin" and relation != "yonetici":
        mismatch = f"admin rolü, is_staff olmayan kullanıcıyla ({username})"
    elif role in ("user", "owner") and relation == "yonetici":
        mismatch = f"{role} rolü, is_staff kullanıcıyla ({username})"
    elif role == "owner" and relation == "sahip_olmayan":
        mismatch = f"owner rolü, kaynağın sahibi olmayan kullanıcıyla ({username}, kaynak {lookup})"
    elif role == "user" and relation == "kaynak_sahibi":
        mismatch = f"user rolü, kaynağın sahibiyle ({username}, kaynak {lookup})"
    if mismatch:
        return _fail(case, [_err(Code.ROLE_MISMATCH, "Rol etiketi fixture verisiyle çelişiyor", case,
                                 ep.endpoint_id, mismatch)])
    if role == "owner" and relation in ("kimligi_dogrulanmis", "belirlenemez"):
        why = "hedef nesne yok (koleksiyon ucu)" if lookup is None else f"kaynak {lookup} fixture'da yok"
        diags.append(_warn(Code.OWNERSHIP_UNVERIFIABLE, "owner rolünün sahipliği fixture'dan doğrulanamadı; "
                           "test kimliği doğrulanmış kullanıcı olarak üretildi", case, ep.endpoint_id, why))
    # 6) İstek gövdesi
    payload = case.request_input
    if payload is not None and not isinstance(payload, dict):
        return _fail(case, [_err(Code.INVALID_PAYLOAD, "request_input bir JSON nesnesi veya null olmalı", case,
                                 ep.endpoint_id, f"tip={type(payload).__name__}")])
    if payload and method not in BODY_METHODS:
        return _fail(case, [_err(Code.INVALID_PAYLOAD, f"{method} isteği için gövde tanımlanmış", case,
                                 ep.endpoint_id, f"request_input={payload!r}")])
    if payload:
        unknown = sorted(set(payload) - set(ep.writable_fields))
        if unknown:
            diags.append(_warn(Code.UNKNOWN_PAYLOAD_FIELD, "Gövdede endpoint özetinde yazılabilir olarak "
                               "tanımlanmamış alan var; alan gönderilir ancak yan etki kontrolüne katılmaz",
                               case, ep.endpoint_id, f"alanlar={unknown}"))
    # 7) İşlem ve yan etki kuralı
    op = ep.operations.get(method)
    method_allowed = op is not None
    action = op.action if op else "method_not_allowed"
    if not method_allowed:
        diags.append(_warn(Code.METHOD_NOT_IN_OPERATIONS, f"{method} bu endpoint'in işlemleri arasında yok; "
                           "beklenen sonuç referanstan alınır", case, ep.endpoint_id,
                           f"işlemler={sorted(ep.operations)}; referans={status}"))
    exists = lookup is not None and lookup in res_by_pk
    if case.is_known_flaw and (case.security_finding or {}).get("deviation_kind") == "content":
        diags.append(_warn(Code.CONTENT_ASSERTION_UNSUPPORTED, "Referanstaki güvenlik beklentisi içerik "
                           "düzeyinde ve makine-okunur değil; yalnızca durum kodu doğrulanır, bilinen kusur bu "
                           "testle tespit EDİLEMEZ", case, ep.endpoint_id,
                           (case.security_finding or {}).get("expected_security_state", "")))
    plan = TestPlan(
        scenario_id=case.scenario_id, test_name=make_test_name(case), module=module_for(method),
        http_method=method, endpoint_id=ep.endpoint_id, url_name=ep.url_name, url_kwargs=kwargs,
        path=case.endpoint, action=action, method_allowed=method_allowed, user_role=role, username=username,
        actor_relation=relation, payload=payload, expected_status=status, expected_behavior=case.expected_behavior,
        reference_source=case.reference_source, validation_status=case.validation_status, category=case.category,
        model=ep.model, lookup_value=lookup, resource_exists=exists, writable_fields=ep.writable_fields,
        is_known_flaw=case.is_known_flaw, security_finding=case.security_finding,
        intentionally_insecure_endpoint=ep.intentionally_insecure,
        side_effect_check=side_effect_rule(action, method, method_allowed, status, exists),
        warnings=list(diags),
    )
    return ScenarioOutcome(case.scenario_id, Status.GENERATED, plan, diags)
