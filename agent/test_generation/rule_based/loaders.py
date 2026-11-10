"""Girdi yükleyicileri — H3-04 / Issue #30.

Her girdi kendi JSON Schema'sıyla doğrulanır. Doğrulama hataları tanı (Diagnostic) olarak
döndürülür; hiçbir girdi sessizce düzeltilmez veya atlanmaz.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import (
    Code,
    Diagnostic,
    Endpoint,
    EndpointSummary,
    Operation,
    ReferenceCase,
    RouteParam,
    Severity,
)

PACKAGE_DIR = Path(__file__).resolve().parent
ENDPOINT_SCHEMA = PACKAGE_DIR / "schemas" / "endpoint_summary.schema.json"


class InputError(Exception):
    """Girdinin tamamı kullanılamaz durumda (ör. geçersiz JSON veya şema ihlali)."""

    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        super().__init__("; ".join(f"{d.code.value}: {d.message}" for d in diagnostics))


def read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError([Diagnostic(Code.INVALID_JSON, Severity.ERROR, f"Dosya bulunamadı: {path}")]) from exc
    except json.JSONDecodeError as exc:
        raise InputError([Diagnostic(Code.INVALID_JSON, Severity.ERROR, f"Geçersiz JSON: {path}",
                                     detail=f"satır {exc.lineno}, sütun {exc.colno}: {exc.msg}")]) from exc


def schema_errors(instance: Any, schema: dict, label: str) -> list[Diagnostic]:
    out = []
    for err in sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: [str(p) for p in e.path]):
        loc = "/".join(str(p) for p in err.path) or "<kök>"
        out.append(Diagnostic(Code.SCHEMA_VIOLATION, Severity.ERROR, f"{label}: şema ihlali ({loc})",
                              detail=err.message))
    return out


# --------------------------------------------------------------------------------------
# Endpoint özeti
# --------------------------------------------------------------------------------------
def parse_endpoint_summary(data: Any) -> EndpointSummary:
    schema = json.loads(ENDPOINT_SCHEMA.read_text(encoding="utf-8"))
    errors = schema_errors(data, schema, "endpoint özeti")
    if errors:
        raise InputError(errors)
    ids = [e["endpoint_id"] for e in data["endpoints"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise InputError([Diagnostic(Code.SCHEMA_VIOLATION, Severity.ERROR, "Yinelenen endpoint_id",
                                     detail=", ".join(dup))])
    endpoints = []
    for e in data["endpoints"]:
        declared = {p.split("}")[0] for p in e["path"].split("{")[1:]}
        params = tuple(RouteParam(p["name"], p["type"], p["source"]) for p in e["route_params"])
        if declared != {p.name for p in params}:
            raise InputError([Diagnostic(
                Code.MISSING_ROUTE_PARAM, Severity.ERROR, "Yol şablonu ile route_params uyuşmuyor",
                endpoint_id=e["endpoint_id"], detail=f"şablon={sorted(declared)}, route_params={[p.name for p in params]}")])
        endpoints.append(Endpoint(
            endpoint_id=e["endpoint_id"], path=e["path"], url_name=e["url_name"], route_params=params,
            view_name=e["view"]["name"], view_module=e["view"]["module"], view_type=e["view"]["type"],
            operations={m: Operation(m, o["action"], o["authentication_required"], o["object_permission"])
                        for m, o in e["operations"].items()},
            permissions=tuple(e["permissions"]), model=e["resource"]["model"],
            lookup_field=e["resource"]["lookup_field"], owner_field=e["resource"]["owner_field"],
            writable_fields=tuple(e["request"]["writable_fields"]), supported=e["supported"],
            unsupported_reason=e.get("unsupported_reason"), intentionally_insecure=e["intentionally_insecure"],
        ))
    t = data["target_app"]
    return EndpointSummary(
        schema_version=data["schema_version"], source_kind=data["source"]["kind"],
        ast_integration=data["source"]["ast_integration"], target_app=t["path"],
        settings_module=t["settings_module"], fixtures=tuple(t["fixtures"]),
        users_fixture=t["fixture_files"]["users"], resources_fixture=t["fixture_files"]["resources"],
        auth_mechanisms=tuple(data["authentication"]["mechanisms"]), endpoints=tuple(endpoints),
    )


def load_endpoint_summary(path: Path) -> EndpointSummary:
    return parse_endpoint_summary(read_json(path))


# --------------------------------------------------------------------------------------
# Bağımsız referans gereksinimleri + senaryo istek verisi
# --------------------------------------------------------------------------------------
def join_references(ground_truth: dict, scenarios: dict) -> tuple[list[ReferenceCase], list[Diagnostic]]:
    """Ground truth kayıtlarını H3-01 senaryolarıyla ``scenario_id`` üzerinden birleştirir.

    * Beklenen sonuç YALNIZCA ground truth'tan alınır (``expected_result.secure_status``).
    * Senaryodan yalnızca istek bilgisi alınır: endpoint, request_input, fixture_ref, category.
    * Senaryosu olmayan referans → MISSING_SCENARIO_DATA; referansı olmayan senaryo → MISSING_REFERENCE.
    * Metot/rol iki kaynakta farklıysa → REFERENCE_CONFLICT (senaryo üretilmez).
    """
    diags: list[Diagnostic] = []
    records = ground_truth.get("records", [])
    scen_list = scenarios.get("scenarios", [])
    scen: dict[str, dict] = {}
    for s in scen_list:
        sid = s.get("id")
        if sid in scen:
            diags.append(Diagnostic(Code.DUPLICATE_SCENARIO, Severity.ERROR, "Senaryo kimliği yinelenmiş",
                                    scenario_id=sid))
        scen[sid] = s
    seen: set[str] = set()
    cases: list[ReferenceCase] = []
    for r in records:
        sid = r.get("scenario_id")
        if sid in seen:
            diags.append(Diagnostic(Code.DUPLICATE_SCENARIO, Severity.ERROR, "Ground truth kaydı yinelenmiş",
                                    scenario_id=sid))
            continue
        seen.add(sid)
        s = scen.get(sid)
        if s is None:
            diags.append(Diagnostic(Code.MISSING_SCENARIO_DATA, Severity.ERROR,
                                    "Ground truth kaydının istek verisi (endpoint, girdi, fixture) bulunamadı",
                                    scenario_id=sid, detail="scenarios.json içinde bu kimlik yok"))
            continue
        conflicts = [f"{k}: ground_truth={r.get(k)!r}, scenarios={s.get(k)!r}"
                     for k in ("http_method", "user_role") if r.get(k) != s.get(k)]
        if conflicts:
            diags.append(Diagnostic(Code.REFERENCE_CONFLICT, Severity.ERROR,
                                    "Ground truth ile senaryo verisi çelişiyor", scenario_id=sid,
                                    detail="; ".join(conflicts)))
            continue
        fx = s.get("fixture_ref") if isinstance(s.get("fixture_ref"), dict) else {}
        exp = r.get("expected_result") or {}
        cases.append(ReferenceCase(
            scenario_id=sid, http_method=r.get("http_method"), user_role=r.get("user_role"),
            expected_status=exp.get("secure_status"), expected_behavior=exp.get("behavior", ""),
            label=r.get("label"), reference_source=r.get("reference_source"),
            validation_status=r.get("validation_status"), is_known_flaw=bool(r.get("is_known_flaw")),
            security_finding=r.get("security_finding"), endpoint=s.get("endpoint"),
            request_input=s.get("request_input"), fixture_user=fx.get("user"),
            fixture_resource=fx.get("article"), category=s.get("category"),
        ))
    for sid in scen:
        if sid not in seen:
            diags.append(Diagnostic(Code.MISSING_REFERENCE, Severity.ERROR,
                                    "Senaryo için bağımsız referans (ground truth) kaydı yok; beklenen sonuç "
                                    "uydurulmaz, test üretilmez", scenario_id=sid))
    return cases, diags


def load_references(ground_truth_path: Path, ground_truth_schema: Path, scenarios_path: Path,
                    scenarios_schema: Path) -> tuple[list[ReferenceCase], list[Diagnostic]]:
    gt, sc = read_json(ground_truth_path), read_json(scenarios_path)
    errors = (schema_errors(gt, read_json(ground_truth_schema), "ground_truth.json")
              + schema_errors(sc, read_json(scenarios_schema), "scenarios.json"))
    if errors:
        raise InputError(errors)
    return join_references(gt, sc)


def load_fixture_records(path: Path) -> list[dict]:
    data = read_json(path)
    if not isinstance(data, list):
        raise InputError([Diagnostic(Code.SCHEMA_VIOLATION, Severity.ERROR, f"Fixture listesi bekleniyordu: {path}")])
    return data
