"""Guards for a post-result, non-confirmatory match of frozen EOG simulations."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = (ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
               / "matched_source_history_exploratory_result_v1.json")
SCRIPT = ROOT / "scripts/audit_matched_eog_source_history_v1.py"


def load_script():
    spec = importlib.util.spec_from_file_location("eog_matched_history", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def result():
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def test_archived_pins_match_eight_year_frozen_result_source():
    x = result()
    assert x["schema"] == "eog.virtual_worlds.matched_source_geometry_history.v1"
    assert x["status"] == "POST_RESULT_EXPLORATORY_NOT_PREREGISTERED"
    assert x["three_sources_per_design"] is True
    assert x["matched_landscapes"] == 384
    assert x["source_identity_mismatches"] == 0
    assert "occupancy snapshots, not a direct provenance assay" in x["readout"]

    script = load_script()
    assert set(script.ARCHIVES) == {"v18", "v19", "v21", "v22"}
    for phase, summary_path in (
        ("v18", "validation/eog_original_idea_source_placement_v18/result_summary_v18.json"),
        ("v19", "validation/eog_original_idea_source_confluence_v19/result_summary_v19.json"),
        ("v21", "validation/eog_original_idea_source_history_memory_v21/result_summary_v21.json"),
        ("v22", "validation/eog_original_idea_history_observability_v22/result_summary_v22.json"),
    ):
        summary = json.loads((ROOT / summary_path).read_text(encoding="utf-8"))
        assert script.ARCHIVES[phase]["fingerprint"] == x["fingerprints"][phase]
        assert summary["result_fingerprint"] == x["fingerprints"][phase]
        assert summary["authoritative_artifact_digest"] == (
            "sha256:" + x["artifact_zip_sha256"][phase]
        )
        assert script.ARCHIVES[phase]["sha256"] == x["artifact_zip_sha256"][phase]


def test_joint_counts_are_paired_not_pooled_studies():
    x = result()
    assert x["counts"] == {
        "three_source_coverage_insurance_tradeoff": 281,
        "dispersed_only_history_identifiable": 139,
        "clustered_only_history_identifiable": 22,
        "joint_tradeoff_and_dispersed_only_identifiable": 130,
        "clustered_more_provenance_but_dispersed_only_identifiable": 131,
        "clustered_more_overlap_but_dispersed_only_identifiable": 131,
    }
    assert x["history_identifiability_contingency"] == {
        "neither": 14,
        "dispersed_only": 139,
        "clustered_only": 22,
        "both": 209,
    }
    assert sum(x["history_identifiability_contingency"].values()) == 384
    assert x["counts"]["joint_tradeoff_and_dispersed_only_identifiable"] <= (
        x["counts"]["three_source_coverage_insurance_tradeoff"]
    )
    assert x["counts"]["clustered_more_provenance_but_dispersed_only_identifiable"] <= (
        x["counts"]["dispersed_only_history_identifiable"]
    )
    for direction in x["direction_counts"].values():
        assert sum(direction.values()) == 384
    for factor, groups in x["strata"].items():
        assert sum(y["n"] for y in groups.values()) == 384, factor
        assert sum(y["joint"] for y in groups.values()) == 130, factor
        assert sum(y["tradeoff"] for y in groups.values()) == 281, factor
        assert sum(y["dispersed_only"] for y in groups.values()) == 139, factor
        assert sum(y["clustered_only"] for y in groups.values()) == 22, factor
    assert len(x["boundaries"]) >= 5
    assert "not a new randomized or preregistered" in x["boundaries"][0]


def _fixture():
    output = {}
    for placement, cov, ins, overlap, prov, identifiable in (
        ("clustered", 0.40, 0.70, 0.60, 0.70, False),
        ("dispersed", 0.50, 0.25, 0.10, 0.10, True),
    ):
        ids = ["r0c0", "r1c0", "r2c0"] if placement == "clustered" else ["r0c0", "r6c6", "r3c5"]
        output[placement] = {
            "v18": {"source_ids": ids, "union_reachable_node_count": 12,
                    "union_reachable_fraction": cov, "worst_source_loss_retention": ins,
                    "multi_source_overlap_fraction": overlap},
            "v19": {"source_ids": ids, "union_reachable_node_count": 12,
                    "static_ambiguous_fraction": overlap},
            "v21": {"source_ids": ids, "equilibrium_union_node_count": 12,
                    "static_origin_ambiguity_fraction": overlap,
                    "equilibrium_occupancy_equal_across_histories": True,
                    "provenance_disagreement_fraction": prov,
                    "mean_pairwise_transient_occupancy_jaccard_distance": 0.1},
            "v22": {"source_ids": ids, "equilibrium_snapshot_identical": True,
                    "full_history": {"identified": identifiable,
                                     "minimum_size": 1 if identifiable else None}},
        }
    return {
        "v18": {"anchor_source": "r0c0", "designs": {
            p: {"3": output[p]["v18"]} for p in output}},
        "v19": {"anchor_source": "r0c0", "designs": {
            p: {"3": output[p]["v19"]} for p in output}},
        "v21": {"anchor_source": "r0c0", "designs": {
            p: output[p]["v21"] for p in output}},
        "v22": {"designs": {p: output[p]["v22"] for p in output}},
    }


def test_matched_rows_require_same_three_sources_and_same_equilibrium():
    script = load_script()
    key = ("low", "rook", 0.2, 0)
    valid = _fixture()
    row = script.verify_matched_record(key, valid)
    diff = script.paired_differences(row)
    assert diff["coverage_d_minus_c"] == pytest.approx(0.10)
    assert diff["insurance_c_minus_d"] == pytest.approx(0.45)
    assert diff["provenance_c_minus_d"] == pytest.approx(0.60)
    assert diff["observability_d_minus_c"] == 1

    bad = copy.deepcopy(valid)
    bad["v22"]["designs"]["dispersed"]["source_ids"][2] = "DIFFERENT"
    with pytest.raises(ValueError, match="source identities differ"):
        script.verify_matched_record(key, bad)

    bad = copy.deepcopy(valid)
    bad["v21"]["designs"]["clustered"]["equilibrium_occupancy_equal_across_histories"] = False
    with pytest.raises(ValueError, match="history-aliased"):
        script.verify_matched_record(key, bad)

    bad = copy.deepcopy(valid)
    bad["v19"]["designs"]["clustered"]["static_ambiguous_fraction"] = 0.0
    with pytest.raises(ValueError, match="source-basin definitions"):
        script.verify_matched_record(key, bad)
