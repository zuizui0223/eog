"""Check McKee 12h clock-partition necessity under +0/+1/+2 cut slack.

The repository contains only precommitted aggregate receipts, not raw GPS.
Independent brute force enumerates ALL partitions and concrete second-level
clock assignments on small nonconvex synthetic finite worlds. The dense 2h
outcome is NEVER read.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import random
import runpy
import sys

import pytest


HERE=Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
PROTOCOL=HERE / "post_stop_one_extra_cut_budget_protocol_v1.json"
RECEIPT=HERE / "post_stop_one_extra_cut_budget_receipt_v1.json"
OLD=HERE / "post_stop_optimal_cut_necessity_receipt_v1.json"
SCRIPT=HERE / "replay_post_stop_one_extra_cut_budget.py"
sys.path.insert(0,str(HERE))
try:
    src=runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(HERE))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_exact_source_identity_precommitted_before_new_budget_analysis():
    p,r=_load(PROTOCOL),_load(RECEIPT)
    assert p["schema"]=="eog.mckee2024.source_only_optimality_slack_link_identifiability.v1"
    assert p["status"]=="FROZEN_BEFORE_ANY_NEW_12H_LINK_RETENTION_BUDGET_ANALYSIS"
    assert r["protocol_commit_before_source_analysis"]=="17d3611d0333893e9d23e72eeeb261c568020c04"
    assert p["source"]["sha256"]==r["source_sha256"]==src["SHA256"]
    assert p["source"]["size_bytes"]==r["source_bytes"]==1539661
    assert p["source"]["records"]==r["records"]==28953
    assert p["source"]["groups"]==r["groups"]==421
    assert p["source"]["adjacent_pairs"]==r["links"]==28532
    assert src["_validate"]()["schema"]==p["schema"]
    assert p["partition_budget"]["delta_allowed_cuts_per_group"]==[0,1,2]
    assert p["source"]["no_dense_GPS2h"] is True


def test_exact_optimum_zero_budget_reconciles_with_prior_frozen_pr753():
    prior,r=_load(OLD),_load(RECEIPT)
    expected=[("T0_NAIVE",857,793,128,27611),
              ("T1_NAIVE",858,858,0,27674),
              ("T0_IANA",889,800,178,27554),
              ("T1_IANA",890,865,50,27617)]
    p0=r["per_delta_per_world"]["0"]
    for key,minimum,forced,optional,retained in expected:
        data=p0[key]
        assert (data["minimum_cuts"],data["forced_cut"],data["optional"],
                data["forced_retain"])==(minimum,forced,optional,retained)
    assert r["joint_class_patterns"]["0"]==prior["joint_forced_optional_class_patterns"]
    assert r["joint_all_world_mandatory"]["0"]=={
        "forced_cut_in_all_four":793,
        "forced_retain_in_all_four":27553,
        "not_universally_fixed":186,
        "pair_possible_in_all_four":27667,
        "pair_impossible_in_all_four":793,
        "pair_feasibility_clock_dependent":72,
    }


def test_plus_one_and_two_reveal_objective_conditional_retention():
    r=_load(RECEIPT)
    for delta in ("1","2"):
        table=r["per_delta_per_world"][delta]
        assert [table[key]["forced_cut"] for key in src["SHORT_NAMES"]]==[793,858,800,865]
        assert [table[key]["optional"] for key in src["SHORT_NAMES"]]==[27739,27674,27732,27667]
        assert all(table[key]["forced_retain"]==0 for key in src["SHORT_NAMES"])
        assert all(r["groups_with_any_optional_cut"][delta][key]==421
                   for key in src["SHORT_NAMES"])
        assert r["joint_class_patterns"][delta]=={
            "CCCC":793,"OCOC":65,"OOCC":7,"OOOO":27667
        }
        assert r["joint_all_world_mandatory"][delta]["forced_cut_in_all_four"]==793
        assert r["joint_all_world_mandatory"][delta]["forced_retain_in_all_four"]==0
        assert r["joint_all_world_mandatory"][delta]["not_universally_fixed"]==27739
    assert r["joint_class_patterns"]["1"]==r["joint_class_patterns"]["2"]


def test_local_pair_feasibility_exactly_matches_plus_one_forced_cuts():
    r=_load(RECEIPT)
    counts=r["local_pair_feasibility_counts"]
    for key in src["SHORT_NAMES"]:
        data=counts[key]
        assert data["links"]==28532
        assert data["impossible"]==r["per_delta_per_world"]["1"][key]["forced_cut"]
        assert data["possible"]==r["per_delta_per_world"]["1"][key]["optional"]
    assert [counts[key]["affected_groups"] for key in src["SHORT_NAMES"]]==[
        191,205,191,205
    ]
    transitions=r["previous_optimum_to_plus_one_class_transitions"]
    assert [transitions[key]["R=>O"] for key in src["SHORT_NAMES"]]==[
        27611,27674,27554,27617
    ]


def test_constructive_one_extra_cut_theorem_in_tiny_clock_worlds():
    fn=src["classify_budget_links"]
    # All pairs feasible: minimum 0 cuts, all links R; inserting a single
    # voluntary cut makes either source link optional but none mandatory R.
    feasible=(((0,0),),((5,5),),((10,10),))
    out=fn(feasible,max_gap=10)
    assert out["minimum_cut_count"]==0
    assert out["class_by_delta"][0]==("R","R")
    assert out["class_by_delta"][1]==("O","O")
    assert out["class_by_delta"][2]==("O","O")
    # Both pair links feasible separately but no 3-fix path; minimum 1 cut,
    # either link is a valid optimally selected cut.
    mixed=(((0,0),),((1,20),),((25,25),))
    out=fn(mixed,max_gap=10)
    assert out["minimum_cut_count"]==1
    assert out["class_by_delta"][0]==("O","O")
    assert out["class_by_delta"][1]==("O","O")
    # An infeasible pair remains a forced cut under all cut budgets.
    impossible=(((0,0),),((25,25),))
    out=fn(impossible,max_gap=10)
    assert all(out["class_by_delta"][d]==("C",) for d in (0,1,2))


def _legal_clock_seconds(unions):
    return sorted(set(t for lo,hi in unions for t in range(lo,hi+1)))


def _feasible_block(windows,gap):
    return any(
        all(1<=b-a<=gap for a,b in zip(times,times[1:]))
        for times in product(*[_legal_clock_seconds(x) for x in windows])
    )


def _oracle(windows,gap):
    n=len(windows)
    feasible=[]
    for mask in product((0,1),repeat=n-1):
        starts=[0]+[k for k,c in enumerate(mask,start=1) if c]+[n]
        if all(
            _feasible_block(windows[i:j],gap)
            for i,j in zip(starts,starts[1:])
        ):
            feasible.append(mask)
    assert feasible
    opt=min(map(sum,feasible))
    result={}
    for d in (0,1,2):
        selected=[mask for mask in feasible if sum(mask)<=opt+d]
        result[d]=tuple(
            "C" if all(m[k] for m in selected) else
            "R" if not any(m[k] for m in selected) else "O"
            for k in range(n-1)
        )
    return opt,result


def _canonical(intervals):
    out=[]
    for lo,hi in sorted(intervals):
        if out and lo<=out[-1][1]+1:
            out[-1]=(out[-1][0],max(out[-1][1],hi))
        else:
            out.append((lo,hi))
    return tuple(out)


def test_independent_exhaustive_500_small_finite_clock_worlds():
    rng=random.Random(20261124)
    fn=src["classify_budget_links"]
    for _ in range(500):
        n=rng.randint(2,6)
        gap=rng.randint(1,5)
        windows=[]
        for _ in range(n):
            pieces=[]
            for _ in range(rng.randint(1,2)):
                t=rng.randint(-3,10)
                pieces.append((t,t+rng.randint(0,1)))
            windows.append(_canonical(pieces))
        oracle_opt,oracle_cl=_oracle(windows,gap)
        res=fn(windows,max_gap=gap)
        assert res["minimum_cut_count"]==oracle_opt
        assert res["class_by_delta"]==oracle_cl


def test_original_source_only_and_no_2h_or_ecological_score(tmp_path):
    receipt=_load(RECEIPT)
    assert receipt["source_sha256_verified"] is True
    assert receipt["source_author_timestamp_semantics_verified"] is False
    assert receipt["source_author_CRS_verified"] is False
    assert receipt["IANA_DST_is_conditional"] is True
    assert receipt["dense_2h_holdout_opened"] is False
    assert receipt["SHP_geometry_accessed"] is False
    assert receipt["raw_ids_times_coordinates_or_link_indices_exported"] is False
    assert receipt["ecological_prediction_scored"] is False
    assert receipt["original_EOG_WF_scored_endpoints"]==3
    with pytest.raises(ValueError,match="Deltas must be sorted"):
        src["classify_budget_links"]([((0,0),)],deltas=(-1,0,1))
    bad=tmp_path/"GPS12hrs_Locs.zip"
    bad.write_bytes(b"not the original source")
    from replay_post_stop_time_interval_qc import _source_rows
    with pytest.raises(ValueError,match="filename or byte size"):
        _source_rows(bad)



def test_infinite_unreachable_pair_cost_does_not_become_finite_at_plus_two():
    """Regression: a finite n+2 sentinel falsely admits impossible pairs at +2."""
    fn=src["classify_budget_links"]
    for n in range(2, 7):
        # Every source adjacent pair exceeds a ten-second gap.
        windows=tuple(((i*1000,i*1000),) for i in range(n))
        result=fn(windows,max_gap=10)
        assert result["minimum_cut_count"]==n-1
        assert all(result["pair_impossible"])
        for delta in (0,1,2):
            assert result["class_by_delta"][delta]==("C",)*(n-1)
