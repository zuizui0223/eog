#!/usr/bin/env python3
"""Local-only genetic assigned-origin versus EOG existential host/radius worlds.

Requires two source-authenticated plaintext files ALREADY present on local machine:
- Dryad DiLeo fullsibfamLevelData.csv, sha256 fixed below;
- locally decrypted 2019 Schulz survey/network snapshot in original bridge JSON schema.
NEVER run the input files in GitHub CI or commit source/event rows. Output aggregate
family/year and target-year counts only; no identifiers, coordinates or event values.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

GENETIC_SHA="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
PARENT_COUNTS={2008:(157,695),2009:(285,508),2010:(102,587),2011:(521,298),2012:(400,764)}
HOST_DELTA=(0,1,2,3)
RADII=(2,5)


class SourceStop(Exception):
    pass


def number(v):
    try:
        f=float(v)
        return f if math.isfinite(f) else None
    except (ValueError,TypeError,OverflowError):
        return None


def read_local_published_family(path:Path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=GENETIC_SHA:
        raise SourceStop("STOP_PUBLISHER_GENETIC_CSV_SHA")
    rows=[]
    with path.open(encoding="utf-8-sig",newline="") as f:
        it=csv.DictReader(f)
        required=("YearFrom","YearTo","PatchFrom","PatchTo","fullsibfam","dispersalBin","dispersalDistance")
        if not set(required).issubset(it.fieldnames or []):
            raise SourceStop("STOP_GENETIC_HEADER")
        for row in it:
            try:
                yf,yt=int(row["YearFrom"]),int(row["YearTo"])
                source,target=str(int(row["PatchFrom"])),str(int(row["PatchTo"]))
                family=str(row["fullsibfam"]);binary=int(row["dispersalBin"])
                distance=float(row["dispersalDistance"])
            except (ValueError,TypeError) as e:
                raise SourceStop("STOP_GENETIC_ROW_SCHEMA") from e
            if (yt!=yf+1 or yf not in (2007,2008,2009,2010,2011)
                or binary != int(source!=target) or distance<0 or not math.isfinite(distance)
                or (source==target and distance!=0) or (source!=target and distance<=0)):
                raise SourceStop("STOP_GENETIC_ROW_INVARIANT")
            rows.append((yf,yt,source,target,family,binary,distance))
    if len(rows)!=799 or len({(x[0],x[4]) for x in rows})!=760:
        raise SourceStop("STOP_GENETIC_ORIGINAL_GRAIN")
    return rows


def qualified_survey(snapshot:dict):
    if snapshot.get("years")!=[2007,2008,2009,2010,2011,2012]:
        raise SourceStop("STOP_SURVEY_YEAR_SCOPE")
    if len(snapshot.get("survey",[]))!=22406 or len(snapshot.get("network",[]))!=4656:
        raise SourceStop("STOP_SURVEY_SOURCE_ROW_COUNTS")
    survey={}
    for y,p,pop,plant,vero in snapshot["survey"]:
        key=(int(y),str(p))
        if key in survey:
            raise SourceStop("STOP_SURVEY_DUPLICATE")
        survey[key]=(number(pop),number(plant),number(vero))
    network={}
    for patch,x,y in snapshot["network"]:
        key=str(patch)
        if key in network:
            raise SourceStop("STOP_PATCH_DUPLICATE")
        xx,yy=number(x),number(y)
        if xx is not None and yy is not None:
            network[key]=(xx,yy)  # publisher's EPSG:3067 centroid kilometers
    return survey,network


def has_hosts(row):
    return (row is not None and row[1] is not None and row[2] is not None
            and 0<=row[1]<=3 and 0<=row[2]<=3)


def family_structure(rows):
    groups=defaultdict(list)
    for yf,yt,source,target,fam,binary,d in rows:
        groups[(yf,fam)].append((source,target,binary))
    doubles=[items for items in groups.values() if len(items)>1]
    if len(groups)!=760 or len(doubles)!=39 or any(len(items)!=2 for items in doubles):
        raise SourceStop("STOP_FAMILY_GRAIN")
    mixed=sum(sorted(x[2] for x in items)==[0,1] for items in doubles)
    moved_both=sum(sorted(x[2] for x in items)==[1,1] for items in doubles)
    different_origin=sum(len({x[0] for x in items})>1 for items in doubles)
    if (mixed,moved_both,different_origin)!=(21,18,1):
        raise SourceStop("STOP_FAMILY_SPLIT_STRUCTURE")
    return dict(family_count=760,two_destination_families=39,
                one_stay_one_move=mixed,both_move_to_different_destinations=moved_both,
                differing_origin_labels_between_split_family_parts=different_origin)


def make_worlds(genetic,survey,network,strict=True):
    rosters={}
    for yf in range(2007,2012):
        rosters[yf]=[(p,row[1],row[2],network[p]) for (y,p),row in survey.items()
            if y==yf and row[0] is not None and row[0]>0 and has_hosts(row) and p in network]
    if strict:
        for year,(expected_targets,expected_sources) in PARENT_COUNTS.items():
            nt=sum(1 for (y,p),current in survey.items()
                   if y==year and current[0] is not None and current[0]>0 and
                   (year-1,p) in survey and survey[(year-1,p)][0]==0 and
                   has_hosts(survey[(year-1,p)]) and p in network)
            if nt!=expected_targets or len(rosters[year-1])!=expected_sources:
                raise SourceStop("STOP_PARENT_ROSTERS_REPLAY")
    eligible=[]
    nearest_cache={}
    for yf,yt,pf,pt,family,binary,assigned in genetic:
        if not binary:
            continue
        prior=survey.get((yf,pt))
        now=survey.get((yt,pt))
        source=survey.get((yf,pf))
        if not (prior is not None and prior[0]==0 and has_hosts(prior) and
                now is not None and now[0] is not None and now[0]>0 and pt in network):
            continue
        if not (source is not None and source[0] is not None and source[0]>0 and
                has_hosts(source) and pf in network):
            continue
        gap=max(abs(source[1]-prior[1]),abs(source[2]-prior[2]))
        distance=math.dist(network[pf],network[pt])
        if abs(assigned-distance)>0.05:
            raise SourceStop("STOP_SOURCE_GEOMETRY_DIFFERENCE")
        target=(yt,pt)
        if target not in nearest_cache:
            v={d:math.inf for d in HOST_DELTA}
            for sp,a,b,xy in rosters[yf]:
                hg=max(abs(a-prior[1]),abs(b-prior[2]))
                sep=math.dist(network[pt],xy)
                for delta in HOST_DELTA:
                    if hg<=delta:
                        v[delta]=min(v[delta],sep)
            nearest_cache[target]=v
        eligible.append(dict(year=yt,target=target,family=(yf,family),
                             source=pf,host_gap=gap,distance=distance,
                             nearest=nearest_cache[target]))
    if strict and (len(eligible),len(nearest_cache))!=(163,100):
        raise SourceStop("STOP_PREVIOUS_CROSSWALK_GRAIN")
    worlds=[]
    for delta in HOST_DELTA:
        for radius in RADII:
            peryear={}
            for year in range(2008,2013):
                selected=[x for x in eligible if x["year"]==year]
                grouped=defaultdict(list)
                for x in selected:grouped[x["target"]].append(x)
                eligible_count=sum(x["host_gap"]<=delta for x in selected)
                assigned_count=sum(x["host_gap"]<=delta and x["distance"]<=radius for x in selected)
                eog_count=sum(x["nearest"][delta]<=radius for x in selected)
                if any(x["nearest"][delta]>x["distance"]+1e-7 for x in selected if x["host_gap"]<=delta):
                    raise SourceStop("STOP_ASSIGNED_SOURCE_LESS_THAN_NEAREST")
                if any(x["host_gap"]<=delta and x["distance"]<=radius and x["nearest"][delta]>radius for x in selected):
                    raise SourceStop("STOP_EXPLICIT_SOURCE_NOT_EOG_POSSIBLE")
                peryear[str(year)]={
                    "genetic_assignment_rows":len(selected),
                    "destination_patch_years":len(grouped),
                    "genetically_assigned_source_host_compatible_rows":eligible_count,
                    "EOG_any_source_within_r_assignment_rows":eog_count,
                    "genetically_assigned_source_within_r_assignment_rows":assigned_count,
                    "EOG_any_source_within_r_distinct_destinations":
                        sum(group[0]["nearest"][delta]<=radius for group in grouped.values()),
                    "at_least_one_assigned_source_within_r_distinct_destinations":
                        sum(any(x["host_gap"]<=delta and x["distance"]<=radius for x in group) for group in grouped.values()),
                    "all_assigned_sources_within_r_distinct_destinations":
                        sum(all(x["host_gap"]<=delta and x["distance"]<=radius for x in group) for group in grouped.values()),
                }
            totals={k:sum(part[k] for part in peryear.values()) for k in peryear["2008"]}
            worlds.append({"host_gap_delta":delta,"radius_km":radius,"combined":totals,"by_arrival_year":peryear})
    for item in worlds:
        for greater in worlds:
            if greater["host_gap_delta"]>=item["host_gap_delta"] and greater["radius_km"]>=item["radius_km"]:
                for name in ("EOG_any_source_within_r_distinct_destinations",
                             "at_least_one_assigned_source_within_r_distinct_destinations"):
                    if greater["combined"][name]<item["combined"][name]:
                        raise SourceStop("STOP_NESTED_WORLDS")
    return eligible,worlds


def audit(genetic,survey,network):
    eligible,worlds=make_worlds(genetic,survey,network)
    groups=defaultdict(list)
    for x in eligible:
        groups[x["target"]].append(x["distance"])
    def q(v,p):
        v=sorted(v)
        pos=(len(v)-1)*p; lo=int(pos); hi=math.ceil(pos)
        return v[lo] if lo==hi else v[lo]*(hi-pos)+v[hi]*(pos-lo)
    nearest={x["target"]:x["nearest"][3] for x in eligible}
    ass={target:statistics.median(dist) for target,dist in groups.items()}
    if len(eligible)!=163 or len(groups)!=100:
        raise SourceStop("STOP_ELIGIBILITY_REPLAY")
    if abs(q(list(ass.values()),.5)-1.211)>0.02 or abs(q(list(nearest.values()),.5)-.284)>0.02:
        raise SourceStop("STOP_PRIOR_MEDIANS_REPLAY")
    out={
      "schema_version":2,
      "status":"GENETIC_SPECIFIC_SOURCE_VS_EOG_EXISTENTIAL_HOST_WORLD_AUDITED",
      "genetic_source_sha256":GENETIC_SHA,
      "year_range":"YearFrom 2007-2011, YearTo 2008-2012",
      "selected_jointly_eligible_family_destination_rows":len(eligible),
      "distinct_target_patch_years":len(groups),
      "distinct_genetically_inferred_families":len({x["family"] for x in eligible}),
      "family_structure":family_structure(genetic),
      "assigned_source_host_gap_counts":{str(int(d)):sum(x["host_gap"]==d for x in eligible) for d in HOST_DELTA},
      "target_equal_weighted_medians_km":{
        "assigned_origin":q(list(ass.values()),.5),
        "nearest_EOG_source":q(list(nearest.values()),.5),
        "median_of_paired_assigned_minus_nearest":q([d-nearest[t] for t,d in ass.items()],.5),
      },
      "worlds":worlds,
      "uncertainty":"Genetic source is a prior-year sampled-reference GENECLASS2 assignment, NOT true known natal source. Family portions across destinations were assigned separately; no per-row assignment score in source file.",
      "EOG_WF_new_endpoints":0,
      "records_or_site_ids_exported":0,
    }
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--genetic-csv",type=Path,required=True)
    parser.add_argument("--decrypted-local-survey-json",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    genetic=read_local_published_family(args.genetic_csv)
    survey,network=qualified_survey(json.loads(args.decrypted_local_survey_json.read_text()))
    result=audit(genetic,survey,network)
    original=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
    result["fingerprint_without_self_hash"]=hashlib.sha256(original.encode()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"worlds":len(result["worlds"]),
                      "n_targets":result["distinct_target_patch_years"]},sort_keys=True))


if __name__=="__main__":
    main()
