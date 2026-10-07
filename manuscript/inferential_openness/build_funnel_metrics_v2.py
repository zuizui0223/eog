#!/usr/bin/env python3
"""Recompute EOG inferential-openness funnel metrics from the frozen candidate table."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

GROUPS={
 "transport_or_source_identity":{
   "source_transport","bounded_archive_transport","metadata_identity_or_transport",
   "metadata_identity_or_interface","response_blind_archive_range_transport",
   "response_blind_zip_presign_transport","source_transport_dns"
 },
 "registry_geometry_or_time":{
   "publication_registry_reproduction","geometry_registry","temporal_registry",
   "response_independent_calendar_value","response_independent_geometry_registry",
   "temporal_context_estimability"
 },
 "separation_linkage_or_schema":{
   "physical_source_separation","response_linkage","response_header",
   "response_blind_zip_inventory","response_blind_physical_header_schema",
   "full_response_schema_or_linkage"
 },
 "semantic_or_covariate_validity":{
   "surveyed_negative_semantics","response_independent_baseline_covariate_value"
 },
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate-flow",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    x=pd.read_csv(a.candidate_flow)
    scientific=x[x.classification.isin(["predictive_result","scientific_protocol_stop"])].copy()
    stops=x[x.classification.eq("scientific_protocol_stop")].copy()
    admin=x[x.classification.eq("administrative_exclusion")].copy()

    grouped={}
    covered=set()
    for name,labels in GROUPS.items():
        sub=stops[stops.terminal_stage.isin(labels)]
        grouped[name]=int(len(sub))
        covered.update(sub.terminal_stage.astype(str))
    missing=sorted(set(stops.terminal_stage.astype(str))-covered)
    if missing:
        raise SystemExit(f"unmapped scientific STOP labels: {missing}")

    access=stops.biological_response_access.astype(str)
    none=int(access.eq("none").sum())
    header=int(access.eq("header_only").sum())
    full=int(access.eq("full_response_once").sum())

    out={
      "scientific_attempts":int(len(scientific)),
      "scored_predictive_endpoints":int(scientific.classification.eq("predictive_result").sum()),
      "scientific_protocol_stops":int(len(stops)),
      "administrative_exclusions":int(len(admin)),
      "grouped_barriers":grouped,
      "response_access_among_stops":{"none":none,"header_only":header,"full_response_once":full},
      "stops_before_response_row_value_contributed_to_scored_endpoint":none+header,
      "representative_sample_of_ecological_datasets":False
    }
    assert out["scientific_attempts"]==34
    assert out["scored_predictive_endpoints"]==3
    assert out["scientific_protocol_stops"]==31
    assert out["administrative_exclusions"]==3
    assert sum(grouped.values())==31
    assert grouped=={
      "transport_or_source_identity":11,
      "registry_geometry_or_time":10,
      "separation_linkage_or_schema":8,
      "semantic_or_covariate_validity":2,
    }
    assert (none,header,full)==(29,1,1)
    assert none+header==30

    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
