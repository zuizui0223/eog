import hashlib
import json
import runpy
from pathlib import Path

import pytest


CONTRACT = Path("benchmarks/azores_confirmation_world_contract.json")
CLIMATE = Path("validation/azores_confirmation/azores_climate.csv")
EXPECTED_CLIMATE_SHA256 = "ee2aabd22256dd11bbd412ec59443750af695befc85444cc6f79ea1c3946e22a"
EXPECTED_NODE_ORDER = [
    "corvo", "flores", "faial", "pico", "graciosa",
    "sao_jorge", "terceira", "sao_miguel", "santa_maria",
]

_NS = runpy.run_path("benchmarks/freeze_azores_world_universe.py")
freeze_worlds = _NS["freeze_worlds"]


def _contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_world_contract_is_response_blind_and_binds_gate3_climate():
    contract = _contract()
    assert hashlib.sha256(CLIMATE.read_bytes()).hexdigest() == EXPECTED_CLIMATE_SHA256
    assert contract["upstream"]["climate_table_sha256"] == EXPECTED_CLIMATE_SHA256
    assert contract["node_order"] == EXPECTED_NODE_ORDER
    assert contract["variables"] == ["bio1", "bio5", "bio6", "bio12", "bio15"]
    assert contract["firewall"] == {
        "species_island_incidence_parsed": False,
        "heldout_outcomes_scored": False,
        "predictive_model_fitted": False,
    }


def test_world_contract_freezes_exact_twenty_world_family_before_outcomes():
    definition = _contract()["world_definition"]
    assert definition["geography_only_worlds"] == 4
    assert definition["chelsa_worlds"] == 8
    assert definition["worldclim_worlds"] == 8
    assert definition["total_worlds"] == 20
    assert _contract()["geography"]["quantiles"] == [0.25, 0.50, 0.75, 0.90]
    assert _contract()["environment"]["quantiles"] == [0.50, 0.75]


def test_freezer_builds_deterministic_response_blind_world_universe(tmp_path: Path):
    first = tmp_path / "worlds_a.json"
    first_manifest = tmp_path / "manifest_a.json"
    second = tmp_path / "worlds_b.json"
    second_manifest = tmp_path / "manifest_b.json"

    result_a = freeze_worlds(CLIMATE, first, first_manifest)
    result_b = freeze_worlds(CLIMATE, second, second_manifest)
    payload = json.loads(first.read_text(encoding="utf-8"))

    assert result_a == result_b
    assert first.read_bytes() == second.read_bytes()
    assert payload["node_order"] == EXPECTED_NODE_ORDER
    assert payload["world_count"] == 20
    assert len({world["world_id"] for world in payload["worlds"]}) == 20
    assert payload["family_counts"] == {
        "geography_only": 4,
        "chelsa_q50": 4,
        "chelsa_q75": 4,
        "worldclim_q50": 4,
        "worldclim_q75": 4,
    }
    assert payload["species_incidence_used"] is False
    assert payload["heldout_outcomes_scored"] is False
    assert payload["predictive_model_fitted"] is False
    assert all(world["fingerprint"] for world in payload["worlds"])
    assert payload["world_universe_fingerprint"]


def test_freezer_rejects_any_postfreeze_climate_byte_change(tmp_path: Path):
    altered = tmp_path / "altered.csv"
    altered.write_bytes(CLIMATE.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="frozen climate SHA changed"):
        freeze_worlds(altered, tmp_path / "worlds.json", tmp_path / "manifest.json")
