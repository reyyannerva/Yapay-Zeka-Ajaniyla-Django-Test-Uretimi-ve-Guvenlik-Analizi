"""Deterministik hibrit birleştirme politikası — H5-05 / Issue #43.

Girdi: her senaryo için kural tabanlı (H3-04) ve LLM (H3-05) adayları + **referans gereksinim**
(senaryonun yöntemi, uç yolu, aktör kullanıcı, rol ve ``expected_result.secure_status``).
Ground truth değerlendirme etiketleri (``is_known_flaw``, ``security_finding``) bu modüle HİÇ verilmez.

Politika (sıra önemlidir, rastgelelik yok):

1. Her aday ``normalize.signature`` ile imzaya indirgenir.
2. **Referans tutarlılığı:** yöntem, uç yolu, kimlik durumu (anonim ↔ kimlikli), aktör (referansta varsa)
   ve beklenen durum kodu referansla karşılaştırılır. Tutarsız aday ``REJECTED_REFERENCE_CONFLICT``.
   Sözdizimi geçersiz / imzası çıkarılamayan aday ``REJECTED_UNPARSABLE``.
3. Tutarlı adaylar:
   * ikisi de tutarlı ve anahtarları eşit (anlamsal eşitlik; kod eşitliği ayrıca ``code_identical``):
     - LLM'in doğrulama türleri kural tabanlınınkilerin alt kümesiyse → **yinelenen**; kural tabanlı tutulur,
       LLM ``DROPPED_DUPLICATE`` → kaynak ``common``.
     - LLM ek doğrulama türü içeriyorsa (ör. gövde kontrolü) → **birleştirilir**: kural tabanlı test + LLM
       testi (``__llm`` son ekiyle) aynı modülde; hiçbir kontrol kaybolmaz → kaynak ``merged``.
   * ikisi de tutarlı ama anahtarları farklı (ör. referansta aktör yokken farklı kullanıcı) → **çözülmüş
     çelişki**; daha fazla doğrulama türü içeren seçilir, eşitlikte kural tabanlı.
   * yalnızca biri tutarlı → o seçilir (``rule_only`` / ``llm_only``).
   * hiçbiri tutarlı değil → **çözülmemiş çelişki**; hibrit bu senaryo için test üretmez
     (``NO_ARTIFACT``; referansa aykırı test yürütülmez).
4. Her karar ``hybrid_decisions.jsonl``'e, her aday ``hybrid_candidates.jsonl``'e kaynak bilgisiyle yazılır.
"""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field

from agent.evaluation.artifacts import Artifact

from .config import HYBRID_GENERATOR_ID, HYBRID_VERSION
from .normalize import Signature, signature


@dataclass(frozen=True)
class Reference:
    scenario_id: str
    http_method: str
    endpoint: str
    user_role: str
    actor: str | None
    secure_status: int
    reference_requirement_id: str


@dataclass
class Decision:
    scenario_id: str
    final_source: str | None            # rule_based | llm | rule_based+llm | None
    provenance: str                     # common | merged | rule_only | llm_only | resolved_conflict | unresolved | none
    duplicates: int = 0
    conflicts_resolved: int = 0
    conflicts_unresolved: int = 0
    candidate_status: dict = field(default_factory=dict)
    code_identical: bool | None = None       # kaynak kod SHA-256 eşitliği (anlamsal eşitlikten ayrı)
    complement_kinds: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def reference_conflicts(sig: Signature, ref: Reference) -> list[str]:
    out = []
    if sig.http_method != ref.http_method:
        out.append(f"yöntem {sig.http_method} ≠ referans {ref.http_method}")
    if sig.endpoint != ref.endpoint:
        out.append(f"uç {sig.endpoint} ≠ referans {ref.endpoint}")
    want_auth = "anonymous" if ref.user_role == "anonymous" else "authenticated"
    if sig.auth != want_auth:
        out.append(f"kimlik {sig.auth} ≠ referans {want_auth}")
    if ref.actor and sig.actor != ref.actor:
        out.append(f"aktör {sig.actor} ≠ referans {ref.actor}")
    if sig.expected_status != ref.secure_status:
        out.append(f"beklenen durum {sig.expected_status} ≠ referans {ref.secure_status}")
    return out


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def candidate_record(layer: str, method: str, art: Artifact | None, sig: Signature | None,
                     conflicts: list[str], status: str) -> dict:
    return {"layer": layer, "scenario_id": art.scenario_id if art else None, "generation_method": method,
            "source_artifact": art.origin if art else None,
            "artifact_sha256": _sha(art.source) if art else None,
            "signature": sig.to_json() if sig else None,
            "reference_conflicts": conflicts, "status": status}


