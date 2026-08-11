from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "manuscript/build_structural_results_tables.py"
MANIFEST = ROOT / "manuscript/result_tables/result_table_manifest.json"
METADATA = ROOT / "manuscript/result_tables/structural_results_tables_metadata.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("eog_results_tables", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_inputs_validate_and_table_shape_is_declared():
    module = load_builder()
    manifest = module.load_json(MANIFEST)
    evidence = module.validate_inputs(manifest)
    table3 = module.build_table3(manifest, evidence)
    applicability = module.build_applicability(manifest, evidence)
    assert len(table3) == 12
    assert len(applicability) == 14
    assert [row["system"] for row in table3[:4]] == ["A-Islands"] * 4
    assert [row["system"] for row in table3[4:]] == ["Tanzania"] * 8


def test_primary_rows_match_frozen_results_exactly():
    module = load_builder()
    manifest = module.load_json(MANIFEST)
    evidence = module.validate_inputs(manifest)
    table3 = module.build_table3(manifest, evidence)

    ais = next(row for row in table3 if row["system"] == "A-Islands" and row["analysis"] == "Combined connected frequency")
    assert ais["effect"] == "0.617747"
    assert ais["ci_low"] == "0.608681"
    assert ais["ci_high"] == "0.626944"
    assert ais["null_value"] == "0.500000"
    assert ais["sign_flip_p"] == "0.00001000"
    assert ais["interpretation"] == "favourable"

    tan_log = next(row for row in table3 if row["system"] == "Tanzania" and row["analysis"] == "Primary weighting | LOSO" and row["metric"] == "log loss difference")
    assert tan_log["effect"] == "0.032113"
    assert tan_log["ci_low"] == "0.017458"
    assert tan_log["ci_high"] == "0.048675"
    assert tan_log["n_matched"] == "826"
    assert tan_log["interpretation"] == "adverse"

    tan_brier = next(row for row in table3 if row["system"] == "Tanzania" and row["analysis"] == "Primary weighting | LOSO" and row["metric"] == "Brier difference")
    assert tan_brier["effect"] == "0.004799"
    assert tan_brier["ci_low"] == "0.002281"
    assert tan_brier["ci_high"] == "0.007315"
    assert tan_brier["interpretation"] == "adverse"


def test_spatial_block_sensitivities_remain_uncertain():
    module = load_builder()
    manifest = module.load_json(MANIFEST)
    table3 = module.build_table3(manifest, module.validate_inputs(manifest))
    spatial = [row for row in table3 if row["system"] == "Tanzania" and "spatial MST blocks" in row["analysis"]]
    assert len(spatial) == 4
    assert {row["interpretation"] for row in spatial} == {"uncertain"}


def test_non_estimability_is_retained():
    module = load_builder()
    manifest = module.load_json(MANIFEST)
    applicability = module.build_applicability(manifest, module.validate_inputs(manifest))
    lookup = {(row["system"], row["analysis"], row["status"]): int(row["count"]) for row in applicability}
    assert lookup[("A-Islands", "primary_combined", "evaluable")] == 3041
    assert lookup[("A-Islands", "primary_combined", "no_comparable_pairs_within_frozen_strata")] == 1190
    assert lookup[("A-Islands", "primary_combined", "insufficient_training_classes")] == 199
    assert lookup[("Tanzania", "primary::primary_loso", "matched")] == 826
    assert lookup[("Tanzania", "primary::primary_loso", "invalid")] == 14
    assert lookup[("Tanzania", "primary::spatial_mst_block", "matched")] == 718
    assert lookup[("Tanzania", "primary::spatial_mst_block", "invalid")] == 122


def test_committed_outputs_match_metadata_fingerprints():
    module = load_builder()
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata["table_3_rows"] == 12
    assert metadata["applicability_rows"] == 14
    for name, expected in metadata["outputs"].items():
        path = ROOT / "manuscript/result_tables" / name
        assert path.is_file()
        assert module.sha256(path) == expected


def test_changed_sidecar_sha_is_rejected(tmp_path: Path):
    module = load_builder()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["inputs"]["aislands_mode_estimates"]["sha256"] = "0" * 64
    altered = tmp_path / "manifest.json"
    altered.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(module.TableContractError, match="SHA changed"):
        module.validate_inputs(module.load_json(altered))
