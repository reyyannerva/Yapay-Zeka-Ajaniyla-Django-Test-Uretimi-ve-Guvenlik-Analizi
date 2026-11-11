"""Üretim orkestrasyonu — H3-05 / Issue #31.

Her senaryo için: prompt üret -> LLM çağır -> kodu ayıkla -> sözdizimi doğrula -> dosya yaz.
Ham model yanıtları (sır içermez) izlenebilirlik için kaydedilir.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from . import PROMPT_VERSION
from .client import GroqClient, LLMError
from .contracts import Case, GenerationOutcome
from .extract import extract_code
from .prompt import SYSTEM, render, test_name
from .validation import check_syntax

# Geçici (yeniden denenebilir) hata türleri ve "try again in Xs" ipucu.
_TRANSIENT = {"quota", "timeout", "connection"}
_WAIT_RE = re.compile(r"try again in ([0-9.]+)\s*s", re.IGNORECASE)


def _retry_wait(message: str, attempt: int, base: float, cap: float) -> float:
    """Mesajdaki 'try again in Xs' ipucunu kullan; yoksa üstel geri çekilme."""
    m = _WAIT_RE.search(message or "")
    if m:
        return min(float(m.group(1)) + 0.5, cap)
    return min(base * (2 ** attempt), cap)


def _complete_with_retry(client, system, user, max_retries, base_delay, cap, sleep):
    """Geçici hatalarda geri çekilerek yeniden dener; kalıcı hatada son hatayı yükseltir."""
    attempt = 0
    while True:
        try:
            return client.complete(system, user)
        except LLMError as exc:
            if exc.kind in _TRANSIENT and attempt < max_retries:
                sleep(_retry_wait(exc.message, attempt, base_delay, cap))
                attempt += 1
                continue
            raise

_HEADER = '''\
"""LLM ile üretilmiş test — H3-05 / Issue #31. ELLE DÜZENLEMEYİN.
Senaryo: {sid} · Model: {model} · Prompt: {prompt}
Beklenen durum kodu bağımsız referanstan (ground_truth.secure_status) alınmıştır.
"""
'''


def dump_prompts(cases: list[Case], prompts_dir: Path) -> int:
    """LLM'e gönderilecek render edilmiş istemleri (system + user) kaydeder (çağrı yapmaz)."""
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        content = f"=== SYSTEM ===\n{SYSTEM}\n\n=== USER ===\n{render(case)}\n"
        (prompts_dir / f"{case.scenario_id}.txt").write_text(content, encoding="utf-8")
    return len(cases)


def run(cases: list[Case], client: GroqClient, out_dir: Path, raw_dir: Path,
        model: str, *, prompts_dir: Path | None = None, max_retries: int = 6,
        inter_delay: float = 0.8, base_delay: float = 2.0, cap: float = 30.0,
        sleep=time.sleep) -> list[GenerationOutcome]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    if prompts_dir is not None:
        dump_prompts(cases, prompts_dir)  # giriş verilerini (istemleri) kaydet
    outcomes: list[GenerationOutcome] = []

    for i, case in enumerate(cases):
        if i and inter_delay:
            sleep(inter_delay)  # TPM sınırını aşmamak için istekler arası küçük bekleme
        tname = test_name(case.scenario_id)
        oc = GenerationOutcome(
            scenario_id=case.scenario_id, status="", test_name=tname,
            http_method=case.http_method, model=model, prompt_version=PROMPT_VERSION,
        )
        user_prompt = render(case)
        try:
            resp = _complete_with_retry(client, SYSTEM, user_prompt, max_retries, base_delay, cap, sleep)
        except LLMError as exc:
            oc.status = "LLM_ERROR"
            oc.error = f"{exc.kind}: {exc.message}"
            outcomes.append(oc)
            continue

        oc.prompt_tokens = resp.prompt_tokens
        oc.completion_tokens = resp.completion_tokens
        oc.latency_ms = resp.latency_ms
        raw_file = raw_dir / f"{case.scenario_id}.txt"
        raw_file.write_text(resp.text or "", encoding="utf-8")
        oc.raw_response_file = str(raw_file)

        code = extract_code(resp.text)
        if not code.strip():
            oc.status = "EMPTY_OUTPUT"
            outcomes.append(oc)
            continue

        ok, err = check_syntax(code, expected_func=tname)
        oc.code = code
        if not ok:
            oc.status = "INVALID_SYNTAX"
            oc.syntax_error = err
            outcomes.append(oc)
            continue

        oc.status = "GENERATED"
        header = _HEADER.format(sid=case.scenario_id, model=model, prompt=PROMPT_VERSION)
        (out_dir / f"{tname}.py").write_text(header + "\n" + code + "\n", encoding="utf-8")
        outcomes.append(oc)

    return outcomes
