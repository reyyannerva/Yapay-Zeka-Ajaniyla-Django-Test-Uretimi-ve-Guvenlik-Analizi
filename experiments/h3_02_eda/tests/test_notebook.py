"""Commit edilmiş notebook'un yapısal regresyon testleri — H3-02 / Issue #28."""
from __future__ import annotations

import json

import pytest
from conftest import PKG_ROOT

NOTEBOOK = PKG_ROOT / "H3_02_EDA_Veri_Kalitesi.ipynb"


@pytest.fixture(scope="module")
def code_cells():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return [c for c in nb["cells"] if c["cell_type"] == "code"]


def test_all_cells_executed_in_order_without_errors(code_cells):
    counts = [c["execution_count"] for c in code_cells]
    assert counts == list(range(1, len(code_cells) + 1)), "Notebook baştan sona sırayla çalıştırılmamış."
    for c in code_cells:
        for o in c["outputs"]:
            assert o["output_type"] != "error"
            assert not (o["output_type"] == "stream" and o["name"] == "stderr"), "".join(o["text"])


def test_colab_zip_contains_only_reports_and_figures(code_cells):
    src = next("".join(c["source"]) for c in code_cells if "files.download" in "".join(c["source"]))
    assert "make_archive" not in src
    assert "REPORT_DIR, FIG_DIR" in src


def test_outputs_have_no_local_absolute_paths(code_cells):
    text = json.dumps([c["outputs"] for c in code_cells])
    for marker in ("/home/", "/tmp/", "C:\\\\Users"):
        assert marker not in text
