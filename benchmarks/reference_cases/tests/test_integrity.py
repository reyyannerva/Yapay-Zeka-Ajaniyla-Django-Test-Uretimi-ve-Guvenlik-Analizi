"""Sabitleme (SHA-256) ve satır sonu bağımsızlığı regresyon testleri — denetim bulgusu D-02, D-03.

H3-03 / Issue #29 kapsamındaki bağımsız test kümesi ve ground truth içeriğinin değişmediğini ve
bütünlük doğrulamasının platformdan (LF / CRLF çalışma kopyası) bağımsız olduğunu kanıtlar.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
INTEGRITY = BASE / "INTEGRITY.txt"
FROZEN = ("test_set.json", "ground_truth.json")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check = _load("check_references", BASE / "scripts" / "check_references.py")
export = _load("export_ground_truth_csv", BASE / "scripts" / "export_ground_truth_csv.py")


def _records(prefix: str = "") -> dict[str, str]:
    out = {}
    for line in INTEGRITY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if prefix:
            if line.startswith(f"# {prefix} "):
                _, _, name, digest = line.split()
                out[name] = digest
        elif line and not line.startswith("#"):
            name, digest = line.split()
            out[name] = digest
    return out


def test_check_references_passes_on_repository_files():
    assert check.main() == 0


@pytest.mark.parametrize("name", FROZEN)
def test_recorded_digest_matches_canonical_content(name):
    assert _records()[name] == check.sha256(BASE / name)


@pytest.mark.parametrize("name", FROZEN)
def test_frozen_content_unchanged_since_original_freeze(name):
    """Eski (CRLF ile hesaplanmış) özet, mevcut içeriğin CRLF kodlamasına birebir eşit olmalı."""
    raw = (BASE / name).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest() == _records("legacy-crlf")[name]


@pytest.mark.parametrize("name", FROZEN)
def test_digest_is_line_ending_independent(tmp_path, name):
    raw = (BASE / name).read_bytes().replace(b"\r\n", b"\n")
    lf, crlf = tmp_path / "lf.json", tmp_path / "crlf.json"
    lf.write_bytes(raw)
    crlf.write_bytes(raw.replace(b"\n", b"\r\n"))
    assert check.sha256(lf) == check.sha256(crlf) == _records()[name]


def test_content_change_is_still_detected(tmp_path):
    data = json.loads((BASE / "test_set.json").read_text(encoding="utf-8"))
    data["scenario_ids"] = data["scenario_ids"][:-1]
    changed = tmp_path / "test_set.json"
    changed.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert check.sha256(changed) != _records()["test_set.json"]


def test_frozen_files_are_stored_with_lf():
    for name in FROZEN + ("ground_truth.csv", "INTEGRITY.txt"):
        assert b"\r" not in (BASE / name).read_bytes(), name


def test_ground_truth_csv_export_is_deterministic_and_lf(tmp_path, monkeypatch):
    out = tmp_path / "ground_truth.csv"
    monkeypatch.setattr(export, "DST", out)
    assert export.main() == 0
    produced = out.read_bytes()
    assert b"\r" not in produced
    assert produced == (BASE / "ground_truth.csv").read_bytes()
