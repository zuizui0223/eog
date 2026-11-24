"""Independent finite-clock audit of mandatory vs optional optimal BBMM time cuts.

No original McKee GPS records live in this GitHub repo. The exhaustive
oracle independently enumerates both concrete time assignments and ALL
contiguous partitions for small synthetic unions of integer instants.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import random
import runpy
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
PROTOCOL = ROOT / "post_stop_optimal_cut_necessity_protocol_v1.json"
RECEIPT = ROOT / "post_stop_optimal_cut_necessity_receipt_v1.json"
SCRIPT = ROOT / "replay_post_stop_optimal_cut_necessity.py"
sys.path.insert(0,str(ROOT))
try:
    ns=runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(ROOT))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_precommitted_protocol_and_source_hash_integrity():
    p,r=load(PROTOCOL),load(RECEIPT)
    assert p["schema"]=="eog.mckee2024.source_only_optimal_cut_necessity.v1"
    assert p["status"]=="FROZEN_BEFORE_MINIMUM_PARTITION_ENSEMBLE_SOURCE_ANALYSIS"
    assert r["protocol_frozen_commit"]=="5319159417d944586913a3abd06b54331a150af5"
    assert p["source"]["sha256"]==ns["SHA256"]==r["source_sha256"]
    assert r["record_count"]==28953
    assert r["group_count"]==421
    assert r["original_within_group_link_count"]==28532
    assert ns["_check_protocol"]()["schema"]==p["schema"]
    assert p["source"]["forbidden"][0]=="SHP point coordinates"
    assert r["dense_2h_GPS_opened"] is False


def test_857_selected_greedy_cuts_are_not_all_mandatory():
    r=load(RECEIPT)
    labels=r["world_order"]
    assert len(labels)==4
    counts=r["per_world"]
    expected=[
        (857,793,128,27611,793,64),
        (858,858,0,27674,858,0),
        (889,800,178,27554,800,89),
        (890,865,50,27617,865,25)
    ]
    for label,vals in zip(labels,expected):
        d=counts[label]
        assert (d["minimum_cuts"],d["forced_cut"],d["optional"],
                d["forced_retain"],d["greedy_selected_forced_cuts"],
                d["greedy_selected_optional_cuts"])==vals
        assert sum(d[k] for k in ("forced_cut","optional","forced_retain"))==28532
        assert d["greedy_selected_forced_cuts"]+d["greedy_selected_optional_cuts"]==d["minimum_cuts"]
    assert list(r["groups_with_multiple_minimum_cut_partitions"].values())==[41,0,65,25]
    assert list(r["groups_with_greedy_selected_optional_cut"].values())==[41,0,65,25]
    assert r["joint"]["selected_cut_by_all_4_greedy"]==857
    assert r["joint"]["forced_cut_in_all_4_optimal_ensembles"]==793
    assert r["joint"]["forced_retain_in_all_4_optimal_ensembles"]==27553
    assert r["joint"]["not_universally_forced_either_way"]==186
    assert 793+27553+186==28532


def test_joint_source_clock_policy_statuses_are_a_partition():
    r=load(RECEIPT)
    patterns=r["joint_forced_optional_class_patterns"]
    assert patterns=={
        "CCCC":793,
        "OCOC":64,
        "OROR":64,
        "RCRC":1,
        "RRCC":7,
        "RROO":50,
        "RRRR":27553,
    }
    assert sum(patterns.values())==28532
    selected=r["joint_greedy_cut_mask_patterns"]
    assert selected=={"0000":27642,"0011":32,"0101":1,"1111":857}
    assert sum(selected.values())==28532
    assert r["joint"]["optional_in_at_least_one_world"]==178
    assert r["joint"]["forced_cut_in_some_and_forced_retain_in_another_world"]==8
    assert r["joint"]["groups_with_any_link_class_difference_across_worlds"]==70
    assert r["joint"]["fixed_MST_negative_control_groups"]==421


def test_canonical_three_time_fixes_have_two_equally_optimal_cut_placements():
    f=ns["optimal_partition_links"]
    w=(((0,0),),((1,20),),((25,25),))
    ans=f(w,gap=10)
    assert ans["minimum_cuts"]==1
    assert ans["classification"]==("O","O")
    assert ans["minimum_partition_count_capped"]==2
    assert len(ans["greedy_cut_indices"])==1


def test_forced_cut_and_forced_retain_synthetic_links():
    f=ns["optimal_partition_links"]
    r=f((((0,0),),((25,25),)),gap=10)
    assert r["minimum_cuts"]==1
    assert r["classification"]==("C",)
    assert r["greedy_cut_indices"]==frozenset((1,))
    r=f((((0,0),),((5,5),)),gap=10)
    assert r["minimum_cuts"]==0
    assert r["classification"]==("R",)
    assert r["minimum_partition_count_capped"]==1


def _merge(intervals):
    out=[]
    for lo,hi in sorted(intervals):
        if out and lo<=out[-1][1]+1:
            out[-1]=(out[-1][0],max(out[-1][1],hi))
        else:
            out.append((lo,hi))
    return tuple(out)


def _explicit_block_possible(block,gap):
    allowed=[
        sorted({second for lo,hi in rec for second in range(lo,hi+1)})
        for rec in block
    ]
    return any(
        all(1<=t1-t0<=gap for t0,t1 in zip(clocks,clocks[1:]))
        for clocks in product(*allowed)
    )


def _enumerate_every_optimal_partition(windows,gap):
    n=len(windows)
    partitions=[]
    for mask in product((0,1),repeat=n-1):
        blocks=[]
        start=0
        for index,is_cut in enumerate(mask,start=1):
            if is_cut:
                blocks.append(windows[start:index])
                start=index
        blocks.append(windows[start:])
        if all(_explicit_block_possible(block,gap) for block in blocks):
            partitions.append(mask)
    assert partitions
    mincuts=min(sum(mask) for mask in partitions)
    best=[mask for mask in partitions if sum(mask)==mincuts]
    classes=tuple(
        "C" if all(mask[k] for mask in best) else
        "R" if not any(mask[k] for mask in best) else "O"
        for k in range(n-1)
    )
    return mincuts,classes,len(best)


def test_independent_bruteforce_450_clock_worlds_match_optimal_cut_link_classes():
    rng=random.Random(20261124)
    for _ in range(450):
        n=rng.randint(2,6)
        gap=rng.randint(1,5)
        intervals=[]
        for _ in range(n):
            parts=[]
            for _ in range(rng.randint(1,2)):
                lo=rng.randint(-3,12)
                parts.append((lo,lo+rng.randint(0,1)))
            intervals.append(_merge(parts))
        oracle=_enumerate_every_optimal_partition(intervals,gap)
        result=ns["optimal_partition_links"](intervals,gap=gap)
        assert (
            result["minimum_cuts"],result["classification"],
            result["minimum_partition_count_capped"]
        )==oracle


def test_producer_fails_closed_on_invalid_input_and_locks_scientific_claims(tmp_path):
    check=ns["optimal_partition_links"]
    with pytest.raises(ValueError,match="nonempty"):
        check([])
    with pytest.raises(ValueError,match="positive integral"):
        check([((0,0),)],gap=0)
    bad=tmp_path/"GPS12hrs_Locs.zip"
    bad.write_bytes(b"not real GPS")
    from replay_post_stop_time_interval_qc import _source_rows
    with pytest.raises(ValueError,match="filename or byte size"):
        _source_rows(bad)
    r=load(RECEIPT)
    assert r["source_timestamp_semantics_author_confirmed"] is False
    assert r["source_CRS_author_confirmed"] is False
    assert r["source_QC_STOP_retained"] is True
    assert r["source_point_geometry_read"] is False
    assert r["raw_IDs_timestamps_coordinates_or_link_locations_exported"] is False
    assert r["BBMM_or_EOG_predictive_score_computed"] is False
    assert r["original_EOG_WF_scored_endpoints"]==3
