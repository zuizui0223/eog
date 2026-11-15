"""Cross-language source-stage verification of original R nmixmatrix counts.

The original published R calls nmixmatrix after constructing 20 pseudo-rows
per site. This audit authenticates source data, source-row maps, and R matrix
cells. It never fits an occupancy model or infers field-independent effort.
"""
import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

SURVEY_SHA = "45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
NMIX_BLOB = "40e0f5547cd67729e1c6d46d29a0ce2b75712a3a"
META = {"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}
EXPECTED = {"published_q1":(27,540,144,3), "published_q2":(13,260,77,6)}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        rdr=csv.DictReader(f)
        return list(rdr), list(rdr.fieldnames)


def kish_weight_concentration(source_ids):
    """Duplicate-weight concentration only, NOT inferential sample size."""
    c=Counter(source_ids)
    n=len(source_ids)
    if not n:
        raise ValueError("empty pseudo-occasion list")
    return n*n / sum(w*w for w in c.values())


def inspect_one(native, species, mapping, cells, cohort):
    sites,positions,expected_native_pos,expected_lost=EXPECTED[cohort]
    if len(mapping)!=positions or len(cells)!=positions*len(species):
        raise ValueError("pseudo-row or species-cell dimension drift")
    mapped={}
    selected=defaultdict(list)
    for m in mapping:
        try:
            key=(m["site"],int(m["eog_replay_repeat_index"]))
            rid=int(m["eog_native_row_index"])
        except (ValueError,TypeError,KeyError) as err:
            raise ValueError("invalid pseudo-occasion source key") from err
        if not 1<=rid<=len(native) or key in mapped or not 1<=key[1]<=20:
            raise ValueError("reused or out-of-range pseudo index")
        if m["site"]!=native[rid-1]["site"]:
            raise ValueError("mapped native site mismatch")
        mapped[key]=(rid,m)
        selected[key[0]].append(rid)
    if len(selected)!=sites or any(len(v)!=20 for v in selected.values()):
        raise ValueError("not 20 source-based positions at each site")
    if set(k[1] for k in mapped)!={*range(1,21)}:
        raise ValueError("missing repeated-index positions")
    species_cells=set()
    selected_positive=set()
    entries_gt1=0
    matrix_positive=0
    sum_matrix_counts=0
    for entry in cells:
        sp=entry.get("species")
        if sp not in species:
            raise ValueError("unexpected R species")
        try:
            key=(entry["site"],int(entry["repeat_index"]))
            rid=int(entry["source_row_id"])
            count=int(entry["nmix_count"])
            native_count=int(entry["native_count"])
            detected=int(entry["nmix_detected"])
        except (KeyError,TypeError,ValueError) as err:
            raise ValueError("nonnumeric R matrix cell metadata") from err
        triple=(key[0],key[1],sp)
        if triple in species_cells or key not in mapped:
            raise ValueError("duplicate R cell or unregistered site/repeat")
        species_cells.add(triple)
        mapped_id,m=mapped[key]
        source=native[mapped_id-1]
        if rid!=mapped_id or any(entry.get(k)!=source[k] for k in
            ("site","surv","date","method")):
            raise ValueError("R matrix cell source identity mismatch")
        if count<0 or count!=native_count or count!=int(source[sp]):
            raise ValueError("R nmixmatrix cell did not retain native count")
        if detected!=int(count>0):
            raise ValueError("R derived binary detection label mismatch")
        if count>0:
            matrix_positive+=1
            selected_positive.add((key[0],sp))
        entries_gt1+=int(count>1)
        sum_matrix_counts+=count
    if len(species_cells)!=len(cells):
        raise ValueError("incomplete R matrix cells")
    source_positive={(r["site"],sp) for r in native
                     if r["site"] in selected for sp in species if int(r[sp])>0}
    if len(source_positive)!=expected_native_pos:
        raise ValueError("native positive source scope drift")
    if not selected_positive<=source_positive:
        raise ValueError("R matrix introduced an absent-from-source positive species")
    missing=sorted(source_positive-selected_positive)
    if len(missing)!=expected_lost:
        raise ValueError("R matrix native-positive loss disagrees with source-map replay")
    kis=[kish_weight_concentration(v) for v in selected.values()]
    weights_by_site={site:kish_weight_concentration(ids) for site,ids in sorted(selected.items())}
    by_method=Counter()
    uniq_by_method=defaultdict(set)
    group_keys=set()
    dates=set()
    for (site,_),(_,m) in mapped.items():
        method=m["method"]
        by_method[method]+=1
        uniq_by_method[method].add(m["eog_native_row_index"])
        group_keys.add((site,m["surv"]))
        dates.add((site,m["date"]))
    return {
        "sites":sites, "pseudo_positions":positions,
        "R_nmixmatrix_cells":len(cells), "source_species_columns":len(species),
        "all_R_counts_match_native_selected_rows":True,
        "positive_R_cells_gt_zero":matrix_positive,
        "R_cells_with_native_count_gt_one":entries_gt1,
        "sum_R_matrix_native_counts":sum_matrix_counts,
        "raw_source_positive_site_species":len(source_positive),
        "R_stage_positive_site_species":len(selected_positive),
        "lost_native_positive_site_species":[{"site":site,"species":sp} for site,sp in missing],
        "repeated_source_row_positions":sum(20-len(set(v)) for v in selected.values()),
        "distinct_native_rows_selected":sum(len(set(v)) for v in selected.values()),
        "unique_site_method_day_group_keys_represented":len(group_keys),
        "unique_site_date_combinations_represented":len(dates),
        "method_pseudo_row_positions":dict(sorted(by_method.items())),
        "method_distinct_native_source_rows":{k:len(v) for k,v in sorted(uniq_by_method.items())},
        "Kish_duplicate_weight_concentration_not_inferential_ESS":{
            "mean_per_site":statistics.mean(kis),
            "median_per_site":statistics.median(kis),
            "min_per_site":min(kis),
            "max_per_site":max(kis),
            "sum_across_sites":sum(kis),
            "fraction_of_nominal_pseudo_rows":sum(kis)/positions,
            "by_site":weights_by_site,
        }
    }


def run(surveys,run_dir):
    if hashlib.sha256(Path(surveys).read_bytes()).hexdigest()!=SURVEY_SHA:
        raise ValueError("source survey SHA drift")
    native,columns=read_csv(surveys)
    species=[c for c in columns if c not in META]
    if len(species)!=9:
        raise ValueError("source species column count drift")
    out={
      "schema":"eog.wetland_nmixmatrix_stage_v1.result",
      "status":"EXACT_R_STAGE_MATRIX_PARITY_NOT_OCCUPANCY",
      "scientific_role":"POST_EXPOSURE_SOURCE_STAGE_METHOD_AUDIT",
      "source_sha256":SURVEY_SHA,
      "upstream_nmixmatrix_blob_sha1":NMIX_BLOB,
      "historical_installed_R_package_verified":False,
      "original_unmarked_fitted_model_reproduced":False,
      "cohorts":{},
      "limits":[
        "nmixmatrix returns raw counts; the MD5-verified published Q1/Q2 scripts separately clip all nine species counts >1 to binary 1 before ylist/unmarked.",
        "Binary count>0 matches the authors\u0027 declared ylist conversion for nonnegative native counts, not a verified ecological absence.",
        "Kish is a source-row weight concentration summary, not estimated inferential effective sample size.",
        "Resampled site positions do not establish 20 independent survey occasions.",
        "No field trap IDs, effort, closure, species movement or causal A/B/M inference established.",
        "The closed EOG-WF three scored endpoints are unchanged.",
      ]
    }
    for cohort in EXPECTED:
        root=Path(run_dir)
        mfile=root/f"{cohort}_source_row_mapping.csv"
        cfile=root/f"{cohort}_nmixmatrix_cells.csv"
        mapping,_=read_csv(mfile)
        cells,_=read_csv(cfile)
        out["cohorts"][cohort]={
            "diagnostic":inspect_one(native,species,mapping,cells,cohort),
            "nmix_cells_sha256":hashlib.sha256(cfile.read_bytes()).hexdigest(),
            "mapping_sha256":hashlib.sha256(mfile.read_bytes()).hexdigest(),
        }
    out["fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",type=Path,required=True)
    p.add_argument("--run-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.surveys,a.run_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("WETLAND_NMIX_PARITY="+json.dumps({
        "fingerprint":result["fingerprint"],
        "cohorts":{k:{
            "cells":v["diagnostic"]["R_nmixmatrix_cells"],
            "positive_cells":v["diagnostic"]["positive_R_cells_gt_zero"],
            "count_gt_one":v["diagnostic"]["R_cells_with_native_count_gt_one"],
            "Kish_mean":v["diagnostic"]["Kish_duplicate_weight_concentration_not_inferential_ESS"]["mean_per_site"],
            "method_positions":v["diagnostic"]["method_pseudo_row_positions"],
        }for k,v in result["cohorts"].items()}
    },sort_keys=True))
