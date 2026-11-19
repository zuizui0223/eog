#!/usr/bin/env python3
"""Post-exposure Glanville conditional min-relaxation tail/exception audit.

An explicit k-exception budget allows *unexplained recorded positives* in the
one-hop source model; it never classifies positive records as false observations.
No direction of butterfly movement, occupancy probability or causal effect is
estimated. Source and parent metrics are authenticated before reporting.
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


class AuditStop(Exception):
    pass


def _legacy():
    return runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py")


def _quantile(sorted_distances, probability):
    if not sorted_distances:
        return None
    i=(len(sorted_distances)-1)*probability
    low,high=int(math.floor(i)),int(math.ceil(i))
    if low==high:
        return float(sorted_distances[low])
    return float(sorted_distances[low]*(high-i)+sorted_distances[high]*(i-low))


def _budget(budget, n):
    if budget["type"]=="fixed":
        k=int(budget["value"])
    elif budget["type"]=="floor_fraction":
        k=int(math.floor(n*float(budget["value"])))
    else:
        raise AuditStop("STOP_UNKNOWN_EXCEPTION_BUDGET_TYPE")
    if n<=0 or k<0 or k>=n:
        raise AuditStop("STOP_EXCEPTION_BUDGET_WITH_NO_REMAINING_TARGETS")
    return k


def _target_and_source_rosters(year,policy,network,survey,legacy):
    eligible_host=legacy["_eligible_host"]
    targets=[]
    for (yy,patch),row in survey.items():
        if yy!=year or row[0] is None or row[0]<=0:
            continue
        prior=survey.get((year-1,patch))
        if prior is None or prior[0] is None or prior[0]!=0:
            continue
        host=eligible_host(prior)
        if host is None or patch not in network:
            continue
        targets.append((patch,host,network[patch]))

    source_years=(year-1,) if policy=="previous_year_recorded_positive" else (year-1,year-2)
    sources=[]
    seen=set()
    for yy in source_years:
        for (cy,patch),row in survey.items():
            if cy!=yy or row[0] is None or row[0]<=0:
                continue
            host=eligible_host(row)
            if host is None or patch not in network or patch in seen:
                continue
            seen.add(patch)
            sources.append((patch,host,network[patch]))
    return targets,sources


def _distance_lists(targets,sources,deltas):
    """Evaluate each target/source pair once; accumulate distance minima by gap."""
    output={delta:[] for delta in deltas}
    if deltas!=tuple(sorted(set(deltas))):
        raise AuditStop("STOP_HOST_GAP_GRID_UNORDERED")
    for _target,host,(x,y) in targets:
        minima_by_gap=[math.inf]*4
        for _source,s_host,(xx,yy) in sources:
            gap=max(abs(host[0]-s_host[0]),abs(host[1]-s_host[1]))
            # Original host scores are ordinal in 0..3; fractional but valid
            # scores are handled through threshold checks below.
            if gap>3:
                continue
            distance=math.hypot(x-xx,y-yy)/1000.0
            for delta in deltas:
                if gap<=delta and distance<minima_by_gap[delta]:
                    minima_by_gap[delta]=distance
        for delta in deltas:
            output[delta].append(minima_by_gap[delta])
    return output


def analyze_panel(year,policy,network,survey,legacy,deltas,budgets,parent):
    targets,sources=_target_and_source_rosters(year,policy,network,survey,legacy)
    old=legacy["_radius_for_year"](year,policy,network,survey,deltas)
    if len(targets)!=old["eligible_newly_recorded_positive_targets"] or len(sources)!=old["eligible_candidate_source_patches"]:
        raise AuditStop(f"STOP_PARENT_ROSTER_INTERNAL_MISMATCH_{year}_{policy}")
    if len(targets)!=parent["n_targets"] or len(sources)!=parent["n_sources"]:
        raise AuditStop(f"STOP_FROZEN_PARENT_ROSTER_MISMATCH_{year}_{policy}")
    ds=_distance_lists(targets,sources,deltas)
    k_by_name={b["id"]:_budget(b,len(targets)) for b in budgets}
    rows=[]
    for d_idx,delta in enumerate(deltas):
        values=sorted(ds[delta])
        unsupported=sum(not math.isfinite(x) for x in values)
        oldrow=old["conditional_radius_by_host_tolerance"][d_idx]
        if unsupported!=oldrow["targets_without_allowed_source"] or unsupported!=parent["n_no_source_by_host_gap"][d_idx]:
            raise AuditStop(f"STOP_FROZEN_PARENT_UNSUPPORTED_MISMATCH_{year}_{policy}_{delta}")
        strict=values[-1] if values and math.isfinite(values[-1]) else None
        parent_r=parent["r_km_by_host_gap"][d_idx]
        if strict is not None and (parent_r is None or abs(strict-parent_r)>1e-5):
            raise AuditStop(f"STOP_FROZEN_PARENT_RADIUS_MISMATCH_{year}_{policy}_{delta}")
        if strict is None and parent_r is not None:
            raise AuditStop(f"STOP_FROZEN_PARENT_RADIUS_NOT_NULL_{year}_{policy}_{delta}")
        finite=[value for value in values if math.isfinite(value)]
        desc={
            "finite_target_count":len(finite),
            "missing_compatible_source_count":unsupported,
            "q50_finite_km":_quantile(finite,.50),
            "q90_finite_km":_quantile(finite,.90),
            "q95_finite_km":_quantile(finite,.95),
            "q99_finite_km":_quantile(finite,.99),
            "q95_to_strict_max_ratio":None if strict in (None,0.0) else _quantile(finite,.95)/strict,
        }
        perbudget=[]
        for b in budgets:
            k=k_by_name[b["id"]]
            r=values[len(values)-k-1]
            radius=None if not math.isfinite(r) else float(r)
            perbudget.append({
                "budget_id":b["id"],
                "allowed_unexplained_targets":k,
                "locally_explained_target_count":len(values)-k,
                "minimum_required_radius_km":radius,
                "relative_radius_reduction_vs_strict":(
                    None if strict in (None,0.0) or radius is None
                    else (strict-radius)/strict
                ),
                "not_claiming_excluded_positives_false":True,
            })
        # With more unexplained slots, the required radius cannot increase.
        for a,b in zip(
            sorted(perbudget,key=lambda z:z["allowed_unexplained_targets"]),
            sorted(perbudget,key=lambda z:z["allowed_unexplained_targets"])[1:]
        ):
            x,y=a["minimum_required_radius_km"],b["minimum_required_radius_km"]
            if x is not None and (y is None or y>x+1e-9):
                raise AuditStop(f"STOP_EXCEPTION_MONOTONICITY_{year}_{policy}_{delta}")
        rows.append({
            "host_gap_tolerance":delta,
            "original_strict_radius_km":strict,
            "distribution_of_nearest_source_distances":desc,
            "exception_budgets":perbudget,
        })
    for budget_id in k_by_name:
        previous=math.inf
        for r in rows:
            value=next(x for x in r["exception_budgets"] if x["budget_id"]==budget_id)["minimum_required_radius_km"]
            current=math.inf if value is None else value
            if current>previous+1e-9:
                raise AuditStop(f"STOP_HOST_TOLERANCE_MONOTONICITY_{year}_{policy}_{budget_id}")
            previous=current
    return {
        "year":year,"source_policy":policy,"targets":len(targets),"sources":len(sources),
        "host_gap_rows":rows,
        "same_target_roster_as_frozen_parent":True,
    }


def run_audit(protocol,parent,result_path):
    legacy=_legacy()
    report={
        "schema_version":1,
        "status":"STOP_NOT_STARTED",
        "parent_full_precision_sha256_without_self_hash":protocol["parent_full_precision_sha256_without_self_hash"],
        "parent_replay_exact_metrics_verified":False,
        "source_hashes":{},
        "models_fit":0,
        "new_EOG_WF_endpoints":0,
        "independent_field_replicates_added":0,
        "claim_boundary":"post-exposure target-exception sensitivity, not measured migration or independent biological replication",
    }
    try:
        if protocol["status"]!="pre-score_frozen_post_exposure_sensitivity":
            raise AuditStop("STOP_PROTOCOL_NOT_FROZEN")
        if parent["source_result_fingerprint_without_self_hash"]!=protocol["parent_full_precision_sha256_without_self_hash"]:
            raise AuditStop("STOP_PARENT_FINGERPRINT_MISMATCH")
        years=protocol["original_scientific_contract_unchanged"]["years"]
        policies=protocol["original_scientific_contract_unchanged"]["source_policies"]
        deltas=tuple(protocol["original_scientific_contract_unchanged"]["host_gap_thresholds"])
        if len(parent["annual"])!=len(years)*len(policies):
            raise AuditStop("STOP_PARENT_PANEL_COUNT_MISMATCH")
        with tempfile.TemporaryDirectory(prefix="eog_kexception_source_") as folder:
            base=Path(folder)
            src=protocol["data_source"]
            occ=legacy["_download"]({
                "archive_url":src["schulz2019"]["url"],
                "sha256":src["schulz2019"]["sha256"],
                "tag":"schulz2019_occupancy",
                "filename":"ECOG-04799.zip",
                "max_bytes":src["schulz2019"]["max_bytes"],
            },base)
            gen=legacy["_download"]({
                "archive_url":src["fountain2017"]["url"],
                "sha256":src["fountain2017"]["sha256"],
                "tag":"fountain2017_families",
                "filename":"supplementary-data-COLONY2.tar.gz",
                "max_bytes":src["fountain2017"]["max_bytes"],
            },base)
            network,survey,genotype,coords,families,nrows=legacy["_load_tables"](occ,gen)
            factor=1000.0
            network={patch:(x*factor,y*factor) for patch,(x,y) in network.items()}
            parent_contract=json.loads(Path("validation/glanville_minrelax_empirical_v1/protocol_v1.json").read_text())
            legacy["_check_geographic_contract"](network,coords,genotype,families,parent_contract)
            report["source_hashes"]={name:x["sha256"] for name,x in src.items()}
            frozen={(int(row["year"]),int(row["source_lookback_years"])):row for row in parent["annual"]}
            all_panels=[]
            for year in years:
                for pi,policy in enumerate(policies,1):
                    pkey=(year,pi)
                    all_panels.append(analyze_panel(
                        year,policy,network,survey,legacy,deltas,protocol["new_primary_estimand"]["exception_budgets"],frozen[pkey]
                    ))
            report["parent_replay_exact_metrics_verified"]=True
            report["panels"]=all_panels
            # Source extension adds options, never removes them for the same targets.
            for year in years:
                before=next(p for p in all_panels if p["year"]==year and p["source_policy"]==policies[0])
                after=next(p for p in all_panels if p["year"]==year and p["source_policy"]==policies[1])
                if before["targets"]!=after["targets"]:
                    raise AuditStop("STOP_SOURCE_POLICY_TARGET_ROSTER_DIFFERENCE")
                for r1,r2 in zip(before["host_gap_rows"],after["host_gap_rows"],strict=True):
                    for b1,b2 in zip(r1["exception_budgets"],r2["exception_budgets"],strict=True):
                        a,b=b1["minimum_required_radius_km"],b2["minimum_required_radius_km"]
                        if a is not None and (b is None or b>a+1e-9):
                            raise AuditStop(f"STOP_SOURCE_POLICY_NONMONOTONE_{year}")
            focus=set(protocol["new_primary_estimand"]["primary_environment_panels"])
            primary=[(p,row) for p in all_panels for row in p["host_gap_rows"]
                     if row["host_gap_tolerance"] in focus]
            exception_one_large=0
            strict_nonestimable_rescued={}
            for budget in ("one_percent","five_percent"):
                strict_nonestimable_rescued[budget]=0
            for p,row in primary:
                by_id={b["budget_id"]:b for b in row["exception_budgets"]}
                one=by_id["one"]
                if one["relative_radius_reduction_vs_strict"] is not None and one["relative_radius_reduction_vs_strict"]>=.25:
                    exception_one_large+=1
                if row["original_strict_radius_km"] is None:
                    for budget in strict_nonestimable_rescued:
                        if by_id[budget]["minimum_required_radius_km"] is not None:
                            strict_nonestimable_rescued[budget]+=1
            report["summary"]={
                "total_year_source_panels":len(all_panels),
                "primary_host_gap_panel_count":len(primary),
                "primary_panels_one_exception_reduces_radius_at_least_25_percent":exception_one_large,
                "primary_nonestimable_strict_but_estimable_with_exception_budget":strict_nonestimable_rescued,
                "all_monotonicity_and_frozen_parent_checks_passed":True,
            }
            report["status"]="EXPLORATORY_K_EXCEPTION_AUDIT_PASSED"
    except (AuditStop,legacy["SourceStop"],KeyError,ValueError) as exc:
        report["status"]=str(exc) if isinstance(exc,(AuditStop,legacy["SourceStop"])) else "STOP_SCHEMA_OR_RUNTIME"
        report["error_type"]=type(exc).__name__
        report.pop("panels",None)
        report.pop("summary",None)
    result_path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n"
    report["fingerprint_without_self_hash"]=hashlib.sha256(raw.encode()).hexdigest()
    result_path.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "panels":len(report.get("panels",[])),
        "fingerprint":report["fingerprint_without_self_hash"],
        "result_file":str(result_path),
    },sort_keys=True))
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=Path("validation/glanville_minrelax_exception_budget_v1/protocol_v1.json"))
    parser.add_argument("--parent",type=Path,default=Path("validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json"))
    parser.add_argument("--output",type=Path,default=Path("results/glanville_minrelax_exception_budget_v1/result.json"))
    args=parser.parse_args()
    run_audit(
        json.loads(args.protocol.read_text(encoding="utf-8")),
        json.loads(args.parent.read_text(encoding="utf-8")),
        args.output,
    )


if __name__=="__main__":
    main()