def merge(layer: str, ref: Reference, rb: list[Artifact], llm: list[Artifact],
          routes: dict[str, str]) -> tuple[Artifact | None, Decision, list[dict]]:
    """Tek senaryo için hibrit artefaktı, kararı ve aday kayıtlarını döndürür."""
    sid = ref.scenario_id
    dec = Decision(sid, None, "none")
    cands: list[dict] = []
    consistent: dict[str, tuple[Artifact, Signature]] = {}
    for method, arts in (("rule_based", rb), ("llm", llm)):
        if not arts:
            dec.candidate_status[method] = "ABSENT"
            dec.reasons.append(f"{method}: aday yok")
            continue
        if len(arts) > 1:
            # Birden fazla aday: ilk (kaynak sırası) değerlendirilir, diğerleri yinelenen sayılır.
            dec.duplicates += len(arts) - 1
            for extra in arts[1:]:
                cands.append(candidate_record(layer, method, extra, None, [], "DROPPED_DUPLICATE_SAME_METHOD"))
        art = arts[0]
        sig = signature(art.source, routes)
        if not sig.parse_ok or sig.http_method is None or sig.expected_status is None:
            status, conf = "REJECTED_UNPARSABLE", [sig.error or "istek/beklenti çıkarılamadı"]
        else:
            conf = reference_conflicts(sig, ref)
            status = "REJECTED_REFERENCE_CONFLICT" if conf else "CONSISTENT"
        dec.candidate_status[method] = status
        cands.append(candidate_record(layer, method, art, sig, conf, status))
        if status == "CONSISTENT":
            consistent[method] = (art, sig)
        else:
            dec.reasons.append(f"{method}: {status} ({'; '.join(conf)})")

    chosen: tuple[str, Artifact, Signature] | None = None
    if "rule_based" in consistent and "llm" in consistent:
        (ra, rs), (la, ls) = consistent["rule_based"], consistent["llm"]
        dec.code_identical = _sha(ra.source) == _sha(la.source)
        if rs.key() == ls.key():
            extra = sorted(set(ls.assertion_kinds) - set(rs.assertion_kinds))
            dec.complement_kinds = extra
            if extra:
                # Aynı istek/beklenti ama LLM ek doğrulama türü içeriyor: kontrol kaybolmasın diye iki test
                # aynı modülde birleştirilir (kural tabanlı + LLM'in tamamlayıcı testi).
                dec.provenance = "merged"
                dec.final_source = "rule_based+llm"
                dec.reasons.append(f"anlamsal anahtar aynı, kod farklı; LLM ek doğrulama türü içeriyor {extra} → "
                                   "kural tabanlı test + LLM tamamlayıcı testi birleştirildi")
                _mark(cands, "rule_based", "SELECTED")
                _mark(cands, "llm", "SELECTED_COMPLEMENT")
                merged = merge_modules(ra.source, la.source)
                return (Artifact(sid, "hybrid", f"hybrid<-rule_based:{ra.origin}+llm:{la.origin}", merged, ra.function,
                                 dict(ra.support_files), generation_status="GENERATED",
                                 notes=[f"{HYBRID_GENERATOR_ID} v{HYBRID_VERSION}", "merged"]), dec, cands)
            dec.duplicates += 1
            dec.provenance = "common"
            chosen = ("rule_based", ra, rs)
            dec.reasons.append("yinelenen (anlamsal): aynı istek ve beklenti, LLM'in doğrulama türleri kural tabanlının "
                               "alt kümesi; kural tabanlı tutuldu. Kod birebir aynı DEĞİL"
                               if not dec.code_identical else "yinelenen: kod birebir aynı")
            _mark(cands, "llm", "DROPPED_DUPLICATE")
        else:
            dec.conflicts_resolved += 1
            dec.provenance = "resolved_conflict"
            pick_llm = len(ls.assertion_kinds) > len(rs.assertion_kinds)
            chosen = ("llm", la, ls) if pick_llm else ("rule_based", ra, rs)
            dec.reasons.append("çelişki çözüldü: ikisi de referansla tutarlı fakat imzalar farklı; "
                               f"doğrulama türü sayısına göre {chosen[0]} seçildi (eşitlikte kural tabanlı)")
            _mark(cands, "rule_based" if pick_llm else "llm", "DROPPED_RESOLVED_CONFLICT")
    elif consistent:
        method = next(iter(consistent))
        chosen = (method, *consistent[method])
        dec.provenance = "rule_only" if method == "rule_based" else "llm_only"
        other = "llm" if method == "rule_based" else "rule_based"
        if dec.candidate_status.get(other) in ("REJECTED_REFERENCE_CONFLICT", "REJECTED_UNPARSABLE"):
            dec.conflicts_resolved += 1
            dec.reasons.append(f"çelişki çözüldü: {other} referansla tutarsız, {method} seçildi")
    else:
        present = [m for m in ("rule_based", "llm") if dec.candidate_status.get(m) != "ABSENT"]
        if present:
            dec.conflicts_unresolved += 1
            dec.provenance = "unresolved"
            dec.reasons.append("çözülmemiş çelişki: hiçbir aday referansla tutarlı değil; test üretilmedi")
    for c in cands:
        if chosen and c["generation_method"] == chosen[0] and c["status"] == "CONSISTENT":
            c["status"] = "SELECTED"
    if chosen is None:
        return None, dec, cands
    method, art, _ = chosen
    dec.final_source = method
    hybrid = Artifact(sid, "hybrid", f"hybrid<-{method}:{art.origin}", art.source, art.function,
                      dict(art.support_files), generation_status="GENERATED",
                      notes=[f"{HYBRID_GENERATOR_ID} v{HYBRID_VERSION}", dec.provenance])
    return hybrid, dec, cands


