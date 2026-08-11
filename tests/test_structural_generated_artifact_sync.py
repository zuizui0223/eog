from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT_BUILDER = ROOT / "manuscript" / "build_structural_results_tables.py"
RESULT_MANIFEST = ROOT / "manuscript" / "result_tables" / "result_table_manifest.json"
TABLE3 = ROOT / "manuscript" / "result_tables" / "table_3_main_sensitivity_results.csv"
TABLE_S1 = ROOT / "manuscript" / "result_tables" / "table_s1_applicability_accounting.csv"
RESULT_MD = ROOT / "manuscript" / "result_tables" / "structural_results_tables.md"
RESULT_METADATA = ROOT / "manuscript" / "result_tables" / "structural_results_tables_metadata.json"
FIGURE5_BUILDER = ROOT / "figures" / "build_figure_5_audit.py"
FIGURE5_CONTRACT = ROOT / "figures" / "figure_5_audit_contract.json"
FIGURE5_SVG = ROOT / "figures" / "output" / "figure_5_audit.svg"
FIGURE5_ALT = ROOT / "manuscript" / "figure_5_accessibility.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_result_tables_equal_current_frozen_builder_projection() -> None:
    module = _load(RESULT_BUILDER, "eog_result_sync")
    manifest = module.load_json(RESULT_MANIFEST)
    evidence = module.validate_inputs(manifest)
    assert module.read_csv(TABLE3) == module.build_table3(manifest, evidence)
    assert module.read_csv(TABLE_S1) == module.build_applicability(manifest, evidence)


def test_full_result_table_rebuild_is_byte_identical() -> None:
    module = _load(RESULT_BUILDER, "eog_result_rebuild")
    paths = (TABLE3, TABLE_S1, RESULT_MD, RESULT_METADATA)
    before = {path: path.read_bytes() for path in paths}
    try:
        module.build()
        for path in paths:
            assert path.read_bytes() == before[path]
    finally:
        for path, payload in before.items():
            path.write_bytes(payload)


def test_all_tanzania_rows_remain_synced_to_frozen_expected_projection() -> None:
    module = _load(RESULT_BUILDER, "eog_result_values")
    manifest = module.load_json(RESULT_MANIFEST)
    table = module.build_table3(manifest, module.validate_inputs(manifest))
    lookup = {(row["analysis"], row["metric"]): row for row in table if row["system"] == "Tanzania"}
    expected = {
        ("Primary weighting | LOSO", "log loss difference"): ("0.032113", "0.017458", "0.048675"),
        ("Inverse-area weighting | LOSO", "log loss difference"): ("0.030630", "0.016214", "0.046937"),
        ("Primary weighting | spatial MST blocks", "log loss difference"): ("0.010954", "-0.012171", "0.033431"),
        ("Inverse-area weighting | spatial MST blocks", "log loss difference"): ("0.005702", "-0.015533", "0.025824"),
    }
    for key, values in expected.items():
        row = lookup[key]
        assert (row["effect"], row["ci_low"], row["ci_high"]) == values


def test_committed_figure5_matches_current_audit_builder() -> None:
    module = _load(FIGURE5_BUILDER, "eog_figure5_sync")
    contract, figure_manifest, result_manifest, result_metadata = module.validate_contract(FIGURE5_CONTRACT)
    records = module.build_records(contract, figure_manifest, result_manifest, result_metadata)
    assert FIGURE5_SVG.read_text(encoding="utf-8") == module.render_svg(contract, records)
    assert FIGURE5_ALT.read_text(encoding="utf-8") == module.accessibility_text(records)
