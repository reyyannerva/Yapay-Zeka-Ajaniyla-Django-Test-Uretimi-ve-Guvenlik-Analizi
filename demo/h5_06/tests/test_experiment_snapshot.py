"""Frontend deney anlık görüntüsü H5-05 sonuçlarıyla birebir aynı olmalı (H5-06 / #44)."""
from __future__ import annotations

import json

from demo.h5_06 import export_experiment_snapshot as ex


def test_snapshot_is_current():
    assert ex.TARGET.read_text(encoding="utf-8") == ex.render(), \
        "anlık görüntü eski: python -m demo.h5_06.export_experiment_snapshot"


def test_snapshot_values_are_copied_not_recomputed():
    src = json.loads(ex.SOURCE.read_text(encoding="utf-8"))
    snap = json.loads(ex.TARGET.read_text(encoding="utf-8"))
    for layer in snap["layers"]:
        for m in layer["methods"]:
            s = src["layers"][layer["key"]]["methods"][m["key"]]
            assert m["f1"]["exact"] == s["f1"]["exact"] and m["f1"]["display"] == s["f1"]["display"]
            assert m["confusion"] == s["confusion"]
            assert (m["firstPassExecutable"]["count"], m["firstPassExecutable"]["of"]) == \
                (s["first_pass_executable"]["count"], s["first_pass_executable"]["of"])


def test_unmeasurable_values_stay_null():
    snap = json.loads(ex.TARGET.read_text(encoding="utf-8"))
    a = next(l for l in snap["layers"] if l["key"] == "A")
    assert all(m["f1"]["value"] is None and m["f1"]["display"] == "Ölçülemedi" for m in a["methods"])
