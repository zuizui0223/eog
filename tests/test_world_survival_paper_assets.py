from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    ROOT
    / "manuscript"
    / "world_survival_identifiability"
    / "build_paper_assets.py"
)

spec = importlib.util.spec_from_file_location(
    "world_survival_paper_assets",
    BUILDER_PATH,
)
assert spec is not None and spec.loader is not None
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_frozen_world_survival_paper_values_and_svg_generation(tmp_path):
    builder.OUT = tmp_path
    rows = builder.load_scored_rows()
    lock = json.loads(builder.LOCK.read_text(encoding="utf-8"))

    builder.validate_lock(rows, lock)
    builder.main()

    manifest = json.loads(
        (tmp_path / "asset_manifest_v1.json").read_text(encoding="utf-8")
    )
    values = manifest["frozen_values"]

    assert values["fixed_sites"] == 16
    assert values["scored_sites"] == 9
    assert values["stopped_sites"] == 7
    assert values["exact_matches"] == 2
    assert values["observed_saturated"] == 7
    assert values["observed_contracting"] == 2
    assert values["observed_falsified"] == 0

    expected = {
        "figure_1_adequacy_vs_survival.svg",
        "figure_2_neon_validation.svg",
        "figure_3_identifiability_witness.svg",
        "table_s1_scored_sites.csv",
        "table_s2_response_consumed_stops.csv",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})

    for name in (
        "figure_1_adequacy_vs_survival.svg",
        "figure_2_neon_validation.svg",
        "figure_3_identifiability_witness.svg",
    ):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert text.startswith("<svg")
        assert "</svg>" in text


def test_figure_two_encodes_all_nine_scored_sites():
    rows = builder.load_scored_rows()
    lock = json.loads(builder.LOCK.read_text(encoding="utf-8"))
    svg = builder.build_figure2(rows, lock)

    for site in ("ABBY", "BARR", "BLAN", "CPER", "DCFS", "DELA", "DSNY", "GRSM", "GUAN"):
        assert site in svg
    assert "exact matches: 2/9" in svg
    assert "MAE = 0.417" in svg


def test_identifiability_figure_states_unchanged_graph_and_positive_count():
    svg = builder.build_figure3()
    assert "Same graph, same positive count" in svg
    assert "global graph unchanged" in svg
    assert "positive-set size unchanged" in svg
