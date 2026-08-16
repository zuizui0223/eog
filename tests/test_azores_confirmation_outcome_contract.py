import json
from pathlib import Path


CONTRACT = Path("benchmarks/azores_confirmation_outcome_contract.json")
SCHEMA = Path("validation/azores_confirmation/dwca_schema_record.json")


def _contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_contract_was_frozen_at_schema_only_firewall():
    contract = _contract()
    schema = _schema()
    assert schema["response_values_inspected"] is False
    assert schema["eog_outcome_computed"] is False
    assert contract["firewall_at_freeze"] == {
        "taxon_rows_read": False,
        "distribution_rows_read": False,
        "species_island_response_values_inspected": False,
        "confirmation_models_fitted": False,
        "confirmation_metric_computed": False,
    }


def test_schema_supports_the_predeclared_response_fields():
    schema = _schema()
    core = set(schema["core"]["fields"])
    distribution = set(schema["distribution_extension"]["fields"])
    assert {
        "taxonID", "acceptedNameUsageID", "scientificName", "higherClassification",
        "kingdom", "phylum", "taxonRank",
    }.issubset(core)
    assert {"locality", "occurrenceStatus", "establishmentMeans"}.issubset(distribution)


def test_primary_comparison_is_exact_identity_against_strong_compressed_R2():
    contract = _contract()
    assert contract["frozen_world_universe"]["world_count"] == 20
    assert contract["frozen_world_universe"]["fingerprint"] == "0cdf326bb0aa670b10bb7004b6cbb5294c3c5f9cb22c4c45601482535f583ec6"
    assert contract["primary_metric"]["primary_contrast"] == "C_identity_minus_R2"
    assert contract["features"]["R1_addition"] == "total 20-world reachability frequency"
    assert len(contract["features"]["R2_additions"]) == 5
    assert contract["features"]["C_identity_addition"] == "complete ordered 20-bit world reachability vector"


def test_nine_island_scale_rules_are_fixed_before_response_access():
    contract = _contract()
    validation = contract["outer_validation"]
    gate = contract["favourable_gate"]
    assert validation["split"] == "leave_one_island_out_9"
    assert validation["minimum_outer_training_positive_islands"] == 2
    assert validation["minimum_outer_training_catalogue_nonrecord_islands"] == 2
    assert validation["minimum_evaluable_outer_islands"] == 7
    assert gate["minimum_evaluable_outer_islands"] == 7
    assert gate["C_better_outer_islands_at_least"] == 6
    assert gate["all_conditions_required"] is True


def test_catalogue_zero_is_not_biological_absence_and_no_retuning_is_allowed():
    contract = _contract()
    assert "never biological absence" in contract["response"]["zero_interpretation"]
    assert "Do not retune" in contract["no_added_value_rule"]
    assert "true dispersal routes" in contract["claim_if_favourable"]
