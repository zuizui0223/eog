"""Geographic site-level systematic A/B/M error: exact robustness contracts."""
from pathlib import Path
import json

import pytest

from benchmarks import bam_systematic_site_error_v1 as m


def model(a,b,move,sign):
    return {"masks":(a,b,move),"sign":sign,"n_labels":1}


def test_one_discriminating_site_cannot_correct_site_wide_bias():
    states=[model(0,0,0,-1), model(1,0,0,1)]
    zero=m.min_site_panel(states,3,corrupt_sites=0)
    robust=m.min_site_panel(states,3,corrupt_sites=1)
    assert zero["minimum_sites"]==1
    assert zero["status"]=="OPTIMAL"
    assert robust["status"]=="IMPOSSIBLE"
    assert robust["minimum_sites"] is None
    assert robust["min_pairwise_separating_sites"]==1


def test_two_discriminating_sites_still_insufficient():
    states=[model(0,0,0,-1),model(0b11,0,0,1)]
    assert m.min_site_panel(states,3,corrupt_sites=1)["status"]=="IMPOSSIBLE"


def test_three_distinct_geographic_sites_allow_one_corrupted_site():
    states=[model(0,0,0,-1),model(0b111,0,0,1)]
    robust=m.min_site_panel(states,4,corrupt_sites=1)
    assert robust["status"]=="OPTIMAL"
    assert robust["minimum_sites"]==3
    assert robust["sites"]==[0,1,2]
    assert robust["minimum_axis_readings"]==9
    assert m.validate_all_site_corruptions(states,robust["sites"],corrupt_sites=1)


def test_three_axes_at_one_site_do_not_count_as_three_independent_sites():
    states=[model(0,0,0,-1),model(1,1,1,1)]
    x=m.min_site_panel(states,3,corrupt_sites=1)
    assert x["status"]=="IMPOSSIBLE"
    assert x["min_pairwise_separating_sites"]==1
    assert m.min_site_panel(states,3,corrupt_sites=0)["minimum_sites"]==1


def test_systematic_decoder_rejects_two_site_separation():
    states=[model(0,0,0,-1),model(3,0,0,1)]
    assert not m.validate_all_site_corruptions(states,[0,1],corrupt_sites=1)
    assert m.validate_all_site_corruptions(states,[0],corrupt_sites=0)


def test_unanimous_target_does_not_need_any_site():
    states=[model(0,0,0,0),model(7,7,7,0)]
    r=m.min_site_panel(states,4,corrupt_sites=1)
    assert r["status"]=="OPTIMAL"
    assert r["minimum_sites"]==0
    assert r["sites"]==[]


def test_invalid_mask_and_error_budget_fail_closed():
    states=[model(0,0,0,-1),model(7,0,0,1)]
    with pytest.raises(ValueError):
        m.min_site_panel(states,2,corrupt_sites=1)
    with pytest.raises(ValueError):
        m.min_site_panel(states,3,corrupt_sites=2)


def test_frozen_source_contract_and_budget():
    p=json.loads(Path("validation/bam_systematic_site_error_v1/protocol_v1.json").read_text())
    assert p["source"]["n_worlds"]==768
    assert p["source"]["n_distinct_observed_D"]==2627
    assert p["assay"]["optimization"].startswith("SciPy MILP")
    assert p["assay"]["max_site_budget"]==[0,1,2,3,4,5,6,8,10,12,15]
