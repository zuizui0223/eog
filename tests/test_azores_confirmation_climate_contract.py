import hashlib
import json
from pathlib import Path


CONTRACT = Path("benchmarks/azores_confirmation_climate_contract.json")
NODES = Path("validation/azores_confirmation/azores_nodes.csv")
EXPECTED_NODE_SHA256 = "df6117ce4b68098b22ab6af0c769cbdbfa9f9adf1101307b2619b206e624dc62"


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_climate_contract_uses_the_immutable_frozen_node_table():
    contract = _load()
    assert contract["frozen_node_table"] == str(NODES)
    assert hashlib.sha256(NODES.read_bytes()).hexdigest() == EXPECTED_NODE_SHA256


def test_climate_products_and_variables_are_declared_before_sampling():
    contract = _load()
    assert contract["variables"] == ["bio1", "bio5", "bio6", "bio12", "bio15"]
    assert contract["products"]["chelsa"]["version"] == "2.1"
    assert contract["products"]["worldclim"]["version"] == "2.1"
    assert contract["products"]["worldclim"]["resolution"] == "2.5m"


def test_climate_gate_forbids_coordinate_and_missing_value_rescue():
    contract = _load()
    rule = contract["sampling_rule"].lower()
    assert "no snapping" in rule
    assert "imputation" in rule
    assert "coordinate replacement" in rule
    assert "resolution change" in rule
    rules = "\n".join(contract["stop_rules"])
    assert "missing/nodata" in rules
    assert "do not parse species-island incidence" in rules


def test_outcome_firewall_remains_closed():
    assert _load()["firewall"] == {
        "species_island_incidence_parsed": False,
        "world_universe_frozen": False,
        "outcome_statistics_computed": False,
    }
