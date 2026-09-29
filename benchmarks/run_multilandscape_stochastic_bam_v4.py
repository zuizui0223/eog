#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from independent_multilandscape_bam_generator_v4 import (
    LANDSCAPE_PANEL,
    abiotic_mask as generator_abiotic_mask,
    candidate_parameter_grid,
    make_landscape,
    simulate_associates,
    simulate_focal,
    truth_scenarios,
)
from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
)
from eog.v2.world_reconstruction import (
    FiniteWorld,
    forward_reachable_configuration,
    reconstruct_compatible_worlds,
)


def _crosses_barrier(landscape, i, j):
    col=landscape.spec.barrier_col
    if col is None: return False
    x1,y1=landscape.coordinates[i]; x2,y2=landscape.coordinates[j]
    if not (min(x1,x2)<col<=max(x1,x2)): return False
    gap=landscape.spec.barrier_gap_row
    if gap is not None and int(round(y1))==int(round(y2))==gap: return False
    return True


def _evaluator_A(landscape,spec):
    c=np.asarray(spec.niche_center,float); r=np.asarray(spec.niche_radius,float)
    s=(landscape.environment-c)/r
    return np.sum(s*s,axis=1)<=1.0+1e-12


def _evaluator_B(landscape,associates,mode):
    if mode=="none": return np.ones(len(landscape.node_ids),bool)
    if mode=="obligate_partner": return associates.partner_mask.copy()
    if mode=="antagonist_exclusion": return ~associates.antagonist_mask
    if mode=="partner_and_antagonist": return associates.partner_mask & ~associates.antagonist_mask
    raise ValueError(mode)


def _build_world(landscape,associates,spec):
    A=_evaluator_A(landscape,spec); B=_evaluator_B(landscape,associates,spec.biotic_mode); eligible=A&B
    src=landscape.node_ids.index(spec.source_id)
    if not bool(eligible[src]): raise ValueError("candidate_source_invalid")
    edges=[]; n=len(landscape.node_ids)
    for i in range(n):
        if not bool(eligible[i]): continue
        for j in range(n):
            if i==j or not bool(eligible[j]): continue
            if float(np.linalg.norm(landscape.coordinates[i]-landscape.coordinates[j]))>spec.step_radius+1e-12: continue
            if not spec.barrier_permeable and _crosses_barrier(landscape,i,j): continue
            edges.append(DynamicReachabilityEdge(source=i,target=j,geographic_support=1.0))
    op=build_dynamic_transition_operator(landscape.node_ids,edges,loss_support=1.0)
    return FiniteWorld(spec.scenario_id,op,(spec.source_id,),analytical_variant="multilandscape_stochastic_bam_v4")


def _first_observed_steps(history,horizon):
    p=history[:horizon+1]; out={}
    for node in np.flatnonzero(np.any(p,axis=0)):
        out[int(node)]=int(np.flatnonzero(p[:,node])[0])
    return out


