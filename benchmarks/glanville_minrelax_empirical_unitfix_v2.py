#!/usr/bin/env python3
"""Glanville exploratory EOG minimum relaxation with documented km->m correction.

Corrects ONLY Schulz2019 patch_network x/y units using the original README
and source-only coordinate diagnostic. Inherits v1 source, biological estimand,
years, source policies and host gap thresholds without outcome retuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import tempfile


def run_unit_corrected(parent_contract: dict, repair_contract: dict, output: Path) -> dict:
    core=runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py")
    result={
        "schema_version":2,
        "status":"STOP_UNSTARTED",
        "scientific_provenance":{
            "parent_stop_run":repair_contract["parent_scientific_stop_run"],
            "diagnostic_run":repair_contract["source_only_diagnostic_run"],
            "readme_unit":"2019 EPSG3067 coordinates in kilometers",
            "corrected_unit":"meters",
            "only_change":"multiply both 2019 patch-network centroid coordinates by 1000",
        },
        "source_shas":parent_contract["source_evidence"],
        "models_fit":0,
        "EOG_WF_new_endpoints":0,
        "exploratory_not_confirmatory":True,
    }
    try:
        if repair_contract["status"] != "frozen_source_unit_repair_before_first_ecological_score":
            raise core["SourceStop"]("STOP_REPAIR_PROTOCOL_NOT_FROZEN")
        if repair_contract["only_authorized_change"]["multiply_by"] != 1000.0:
            raise core["SourceStop"]("STOP_UNAPPROVED_GEOGRAPHIC_UNIT_CONVERSION")
        if not repair_contract["only_authorized_change"]["no_analytical_threshold_changes"]:
            raise core["SourceStop"]("STOP_UNAPPROVED_SCIENTIFIC_REDEFINITION")
        with tempfile.TemporaryDirectory(prefix="eog_glanville_unit_repair_v2_") as dirname:
            tmp=Path(dirname)
            original=core["_download"]({
                "archive_url":"https://zenodo.org/records/4987060/files/ECOG-04799.zip?download=1",
                "filename":"ECOG-04799.zip",
                "tag":"schulz2019_occupancy",
                "sha256":parent_contract["source_evidence"]["2019_occupancy_sha256"],
                "max_bytes":5000000},tmp)
            family_source=core["_download"]({
                "archive_url":"https://zenodo.org/records/5010194/files/supplementary-data-COLONY2.tar.gz?download=1",
                "filename":"supplementary-data-COLONY2.tar.gz",
                "tag":"fountain2017_families",
                "sha256":parent_contract["source_evidence"]["2017_family_sha256"],
                "max_bytes":30000000},tmp)
            network, survey, genotype, gene_coord, families, n_survey=core["_load_tables"](
                original,family_source)
            factor=repair_contract["only_authorized_change"]["multiply_by"]
            network_m={k:(v[0]*factor,v[1]*factor) for k,v in network.items()}
            result["source_record_counts"]={
                "survey":n_survey,
                "spatial_patches":len(network_m),
                "genotype_individual_years":len(genotype),
                "family_individual_years":len(families)
            }
            result["coordinate_family_join_qc"]=core["_check_geographic_contract"](
                network_m,gene_coord,genotype,families,parent_contract
            )
            years=tuple(parent_contract["years"])
            result["reconstructed_family_spatial_summary"]=core["_family_summary"](
                network_m,genotype,families,years
            )
            delta_values=tuple(parent_contract["environmental_threshold_grid"])
            policies=(parent_contract["primary_source_policy"],
                      parent_contract["sensitivity_source_policy"])
            panels=[
                core["_radius_for_year"](year,policy,network_m,survey,delta_values)
                for year in years for policy in policies
            ]
            if len(panels)!=len(years)*2:
                raise core["SourceStop"]("STOP_PANEL_COUNT_CHANGED")
            by_year={(r["year"],r["source_policy"]):r for r in panels}
            for year in years:
                one=by_year[(year,policies[0])]
                two=by_year[(year,policies[1])]
                if one["eligible_newly_recorded_positive_targets"] != two["eligible_newly_recorded_positive_targets"]:
                    raise core["SourceStop"]("STOP_TARGET_ROSTER_CHANGED_BY_SOURCE_POLICY")
                for a,b in zip(one["conditional_radius_by_host_tolerance"],
                               two["conditional_radius_by_host_tolerance"],strict=True):
                    x,y=a["max_of_nearest_compatible_source_km"],b["max_of_nearest_compatible_source_km"]
                    if x is not None and (y is None or y > x + 1e-10):
                        raise core["SourceStop"]("STOP_SOURCE_SET_MONOTONICITY_FAILURE")
            result["annual_minimum_relaxation"]=panels
            result["barrier_axis"]="NOT_IDENTIFIABLE_FROM_THIS_SOURCE"
            result["true_colonization_or_founder_status"]="NOT_IDENTIFIED"
            result["status"]="EXPLORATORY_CONDITIONAL_EMPIRICAL_RELAXATION_ESTIMATED"
    except (core["SourceStop"], ValueError, KeyError) as exc:
        result["status"]=str(exc) if isinstance(exc,core["SourceStop"]) else "STOP_SCHEMA_OR_ANALYSIS"
        result["error_type"]=type(exc).__name__
    output.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    result["fingerprint_without_self_hash"]=hashlib.sha256(raw.encode()).hexdigest()
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "year_policy_panels":len(result.get("annual_minimum_relaxation",[])),
        "output":str(output),
    },sort_keys=True))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--parent-protocol",type=Path,default=Path("validation/glanville_minrelax_empirical_v1/protocol_v1.json"))
    parser.add_argument("--unit-protocol",type=Path,default=Path("validation/glanville_minrelax_empirical_unitfix_v2/protocol_v2.json"))
    parser.add_argument("--output",type=Path,default=Path("results/glanville_minrelax_empirical_unitfix_v2/result.json"))
    args=parser.parse_args()
    parent=json.loads(args.parent_protocol.read_text(encoding="utf-8"))
    repair=json.loads(args.unit_protocol.read_text(encoding="utf-8"))
    run_unit_corrected(parent,repair,args.output)


if __name__=="__main__":
    main()
