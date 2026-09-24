import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation" / "layer_b_mechanism_v3" / "protocol_v1.json"


def _load():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_v3_protocol_cannot_reopen_closed_eogwf_endpoints():
    protocol = _load()
    separation = protocol["scientific_separation"]
    assert separation["post_closure_research"] is True
    assert separation["changes_closed_eog_wf_synthesis"] is False
    assert separation["counts_as_fourth_eog_wf_endpoint"] is False
    assert separation["consumed_endpoint_rescoring_allowed"] is False
    assert separation["consumed_response_reopening_allowed"] is False


def test_v3_protocol_uses_compact_source_symmetric_representation():
    protocol = _load()
    representation = protocol["representation"]
    assert representation["source_label_invariant"] is True
    assert representation["world_label_invariant"] is True
    assert representation["feature_representation"] == (
        "compact_source_symmetric_world_support_summary_v3_candidate"
    )
    assert representation["feature_names"] == [
        "surviving_world_fraction",
        "support_mean",
        "support_std",
        "support_min",
    ]
    assert "support_range" in representation["deterministic_expansions_forbidden"]
    assert (
        representation["larger_world_universe_requires_independent_scientific_justification"]
        is True
    )


def test_v3_primary_and_placebo_randomness_are_symmetric():
    protocol = _load()
    learner = protocol["learner_seed_contract"]
    placebo = protocol["placebo_contract"]

    assert learner["require_multiple_primary_seeds"] is True
    assert learner["same_seed_sequence_baseline_and_augmented"] is True
    assert len(learner["learner_seeds"]) == 10
    assert len(set(learner["learner_seeds"])) == 10
    assert (
        learner["placebo_may_not_receive_richer_learner_seed_treatment_than_primary"]
        is True
    )

    assert placebo["independent_column_permutation_allowed"] is False
    assert placebo["preserve_cross_column_joint_structure"] is True
    assert placebo["admissible_modes"] == ["joint_row", "group_vector"]
    assert len(placebo["permutation_seeds"]) == 10


def test_v3_does_not_relabel_tampa_causally():
    protocol = _load()
    claims = protocol["mechanism_claim_boundary"]
    assert claims["tampa_adverse_status_remains_frozen"] is True
    assert claims["tampa_cause_identified"] is False
    assert claims["v3_improvement_would_not_retroactively_rescue_tampa"] is True