def _compatible(observed_ids,supports):
    obs=set(observed_ids)
    return tuple(w for w in sorted(supports) if obs.issubset(supports[w]))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=Path("validation/multilandscape_stochastic_bam_v4/result_v4.json"))
    args=ap.parse_args()

    specs=candidate_parameter_grid(); specs_by={x.scenario_id:x for x in specs}; truths=truth_scenarios()
    horizons=(10,40); reps=32
    landscape_rows=[]; design_stops=[]

    total_truth_fail=0; total_static_expand=0; total_nesting_viol=0; total_api_mismatch=0; total_api_audits=0
    eligible_landscapes=0
    u4_failed=[]; u5_failed=[]; u6_failed=[]; u7_failed=[]

    for ls in LANDSCAPE_PANEL:
        landscape=make_landscape(ls)
        stop_reasons=[]
        try:
            associates=simulate_associates(landscape)
        except ValueError as exc:
            design_stops.append({"landscape_id":ls.landscape_id,"reasons":[str(exc)]})
            continue

        n=len(landscape.node_ids); source=landscape.node_ids.index("r4c0")
        pc=int(np.sum(associates.partner_mask)); ac=int(np.sum(associates.antagonist_mask))
        if pc in (0,n): stop_reasons.append("partner_degenerate")
        if ac in (0,n): stop_reasons.append("antagonist_degenerate")
        if not bool(associates.partner_mask[source]): stop_reasons.append("partner_missing_focal_source")
        if bool(associates.antagonist_mask[source]): stop_reasons.append("antagonist_blocks_focal_source")

        worlds=[]; build_fail=[]
        for spec in specs:
            try: worlds.append(_build_world(landscape,associates,spec))
            except ValueError as exc: build_fail.append({"world_id":spec.scenario_id,"reason":str(exc)})
        worlds=tuple(sorted(worlds,key=lambda w:w.world_id)); world_ids=tuple(w.world_id for w in worlds)
        if build_fail: stop_reasons.append("candidate_build_failure")
        if len(worlds)!=32: stop_reasons.append("candidate_world_count_not_32")
        for tid in truths.values():
            if tid not in world_ids: stop_reasons.append(f"truth_missing:{tid}")

        if stop_reasons:
            design_stops.append({"landscape_id":ls.landscape_id,"reasons":stop_reasons,"partner_count":pc,"antagonist_count":ac,"build_failures":build_fail})
            continue

        supports={}; arrivals={}
        for world in worlds:
            supports[world.world_id]=frozenset(forward_reachable_configuration(world,max_steps=40,support_tolerance=0.0).reachable_ids)
            p=propagate_dynamic_reachability(world.operator,world.source_weight_mapping,max_steps=40,arrival_tolerance=0.0)
            arrivals[world.world_id]=tuple(None if int(x)<0 else int(x) for x in p.first_arrival_step)

        parity_fail=[]
        for scenario_id,tid in truths.items():
            real=simulate_focal(landscape,associates,specs_by[tid],replicate=-1)
            if set(real.structural_reachable_ids)!=set(supports[tid]): parity_fail.append(scenario_id)
        if parity_fail:
            design_stops.append({"landscape_id":ls.landscape_id,"reasons":["generator_evaluator_structural_mismatch"],"scenarios":parity_fail})
            continue

        eligible_landscapes+=1

        # exact complete-positive ambiguity and nesting audit
        complete_counts={}
        nesting=0
        for tid,tset in supports.items():
            complete_counts[tid]=sum(1 for s in supports.values() if tset.issubset(s))
        ids=sorted(supports)
        for a in ids:
            for b in ids:
                if a!=b and supports[a] < supports[b]:
                    if complete_counts[a] < complete_counts[b]: nesting+=1
        total_nesting_viol += nesting

        scenario_complete={sid:complete_counts[tid] for sid,tid in truths.items()}
        joint=scenario_complete["joint_ABM"]
        comparators=[v for k,v in scenario_complete.items() if k!="joint_ABM"]
        if not all(joint>=v for v in comparators): u4_failed.append(ls.landscape_id)

        static_classes=defaultdict(list); temporal_classes=defaultdict(list)
        for wid in ids:
            static_classes[supports[wid]].append(wid)
            temporal_classes[(supports[wid],arrivals[wid])].append(wid)
        if len(temporal_classes)<=len(static_classes): u5_failed.append(ls.landscape_id)

        truth_fail=0; static_expand=0; api_mismatch=0; api_audits=0; temporal_gain_runs=0; temporal_nonidentified_h40=0
        scenario_static=defaultdict(lambda:defaultdict(list)); scenario_temporal=defaultdict(lambda:defaultdict(list))
        scenario_unique_temp=defaultdict(lambda:defaultdict(int))

        for sid,tid in truths.items():
            spec=specs_by[tid]
            for rep in range(reps):
                real=simulate_focal(landscape,associates,spec,replicate=rep)
                previous=set(ids); run_gain=False
                for h in horizons:
                    first=_first_observed_steps(real.occupancy_history,h)
                    observed={landscape.node_ids[i] for i in first}
                    static=_compatible(observed,supports); static_set=set(static)
                    temporal=[]
                    for wid in static:
                        ea=arrivals[wid]; ok=True
                        for node,tobs in first.items():
                            if ea[node] is None or ea[node]>tobs: ok=False; break
                        if ok: temporal.append(wid)
                    temporal=tuple(temporal); temporal_set=set(temporal)
                    if tid not in temporal_set: truth_fail+=1
                    if not static_set.issubset(previous): static_expand+=1
                    previous=static_set
                    if len(temporal)<len(static): run_gain=True
                    if h==40 and len(temporal)>1: temporal_nonidentified_h40+=1
                    if temporal==(tid,): scenario_unique_temp[sid][h]+=1
                    scenario_static[sid][h].append(len(static)); scenario_temporal[sid][h].append(len(temporal))
                    if rep==0 and len(observed)>=2:
                        rec=reconstruct_compatible_worlds(worlds,tuple(observed),max_steps=40,support_tolerance=0.0)
                        api_audits+=1
                        if rec.compatible_world_ids!=static: api_mismatch+=1
                if run_gain: temporal_gain_runs+=1

        total_truth_fail+=truth_fail; total_static_expand+=static_expand; total_api_mismatch+=api_mismatch; total_api_audits+=api_audits
        if temporal_gain_runs==0: u6_failed.append(ls.landscape_id)
        if temporal_nonidentified_h40==0: u7_failed.append(ls.landscape_id)

        landscape_rows.append({
            "landscape_id":ls.landscape_id,
            "family":ls.family,
            "partner_count":pc,
            "antagonist_count":ac,
            "static_support_class_count":len(static_classes),
            "temporal_signature_class_count":len(temporal_classes),
            "nesting_monotonicity_violations":nesting,
            "complete_positive_compatible_count_by_truth":scenario_complete,
            "temporal_strict_gain_runs":temporal_gain_runs,
            "temporal_nonidentified_h40_runs":temporal_nonidentified_h40,
            "truth_retention_failures":truth_fail,
            "static_expansion_violations":static_expand,
            "api_parity_audits":api_audits,
            "api_parity_mismatches":api_mismatch,
            "median_static_h40":{sid:float(np.median(scenario_static[sid][40])) for sid in truths},
            "median_temporal_h40":{sid:float(np.median(scenario_temporal[sid][40])) for sid in truths},
            "temporal_unique_fraction_h40":{sid:scenario_unique_temp[sid][40]/reps for sid in truths},
        })

    verdicts={
        "U1_truth_retention":"SUPPORTED" if total_truth_fail==0 and eligible_landscapes>0 else "REFUTED",
        "U2_positive_contraction_monotonicity":"SUPPORTED" if total_static_expand==0 and eligible_landscapes>0 else "REFUTED",
        "U3_restrictiveness_nesting":"SUPPORTED" if total_nesting_viol==0 and eligible_landscapes>0 else "REFUTED",
        "U4_joint_limitation_ambiguity":"SUPPORTED" if not u4_failed and eligible_landscapes>0 else "REFUTED",
        "U5_temporal_signature_refinement":"SUPPORTED" if not u5_failed and eligible_landscapes>0 else "REFUTED",
        "U6_realised_temporal_gain":"SUPPORTED" if not u6_failed and eligible_landscapes>0 else "REFUTED",
        "U7_nonidentification_persists":"SUPPORTED" if not u7_failed and eligible_landscapes>0 else "REFUTED",
        "U8_independent_evaluator_parity":"SUPPORTED" if total_api_mismatch==0 and total_api_audits>0 else "REFUTED",
    }
    result={
        "schema":"eog.multilandscape_independent_stochastic_bam.result.v4",
        "eligible_landscape_count":eligible_landscapes,
        "design_stop_count":len(design_stops),
        "design_stops":design_stops,
        "planned_landscape_count":len(LANDSCAPE_PANEL),
        "planned_stochastic_runs":len(LANDSCAPE_PANEL)*len(truths)*reps,
        "eligible_stochastic_runs":eligible_landscapes*len(truths)*reps,
        "truth_retention_failures":total_truth_fail,
        "static_expansion_violations":total_static_expand,
        "nesting_monotonicity_violations":total_nesting_viol,
        "api_parity_audits":total_api_audits,
        "api_parity_mismatches":total_api_mismatch,
        "U4_failed_landscapes":u4_failed,
        "U5_failed_landscapes":u5_failed,
        "U6_failed_landscapes":u6_failed,
        "U7_failed_landscapes":u7_failed,
        "landscapes":landscape_rows,
        "verdicts":verdicts,
    }
    enc=json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    result["fingerprint"]=hashlib.sha256(enc).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "eligible_landscape_count":eligible_landscapes,"design_stop_count":len(design_stops),
        "truth_retention_failures":total_truth_fail,"static_expansion_violations":total_static_expand,
        "nesting_monotonicity_violations":total_nesting_viol,"api_parity_mismatches":total_api_mismatch,
        "U4_failed_landscapes":u4_failed,"U5_failed_landscapes":u5_failed,"U6_failed_landscapes":u6_failed,"U7_failed_landscapes":u7_failed,
        "landscapes":landscape_rows,"verdicts":verdicts,"fingerprint":result["fingerprint"]
    },indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
