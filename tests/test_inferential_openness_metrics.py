import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"manuscript"/"inferential_openness"/"build_funnel_metrics_v2.py"
FLOW=ROOT/"manuscript"/"paper_ready"/"candidate_flow_table.csv"

def test_inferential_openness_funnel_reproduces_frozen_denominator(tmp_path):
    out=tmp_path/"metrics.json"
    subprocess.run([sys.executable,str(SCRIPT),"--candidate-flow",str(FLOW),"--output",str(out)],check=True,cwd=ROOT)
    p=json.loads(out.read_text())
    assert p["scientific_attempts"]==34
    assert p["scored_predictive_endpoints"]==3
    assert p["scientific_protocol_stops"]==31
    assert p["administrative_exclusions"]==3
    assert p["grouped_barriers"]=={
      "transport_or_source_identity":11,
      "registry_geometry_or_time":10,
      "separation_linkage_or_schema":8,
      "semantic_or_covariate_validity":2,
    }
    assert p["response_access_among_stops"]=={
      "none":29,"header_only":1,"full_response_once":1
    }
