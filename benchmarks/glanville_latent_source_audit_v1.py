#!/usr/bin/env python3
"""Post-exposure Glanville latent-source compatibility sensitivity.

t-1 recorded zeros are HYPOTHETICAL sources, not certified occupied patches.
Given distance/host gates, compare coverage by known t-1 positives with
retrospectively optimized 1/5/10 latent zero-source additions. Selection is
descriptive optimization on already-seen targets, not prospective validation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import runpy
import tempfile


class GateStop(Exception):
    pass


def _source_modules():
    return (runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py"),
            runpy.run_path("benchmarks/glanville_minrelax_exception_budget_v1.py"))


def _keys(p):
    return (str(p[0]), p[1], p[2])


def _grid(points, radius_m):
    cells=defaultdict(list)
    for p in points:
        x,y=p[2]
        cells[(math.floor(x/radius_m),math.floor(y/radius_m))].append(p)
    return cells


def _neighbors(grid,x,y,radius_m):
    i,j=math.floor(x/radius_m), math.floor(y/radius_m)
    for ci in (i-1,i,i+1):
        for cj in (j-1,j,j+1):
            yield from grid.get((ci,cj),())


def _compatible(host_a,host_b,delta):
    return max(abs(host_a[0]-host_b[0]),abs(host_a[1]-host_b[1])) <= delta


def _base_mask(targets,sources,delta,radius_km):
    radius_m=radius_km*1000.0
    grid=_grid(sources,radius_m)
    radius_sq=radius_m*radius_m
    mask=0
    for index,(_pid,host,(x,y)) in enumerate(targets):
        for _source,source_host,(sx,sy) in _neighbors(grid,x,y,radius_m):
            if _compatible(host,source_host,delta) and (x-sx)**2+(y-sy)**2 <= radius_sq+1e-7:
                mask |= 1<<index
                break
    return mask


def _candidate_masks(targets,candidates,base_mask,delta,radius_km,allow_same_patch):
    radius_m=radius_km*1000.0
    radius_sq=radius_m**2
    uncovered_targets=[
        (index,patch,host,xy)
        for index,(patch,host,xy) in enumerate(targets)
        if not base_mask & (1<<index)
    ]
    cells=defaultdict(list)
    for index,patch,host,(x,y) in uncovered_targets:
        cells[(math.floor(x/radius_m), math.floor(y/radius_m))].append((index,patch,host,(x,y)))
    out=[]
    for source_patch,source_host,(sx,sy) in sorted(candidates,key=lambda row:row[0]):
        mask=0
        for index,target_patch,target_host,(tx,ty) in _neighbors(cells,sx,sy,radius_m):
            if not allow_same_patch and source_patch==target_patch:
                continue
            if _compatible(source_host,target_host,delta) and (tx-sx)**2+(ty-sy)**2 <= radius_sq+1e-7:
                mask |= 1<<index
        if mask:
            out.append((source_patch,mask))
    return out


def _greedy(mask_pairs,base_mask,budgets):
    selected=set()
    covered=base_mask
    full_union=base_mask
    for _,mask in mask_pairs:
        full_union |= mask
    results={0:{"locally_explained":base_mask.bit_count(),"additional_sources_selected":0}}
    for step in range(1,max(budgets)+1):
        best_patch=None
        best_gain=0
        best_mask=0
        for patch,mask in mask_pairs:
            if patch in selected:
                continue
            gain=(mask & ~covered).bit_count()
            if gain>best_gain:
                best_patch,best_mask,best_gain=patch,mask,gain
        if best_gain==0:
            for remain in range(step,max(budgets)+1):
                if remain in budgets:
                    results[remain]={
                        "locally_explained":covered.bit_count(),
                        "additional_sources_selected":len(selected),
                    }
            break
        selected.add(best_patch)
        covered |= best_mask
        if step in budgets:
            results[step]={
                "locally_explained":covered.bit_count(),
                "additional_sources_selected":len(selected),
            }
    return results, full_union.bit_count()


def _candidate_roster(year, network, survey, legacy):
    eligible_host=legacy["_eligible_host"]
    zeros=[]
    historically_supported=[]
    for (yy,patch),row in survey.items():
        if yy!=year-1 or row[0] is None or row[0]!=0:
            continue
        host=eligible_host(row)
        if host is None or patch not in network:
            continue
        info=(patch,host,network[patch])
        zeros.append(info)
        past=survey.get((year-2,patch))
        if past is not None and past[0] is not None and past[0]>0:
            historically_supported.append(info)
    return {"all_recorded_zero":zeros,"supported_tminus2":historically_supported}


def _parent_replay(years,policies,deltas,network,survey,legacy,parent):
    parent_by={(row["year"],row["source_lookback_years"]):row for row in parent["annual"]}
    if len(parent_by)!=len(years)*len(policies):
        raise GateStop("STOP_PARENT_PANEL_COUNT")
    for year in years:
        for index,policy in enumerate(policies,1):
            frozen=parent_by[(year,index)]
            actual=legacy["_radius_for_year"](year,policy,network,survey,deltas)
            if (actual["eligible_newly_recorded_positive_targets"]!=frozen["n_targets"]
                or actual["eligible_candidate_source_patches"]!=frozen["n_sources"]):
                raise GateStop(f"STOP_PARENT_ROSTER_{year}_{index}")
            for d,row in enumerate(actual["conditional_radius_by_host_tolerance"]):
                expected=frozen["r_km_by_host_gap"][d]
                observed=row["max_of_nearest_compatible_source_km"]
                if row["targets_without_allowed_source"]!=frozen["n_no_source_by_host_gap"][d]:
                    raise GateStop(f"STOP_PARENT_UNSUPPORTED_{year}_{index}_{d}")
                if (expected is None)!=(observed is None):
                    raise GateStop(f"STOP_PARENT_RADIUS_DEFINED_{year}_{index}_{d}")
                if expected is not None and abs(expected-observed)>1e-5:
                    raise GateStop(f"STOP_PARENT_RADIUS_{year}_{index}_{d}")


def panel(year,delta,radius_km,candidate_pool,same_patch,targets,sources,candidates,budgets):
    base=_base_mask(targets,sources,delta,radius_km)
    allow_self=(same_patch=="allow_same_patch")
    masks=_candidate_masks(targets,candidates,base,delta,radius_km,allow_self)
    coverage, union_count=_greedy(masks,base,tuple(budgets))
    possible_extra=sum(1 for _,mask in masks if mask)
    if 1 in coverage:
        best=coverage[1]["locally_explained"]-base.bit_count()
        exhaustive=max((mask.bit_count() for _,mask in masks),default=0)
        if best!=exhaustive:
            raise GateStop("STOP_EXACT_ONE_CANDIDATE_COVERAGE")
    n=len(targets)
    if not 0<=base.bit_count()<=union_count<=n:
        raise GateStop("STOP_COVERAGE_ORDER")
    previous=base.bit_count()
    rows=[]
    for budget in budgets:
        info=coverage[budget]
        count=info["locally_explained"]
        if not previous<=count<=union_count:
            raise GateStop("STOP_BUDGET_MONOTONICITY")
        previous=count
        rows.append({
            "hypothetical_hidden_source_budget":budget,
            "explained_target_count":count,
            "still_unexplained_target_count":n-count,
            "additional_sources_selected":info["additional_sources_selected"],
        })
    return {
        "year":year,
        "host_gap_tolerance":delta,
        "radius_km":radius_km,
        "candidate_pool":candidate_pool,
        "same_patch_policy":same_patch,
        "total_positive_targets":n,
        "positive_observed_source_count":len(sources),
        "recorded_zero_candidate_count":len(candidates),
        "recorded_zero_candidates_covering_new_targets":possible_extra,
        "baseline_covered_by_observed_positive_sources":base.bit_count(),
        "baseline_unexplained_target_count":n-base.bit_count(),
        "optimistic_coverage_if_all_zero_candidates_are_occupied":union_count,
        "optimistic_unexplained_if_all_zero_candidates_are_occupied":n-union_count,
        "max_additional_targets_explained_by_one_source_exact":max(
            (mask.bit_count() for _,mask in masks), default=0
        ),
        "greedy_feasible_not_global_minimum":True,
        "hypothetical_source_budget_results":rows,
    }


def run_audit(protocol,parent,prior_exception,out_path):
    legacy,tail=_source_modules()
    result={
        "schema_version":1,
        "status":"STOP_NOT_STARTED",
        "post_exposure_exploratory":True,
        "real_detection_posterior_estimated":False,
        "mechanism_identified":False,
        "model_fits":0,
        "new_EOG_WF_endpoints":0,
        "parent_strict_source_sha256":protocol["prior_results"]["strict_result_sha256"],
        "parent_exception_source_sha256":protocol["prior_results"]["exception_result_sha256"],
    }
    try:
        if protocol["status"]!="frozen_before_latent_source_sensitivity_scoring":
            raise GateStop("STOP_PROTOCOL_NOT_FROZEN")
        if (parent["source_result_fingerprint_without_self_hash"]!=protocol["prior_results"]["strict_result_sha256"] or
            prior_exception["full_result_sha256_without_self_hash"]!=protocol["prior_results"]["exception_result_sha256"]):
            raise GateStop("STOP_PARENT_FINGERPRINT")
        years=tuple(protocol["target_years"])
        policies=("previous_year_recorded_positive","previous_two_years_recorded_positive")
        with tempfile.TemporaryDirectory(prefix="eog_zero_source_") as d:
            root=Path(d)
            soc=protocol["sources"]
            occ=legacy["_download"]({
                "archive_url":soc["occurrence"]["url"],
                "sha256":soc["occurrence"]["sha256"],
                "max_bytes":soc["occurrence"]["size_limit_bytes"],
                "tag":"schulz2019_occupancy",
                "filename":"ECOG-04799.zip",
            },root)
            gen=legacy["_download"]({
                "archive_url":soc["genetic"]["url"],
                "sha256":soc["genetic"]["sha256"],
                "max_bytes":soc["genetic"]["size_limit_bytes"],
                "tag":"fountain2017_families",
                "filename":"supplementary-data-COLONY2.tar.gz",
            },root)
            network,survey,genotype,coords,families,_=legacy["_load_tables"](occ,gen)
            network={p:(x*1000,y*1000) for p,(x,y) in network.items()}
            check=json.loads(Path("validation/glanville_minrelax_empirical_v1/protocol_v1.json").read_text())
            legacy["_check_geographic_contract"](network,coords,genotype,families,check)
            # This verifies exactly 48 prior strict compatibility cells, BEFORE
            # the new hypothetical-zero-source compatibility calculations.
            _parent_replay(years,policies,(0,1,2,3),network,survey,legacy,parent)
            result["parent_strict_48_cells_reproduced"]=True
            result["source_archive_sha256"]={key:value["sha256"] for key,value in soc.items()}
            limit=protocol["computational_maxima"]["max_patch_universe"]
            if len(network)>limit:
                raise GateStop("STOP_PATCH_UNIVERSE_BUDGET")
            budgets=tuple(protocol["latent_source_addition_budgets"])
            all_rows=[]
            for year in years:
                targets,sources=tail["_target_and_source_rosters"](
                    year,policies[0],network,survey,legacy
                )
                zeros=_candidate_roster(year,network,survey,legacy)
                eligible_sources={p for p,_,_ in sources}
                if any(p in eligible_sources for rows in zeros.values() for p,_,_ in rows):
                    raise GateStop("STOP_ZERO_POOL_OVERLAPS_RECORDED_POSITIVES")
                for delta in protocol["fixed_host_tolerances"]:
                    for radius in protocol["fixed_radius_km"]:
                        base=_base_mask(targets,sources,delta,radius).bit_count()
                        for c in protocol["latent_candidate_subsets"]:
                            for s in protocol["same_patch_cases"]:
                                row=panel(
                                    year,delta,radius,c["id"],s["id"],
                                    targets,sources,zeros[c["id"]],budgets
                                )
                                if row["baseline_covered_by_observed_positive_sources"]!=base:
                                    raise GateStop("STOP_BASELINE_CHANGED_BY_LATENT_POLICY")
                                all_rows.append(row)
            expected=math.prod([
                len(years),
                len(protocol["fixed_host_tolerances"]),
                len(protocol["fixed_radius_km"]),
                len(protocol["latent_candidate_subsets"]),
                len(protocol["same_patch_cases"]),
            ])
            if expected!=len(all_rows) or expected!=protocol["computational_maxima"]["max_matrix_rows"]:
                raise GateStop("STOP_MATRIX_COUNT")
            # With same target/source, extra candidate zeros are a superset.
            by={
                (r["year"],r["host_gap_tolerance"],r["radius_km"],r["candidate_pool"],r["same_patch_policy"]):r
                for r in all_rows
            }
            for r in all_rows:
                key=(r["year"],r["host_gap_tolerance"],r["radius_km"])
                if r["candidate_pool"]=="supported_tminus2":
                    broad=by[(*key,"all_recorded_zero",r["same_patch_policy"])]
                    if broad["optimistic_coverage_if_all_zero_candidates_are_occupied"]<r["optimistic_coverage_if_all_zero_candidates_are_occupied"]:
                        raise GateStop("STOP_POOL_MONOTONICITY")
                if r["same_patch_policy"]=="exclude_same_patch":
                    allow=by[(*key,r["candidate_pool"],"allow_same_patch")]
                    if allow["optimistic_coverage_if_all_zero_candidates_are_occupied"]<r["optimistic_coverage_if_all_zero_candidates_are_occupied"]:
                        raise GateStop("STOP_SAME_PATCH_MONOTONICITY")
                if r["radius_km"]==min(protocol["fixed_radius_km"]):
                    wider=by[(r["year"],r["host_gap_tolerance"],
                              max(protocol["fixed_radius_km"]),r["candidate_pool"],r["same_patch_policy"])]
                    if wider["baseline_covered_by_observed_positive_sources"]<r["baseline_covered_by_observed_positive_sources"] or wider["optimistic_coverage_if_all_zero_candidates_are_occupied"]<r["optimistic_coverage_if_all_zero_candidates_are_occupied"]:
                        raise GateStop("STOP_RADIUS_MONOTONICITY")
                if r["host_gap_tolerance"]==min(protocol["fixed_host_tolerances"]):
                    wider=by[(r["year"],max(protocol["fixed_host_tolerances"]),
                              r["radius_km"],r["candidate_pool"],r["same_patch_policy"])]
                    if wider["baseline_covered_by_observed_positive_sources"]<r["baseline_covered_by_observed_positive_sources"] or wider["optimistic_coverage_if_all_zero_candidates_are_occupied"]<r["optimistic_coverage_if_all_zero_candidates_are_occupied"]:
                        raise GateStop("STOP_HOST_MONOTONICITY")
            result["matrix"]=all_rows
            result["summary"]={
                "matrix_panels":len(all_rows),
                "parent_strict_cells_reproduced":48,
                "all_invariants_passed":True,
                "source_history_moved_into_latent_unknown_not_truth":True,
            }
            result["status"]="EXPLORATORY_LATENT_SOURCE_COMPATIBILITY_AUDIT_PASSED"
    except (GateStop,legacy["SourceStop"],KeyError,ValueError) as exc:
        result["status"]=str(exc) if isinstance(exc,(GateStop,legacy["SourceStop"])) else "STOP_SOURCE_SCHEMA_OR_RUNTIME"
        result["error_type"]=type(exc).__name__
        result.pop("matrix",None)
        result.pop("summary",None)
    out_path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    result["fingerprint_without_self_hash"]=hashlib.sha256(content.encode()).hexdigest()
    out_path.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "matrix_panels":len(result.get("matrix",[])),
        "sha256":result["fingerprint_without_self_hash"],
    },sort_keys=True))
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=Path("validation/glanville_latent_source_audit_v1/protocol_v1.json"))
    p.add_argument("--parent",type=Path,default=Path("validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json"))
    p.add_argument("--exception-parent",type=Path,default=Path("validation/glanville_minrelax_exception_budget_v1/frozen_primary_aggregate_summary_v1.json"))
    p.add_argument("--output",type=Path,default=Path("results/glanville_latent_source_audit_v1/result.json"))
    args=p.parse_args()
    run_audit(
        json.loads(args.protocol.read_text()),
        json.loads(args.parent.read_text()),
        json.loads(args.exception_parent.read_text()),
        args.output,
    )


if __name__=="__main__":
    main()
