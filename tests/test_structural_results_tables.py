from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "manuscript/build_structural_results_tables.py"
MANIFEST = ROOT / "manuscript/result_tables/result_table_manifest.json"
METADATA = ROOT / "manuscript/result_tables/structural_results_tables_metadata.json"
AIS_STRONG_FP = "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"


def load_builder():
    spec = importlib.util.spec_from_file_location("eog_results_tables", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_inputs_validate_and_table_shape_is_declared():
    module = load_builder()
    manifest = module.load_json(MANIFEST)
    assert manifest["schema_version"] == "eog_structural_results_tables_v2"
    evidence = module.validate_inputs(manifest)
    table3 = module.build_table3(manifest, evidence)
    applicability = module.build_applicability(manifest, evidence)
    assert len(table3) == 14
    assert len(applicability) == 16
    assert [row["system"] for row in table3[:6]] == ["A-Islands"] * 6
    assert [row["system"] for row in table3[6:]] == ["Tanzania"] * 8


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

    strong_log = next(row for row in table3 if row["system"] == "A-Islands" and row["analysis"] == "Prospective strong island reference | C vs R3" and row["metric"] == "log loss difference")
    assert strong_log["n_species"] == "886"
    assert strong_log["n_matched"] == "712515"
    assert strong_log["effect"] == "0.003485"
    assert strong_log["ci_low"] == "0.002466"
    assert strong_log["ci_high"] == "0.004508"
    assert strong_log["sign_flip_p"] == "0.00001000"
    assert strong_log["interpretation"] == "adverse"

    strong_brier = next(row for row in table3 if row["system"] == "A-Islands" and row["analysis"] == "Prospective strong island reference | C vs R3" and row["metric"] == "Brier difference")
    assert strong_brier["effect"] == "0.000268"
    assert strong_brier["ci_low"] == "0.000079"
    assert strong_brier["ci_high"] == "0.000457"
    assert strong_brier["interpretation"] == "adverse"

    tan_log = next(row for row in table3 if row["system"] == "Tanzania" and row["analysis"] == "Primary weighting | LOSO" and row["metric"] == "log loss difference")
    assert tan_log["effect"] == "0.032113"
    assert tan_log["ci_low"] == "0.017458"
    assert tan_log["ci_high"] == "0.048675"
    assert tan_log["n_matched"] == "826"
    assert tan_log["interpretation"] == "adverse"


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
    assert lookup[("A-Islands", "isolation_adequacy_C_vs_R3", "evaluable_folds")] == 4231
    assert lookup[("A-Islands", "isolation_adequacy_C_vs_R3", "insufficient_training_class_count_5_5")] == 199
    assert lookup[("Tanzania", "primary::primary_loso", "matched")] == 826
    assert lookup[("Tanzania", "primary::primary_loso", "invalid")] == 14
    assert lookup[("Tanzania", "primary::spatial_mst_block", "matched")] == 718
    assert lookup[("Tanzania", "primary::spatial_mst_block", "invalid")] == 122


def test_committed_outputs_match_metadata_fingerprints():
    module = load_builder()
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata["schema_version"] == "eog_structural_results_tables_v2"
    assert metadata["table_3_rows"] == 14
    assert metadata["applicability_rows"] == 16
    assert metadata["aislands_strong_reference_result_fingerprint"] == AIS_STRONG_FP
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
