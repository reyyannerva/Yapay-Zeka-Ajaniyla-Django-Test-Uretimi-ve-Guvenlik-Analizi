"""Kanonik destek tabloları: Endpoint, Report, LlmCall (Issue #33'ün yedi temel varlığı dışında)."""
import pytest

from core.models import Endpoint, LlmCall, Report

from .conftest import assert_integrity, make_endpoint, make_test

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_endpoint_methods(run, method):
    assert Endpoint.objects.get(pk=make_endpoint(run, http_method=method).pk).http_method == method


def test_endpoint_constraints(run):
    assert_integrity(lambda: make_endpoint(run, http_method="HEAD"), "ck_endpoints_http_method_valid")
    assert_integrity(lambda: make_endpoint(run, is_supported=False), "ck_endpoints_unsupported_has_reason")
    make_endpoint(run, path="/api/a/", http_method="GET")
    assert_integrity(lambda: make_endpoint(run, path="/api/a/", http_method="GET"), "uq_endpoints_run_path_method")
    e = make_endpoint(run, is_supported=False, unsupported_reason="DYNAMIC_ROUTE", permission_classes=["IsAdmin"])
    assert Endpoint.objects.get(pk=e.pk).permission_classes == ["IsAdmin"]


def test_report(run):
    r = Report.objects.create(analysis_run=run, format="PDF", scope="FULL", file_path="reports/1.pdf",
                              file_size_bytes=1024, sections=["summary", "findings"])
    assert Report.objects.get(pk=r.pk).sections == ["summary", "findings"]
    assert_integrity(lambda: Report.objects.create(analysis_run=run, format="PDF", scope="FULL",
                                                   file_path="/abs.pdf", file_size_bytes=1),
                     "ck_reports_file_path_relative")


def test_llm_call(run):
    t = make_test(run, generation_method="LLM")
    c = LlmCall.objects.create(analysis_run=run, generated_test=t, provider="GROQ", model="openai/gpt-oss-120b",
                               purpose="GENERATE", status="SUCCESS", prompt_tokens=674, completion_tokens=248,
                               latency_ms=1666)
    assert list(t.llm_calls.all()) == [c]
    assert_integrity(lambda: LlmCall.objects.create(analysis_run=run, provider="GROQ", model="m",
                                                    purpose="GENERATE", status="SUCCESS"),
                     "ck_llm_calls_success_has_tokens")
    t.delete()
    c.refresh_from_db()
    assert c.generated_test is None
