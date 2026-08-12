import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json"
PROSE = ROOT / "docs/aislands_isolation_adequacy_preoutcome_contract.md"


def _contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_extension_is_explicitly_preoutcome_and_preserves_authoritative_result() -> None:
    payload = _contract()
    assert payload["outcomes_inspected_for_this_extension"] is False
    assert payload["upstream_frozen"]["surveyed_islands"] == 842
    assert payload["upstream_frozen"]["taxa"] == 886
    assert payload["upstream_frozen"]["authoritative_conditional_concordance"] == 0.6177465917820878
    assert payload["upstream_frozen"]["fold_sha256"] == "221a925e289347069c89354d26acfab83fa3d4bc130b56f0178b8db30ab427fa"
    assert payload["upstream_frozen"]["climate_sha256"] == "6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285"
    assert payload["upstream_frozen"]["cohort_sha256"] == "cf645d55b8bcc46be8a8dc5399db736bbcc20bb7114a72c79a5dee61ec918e12"


def test_primary_contrast_uses_strongest_declared_reference() -> None:
    payload = _contract()
    tiers = payload["reference_tiers"]
    assert "log_area_km2" in tiers["R1"]
    assert "multi_source_pressure" in tiers["R2"]
    for feature in (
        "nearest_other_island_km",
        "surrounding_island_pressure",
        "unanchored_component_exposure",
    ):
        assert feature in tiers["R3"]
    assert tiers["C"][:-1] == tiers["R3"]
    assert tiers["C"][-1] == "geography_only_eog_connected_frequency"
    assert payload["primary_contrast"] == "candidate C minus reference R3 matched held-out log loss"
    assert payload["favourable_direction"] == "negative"


def test_response_derived_features_are_cross_fitted_and_self_excluded() -> None:
    payload = _contract()
    rules = payload["feature_rules"]
    assert rules["training_row_self_anchor_exclusion"] is True
    assert rules["heldout_labels_used"] is False
    assert "training presence a != focal" in rules["multi_source_pressure"]
    assert "outer-training presence other than focal" in rules["geography_only_eog_connected_frequency"]


def test_area_gate_cannot_be_weakened_to_external_posthoc_data() -> None:
    payload = _contract()
    gate = payload["geometry_gate"]
    assert gate["required_positive_finite_area_islands"] == 842
    assert gate["external_area_sources_allowed"] is False
    assert gate["outcome_run_allowed_if_gate_fails"] is False
    text = PROSE.read_text(encoding="utf-8")
    assert "No external island-area database" in text
    assert "do not run the area-adjusted outcome analysis" in text


def test_contract_forbids_postoutcome_reference_weakening() -> None:
    payload = _contract()
    forbidden = set(payload["forbidden_postoutcome_changes"])
    assert "drop area after seeing its effect" in forbidden
    assert "replace R3 primary contrast with a weaker reference" in forbidden
    assert "select favourable taxa" in forbidden
    assert "change geographic scales" in forbidden
