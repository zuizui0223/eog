"""Exact 64-graph EOG source-policy enumeration with original wetland provenance.

This is a COMPLETE finite enumeration of all simple directed 3-node graphs,
using native EOG v2 world reconstruction and self-excluded occurrence-rule
operators. No graph node, edge, world count or source policy is an estimated
Hungarian wetland ecological process. Original archived wetland source rows
are authenticated separately to motivate the observation-witness loss.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.occurrence_constraints import evaluate_occurrence_rule_compatibility
from eog.v2.world_reconstruction import (
    FiniteWorld,
    compare_reconstructions,
    reconstruct_compatible_worlds,
)
from benchmarks import wetland_observation_source_policy_bridge_v1 as bridge

NODE_IDS=("A","B","C")
ALL_OCCURRENCES=("A","B","C")
GATED_OCCURRENCES=("A","B")
EDGE_BITS=(("A","B"),("A","C"),("B","A"),
           ("B","C"),("C","A"),("C","B"))
GRAPH_COUNT=1<<len(EDGE_BITS)
SOURCE_NODE="A"
MAX_STEPS=1
EXPECTED={
    "fixed_full":16,"fixed_gated":32,
    "fixed_both":16,"fixed_only_full":0,"fixed_only_gated":16,
    "self_full":27,"self_gated":16,
    "self_both":12,"self_only_full":15,"self_only_gated":4,
    "self_neither":33
}


def edges_from_mask(mask):
    """Declared immutable six-edge bit order, never field movement geography."""
    if type(mask) is not int or not 0<=mask<GRAPH_COUNT:
        raise ValueError("synthetic directed edge mask must be integer 0..63")
    return tuple(edge for bit,edge in enumerate(EDGE_BITS) if mask & (1<<bit))


def exact_graph_world(mask):
    edges=edges_from_mask(mask)
    operator=build_dynamic_transition_operator(
        NODE_IDS,[
            DynamicReachabilityEdge(
                source=NODE_IDS.index(a),
                target=NODE_IDS.index(b),
                geographic_support=1.0
            )for a,b in edges
        ],
        loss_support=1.0,
    )
    return FiniteWorld(
        world_id=f"mask_{mask:02d}",
        operator=operator,
        source_ids=(SOURCE_NODE,),
        analytical_variant="synthetic_directed_3node_1step"
    )


def analytic_one_step_mask_compatibility(mask):
    """Independent graph-bit predicates, not the EOG numeric algorithms."""
    ee=set(edges_from_mask(mask))
    has=lambda a,b:(a,b) in ee
    fixed_full=has("A","B") and has("A","C")
    fixed_gated=has("A","B")
    peer_full=(
        (has("B","A") or has("C","A")) and
        (has("A","B") or has("C","B")) and
        (has("A","C") or has("B","C"))
    )
    peer_gated=has("A","B") and has("B","A")
    return {
        "fixed_full":fixed_full,"fixed_gated":fixed_gated,
        "self_full":peer_full,"self_gated":peer_gated
    }


def exact_set_accounting(full, gated, all_world_ids):
    full=set(full);gated=set(gated)
    if not full<=set(all_world_ids) or not gated<=set(all_world_ids):
        raise ValueError("compatible-world result refers outside frozen universe")
    return {
        "full_count":len(full),
        "gated_count":len(gated),
        "shared_world_ids":sorted(full&gated),
        "lost_world_ids_after_dropping_C":sorted(full-gated),
        "gained_world_ids_after_dropping_C":sorted(gated-full),
        "neither_world_ids":sorted(set(all_world_ids)-(full|gated)),
        "shared_count":len(full&gated),
        "lost_count":len(full-gated),
        "gained_count":len(gated-full),
        "neither_count":len(set(all_world_ids)-(full|gated)),
        "full_compatible_world_ids":sorted(full),
        "gated_compatible_world_ids":sorted(gated),
        "full_subset_gated":full<=gated,
        "gated_subset_full":gated<=full,
    }


def exhaustive_native_source_policy_audit():
    """Actually run both native EOG source policies on all 2^6 edge sets."""
    if len(EDGE_BITS)!=6 or len(set(EDGE_BITS))!=6:
        raise ValueError("six unique non-self EOG edge bits required")
    worlds=tuple(exact_graph_world(m) for m in range(GRAPH_COUNT))
    ids=tuple(w.world_id for w in worlds)
    if len(worlds)!=64 or len(set(ids))!=64:
        raise ValueError("synthetic finite graph universe not complete")

    full_fixed=reconstruct_compatible_worlds(
        worlds, ALL_OCCURRENCES, max_steps=MAX_STEPS
    )
    gated_fixed=reconstruct_compatible_worlds(
        worlds, GATED_OCCURRENCES, max_steps=MAX_STEPS
    )
    # EOG's native fixed-world comparison is used ONLY with the same frozen
    # source-A world definitions, and in the evidence-addition direction.
    comparison=compare_reconstructions(gated_fixed,full_fixed)
    ffull={r.world_id:r for r in full_fixed.world_results}
    fgated={r.world_id:r for r in gated_fixed.world_results}

    source_policy={"full":{}, "gated":{}}
    for obs_label,observations in (
        ("full",ALL_OCCURRENCES),("gated",GATED_OCCURRENCES)
    ):
        for w in worlds:
            native=evaluate_occurrence_rule_compatibility(
                w.operator,observations,rule_id=w.world_id,
                max_steps=MAX_STEPS,
                fixed_source_ids=None
            )
            if native.source_policy!="self_excluded" or native.fixed_source_ids:
                raise ValueError("native EOG self-excluded source-policy contract drift")
            source_policy[obs_label][w.world_id]=native

    full_fixed_ids={w for w,x in ffull.items() if x.compatible}
    gated_fixed_ids={w for w,x in fgated.items() if x.compatible}
    full_self_ids={w for w,x in source_policy["full"].items()
                   if not x.unsupported_occurrence_ids}
    gated_self_ids={w for w,x in source_policy["gated"].items()
                    if not x.unsupported_occurrence_ids}

    fixed=exact_set_accounting(full_fixed_ids,gated_fixed_ids,ids)
    selfx=exact_set_accounting(full_self_ids,gated_self_ids,ids)
    expected_fixed={
        "full_count":EXPECTED["fixed_full"],
        "gated_count":EXPECTED["fixed_gated"],
        "shared_count":EXPECTED["fixed_both"],
        "lost_count":EXPECTED["fixed_only_full"],
        "gained_count":EXPECTED["fixed_only_gated"],
    }
    expected_self={
        "full_count":EXPECTED["self_full"],
        "gated_count":EXPECTED["self_gated"],
        "shared_count":EXPECTED["self_both"],
        "lost_count":EXPECTED["self_only_full"],
        "gained_count":EXPECTED["self_only_gated"],
        "neither_count":EXPECTED["self_neither"],
    }
    for key,v in expected_fixed.items():
        if fixed[key]!=v:
            raise ValueError(f"native fixed EOG 64-graph count drift {key}={fixed[key]}, expected {v}")
    for key,v in expected_self.items():
        if selfx[key]!=v:
            raise ValueError(f"native peer-source EOG 64-graph count drift {key}={selfx[key]}, expected {v}")
    if not fixed["full_subset_gated"] or selfx["full_subset_gated"] or selfx["gated_subset_full"]:
        raise ValueError("expected frozen-source monotonicity or peer-source nonnesting lost")
    if len(comparison.eliminated_world_ids)!=16 or len(comparison.retained_world_ids)!=16:
        raise ValueError("native EOG fixed-source compare_reconstructions disagrees with enumeration")
    if abs(comparison.contraction_fraction-0.5)>1e-12:
        raise ValueError("native fixed-source added-positive contraction fraction drift")
    if set(comparison.retained_world_ids)!=full_fixed_ids:
        raise ValueError("fixed EOG retained world identities differ after positive C")

    rows=[]
    for mask,w in enumerate(worlds):
        native={
            "fixed_full":ffull[w.world_id].compatible,
            "fixed_gated":fgated[w.world_id].compatible,
            "self_full":not source_policy["full"][w.world_id].unsupported_occurrence_ids,
            "self_gated":not source_policy["gated"][w.world_id].unsupported_occurrence_ids
        }
        expectation=analytic_one_step_mask_compatibility(mask)
        if native!=expectation:
            raise ValueError(f"independent one-step graph predicate vs EOG mismatch at mask {mask}: {native} != {expectation}")
        if (ffull[w.world_id].world_fingerprint!=fgated[w.world_id].world_fingerprint
            or ffull[w.world_id].world_fingerprint!=w.fingerprint
            or source_policy["full"][w.world_id].operator_fingerprint!=w.operator.fingerprint
            or source_policy["gated"][w.world_id].operator_fingerprint!=w.operator.fingerprint):
            raise ValueError("source filtering changed frozen graph/operator fingerprint")
        rows.append({
            "graph_id":w.world_id,
            "edge_mask":mask,
            "number_directed_edges":len(edges_from_mask(mask)),
            "directed_edges":";".join(f"{a}>{b}" for a,b in edges_from_mask(mask)),
            "world_fingerprint":w.fingerprint,
            "operator_fingerprint":w.operator.fingerprint,
            "declared_fixed_source":SOURCE_NODE,
            "EOG_fixed_full_ABC_compatible":int(native["fixed_full"]),
            "EOG_fixed_gated_AB_compatible":int(native["fixed_gated"]),
            "EOG_self_excluded_full_ABC_compatible":int(native["self_full"]),
            "EOG_self_excluded_gated_AB_compatible":int(native["self_gated"]),
            "analytic_fixed_full_ABC":int(expectation["fixed_full"]),
            "analytic_fixed_gated_AB":int(expectation["fixed_gated"]),
            "analytic_self_full_ABC":int(expectation["self_full"]),
            "analytic_self_gated_AB":int(expectation["self_gated"]),
            "EOG_self_excluded_full_unsupported_targets":";".join(
                source_policy["full"][w.world_id].unsupported_occurrence_ids),
            "EOG_self_excluded_gated_unsupported_targets":";".join(
                source_policy["gated"][w.world_id].unsupported_occurrence_ids),
            "EOG_fixed_full_unsupported_targets":";".join(
                ffull[w.world_id].occurrence_result.unsupported_occurrence_ids),
            "EOG_fixed_gated_unsupported_targets":";".join(
                fgated[w.world_id].occurrence_result.unsupported_occurrence_ids),
        })
    if len(rows)!=GRAPH_COUNT:
        raise ValueError("all original six-edge bit masks were not scored")

    # Connect back to previous three-graph example, but this is still a
    # SYNTHETIC graph result, not an empirical source world.
    if not(rows[58]["EOG_self_excluded_full_ABC_compatible"]==1
           and rows[58]["EOG_self_excluded_gated_AB_compatible"]==0
           and rows[5]["EOG_self_excluded_full_ABC_compatible"]==0
           and rows[5]["EOG_self_excluded_gated_AB_compatible"]==1
           and rows[63]["EOG_self_excluded_full_ABC_compatible"]==1
           and rows[63]["EOG_self_excluded_gated_AB_compatible"]==1):
        raise ValueError("prior example-world support disappeared in exhaustive universe")
    return {
        "schema":"eog.exhaustive_three_node_source_policy_v1.result",
        "status":"COMPLETE_64_SYNTHETIC_EOG_WORLD_SOURCE_POLICY_EXHAUSTION_NOT_REAL_ECOLOGY",
        "graph_status":"ALL_64_POSSIBLE_DIRECTED_SIMPLE_3_NODE_GRAPHS_EXHAUSTIVELY_DECLARED",
        "graph_count":GRAPH_COUNT,
        "node_ids":list(NODE_IDS),
        "edge_bit_order":[f"{a}>{b}" for a,b in EDGE_BITS],
        "observations_full":list(ALL_OCCURRENCES),
        "observations_gated":list(GATED_OCCURRENCES),
        "synthetic_declared_fixed_source":SOURCE_NODE,
        "max_steps":MAX_STEPS,
        "native_fixed_source_frozen_operator_universe":True,
        "native_EOG_decisions_agree_with_independent_analytic_edge_predicates_for_all_worlds":True,
        "native_fixed_policy":{
            **fixed,
            "used_native_EOG_API":"eog.v2.world_reconstruction.reconstruct_compatible_worlds",
            "used_native_added_positive_comparator":"eog.v2.world_reconstruction.compare_reconstructions",
            "added_positive_eliminated_worlds":len(comparison.eliminated_world_ids),
            "added_positive_retained_worlds":len(comparison.retained_world_ids),
            "added_positive_contraction_fraction":comparison.contraction_fraction,
            "compatible_set_monotone_under_positive_witness_loss":True,
            "source_policy":"fixed"
        },
        "native_self_excluded_policy":{
            **selfx,
            "used_native_EOG_API":"eog.v2.occurrence_constraints.evaluate_occurrence_rule_compatibility",
            "source_policy":"self_excluded",
            "monotone_compatible_set_inclusion_does_not_hold":True,
            "NOT_eligible_for_fixed_source_compare_reconstructions":True,
            "source_peer_envelope_changes_with_observed_positive_set":True
        },
        "independent_combinatorial_count_certificate":{
            "fixed_full":"A>B and A>C: 2^4=16 graphs",
            "fixed_gated":"A>B: 2^5=32 graphs",
            "self_excluded_full":"For each target: at least one of two incoming edges; 3^3=27 graphs",
            "self_excluded_gated":"A>B and B>A: 2^4=16 graphs",
            "self_excluded_intersection":"A>B,B>A and (A>C or B>C), with C>A,C>B free: 3*4=12 graphs",
            "self_excluded_lost":"27-12=15 graphs",
            "self_excluded_gained":"16-12=4 graphs",
            "all_64_native_graph_decisions_cross_checked":True,
        },
        "prior_example_world_bit_masks":{
            "hub":58,"isolated_C":5,"complete":63
        },
        "real_EOG_ecological_worlds_enumerated":False,
        "rows":rows
    }


def run(surveys,sites,out_dir):
    if not Path(surveys).is_file() or not Path(sites).is_file():
        raise ValueError("original source CSV paths must exist")
    # This real-record evidence anchors WHY the theoretical source-policy
    # distinction matters, but it is never placed in the abstract node graph.
    source_record=bridge.authenticate_wetland_split(surveys,sites)
    if (source_record["Q1_last14_split_witness_pairs"],
        source_record["Q2_last14_split_witness_pairs"])!=(16,9):
        raise ValueError("authentic source method/calendar loss baseline drift")
    outcome=exhaustive_native_source_policy_audit()
    rows=outcome.pop("rows")
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    path=out/"synthetic_64_eog_graph_source_policy_results.csv"
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    outcome["output_csv"]={
        "filename":path.name,
        "rows":len(rows),
        "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    outcome["authenticated_real_wetland_record_provenance"]={
        "site":source_record["site"],
        "species":source_record["species"],
        "source_positive_rows":source_record["source_positive_rows"],
        "Q1_last14_split_witness_pairs":source_record["Q1_last14_split_witness_pairs"],
        "Q2_last14_split_witness_pairs":source_record["Q2_last14_split_witness_pairs"],
        "original_source_sha256":{
            "surveys":"45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd",
            "sites":"93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
        },
        "actual_wetland_nodes_are_NOT_synthetic_A_B_C":True
    }
    outcome["inference_limits"]=[
        "Only 64 SIMPLE DIRECTED abstract 3-node one-step transition operators are exhaustively enumerated, NOT all real ecology, spatial barriers, movement models or global possible biological worlds.",
        "The source-observation example is an authentic method/date-split wetland positive witness, but is NOT an observed source/target graph, ecological pathway or mapped synthetic node.",
        "Fixed-source monotonicity relies on fixed world/source/operator/threshold identities; self-excluded policy changes peer sources and can both lose and gain compatible rules when positive records are filtered.",
        "No true biological absence is identified from unrecorded source positive rows; detection probability, physical trap identities, equal field effort and temporal closure are unknown.",
        "No occupancy fit, original unmarked model refit, abiotic/biotic/movement A/B/M mechanism, causal restoration effect, independent EOG-WF endpoint or merge of Draft PR #697."
    ]
    outcome["fingerprint"]=hashlib.sha256(json.dumps(
        outcome,sort_keys=True,separators=(",",":"),allow_nan=False
    ).encode()).hexdigest()
    return outcome


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--surveys",required=True,type=Path)
    ap.add_argument("--sites",required=True,type=Path)
    ap.add_argument("--out-dir",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    result=run(args.surveys,args.sites,args.out_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("EOG_EXHAUSTIVE_64_SOURCE_POLICY="+json.dumps({
        "fingerprint":result["fingerprint"],
        "graph_count":result["graph_count"],
        "fixed":{
            key:result["native_fixed_policy"][key]
            for key in ("full_count","gated_count","shared_count","lost_count","gained_count")
        },
        "self_excluded":{
            key:result["native_self_excluded_policy"][key]
            for key in ("full_count","gated_count","shared_count","lost_count","gained_count","neither_count")
        },
        "output_csv":result["output_csv"],
        "authentic_wetland_witness":result["authenticated_real_wetland_record_provenance"]
    },sort_keys=True))
