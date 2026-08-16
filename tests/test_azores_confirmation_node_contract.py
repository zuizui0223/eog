import json
from pathlib import Path


CONTRACT = Path("benchmarks/azores_confirmation_node_contract.json")


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_node_rule_is_response_blind_and_exactly_nine_islands():
    contract = _load()
    assert contract["expected_node_count"] == 9
    assert len(contract["targets"]) == 9
    assert len({row["island_id"] for row in contract["targets"]}) == 9
    assert contract["selection_rule"]["feature_class"] == "T"
    assert contract["selection_rule"]["feature_code"] == "ISL"
    assert contract["selection_rule"]["require_exactly_one_match_per_target"] is True
    assert contract["selection_rule"]["require_distinct_geonameids"] is True


def test_node_gate_does_not_open_climate_or_species_outcomes():
    firewall = _load()["firewall"]
    assert firewall == {
        "species_island_incidence_parsed": False,
        "climate_sampled": False,
        "world_universe_frozen": False,
        "outcome_statistics_computed": False,
    }


def test_coordinates_cannot_be_rescued_after_climate_is_seen():
    rules = "\n".join(_load()["stop_rules"])
    assert "zero or multiple" in rules
    assert "do not move or snap coordinates" in rules
    assert "do not sample climate" in rules
