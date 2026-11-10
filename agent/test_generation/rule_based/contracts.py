"""Kural tabanlı Pytest üreticisinin veri sözleşmeleri — H3-04 / Issue #30.

Üretici üç girdiyle çalışır:
  1. Endpoint özeti (``schemas/endpoint_summary.schema.json``) — AST analizinin ileride üreteceği format.
  2. Bağımsız referans gereksinimleri (H3-03 ``ground_truth.json``) — BEKLENEN sonuç buradan alınır.
  3. Senaryo istek verisi (H3-01 ``scenarios.json``) — endpoint, örnek girdi ve fixture referansları.

Beklenen HTTP durum kodu hiçbir koşulda role, metoda veya hedef uygulamanın gözlemlenen
davranışına göre türetilmez; yalnızca ``ground_truth.json`` içindeki ``secure_status`` kullanılır.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

SUPPORTED_METHODS: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE")
KNOWN_HTTP_METHODS: frozenset[str] = frozenset(SUPPORTED_METHODS + ("HEAD", "OPTIONS", "TRACE", "CONNECT"))
SUPPORTED_STATUSES: frozenset[int] = frozenset({200, 201, 204, 400, 401, 403, 404, 405})
SUPPORTED_VIEW_TYPES: frozenset[str] = frozenset({"ViewSet", "APIView", "GenericAPIView"})
SUPPORTED_AUTH_MECHANISMS: frozenset[str] = frozenset(
    {"BasicAuthentication", "SessionAuthentication", "TokenAuthentication"})
ROLES: frozenset[str] = frozenset({"anonymous", "user", "owner", "admin"})
BODY_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH"})


class Status(str, Enum):
    """Senaryo düzeyinde üretim sonucu."""

    GENERATED = "GENERATED"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REFERENCE = "MISSING_REFERENCE"
    GENERATION_ERROR = "GENERATION_ERROR"


class Severity(str, Enum):
    ERROR = "error"      # senaryo üretilmez
    WARNING = "warning"  # senaryo üretilir; kısıt açıkça raporlanır


class Code(str, Enum):
    """Tanı kodları. Her kod tek bir anlam taşır ve raporda Türkçe açıklamayla birlikte gösterilir."""

    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    INVALID_JSON = "INVALID_JSON"
    MISSING_REFERENCE = "MISSING_REFERENCE"
    MISSING_SCENARIO_DATA = "MISSING_SCENARIO_DATA"
    REFERENCE_CONFLICT = "REFERENCE_CONFLICT"
    UNKNOWN_METHOD = "UNKNOWN_METHOD"
    UNSUPPORTED_METHOD = "UNSUPPORTED_METHOD"
    INVALID_STATUS = "INVALID_STATUS"
    UNRESOLVED_ROUTE = "UNRESOLVED_ROUTE"
    AMBIGUOUS_ENDPOINT = "AMBIGUOUS_ENDPOINT"
    MISSING_ENDPOINT_METADATA = "MISSING_ENDPOINT_METADATA"
    UNSUPPORTED_ENDPOINT = "UNSUPPORTED_ENDPOINT"
    UNSUPPORTED_VIEW = "UNSUPPORTED_VIEW"
    UNSUPPORTED_AUTH = "UNSUPPORTED_AUTH"
    MISSING_ROUTE_PARAM = "MISSING_ROUTE_PARAM"
    ROUTE_PARAM_MISMATCH = "ROUTE_PARAM_MISMATCH"
    MISSING_FIXTURE_USER = "MISSING_FIXTURE_USER"
    UNKNOWN_ROLE = "UNKNOWN_ROLE"
    ROLE_MISMATCH = "ROLE_MISMATCH"
    OWNERSHIP_UNVERIFIABLE = "OWNERSHIP_UNVERIFIABLE"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    UNKNOWN_PAYLOAD_FIELD = "UNKNOWN_PAYLOAD_FIELD"
    DUPLICATE_SCENARIO = "DUPLICATE_SCENARIO"
    CONTENT_ASSERTION_UNSUPPORTED = "CONTENT_ASSERTION_UNSUPPORTED"
    METHOD_NOT_IN_OPERATIONS = "METHOD_NOT_IN_OPERATIONS"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    DUPLICATE_TEST_NAME = "DUPLICATE_TEST_NAME"
    TRACEABILITY_ERROR = "TRACEABILITY_ERROR"


# Hata kodu → senaryo durumu eşlemesi (uyarılar senaryoyu durdurmaz)
CODE_STATUS: dict[Code, Status] = {
    Code.SCHEMA_VIOLATION: Status.INVALID_INPUT,
    Code.INVALID_JSON: Status.INVALID_INPUT,
    Code.MISSING_REFERENCE: Status.MISSING_REFERENCE,
    Code.MISSING_SCENARIO_DATA: Status.MISSING_REFERENCE,
    Code.REFERENCE_CONFLICT: Status.INVALID_INPUT,
    Code.UNKNOWN_METHOD: Status.INVALID_INPUT,
    Code.UNSUPPORTED_METHOD: Status.UNSUPPORTED,
    Code.INVALID_STATUS: Status.INVALID_INPUT,
    Code.UNRESOLVED_ROUTE: Status.INVALID_INPUT,
    Code.AMBIGUOUS_ENDPOINT: Status.INVALID_INPUT,
    Code.MISSING_ENDPOINT_METADATA: Status.INVALID_INPUT,
    Code.UNSUPPORTED_ENDPOINT: Status.UNSUPPORTED,
    Code.UNSUPPORTED_VIEW: Status.UNSUPPORTED,
    Code.UNSUPPORTED_AUTH: Status.UNSUPPORTED,
    Code.MISSING_ROUTE_PARAM: Status.INVALID_INPUT,
    Code.ROUTE_PARAM_MISMATCH: Status.INVALID_INPUT,
    Code.MISSING_FIXTURE_USER: Status.INVALID_INPUT,
    Code.UNKNOWN_ROLE: Status.INVALID_INPUT,
    Code.ROLE_MISMATCH: Status.INVALID_INPUT,
    Code.INVALID_PAYLOAD: Status.INVALID_INPUT,
    Code.DUPLICATE_SCENARIO: Status.INVALID_INPUT,
    Code.SYNTAX_ERROR: Status.GENERATION_ERROR,
    Code.DUPLICATE_TEST_NAME: Status.GENERATION_ERROR,
    Code.TRACEABILITY_ERROR: Status.GENERATION_ERROR,
}


@dataclass(frozen=True)
class Diagnostic:
    code: Code
    severity: Severity
    message: str
    scenario_id: str | None = None
    endpoint_id: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "severity": self.severity.value, "scenario_id": self.scenario_id,
                "endpoint_id": self.endpoint_id, "message": self.message, "detail": self.detail}


@dataclass(frozen=True)
class Operation:
    method: str
    action: str
    authentication_required: bool
    object_permission: str


@dataclass(frozen=True)
class RouteParam:
    name: str
    type: str
    source: str


@dataclass(frozen=True)
class Endpoint:
    endpoint_id: str
    path: str
    url_name: str
    route_params: tuple[RouteParam, ...]
    view_name: str
    view_module: str
    view_type: str
    operations: dict[str, Operation]
    permissions: tuple[str, ...]
    model: str
    lookup_field: str
    owner_field: str | None
    writable_fields: tuple[str, ...]
    supported: bool
    unsupported_reason: str | None
    intentionally_insecure: bool


@dataclass(frozen=True)
class EndpointSummary:
    schema_version: str
    source_kind: str
    ast_integration: bool
    target_app: str
    settings_module: str
    fixtures: tuple[str, ...]
    users_fixture: str
    resources_fixture: str
    auth_mechanisms: tuple[str, ...]
    endpoints: tuple[Endpoint, ...]


@dataclass(frozen=True)
class ReferenceCase:
    """Ground truth kaydı + H3-01 senaryosunun istek verisi (scenario_id ile birleştirilmiş)."""

    scenario_id: str
    http_method: str
    user_role: str
    expected_status: Any
    expected_behavior: str
    label: str
    reference_source: str
    validation_status: str
    is_known_flaw: bool
    security_finding: dict | None
    endpoint: Any
    request_input: Any
    fixture_user: Any
    fixture_resource: Any
    category: str | None


@dataclass
class TestPlan:
    """Üretilecek tek bir testin tam tanımı (üretim kararlarının izlenebilir kaydı)."""

    __test__ = False  # pytest bu sınıfı test sınıfı olarak toplamasın

    scenario_id: str
    test_name: str
    module: str
    http_method: str
    endpoint_id: str
    url_name: str
    url_kwargs: dict[str, Any]
    path: str
    action: str
    method_allowed: bool
    user_role: str
    username: str | None
    actor_relation: str
    payload: Any
    expected_status: int
    expected_behavior: str
    reference_source: str
    validation_status: str
    category: str | None
    model: str
    lookup_value: Any
    resource_exists: bool
    writable_fields: tuple[str, ...]
    is_known_flaw: bool
    security_finding: dict | None
    intentionally_insecure_endpoint: bool
    side_effect_check: str
    warnings: list[Diagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["warnings"] = [w.to_dict() for w in self.warnings]
        d["writable_fields"] = list(self.writable_fields)
        return d


@dataclass
class ScenarioOutcome:
    scenario_id: str
    status: Status
    plan: TestPlan | None
    diagnostics: list[Diagnostic]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "test_name": self.plan.test_name if self.plan else None,
            "module": self.plan.module if self.plan else None,
            "http_method": self.plan.http_method if self.plan else None,
            "endpoint_id": self.plan.endpoint_id if self.plan else None,
            "expected_status": self.plan.expected_status if self.plan else None,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }
