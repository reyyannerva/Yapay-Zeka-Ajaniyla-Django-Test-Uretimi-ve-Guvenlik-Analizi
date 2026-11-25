"""OpenAPI şeması ↔ gerçek API davranışı sözleşme testleri — H4-05 / Issue #37.

Testler yalnızca dokümantasyon metnini değil, şemanın gerçek API ile tutarlılığını doğrular:
gerçek yanıtlar OpenAPI bileşen şemalarına karşı JSON Schema ile doğrulanır, belgelenen hata örnekleri
gerçek isteklerle birebir karşılaştırılır, korumalı/herkese açık işaretlemesi kimliksiz isteklerle sınanır
ve depodaki dışa aktarılmış şemanın güncel olduğu denetlenir.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import jsonschema
import pytest
import yaml
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from drf_spectacular.drainage import GENERATOR_STATS
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.projects.archive import ArchiveLimits

from .zipkit import build_zip, django_files, valid_django_zip

pytestmark = pytest.mark.django_db

DOCS = Path(__file__).resolve().parents[3] / "docs" / "api"
PASSWORD = "Gizli-Parola-123"
METHODS = ("get", "post", "put", "patch", "delete")
DEFAULT_LIMITS = {k: getattr(ArchiveLimits(), k) for k in (
    "max_upload_bytes", "max_total_uncompressed_bytes", "max_member_bytes", "max_entries", "max_depth",
    "max_path_length", "max_compression_ratio", "ratio_check_min_bytes")}


@pytest.fixture(autouse=True)
def _isolate(settings, tmp_path):
    settings.PROJECT_ARCHIVE_ROOT = tmp_path / "arşiv deposu"
    settings.PROJECT_UPLOAD_LIMITS = dict(DEFAULT_LIMITS)  # dışa aktarılan şema varsayılan sınırlarla üretilir
    settings.API_DOCS_PUBLIC = True
    cache.clear()
    yield
    cache.clear()


def generate() -> dict:
    GENERATOR_STATS.reset()
    schema = SchemaGenerator().get_schema(request=None, public=True)
    return json.loads(json.dumps(schema, default=str))


@pytest.fixture(scope="module")
def schema(django_db_blocker):
    with django_db_blocker.unblock():
        return generate()


def operations(schema):
    for path, item in schema["paths"].items():
        for method, op in item.items():
            if method in METHODS:
                yield path, method, op


# ---------------------------------------------------------------------- JSON Schema yardımcıları

def to_jsonschema(node, components):
    """OpenAPI 3.0 alt şemasını ($ref, nullable, readOnly) JSON Schema'ya çevirir."""
    if isinstance(node, list):
        return [to_jsonschema(n, components) for n in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        return to_jsonschema(components[node["$ref"].rsplit("/", 1)[-1]], components)
    out = {k: to_jsonschema(v, components) for k, v in node.items()
           if k not in ("nullable", "readOnly", "writeOnly", "example", "format", "description")}
    if node.get("nullable"):
        out = {"anyOf": [out, {"type": "null"}]}
    return out


def assert_matches(schema, component: str, instance):
    js = to_jsonschema({"$ref": f"#/components/schemas/{component}"}, schema["components"]["schemas"])
    jsonschema.validate(instance, js)


def response_schema(schema, path, method, status):
    content = schema["paths"][path][method]["responses"][str(status)].get("content", {})
    return content.get("application/json", {}).get("schema")


def examples_of(schema, path, method, status) -> dict:
    content = schema["paths"][path][method]["responses"][str(status)].get("content", {})
    return {e["summary"]: e["value"] for e in content.get("application/json", {}).get("examples", {}).values()}


# ---------------------------------------------------------------------- istemciler ve veri

@pytest.fixture
def alice(django_user_model):
    return django_user_model.objects.create_user(username="alice", password=PASSWORD, email="alice@example.test")


@pytest.fixture
def api(alice):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(alice)}")
    return c


@pytest.fixture
def project_id(api):
    resp = api.post("/api/projects/", {"name": "Mağaza API", "archive": SimpleUploadedFile("magaza.zip", valid_django_zip())},
                    format="multipart")
    assert resp.status_code == 201
    return resp.json()["id"]


SPEC = {"schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": "DELETE",
        "expected_status_by_role": {"anonymous": 401, "staff": 204}}


def requirement_payload(project_id, **kw):
    data = {"project": project_id, "requirement_code": "ACC-ORDERS-DELETE", "category": "ACCESS_RULE",
            "title": "Sipariş silme", "expected_result": "anonim 401, staff 204", "specification": SPEC}
    data.update(kw)
    return data


# ====================================================================== şemanın kendisi

def test_schema_is_valid_openapi_and_generated_without_warnings(schema):
    validate_schema(schema)
    assert schema["openapi"].startswith("3.0")
    generate()
    assert not GENERATOR_STATS._warn_cache and not GENERATOR_STATS._error_cache


def test_operation_ids_are_unique(schema):
    ids = [op["operationId"] for _, _, op in operations(schema)]
    assert len(ids) == len(set(ids))


def test_all_refs_resolve(schema):
    text = json.dumps(schema)
    for ref in set(re.findall(r'"\$ref": "#/components/schemas/([^"]+)"', text)):
        assert ref in schema["components"]["schemas"], ref


EXPECTED_OPERATIONS = {
    ("/api/auth/login/", "post"), ("/api/auth/refresh/", "post"), ("/api/auth/logout/", "post"),
    ("/api/auth/me/", "get"), ("/api/auth/password-reset/", "post"), ("/api/auth/password-reset/confirm/", "post"),
    ("/api/projects/", "get"), ("/api/projects/", "post"), ("/api/projects/{id}/", "get"),
    ("/api/projects/{id}/", "put"), ("/api/projects/{id}/", "patch"), ("/api/projects/{id}/", "delete"),
    ("/api/analysis-runs/", "get"), ("/api/analysis-runs/", "post"), ("/api/analysis-runs/{id}/", "get"),
    ("/api/reference-requirements/", "get"), ("/api/reference-requirements/", "post"),
    ("/api/reference-requirements/{id}/", "get"), ("/api/reference-requirements/{id}/", "put"),
    ("/api/reference-requirements/{id}/", "patch"), ("/api/reference-requirements/{id}/", "delete"),
}


def test_documented_operations_match_url_resolver_exactly(schema):
    assert {(p, m) for p, m, _ in operations(schema)} == EXPECTED_OPERATIONS


def test_undocumented_methods_really_are_not_allowed(api, project_id):
    # Şemada olmayan işlemler gerçekten 405 döner (belge eksik değil, API'de yok).
    run = api.post("/api/analysis-runs/", {"project": project_id, "method": "RULE_BASED"}, format="json").json()
    assert api.delete(f"/api/analysis-runs/{run['id']}/").status_code == 405
    assert api.patch(f"/api/analysis-runs/{run['id']}/", {}, format="json").status_code == 405
    assert api.delete("/api/projects/").status_code == 405


def test_every_operation_has_tag_summary_and_documented_statuses(schema):
    allowed_tags = {t["name"] for t in schema["tags"]}
    for path, method, op in operations(schema):
        assert op["tags"] and set(op["tags"]) <= allowed_tags, (path, method)
        assert op.get("summary"), (path, method)
        assert any(code.startswith("2") for code in op["responses"]), (path, method)


def test_tags_are_the_six_functional_groups(schema):
    assert [t["name"] for t in schema["tags"]] == [
        "Kimlik Doğrulama", "Parola İşlemleri", "Proje Yükleme", "Proje Yönetimi", "Analiz İşlemleri",
        "Referans Gereksinimler"]


# ====================================================================== güvenlik şeması

PUBLIC = {("/api/auth/login/", "post"), ("/api/auth/refresh/", "post"), ("/api/auth/password-reset/", "post"),
          ("/api/auth/password-reset/confirm/", "post")}


def test_jwt_bearer_scheme(schema):
    assert schema["components"]["securitySchemes"]["jwtAuth"] == {
        "type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    assert "security" not in schema  # genel varsayılan yok; her işlem kendi gereksinimini belirtir


def test_public_and_protected_marking(schema):
    for path, method, op in operations(schema):
        if (path, method) in PUBLIC:
            assert not op.get("security"), (path, method)
            assert "401" not in op["responses"] or path == "/api/auth/login/" or path == "/api/auth/refresh/"
        else:
            assert op.get("security") == [{"jwtAuth": []}], (path, method)
            assert "401" in op["responses"], (path, method)


def test_protected_marking_matches_real_behavior(schema, alice):
    anon = APIClient()
    for path, method, op in operations(schema):
        url = path.replace("{id}", "1")
        resp = getattr(anon, method)(url, {}, format="json")
        if (path, method) in PUBLIC:
            assert resp.status_code != 401 or path in ("/api/auth/login/", "/api/auth/refresh/"), (path, method)
            assert resp.status_code in (400, 401), (path, method, resp.status_code)  # boş gövde → doğrulama hatası
        else:
            assert resp.status_code == 401, (path, method, resp.status_code)


def test_swagger_ui_and_schema_endpoints_public_in_development(client):
    resp = client.get("/api/schema/")
    assert resp.status_code == 200 and b"openapi: 3.0" in resp.content
    assert client.get("/api/schema/?format=json").json()["info"]["version"]
    ui = client.get("/api/docs/")
    assert ui.status_code == 200 and b"swagger-ui" in ui.content
    assert b"cdn.jsdelivr.net" not in ui.content  # Swagger UI dosyaları yerelden (sidecar)
    assert client.get("/api/redoc/").status_code == 200


def test_docs_restricted_to_staff_when_not_public(settings, client, alice, django_user_model):
    settings.API_DOCS_PUBLIC = False
    assert client.get("/api/schema/").status_code in (401, 403)
    assert client.get("/api/docs/").status_code in (401, 403)
    user = APIClient()
    user.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(alice)}")
    assert user.get("/api/schema/").status_code == 403
    staff = django_user_model.objects.create_user(username="yonetici", password=PASSWORD, is_staff=True)
    st = APIClient()
    st.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(staff)}")
    assert st.get("/api/schema/").status_code == 200
    client.force_login(staff)
    assert client.get("/api/docs/").status_code == 200


def test_docs_policy_does_not_weaken_api_permissions(settings):
    settings.API_DOCS_PUBLIC = True
    assert APIClient().get("/api/projects/").status_code == 401


# ====================================================================== istek gövdeleri

def components(schema):
    return schema["components"]["schemas"]


def test_project_upload_is_multipart_with_binary_archive_field(schema):
    body = schema["paths"]["/api/projects/"]["post"]["requestBody"]
    assert list(body["content"]) == ["multipart/form-data"] and body["required"] is True
    req = components(schema)["ProjectCreateRequest"]
    assert req["properties"]["archive"] == {"type": "string", "format": "binary"}
    assert sorted(req["required"]) == ["archive", "name"]
    assert set(req["properties"]) == {"name", "description", "archive"}


def test_upload_limits_in_description_match_configuration(schema, settings):
    text = schema["paths"]["/api/projects/"]["post"]["description"]
    lim = settings.PROJECT_UPLOAD_LIMITS
    assert f"arşiv ≤ {lim['max_upload_bytes'] // (1024 * 1024)} MiB" in text
    assert f"≤ {lim['max_entries']} girdi" in text and "413" in text and "400" in text


@pytest.mark.parametrize("component,required,forbidden", [
    ("ProjectCreateRequest", {"name", "archive"}, {"id", "owner", "source_archive", "archive_sha256",
                                                    "validation_status", "validation_report", "created_at"}),
    ("ProjectUpdateRequest", {"name"}, {"id", "owner", "archive", "source_archive", "validation_status"}),
    ("PatchedProjectUpdateRequest", set(), {"id", "owner", "archive"}),
    ("AnalysisRunCreateRequest", {"project", "method"}, {"id", "status", "celery_task_id", "created_at",
                                                         "started_at", "finished_at", "requirements_snapshot"}),
    ("ReferenceRequirementAPIRequest", {"project", "requirement_code", "category", "title"},
     {"id", "revision", "http_method", "created_at", "updated_at"}),
    ("LoginRequest", {"username", "password"}, set()),
    ("TokenRefreshRequest", {"refresh"}, set()),
    ("PasswordResetRequest", {"email"}, set()),
    ("PasswordResetConfirmRequest", {"uid", "token", "new_password"}, set()),
])
def test_request_required_and_read_only_fields(schema, component, required, forbidden):
    comp = components(schema)[component]
    assert set(comp.get("required", [])) == required
    assert not (set(comp["properties"]) & forbidden), set(comp["properties"]) & forbidden


def test_required_fields_match_real_serializers(schema):
    from core.api.serializers import AnalysisRunCreateSerializer, ReferenceRequirementAPISerializer
    from core.projects.serializers import ProjectCreateSerializer

    for serializer, component in ((ProjectCreateSerializer(), "ProjectCreateRequest"),
                                  (AnalysisRunCreateSerializer(), "AnalysisRunCreateRequest"),
                                  (ReferenceRequirementAPISerializer(), "ReferenceRequirementAPIRequest")):
        real = {n for n, f in serializer.fields.items() if f.required and not f.read_only}
        assert set(components(schema)[component].get("required", [])) == real, component


def test_http_method_enum_is_exactly_five(schema):
    c = components(schema)
    assert c["HttpMethodEnum"]["enum"] == ["GET", "POST", "PUT", "PATCH", "DELETE"]
    assert c["AccessRuleSpecificationRequest"]["properties"]["method"] == {"$ref": "#/components/schemas/HttpMethodEnum"}
    spec = c["ReferenceRequirementAPIRequest"]["properties"]["specification"]
    assert spec == {"$ref": "#/components/schemas/ReferenceSpecificationRequest"}
    assert [s["$ref"].rsplit("/", 1)[-1] for s in c["ReferenceSpecificationRequest"]["oneOf"]] == [
        "RoleSpecificationRequest", "AccessRuleSpecificationRequest", "DeployExpectationSpecificationRequest"]
    assert sorted(c["AccessRuleSpecificationRequest"]["required"]) == [
        "endpoint", "expected_status_by_role", "method", "schema_version"]


@pytest.mark.parametrize("method,ok", [(m, True) for m in ("GET", "POST", "PUT", "PATCH", "DELETE")]
                         + [(m, False) for m in ("HEAD", "OPTIONS", "TRACE", "get", "")])
def test_http_method_enum_matches_real_validator(api, project_id, method, ok):
    resp = api.post("/api/reference-requirements/", requirement_payload(
        project_id, requirement_code=f"ACC-{method or 'BOS'}", specification={**SPEC, "method": method}), format="json")
    assert resp.status_code == (201 if ok else 400), resp.json()


def test_analysis_status_enum_matches_model(schema):
    from core.models import AnalysisRun

    enum = components(schema)["AnalysisRunStatusEnum"]["enum"]
    assert enum == list(AnalysisRun.Status.values)
    assert {"QUEUED", "ANALYZING", "GENERATING", "EXECUTING", "COMPLETED", "FAILED"} <= set(enum)


def test_lockout_and_password_reset_documented(schema):
    login = schema["paths"]["/api/auth/login/"]["post"]
    assert "3 başarısız" in login["description"] and "15 dakika" in login["description"]
    assert "429" in login["responses"] and "Retry-After" in login["description"]
    confirm = schema["paths"]["/api/auth/password-reset/confirm/"]["post"]
    assert "Tek kullanımlıktır" in confirm["description"] and "PASSWORD_RESET_TIMEOUT" in confirm["description"]


# ====================================================================== gerçek yanıtlar ↔ şema

def test_real_success_responses_match_response_schemas(schema, api, alice):
    login = APIClient().post("/api/auth/login/", {"username": "alice", "password": PASSWORD}, format="json")
    assert_matches(schema, "TokenPair", login.json())
    refresh = APIClient().post("/api/auth/refresh/", {"refresh": login.json()["refresh"]}, format="json")
    assert refresh.status_code == 200 and set(refresh.json()) == {"access", "refresh"}
    assert_matches(schema, "Me", api.get("/api/auth/me/").json())

    created = api.post("/api/projects/", {"name": "Mağaza API", "description": "örnek",
                                          "archive": SimpleUploadedFile("m.zip", valid_django_zip())}, format="multipart")
    assert created.status_code == 201
    assert_matches(schema, "Project", created.json())
    pid = created.json()["id"]
    assert_matches(schema, "PaginatedProjectList", api.get("/api/projects/").json())
    assert_matches(schema, "Project", api.patch(f"/api/projects/{pid}/", {"description": "x"}, format="json").json())

    req = api.post("/api/reference-requirements/", requirement_payload(pid), format="json")
    assert req.status_code == 201
    assert_matches(schema, "ReferenceRequirementAPI", req.json())
    for item in api.get("/api/reference-requirements/").json():
        assert_matches(schema, "ReferenceRequirementAPI", item)

    run = api.post("/api/analysis-runs/", {"project": pid, "method": "RULE_BASED"}, format="json")
    assert run.status_code == 201
    assert_matches(schema, "AnalysisRunDetail", run.json())
    assert run.json()["status"] == "QUEUED" and run.json()["celery_task_id"] is None
    for item in api.get("/api/analysis-runs/").json():
        assert_matches(schema, "AnalysisRunList", item)
    assert_matches(schema, "AnalysisRunDetail", api.get(f"/api/analysis-runs/{run.json()['id']}/").json())


def test_documented_status_codes_match_real_responses(api, project_id):
    from core.models import AnalysisRun

    assert api.delete(f"/api/projects/{project_id}/").status_code == 204
    pid = api.post("/api/projects/", {"name": "p2", "archive": SimpleUploadedFile("p.zip", valid_django_zip())},
                   format="multipart").json()["id"]
    AnalysisRun.objects.create(project_id=pid, method="RULE_BASED")
    assert api.delete(f"/api/projects/{pid}/").status_code == 409
    assert api.post("/api/projects/", {"name": "x"}, format="json").status_code == 415
    logout = api.post("/api/auth/logout/", {"refresh": "gecersiz"}, format="json")
    assert logout.status_code == 400


def _error_cases(api, anon, project_id):
    """(belgelenen yol, yöntem, durum, örnek adı) → gerçek yanıt."""
    big = dict(DEFAULT_LIMITS)
    return [
        ("/api/auth/login/", "post", 401, "Hatalı bilgiler",
         lambda: anon.post("/api/auth/login/", {"username": "alice", "password": "yanlis"}, format="json")),
        ("/api/auth/login/", "post", 400, "Eksik alan", lambda: anon.post("/api/auth/login/", {}, format="json")),
        ("/api/auth/refresh/", "post", 401, "Geçersiz refresh",
         lambda: anon.post("/api/auth/refresh/", {"refresh": "gecersiz"}, format="json")),
        ("/api/auth/refresh/", "post", 400, "Eksik alan", lambda: anon.post("/api/auth/refresh/", {}, format="json")),
        ("/api/auth/logout/", "post", 400, "Eksik refresh", lambda: api.post("/api/auth/logout/", {}, format="json")),
        ("/api/auth/logout/", "post", 400, "Geçersiz refresh",
         lambda: api.post("/api/auth/logout/", {"refresh": "x"}, format="json")),
        ("/api/auth/me/", "get", 401, "Token yok", lambda: anon.get("/api/auth/me/")),
        ("/api/auth/password-reset/", "post", 200, "Genel yanıt",
         lambda: anon.post("/api/auth/password-reset/", {"email": "kayitsiz@example.test"}, format="json")),
        ("/api/auth/password-reset/", "post", 400, "Geçersiz e-posta",
         lambda: anon.post("/api/auth/password-reset/", {"email": "gecersiz"}, format="json")),
        ("/api/auth/password-reset/confirm/", "post", 400, "Geçersiz/süresi dolmuş/kullanılmış bağlantı",
         lambda: anon.post("/api/auth/password-reset/confirm/", {"uid": "MQ", "token": "x", "new_password": "Yeni-Parola-2026"},
                           format="json")),
        ("/api/auth/password-reset/confirm/", "post", 400, "Eksik alanlar",
         lambda: anon.post("/api/auth/password-reset/confirm/", {}, format="json")),
        ("/api/projects/", "post", 400, "Zip Slip", lambda: api.post("/api/projects/", {
            "name": "z", "archive": SimpleUploadedFile("z.zip", build_zip(django_files(), raw=[("../evil.py", "x", None)]))},
            format="multipart")),
        ("/api/projects/", "post", 400, "Django projesi değil", lambda: api.post("/api/projects/", {
            "name": "d", "archive": SimpleUploadedFile("d.zip", build_zip({"a.txt": "x"}))}, format="multipart")),
        ("/api/projects/", "post", 400, "Eksik alanlar", lambda: api.post("/api/projects/", {}, format="multipart")),
        ("/api/projects/", "post", 400, "Korumalı alan", lambda: api.post("/api/projects/", {
            "name": "k", "owner": "2", "archive": SimpleUploadedFile("k.zip", valid_django_zip())}, format="multipart")),
        ("/api/projects/", "post", 413, "Çok büyük", lambda: api.post("/api/projects/", {
            "name": "b", "archive": SimpleUploadedFile("b.zip", b"PK\x03\x04" + b"\0" * (big["max_upload_bytes"] + 70_000))},
            format="multipart")),
        ("/api/projects/", "post", 415, "Yanlış içerik türü",
         lambda: api.post("/api/projects/", {"name": "x"}, format="json")),
        ("/api/projects/{id}/", "patch", 400, "Korumalı alan",
         lambda: api.patch(f"/api/projects/{project_id}/", {"owner": 2}, format="json")),
        ("/api/projects/{id}/", "get", 404, "Bulunamadı", lambda: api.get("/api/projects/999999/")),
        ("/api/analysis-runs/", "post", 400, "LLM alanları eksik",
         lambda: api.post("/api/analysis-runs/", {"project": project_id, "method": "DIRECT_LLM"}, format="json")),
        ("/api/analysis-runs/", "post", 400, "RULE_BASED ile LLM alanı",
         lambda: api.post("/api/analysis-runs/", {"project": project_id, "method": "RULE_BASED",
                                                  "llm_provider": "GROQ", "llm_model": "m"}, format="json")),
        ("/api/analysis-runs/", "post", 400, "Başkasının veya olmayan proje",
         lambda: api.post("/api/analysis-runs/", {"project": 99999, "method": "RULE_BASED"}, format="json")),
        ("/api/analysis-runs/{id}/", "get", 404, "Bulunamadı", lambda: api.get("/api/analysis-runs/999999/")),
        ("/api/reference-requirements/", "post", 400, "Desteklenmeyen HTTP metodu",
         lambda: api.post("/api/reference-requirements/", requirement_payload(
             project_id, requirement_code="ACC-X", specification={**SPEC, "method": "HEAD"}), format="json")),
        ("/api/reference-requirements/", "post", 400, "Eksik specification alanları",
         lambda: api.post("/api/reference-requirements/", requirement_payload(
             project_id, requirement_code="ACC-Y", specification={"schema_version": 1, "method": "GET"}), format="json")),
        ("/api/reference-requirements/", "post", 400, "Eksik zorunlu alanlar",
         lambda: api.post("/api/reference-requirements/", {"project": project_id}, format="json")),
        ("/api/reference-requirements/", "post", 400, "expected_result eksik",
         lambda: api.post("/api/reference-requirements/", requirement_payload(
             project_id, requirement_code="ACC-Z", expected_result=""), format="json")),
        ("/api/projects/{id}/", "patch", 400, "Aynı ad", lambda: api.patch(
            f"/api/projects/{project_id}/", {"name": api.post("/api/projects/", {
                "name": "İkinci", "archive": SimpleUploadedFile("i.zip", valid_django_zip())},
                format="multipart").json()["name"]}, format="json")),
        ("/api/projects/{id}/", "delete", 409, "Aktif analiz", lambda: (
            api.post("/api/analysis-runs/", {"project": project_id, "method": "RULE_BASED"}, format="json"),
            api.delete(f"/api/projects/{project_id}/"))[1]),
        # H4-04 bilinen kusuru: koşullu benzersizlik kısıtı özel mesajı gölgeliyor; şema gerçek gövdeyi belgeler.
        ("/api/analysis-runs/", "post", 400, "Projede aktif analiz var",
         lambda: api.post("/api/analysis-runs/", {"project": project_id, "method": "RULE_BASED"}, format="json")),
        ("/api/reference-requirements/{id}/", "get", 404, "Bulunamadı",
         lambda: api.get("/api/reference-requirements/999999/")),
    ]


def test_error_examples_equal_real_responses(schema, api, alice, project_id):
    anon = APIClient()
    checked = 0
    for path, method, status, name, call in _error_cases(api, anon, project_id):
        if path == "/api/projects/" and status == 413:
            examples = examples_of(schema, path, method, status)
            resp = call()
            assert resp.status_code == 413
            assert set(resp.json()) == set(examples[name]) == {"detail"}  # sınır değeri yapılandırmaya bağlıdır
            checked += 1
            continue
        examples = examples_of(schema, path, method, status)
        assert name in examples, (path, method, status, name, list(examples))
        resp = call()
        assert resp.status_code == status, (path, method, name, resp.status_code, resp.content[:300])
        assert resp.json() == examples[name], (path, method, name, resp.json())
        checked += 1
    assert checked == 31


def test_invalid_access_token_example_matches_real_response(schema):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION="Bearer gecersiz.token.degeri")
    examples = examples_of(schema, "/api/auth/me/", "get", 401)
    assert c.get("/api/auth/me/").json() == examples["Geçersiz veya süresi dolmuş token"]


def test_lockout_example_matches_real_behavior(schema, alice):
    anon = APIClient()
    statuses = [anon.post("/api/auth/login/", {"username": "alice", "password": "yanlis"}, format="json").status_code
                for _ in range(3)]
    assert statuses == [401, 401, 429]
    locked = anon.post("/api/auth/login/", {"username": "alice", "password": PASSWORD}, format="json")
    # H5-03 / #41: kilit yanıtı kalan süreyi ve Retry-After başlığını içerir; zaman değerleri dinamiktir.
    example = examples_of(schema, "/api/auth/login/", "post", 429)["Hesap kilitli"]
    body = locked.json()
    assert locked.status_code == 429 and int(locked["Retry-After"]) == body["retry_after_seconds"]
    assert set(body) == set(example)
    assert body["detail"] == example["detail"] and body["code"] == example["code"] == "account_locked"
    assert 0 < body["retry_after_seconds"] <= 15 * 60


def test_successful_examples_have_real_shape(schema):
    for path, method, op in operations(schema):
        for status, resp in op["responses"].items():
            content = resp.get("content", {}).get("application/json", {})
            ref = content.get("schema")
            for name, example in content.get("examples", {}).items():
                if not status.startswith("2") or ref is None:
                    continue
                js = to_jsonschema(ref, components(schema))
                jsonschema.validate(example["value"], js)


def test_request_examples_are_valid_against_request_schemas(schema):
    for path, method, op in operations(schema):
        body = op.get("requestBody", {}).get("content", {}).get("application/json")
        if not body:
            continue
        js = to_jsonschema(body["schema"], components(schema))
        for example in body.get("examples", {}).values():
            if "400" in example["summary"]:
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(example["value"], js)
            else:
                jsonschema.validate(example["value"], js)


# ====================================================================== dışa aktarımlar ve gizlilik

def test_committed_yaml_and_json_exports_are_current_and_equivalent(schema):
    committed_yaml = yaml.safe_load((DOCS / "openapi.yaml").read_text(encoding="utf-8"))
    committed_json = json.loads((DOCS / "openapi.json").read_text(encoding="utf-8"))
    assert committed_yaml == committed_json
    assert committed_yaml == schema, "docs/api/openapi.* güncel değil; README'deki komutla yeniden üretin"


def test_no_secrets_or_internal_paths_in_documentation(schema, settings):
    texts = [json.dumps(schema, ensure_ascii=False)] + [p.read_text(encoding="utf-8") for p in DOCS.glob("*")
                                                       if p.suffix in (".json", ".yaml", ".md")]
    db_password = settings.DATABASES["default"]["PASSWORD"]
    forbidden = [settings.SECRET_KEY, db_password, str(settings.BASE_DIR), str(settings.PROJECT_ARCHIVE_ROOT),
                 "private_storage/project_archives"]
    for text in texts:
        for value in forbidden:
            assert not value or value not in text, value
        assert not re.search(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.", text), "gerçek JWT benzeri değer"
        assert "Gizli-Parola" not in text and "Demo-Parola" not in text


def test_postman_collection_is_valid_and_uses_variables_only():
    data = json.loads((DOCS / "postman_collection.json").read_text(encoding="utf-8"))
    assert data["info"]["schema"] == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    names = {v["key"] for v in data["variable"]}
    assert {"baseUrl", "accessToken", "refreshToken", "username", "password"} <= names
    assert all(not v.get("value") for v in data["variable"] if v["key"] in ("accessToken", "refreshToken", "password"))

    def requests(items):
        for it in items:
            if "item" in it:
                yield from requests(it["item"])
            else:
                yield it

    reqs = list(requests(data["item"]))
    schema_ops = {(p, m.upper()) for p, m in EXPECTED_OPERATIONS}
    for r in reqs:
        url = r["request"]["url"]["raw"]
        assert url.startswith("{{baseUrl}}/api/"), url
        path = re.sub(r"\{\{[a-zA-Z]+Id\}\}", "{id}", url.replace("{{baseUrl}}", "")).split("?")[0]
        assert (path, r["request"]["method"]) in schema_ops, (path, r["request"]["method"])
    upload = next(r for r in reqs if r["request"]["method"] == "POST" and r["request"]["url"]["raw"].endswith("/projects/"))
    assert upload["request"]["body"]["mode"] == "formdata"
    assert {f["key"]: f["type"] for f in upload["request"]["body"]["formdata"]}["archive"] == "file"


@pytest.mark.parametrize("category,spec,expected_result,http_method", [
    ("ROLE", {"schema_version": 1, "role": "staff"}, "", None),
    ("DEPLOY_EXPECTATION", {"schema_version": 1, "setting": "DEBUG", "expected_value": False, "check_id": "DEP-DEBUG"},
     "DEBUG kapalı", None),
    ("ACCESS_RULE", SPEC, "anonim 401, staff 204", "DELETE"),
])
def test_documented_specification_examples_are_accepted(api, project_id, category, spec, expected_result, http_method):
    resp = api.post("/api/reference-requirements/", requirement_payload(
        project_id, requirement_code=f"DOC-{category}", category=category, specification=spec,
        expected_result=expected_result), format="json")
    assert resp.status_code == 201, resp.json()
    assert resp.json()["http_method"] == http_method
