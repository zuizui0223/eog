from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("validation/stoc_eogwf/eligibility_and_preoutcome_contract.json")


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_stoc_source_and_metadata_are_frozen_before_outcome_access():
    contract = _load()
    assert contract["outcomes_inspected_before_freeze"] is False
    source = contract["source"]
    assert source["primary_repository"] == "biomodhub/biomod2"
    assert source["immutable_ref"] == "v4.3-4-6"
    assert source["path"] == "inst/external/DATA_biomod2_STOC.csv"
    assert source["git_blob_sha"] == "4bfa2cd39a7e90340ad6a319e5c611e8646462c8"
    assert source["byte_size"] == 330891

    meta = contract["metadata_only_eligibility"]
    assert meta["declared_rows"] == 2006
    assert meta["declared_sites"] == 1003
    assert meta["declared_species_count"] == 20
    assert meta["declared_periods"] == ["2006-2011", "2012-2017"]


def test_stoc_temporal_response_and_estimability_rules_are_fixed():
    contract = _load()
    response = contract["response_semantics"]
    assert response["primary_binary_target"] == "observed_in_period = raw_response > 0"
    assert "not latent biological occupancy" in response["interpretation"]

    temporal = contract["temporal_design"]
    assert temporal["calibration_period"] == "2006-2011"
    assert temporal["heldout_period"] == "2012-2017"

    species = contract["species_estimability_rule"]
    assert species["calibration_min_positive_sites"] == 30
    assert species["calibration_min_zero_sites"] == 30
    assert species["heldout_min_positive_sites"] == 10
    assert species["heldout_min_zero_sites"] == 10
    assert species["minimum_estimable_species_for_family_claim"] == 10


def test_stoc_world_universe_and_forecast_contract_are_fixed():
    contract = _load()
    worlds = contract["world_universe"]
    assert worlds["world_count"] == 20
    assert worlds["geographic_threshold_rule"].startswith("q25, q50, q75, q90")
    assert worlds["environment_threshold_rule"].startswith("q25, q50, q75, q90")
    assert "not calibrated bird dispersal" in worlds["uncertainty_type"]

    anchor = contract["anchor_and_reconstruction_policy"]
    assert "up to 10" in anchor["anchor_rule"]
    assert anchor["world_survival_rule"].endswith("max_steps=8")

    forecast = contract["forecast_contract"]
    assert forecast["max_steps"] == 8
    assert forecast["primary_horizon"] == 8
    assert forecast["reachability_threshold"] == 1e-15


def test_stoc_comparators_metrics_and_no_retuning_rule_are_fixed():
    contract = _load()
    comparators = contract["comparators"]
    assert len(comparators["same_world_compressions"]) == 3
    assert len(comparators["external"]) == 4
    assert "n_estimators=500" in comparators["hyperparameter_rule"]

    endpoints = contract["primary_endpoints"]
    assert endpoints["prediction_metric"] == "species-macro heldout binary log loss on 2012-2017 observed_in_period"
    assert endpoints["family_summary_unit"] == "species"

    decision = contract["decision_rules"]
    assert decision["no_retuning"] is True
    assert decision["otherwise_status"] == "no_confirmed_predictive_added_value"
    assert "add a new dataset to rescue an adverse result" in contract["forbidden_after_response_open"]
