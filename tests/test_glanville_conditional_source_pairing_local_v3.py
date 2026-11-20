import hashlib
import json
import runpy
import numpy as np
import pytest


def _m():
    return runpy.run_path("scripts/glanville_conditional_source_pairing_local_v3.py")


def _protocol():
    return json.load(open("validation/glanville_conditional_pairing_null_v3/protocol_v3.json"))


def _toy():
    # Five years, each with three source sites and three distinct t−1
    # zero -> t positive targets, all mapped; not actual sample records.
    assigned=[]
    genetic=[]
    survey={}
    network={}
    for year in range(2007,2012):
        for j in range(3):
            source=f"s_{year}_{j}"
            target=f"t_{year}_{j}"
            network[source]=(float(j+1),float(year-2007))
            network[target]=(0.,float(year-2007)+j*0.1)
            survey[(year,source)]=(j+1.,float(j),0.)
            survey[(year,target)]=(0.,0.,0.)
            survey[(year+1,target)]=(1.,0.,0.)
            d=float(np.linalg.norm(np.array(network[source])-np.array(network[target])))
            assigned.append({"source":source,"target":(year+1,target),
                             "year":year+1,"family":(year,f"fam{j}"),
                             "distance":d,"host_gap":float(j)})
            genetic.append((year,year+1,source,target,f"fam{j}",1,d))
    return assigned,genetic,survey,network


def test_protocol_frozen_prior_to_statistic_and_new_encrypted_source():
    p=_protocol()
    assert p["status"]=="frozen_before_opportunity_null_scoring_and_2019_source_reacquisition"
    assert p["sources"]["genetics"]["sha256"]=="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
    assert p["sources"]["survey"]["sha256"]=="c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9"
    assert p["predeclared_primary_conditional_recombination_null"]["seed"]==20261120
    assert p["predeclared_primary_conditional_recombination_null"]["monte_carlo_replicates"]==1999
    assert p["predeclared_secondary_distance_matched_reference"]["min_distinct_candidate_sites"]==3


def test_exact_yearwise_source_frequency_and_zero_self_preserving_permutations():
    m=_m()
    assigned,genetic,survey,network=_toy()
    r=m["permutation"](assigned,survey,network,reps=99,seed=20261120)
    assert r["replicates"]==99
    assert r["target_patch_years"]==15 and r["assignment_rows"]==15
    assert r["total_permutation_year_proposals"]>=99*5
    assert r["rejected_self_pairs"]==0
    assert len(r["per_year_descriptive"])==5
    for k in ("distance_target_equal_mean_within_target_median_log1p_km",
              "host_target_equal_mean_within_target_median_gap"):
        assert 1/(100)<=r[k]["one_sided_conditional_permutation_tail_p"]<=1
    assert not any(v in json.dumps(r) for v in ("s_2007_0","t_2007_0","fam0"))


def test_alternative_host_reference_caliper_respects_previous_year_observation():
    m=_m()
    assigned,genetic,survey,network=_toy()
    # All genetic origin labels are observed positives; each has a mapped site
    # and can be compared at 1-3 km from target. With tight 0.5km caliper,
    # most original toy assignments have <3 candidates and stay unestimable.
    r=m["matched_reference"](genetic,assigned,survey,network,minimum=3)
    for key in ("assigned_source_site_roster_from_all_799_family_assignments",
                "all_prior_year_positive_EOG_source_roster"):
        assert r[key]["assignment_rows_eligible"]<=len(assigned)
        assert r[key]["target_patch_years_eligible"]<=len(assigned)
        assert r[key]["status"]=="DESCRIPTIVE_ONLY_NO_ENVIRONMENTAL_CAUSAL_INFERENCE_OR_PVALUE"
    assert "fams" not in json.dumps(r)


def test_null_replay_is_seed_deterministic_and_rejects_missing_baseline_source():
    m=_m()
    assigned,genetic,survey,network=_toy()
    a=m["permutation"](assigned,survey,network,reps=55,seed=20261120)
    b=m["permutation"](assigned,survey,network,reps=55,seed=20261120)
    assert a==b
    broken=[dict(x) for x in assigned]
    broken[0]["distance"]=999
    with pytest.raises(m["AuditStop"],match="STOP_NULL_DIAGONAL_AND_YEAR_SOURCE_REPLAY"):
        m["permutation"](broken,survey,network,reps=2,seed=20261120)


def test_host_gap_is_same_original_two_host_ordinal_contract():
    m=_m()
    assert m["_host"]((1,0,3))
    assert not m["_host"]((1,0,4))
    assert not m["_host"]((0,None,0))
    assert m["ORIGINAL_SHA"]=="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
    assert m["SURVEY_SHA"]=="c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9"
