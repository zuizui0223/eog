#!/usr/bin/env python3
"""Build manuscript tables for the inferential-openness audit from the frozen EOG ledger."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

FAMILIES={
  "transport_interface_identity":{
    "source_transport","bounded_archive_transport","metadata_identity_or_transport",
    "metadata_identity_or_interface","source_transport_dns",
    "response_blind_archive_range_transport","response_blind_zip_presign_transport",
  },
  "registry_geometry_temporal_frame":{
    "publication_registry_reproduction","geometry_registry","response_independent_geometry_registry",
    "temporal_registry","temporal_context_estimability",
  },
  "linkage_separation_semantics":{
    "response_linkage","physical_source_separation","surveyed_negative_semantics",
    "response_independent_baseline_covariate_value","response_independent_calendar_value",
  },
  "physical_schema_boundary":{
    "response_header","response_blind_physical_header_schema",
    "response_blind_zip_inventory","full_response_schema_or_linkage",
  },
}

def family(stage:str)->str:
    hits=[name for name,stages in FAMILIES.items() if stage in stages]
    if len(hits)!=1:
        raise ValueError(f"terminal stage must map to exactly one barrier family: {stage}: {hits}")
    return hits[0]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ledger",type=Path,default=Path("validation/paper_ready_replication/candidate_flow_ledger.json"))
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    data=json.loads(a.ledger.read_text())
    stops=pd.DataFrame(data["fresh_candidate_stops"])
    scored=pd.DataFrame(data["fresh_predictive_results"])

    stops["barrier_family"]=stops["terminal_stage"].map(family)
    stops["response_row_opened"]=stops["biological_response_access"].eq("full_response_once")
    stops["response_access_level"]=stops["biological_response_access"]

    supp=stops[[
      "issue","system","ecosystem_or_context","terminal_stage","barrier_family",
      "reason","biological_response_access","counts_as_predictive_evidence"
    ]].sort_values("issue")
    family_table=(stops.groupby("barrier_family",as_index=False)
                  .agg(stops=("issue","size"),
                       no_response_access=("biological_response_access",lambda x:int((x=="none").sum())),
                       header_only=("biological_response_access",lambda x:int((x=="header_only").sum())),
                       full_response_once=("biological_response_access",lambda x:int((x=="full_response_once").sum())))
                  .sort_values("stops",ascending=False))

    flow=pd.DataFrame([
      {"class":"scored_predictive_endpoint","count":len(scored)},
      {"class":"protocol_stop","count":len(stops)},
      {"class":"administrative_exclusion","count":len(data["administrative_exclusions"])},
    ])
    summary={
      "scientific_candidates":int(len(scored)+len(stops)),
      "scored_predictive_endpoints":int(len(scored)),
      "protocol_stops":int(len(stops)),
      "administrative_exclusions":int(len(data["administrative_exclusions"])),
      "stops_without_response_access":int(stops.biological_response_access.eq("none").sum()),
      "stops_before_any_response_row":int(~stops.biological_response_access.eq("full_response_once").sum()) if False else int((stops.biological_response_access!="full_response_once").sum()),
      "barrier_family_counts":dict(zip(family_table.barrier_family,family_table.stops)),
    }
    if summary["scientific_candidates"]!=34 or summary["protocol_stops"]!=31:
        raise RuntimeError("frozen inferential-openness denominator changed")
    if sum(summary["barrier_family_counts"].values())!=31:
        raise RuntimeError("barrier-family partition does not cover all STOPs")

    a.output_dir.mkdir(parents=True,exist_ok=True)
    supp.to_csv(a.output_dir/"table_s1_protocol_stops.csv",index=False)
    family_table.to_csv(a.output_dir/"table_1_barrier_families.csv",index=False)
    flow.to_csv(a.output_dir/"table_2_candidate_flow.csv",index=False)
    (a.output_dir/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
