"""No new simulation: audit the already frozen virtual-world ecology synthesis."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = (
    ROOT / "validation" / "eog_virtual_world_ecology_synthesis_v1"
    / "claim_ledger_v1.json"
)
SYNTHESIS = ROOT / "docs" / "eog_virtual_world_ecology_synthesis_v1.md"


def _ledger():
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _find(phase):
    entries = [x for x in _ledger()["source_summaries"] if x["phase"] == phase]
    assert len(entries) == 1
    return entries[0]


def _value(phase, name):
    values = [x["expected"] for x in _find(phase)["observations"] if x["name"] == name]
    assert len(values) == 1
    return values[0]


def test_all_claimed_numbers_and_git_blobs_match_frozen_results():
    ledger = _ledger()
    assert ledger["schema"] == "eog.virtual_world_source_geometry_synthesis.v1"
    assert ledger["status"] == "post_result_cross_phase_audit_only"
    assert ledger["preregistered_joint_test"] is False
    assert ledger["new_simulations_run"] is False
    assert ledger["paper_decision"].startswith("NO_NEW_MANUSCRIPT_LANE")
    assert [x["phase"] for x in ledger["source_summaries"]] == [
        "v10", "v12", "v18", "v19", "v20", "v21", "v22", "v26"
    ]

    for source in ledger["source_summaries"]:
        path = ROOT / source["path"]
        raw = path.read_bytes()
        git_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()
        assert git_blob == source["git_blob_sha"], source["phase"]
        result = json.loads(raw.decode("utf-8"))
        assert result["result_fingerprint"] == source["result_fingerprint"]
        assert result["authoritative_run"] == source["authoritative_run"]
        assert result["protocol"] == source["protocol"]
        for observation in source["observations"]:
            actual = result
            for key in observation["json_path"]:
                actual = actual[key]
            assert actual == observation["expected"], (
                source["phase"], observation["name"], actual, observation["expected"]
            )


def test_ecological_source_geometry_payoff_not_inferred_from_source_count():
    assert _value("v18", "landscapes") == 384
    assert _value("v18", "dispersed_2_coverage") > _value("v18", "clustered_2_coverage")
    assert _value("v18", "clustered_2_insurance") > _value("v18", "dispersed_2_insurance")
    assert _value("v18", "clustered_2_overlap") > _value("v18", "dispersed_2_overlap")
    assert _value("v18", "coverage_insurance_tradeoff_rows") == 280
    assert _value("v18", "two_dispersed_gt_three_clustered_rows") == 225
    assert _value("v20", "design_rows") == 768
    assert _value("v20", "replacement_changes_coverage") == 718
    assert _value("v20", "all_strategies_below_original") == 352
    assert _value("v20", "overshoot_cases") == 407


def test_history_observability_distinguished_from_effect_on_landscape():
    assert _value("v19", "clustered_2_ambiguous_fraction") > _value(
        "v19", "dispersed_2_ambiguous_fraction"
    )
    assert _value("v21", "equilibrium_occupancy_equality_violations") == 0
    assert _value("v21", "equilibrium_provenance_diff_rows") == 507
    assert _value("v21", "clustered_provenance_disagreement") > _value(
        "v21", "dispersed_provenance_disagreement"
    )
    assert _value("v22", "dispersed_history_identifiable") == 348
    assert _value("v22", "clustered_history_identifiable") == 231
    assert _value("v22", "clustered_min_snapshots_if_identifiable") == 1
    assert _value("v22", "dispersed_min_snapshots_if_identifiable") == 1
    assert _value("v22", "earlier_timing_beats_t8_rows") == 428


def test_known_truth_structure_and_refuted_history_mapping_are_preserved():
    assert _value("v10", "replicates") == 192
    assert _value("v10", "knockout_retained_chain_14") < _value(
        "v10", "knockout_retained_star_14"
    )
    assert _value("v12", "replicates") == 144
    assert _value("v12", "worlds_per_row") == 12
    assert _value("v12", "edge_robustness_spearman") > 0
    assert _value("v12", "edge_firstpassage_spearman") < 0
    assert _value("v26", "blind_memory_rows") == 0
    assert _value("v26", "threshold_memory_rows") == 726
    assert _value("v26", "transient_memory_rows") == 726
    assert _value("v26", "threshold_hidden_age_aliases_detected") == 12
    assert _value("v26", "transient_hidden_age_aliases_detected") == 45
    assert _value("v26", "claim_process_incidence_changes") == "REFUTED"
    assert _value("v26", "claim_richer_recovers_threshold_hidden") == "REFUTED"


def test_claim_boundaries_avoid_unjustified_third_manuscript():
    ledger = _ledger()
    claims = {x["id"]: x for x in ledger["admissible_claims"]}
    assert set(claims) == {"A", "B", "C", "D", "E"}
    failures = {x["id"]: x for x in ledger["refused_or_unproven"]}
    assert set(failures) == {"R1", "R2", "U1", "U2"}
    assert failures["R1"]["status"] == "REFUTED_in_v22_Q3"
    assert failures["R2"]["status"] == "REFUTED_in_v26_P5"
    assert failures["U1"]["status"] == "NOT_TESTED"
    assert failures["U2"]["status"] == "NOT_TESTED"
    assert all(phase in {z["phase"] for z in ledger["source_summaries"]}
               for claim in list(claims.values()) + list(failures.values())
               for phase in claim["evidence"])

    doc = SYNTHESIS.read_text(encoding="utf-8")
    for text in (
        "not a single preregistered three-way mediation test",
        "P5 REFUTED",
        "Q3",
        "HOLD third paper",
        "STOP_NOT_IDENTIFIABLE",
        "not a new network-robustness theorem",
    ):
        assert text.lower() in doc.lower(), text
    assert "preregistered_joint_test" in json.dumps(ledger)
