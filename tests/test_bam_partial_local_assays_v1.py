"""Known-truth local assay contracts: no hidden-truth selection or mask weighting."""
import numpy as np
import pytest

from benchmarks import bam_partial_local_assays_v1 as m


def test_different_target_pairs_are_counted_without_parameter_label_weights():
    states=[
        {"mask":(0b0011,0b0011,0b0011),"sign":-1,"world_ids":["a","duplicate_a"]},
        {"mask":(0b0111,0b0011,0b0011),"sign":1,"world_ids":["b"]},
        {"mask":(0b1011,0b0011,0b0011),"sign":1,"world_ids":["c"]},
    ]
    assert m.disagreement_pairs(states,("A",2))==1
    assert m.disagreement_pairs(states,("A",3))==1
    assert m.disagreement_pairs(states,("B",2))==0
    assert m.choose_greedy(states,4,allowed=("A","B","M"))==("A",2)


def test_first_assay_is_selected_without_truth_lookahead():
    states=[
        {"mask":(3,3,3),"sign":-1,"world_ids":["u"]},
        {"mask":(7,3,3),"sign":1,"world_ids":["v"]},
        {"mask":(11,3,3),"sign":1,"world_ids":["w"]},
    ]
    traces=[
        m.simulate_policy(
            states,truth=s,n_nodes=4,policy="greedy_all",seed=5,
            system_id="toy",G=3,target_axis="M",budget=3,
        ) for s in states
    ]
    assert {trace["steps"][0]["test"] for trace in traces}=={"A:2"}
    assert all(trace["steps"][-1]["identified"] for trace in traces)


def test_assay_on_wrong_axis_cannot_manufacture_identification():
    states=[
        {"mask":(3,3,3),"sign":-1,"world_ids":["x"]},
        {"mask":(7,3,3),"sign":1,"world_ids":["y"]},
    ]
    report=m.simulate_policy(
        states,truth=states[0],n_nodes=3,policy="greedy_B",seed=2,
        system_id="toy",G=3,target_axis="M",budget=3,
    )
    assert len(report["steps"])==4
    assert all(not row["identified"] for row in report["steps"])
    assert all(row["test"] is None for row in report["steps"])


def test_generic_random_is_seeded_not_truth_or_target_label_driven():
    states=[
        {"mask":(3,3,3),"sign":-1,"world_ids":["x"]},
        {"mask":(7,3,3),"sign":1,"world_ids":["y"]},
    ]
    inputs=dict(
        states=states,truth=states[0],n_nodes=3,
        policy="hash_all",seed=42,system_id="toy",G=3,target_axis="M",budget=2,
    )
    assert m.simulate_policy(**inputs)==m.simulate_policy(**inputs)
    assert m.simulate_policy(**inputs)["steps"][1]["identified"]


def test_original_mask_triplicates_count_once_even_if_parameter_labels_repeat():
    rows=[
        {"world_id":"a","A_bits":3,"B_bits":3,"M_bits":3,"G_bits":3},
        {"world_id":"a2","A_bits":3,"B_bits":3,"M_bits":3,"G_bits":3},
        {"world_id":"b","A_bits":7,"B_bits":3,"M_bits":3,"G_bits":3},
    ]
    dedup=m.deduplicate_states(rows,{"a":-1,"a2":-1,"b":1})
    assert len(dedup)==2
    assert dedup[0]["world_ids"]==["a","a2"]
    with pytest.raises(ValueError,match="conflicting"):
        m.deduplicate_states(rows,{"a":-1,"a2":1,"b":1})


def test_perfect_evidence_never_loses_identification():
    states=[
        {"mask":(3,3,3),"sign":-1,"world_ids":["x"]},
        {"mask":(7,3,3),"sign":1,"world_ids":["y"]},
    ]
    report=m.simulate_policy(
        states,truth=states[0],n_nodes=3,policy="greedy_all",
        seed=9,system_id="toy",G=3,target_axis="M",budget=3,
    )
    flags=[row["identified"] for row in report["steps"]]
    assert flags==sorted(flags)


def test_fixed_contract_source_has_not_moved():
    from pathlib import Path
    import json
    protocol=json.loads(
        Path("validation/bam_partial_local_assay_v1/protocol_v1.json").read_text()
    )
    assert protocol["source"]["worlds"]==768
    assert protocol["source"]["G_fibres"]==129
    assert protocol["assay"]["budgets"]==[0,1,2,3]
    assert protocol["assay"]["policies"]["greedy_all"].startswith("Choose")
    assert protocol["targets"]["primary"].startswith("sign")
    assert tuple(range(20261107,20261123))==m.SEEDS
