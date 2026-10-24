"""Invented-only verification: do not fit another EOG model or touch bird data."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmarks.audit_eog_source_opportunity_v45 import (
    PROTOCOL, V44_FROZEN, SCHEMA, SOURCE_COLS, LEVELS,
    verify_protocol, classify, summarize,
)


def synthetic(*,ambiguous=True,opportunity=0.5,mi=0.1,policy="cutoff_occupied_confluence_top3",
              panel="primary_early",target="persistent_threshold_lag2",geometry="clustered"):
    fields={
        "design_key":"0|low|rook|0.05|"+geometry,
        "source_geometry":geometry,
        "panel":panel,"cutoff_time":"2","future_target_time":"5",
        "target":target,"policy":policy,
        "target_ambiguous_from_cutoff_occupancy":str(ambiguous),
        "baseline_target_conditional_entropy_bits":"0.6666666666666666" if ambiguous else "0.0",
        "baseline_target_bayes_accuracy":"0.6666666666666666" if ambiguous else "1.0",
        "added_source_information_bits":str(mi),
        "added_target_bayes_accuracy_gain":"0.01" if mi>0 else "0.0",
        "perfect_cutoff_tag_information_bits":"0.25" if mi>0 else "0.0",
        "perfect_cutoff_tag_accuracy_gain":"0.2" if mi>0 else "0.0",
        "mean_nominal_selected_sites":"1.0",
        "mean_cutoff_occupied_selected_sites":str(opportunity),
    }
    assert tuple(fields)==SOURCE_COLS
    return fields


def test_exact_original_source_and_scope_frozen_before_complete_replay():
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source=json.loads(V44_FROZEN.read_text(encoding="utf-8"))
    verify_protocol(p,source)
    assert p["source"]["physical_rows"]==18432
    assert p["source"]["v44_actions_run_id"]==39452406392
    assert p["source"]["original_artifact_id"]==12279172589
    assert p["source"]["original_per_world_csv_sha256"]==(
        "5f7ca0e158f23cc9d479bdb51539458bf6ce4da3dced11a64bd310e80aee5b8e"
    )
    assert p["interpretation_and_stop"]["post_v44_counts_exposed_before_this_protocol"]
    assert p["interpretation_and_stop"]["no_new_EOG_WF_scored_endpoint"]


@pytest.mark.parametrize("row,expected",[
    (synthetic(ambiguous=False,opportunity=0,mi=0),LEVELS[0]),
    (synthetic(ambiguous=True,opportunity=0,mi=0),LEVELS[1]),
    (synthetic(ambiguous=True,opportunity=.333333333333,mi=0),LEVELS[2]),
    (synthetic(ambiguous=True,opportunity=.333333333333,mi=.26),LEVELS[3]),
])
def test_exact_two_gate_category_partition(row,expected):
    assert classify(row)==expected


def test_opportunity_means_potentially_observable_not_guaranteed_label():
    a=synthetic(ambiguous=True,opportunity=.333333333333,mi=0)
    assert classify(a)==LEVELS[2]
    assert a["mean_cutoff_occupied_selected_sites"]!="1.0"
    assert float(a["mean_cutoff_occupied_selected_sites"])>0


def test_positive_target_information_without_potential_tag_opportunity_rejected():
    with pytest.raises(ValueError,match="No selected site"):
        classify(synthetic(opportunity=0,mi=.05))
    with pytest.raises(ValueError,match="Target known"):
        classify(synthetic(ambiguous=False,mi=.05))


def test_invalid_nominal_site_budget_negative_information_and_nonfinite_fail():
    q=synthetic(opportunity=2.0,mi=.01)
    with pytest.raises(ValueError,match="Impossible"):
        classify(q)
    q=synthetic(mi=-.05)
    with pytest.raises(ValueError,match="Impossible"):
        classify(q)
    q=synthetic(mi=float("nan"))
    with pytest.raises(ValueError,match="nonfinite"):
        classify(q)
    q=synthetic(mi=.01)
    q["target_ambiguous_from_cutoff_occupancy"]="Unknown"
    with pytest.raises(ValueError,match="literal True/False"):
        classify(q)


def test_maturity_ambiguity_requires_original_positive_baseline_entropy():
    q=synthetic(ambiguous=True,opportunity=.4,mi=.01)
    q["baseline_target_conditional_entropy_bits"]="0"
    with pytest.raises(ValueError,match="Ambiguous target"):
        classify(q)


def test_one_genuine_target_available_but_no_information_not_called_success():
    cases=[
        synthetic(ambiguous=False,mi=0,opportunity=0),
        synthetic(mi=0,opportunity=0),
        synthetic(mi=0,opportunity=.4),
        synthetic(mi=.12,opportunity=.4),
    ]
    x=summarize(cases,"primary_early","persistent_threshold_lag2",
                "cutoff_occupied_confluence_top3","all_geometries")
    assert x["n_worlds"]==4
    assert x["n_target_uncertain"]==3
    assert x["n_target_known"]==1
    assert x["n_target_uncertain_no_tag_opportunity"]==1
    assert x["n_target_uncertain_tag_opportunity_but_no_information"]==1
    assert x["n_target_uncertain_tag_opportunity_with_information"]==1
    assert x["n_tag_opportunity_given_target_uncertain"]==2
    assert x["target_diagnostic_fraction_given_tag_opportunity"]==pytest.approx(.5)
    assert x["opportunity_fraction_of_target_uncertain"]==pytest.approx(2/3)
    assert x["mean_tag_MI_bits_over_target_uncertain"]==pytest.approx(.04)
    assert x["mean_tag_MI_bits_given_tag_opportunity"]==pytest.approx(.06)


def test_zero_uncertain_denominator_is_null_not_zero_measured_effect():
    only_known=[synthetic(ambiguous=False,opportunity=0,mi=0)]
    x=summarize(only_known,"primary_early","persistent_threshold_lag2",
                "cutoff_occupied_confluence_top3","all_geometries")
    assert x["n_target_uncertain"]==0
    assert x["opportunity_fraction_of_target_uncertain"] is None
    assert x["target_diagnostic_fraction_given_tag_opportunity"] is None
    assert x["mean_tag_MI_bits_over_target_uncertain"] is None


def test_geometry_stratum_and_policy_filters_exact():
    rows=[
        synthetic(ambiguous=False,opportunity=0,mi=0,geometry="clustered"),
        synthetic(ambiguous=True,opportunity=.5,mi=.2,geometry="dispersed"),
        synthetic(ambiguous=True,opportunity=.5,mi=.2,policy="static_sha256_random_top3"),
    ]
    a=summarize(rows,"primary_early","persistent_threshold_lag2",
                "cutoff_occupied_confluence_top3","clustered")
    b=summarize(rows,"primary_early","persistent_threshold_lag2",
                "cutoff_occupied_confluence_top3","dispersed")
    assert (a["n_worlds"],a["n_target_known"])==(1,1)
    assert (b["n_worlds"],b["n_target_uncertain_tag_opportunity_with_information"])==(1,1)


def test_original_source_identity_or_postexposure_caveat_change_fails_closed():
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    old=json.loads(V44_FROZEN.read_text(encoding="utf-8"))
    broken=deepcopy(p)
    broken["source"]["original_per_world_csv_sha256"]="0"*64
    with pytest.raises(ValueError,match="identity changed"):
        verify_protocol(broken,old)
    broken=deepcopy(p)
    broken["interpretation_and_stop"]["post_v44_counts_exposed_before_this_protocol"]=False
    with pytest.raises(ValueError,match="semantics or scope"):
        verify_protocol(broken,old)
    broken=deepcopy(p)
    broken["fixed_diagnostic_rules"]["informative_for_target"]="information when positive"
    with pytest.raises(ValueError,match="semantics or scope"):
        verify_protocol(broken,old)


def test_no_real_data_or_new_field_model_fits_in_derived_audit():
    s=(ROOT/"benchmarks/audit_eog_source_opportunity_v45.py").read_text(encoding="utf-8")
    for forbidden in ("import requests","import urllib","read_csv(","Geneticassignment_README.txt",
                      "Dispersaldata.txt","fit_predict(", "tensorflow", "XGBClassifier"):
        assert forbidden not in s
    assert "load_authenticated_source" in s
    assert "added_source_information_bits" in s
    assert SCHEMA.endswith("v45")
