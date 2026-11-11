"""Veri sözleşmeleri — H3-05 / Issue #31.

`Case`, bir senaryoyu (scenarios.json) + bağımsız referansı (ground_truth.json) + endpoint
özetini (endpoint_summary.json) birleştirir. `prompt_fields`, LLM istemine yalnızca ÜRETİM
girdisini verir; cevap anahtarı meta (is_known_flaw, observed_flawed_status, split) prompt'a
KONULMAZ — bu alanlar yalnızca sınıflandırmada kullanılır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Case:
    scenario_id: str
    http_method: str
    endpoint_path: str          # somut yol, örn. /api/articles/1/
    url_name: str               # reverse() için, örn. article-detail
    pk: Optional[int]           # route param (yoksa None)
    user_username: Optional[str]  # force_authenticate için; anonim ise None
    user_role: str
    request_input: Optional[dict]
    writable_fields: dict       # endpoint özetinden (ad -> kural)
    category: str
    # --- Üretim girdisi (prompt'a KONUR) ---
    expected_secure_status: int
    expected_behavior: str
    # --- Sınıflandırma meta (prompt'a KONMAZ) ---
    is_known_flaw: bool = False
    deviation_kind: Optional[str] = None       # "status" | "content" | None
    observed_flawed_status: Optional[int] = None

    def prompt_fields(self) -> dict[str, Any]:
        """LLM istemine verilecek alanlar (yalnızca üretim girdisi; cevap anahtarı yok)."""
        return {
            "scenario_id": self.scenario_id,
            "http_method": self.http_method,
            "endpoint_path": self.endpoint_path,
            "url_name": self.url_name,
            "pk": self.pk,
            "user_username": self.user_username,
            "user_role": self.user_role,
            "request_input": self.request_input,
            "writable_fields": self.writable_fields,
            "expected_status": self.expected_secure_status,
            "expected_behavior": self.expected_behavior,
        }


@dataclass
class GenerationOutcome:
    scenario_id: str
    status: str                 # GENERATED | INVALID_SYNTAX | EMPTY_OUTPUT | LLM_ERROR
    test_name: str
    http_method: str
    model: str
    prompt_version: str
    code: Optional[str] = None
    error: Optional[str] = None
    syntax_error: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    raw_response_file: Optional[str] = None


@dataclass
class ExecutionOutcome:
    scenario_id: str
    classification: str         # PASSED | KNOWN_FLAW_DETECTED | KNOWN_FLAW_NOT_DETECTED |
                                # APPLICATION_MISMATCH | GENERATION_ERROR | NOT_RUN
    pytest_outcome: Optional[str] = None   # passed | failed | error | None
    detail: str = ""