def merge_modules(base_src: str, extra_src: str) -> str:
    """Kural tabanlı modüle LLM modülünün eksik importlarını ve test fonksiyon(lar)ını ``__llm`` son ekiyle ekler.
    Hiçbir doğrulama değiştirilmez; yalnızca ad çakışması önlenir."""
    base = ast.parse(base_src)
    extra = ast.parse(extra_src)
    have = {ast.unparse(n) for n in base.body if isinstance(n, (ast.Import, ast.ImportFrom))}
    imports, funcs = [], []
    for n in extra.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and ast.unparse(n) not in have:
            imports.append(ast.unparse(n))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            seg = ast.get_source_segment(extra_src, n, padded=False)
            if n.name.startswith("test_"):
                seg = seg.replace(f"def {n.name}(", f"def {n.name}__llm(", 1)
            funcs.append(seg)
    head = ("\n".join(imports) + "\n") if imports else ""
    return (head + base_src.rstrip("\n") + "\n\n\n# --- LLM (H3-05) tamamlayıcı testi: ek doğrulama türü ---\n"
            + "\n\n\n".join(funcs) + "\n")


def _mark(cands: list[dict], method: str, status: str) -> None:
    for c in cands:
        if c["generation_method"] == method and c["status"] == "CONSISTENT":
            c["status"] = status


def summarize(decisions: list[Decision], cand_records: list[dict]) -> dict:
    prov = {}
    for d in decisions:
        prov[d.provenance] = prov.get(d.provenance, 0) + 1
    return {
        "scenarios": len(decisions),
        "rule_based_candidates": sum(1 for c in cand_records if c["generation_method"] == "rule_based"),
        "llm_candidates": sum(1 for c in cand_records if c["generation_method"] == "llm"),
        "duplicates": sum(d.duplicates for d in decisions),
        "conflicts_resolved": sum(d.conflicts_resolved for d in decisions),
        "conflicts_unresolved": sum(d.conflicts_unresolved for d in decisions),
        "final_tests": sum(1 for d in decisions if d.final_source),
        "final_from_rule_based": sum(1 for d in decisions if d.final_source == "rule_based"),
        "final_from_llm": sum(1 for d in decisions if d.final_source == "llm"),
        "final_merged_rule_and_llm": sum(1 for d in decisions if d.final_source == "rule_based+llm"),
        "code_identical_pairs": sum(1 for d in decisions if d.code_identical),
        "semantic_key_equal_pairs": prov.get("common", 0) + prov.get("merged", 0),
        "provenance": dict(sorted(prov.items())),
        "common": prov.get("common", 0),
        "rule_only": prov.get("rule_only", 0),
        "llm_only": prov.get("llm_only", 0),
        "merged": prov.get("merged", 0),
    }
