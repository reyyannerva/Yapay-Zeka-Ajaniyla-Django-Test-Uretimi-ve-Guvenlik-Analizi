"""scenarios.json -> scenarios.csv dışa aktarımının deterministik ve LF olduğu — denetim bulgusu D-03.

Kanonik veri JSON'dur; CSV, H3-02 EDA için türetilmiş kopyadır. Dışa aktarım depodaki CSV'yi bayt
düzeyinde aynen üretmeli; böylece yeniden üretim çalışma kopyasını "değişmiş" göstermez.
"""
import csv
import importlib.util
import json
from pathlib import Path

DRF = Path(__file__).resolve().parents[2]
SCRIPT = DRF / "scripts" / "export_scenarios_csv.py"
CSV_PATH = DRF / "scenarios" / "scenarios.csv"
JSON_PATH = DRF / "scenarios" / "scenarios.json"

_spec = importlib.util.spec_from_file_location("export_scenarios_csv", SCRIPT)
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


def test_export_reproduces_committed_csv_byte_for_byte(tmp_path, monkeypatch):
    out = tmp_path / "scenarios.csv"
    monkeypatch.setattr(export, "DST", out)
    assert export.main() == 0
    produced = out.read_bytes()
    assert b"\r" not in produced
    assert produced == CSV_PATH.read_bytes()


def test_csv_preserves_ids_labels_and_statuses():
    scenarios = json.loads(JSON_PATH.read_text(encoding="utf-8"))["scenarios"]
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8", newline="")))
    assert [r["id"] for r in rows] == [s["id"] for s in scenarios]
    for r, s in zip(rows, scenarios):
        assert (r["label"], r["expected_http_status"], r["http_method"], r["user_role"]) == (
            s["label"], str(s["expected_http_status"]), s["http_method"], s["user_role"])
