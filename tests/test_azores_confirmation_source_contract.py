import json
from pathlib import Path


CONTRACT = Path("benchmarks/azores_confirmation_source_contract.json")


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_source_identity_is_frozen_before_any_response_work():
    contract = _load()
    dataset = contract["dataset"]
    assert dataset["gbif_uuid"] == "ec1a0bfb-7d8e-4c6b-bc4d-dfd68a1e844f"
    assert dataset["doi"] == "10.15468/hyvwxi"
    assert dataset["title"] == "A list of the terrestrial and marine biota from the Azores"
    assert dataset["publisher"] == "Universidade dos Açores"
    assert dataset["license"] == "CC BY 4.0"

    firewall = contract["response_firewall"]
    assert firewall == {
        "archive_downloaded": False,
        "archive_content_parsed": False,
        "species_island_incidence_parsed": False,
        "climate_sampled": False,
        "world_universe_frozen": False,
        "outcome_statistics_computed": False,
    }


def test_metadata_scope_contains_exactly_the_nine_declared_islands():
    contract = _load()
    scope = contract["candidate_scope_metadata_only"]
    assert scope["expected_island_count"] == 9
    assert scope["declared_islands"] == [
        "Corvo",
        "Flores",
        "Faial",
        "Pico",
        "Graciosa",
        "São Jorge",
        "Terceira",
        "São Miguel",
        "Santa Maria",
    ]


def test_contract_keeps_preoutcome_stop_rules_explicit():
    rules = "\n".join(_load()["stop_rules"])
    assert "species-island incidence" in rules
    assert "nodata" in rules
    assert "do not snap" in rules
    assert "transport fallback" in rules
