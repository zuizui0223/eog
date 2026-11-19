#!/usr/bin/env python3
"""Source-coordinate diagnosis after a preregistered empirical km gate STOP.

Uses frozen Glanville archive hashes. Reads only patch-to-coordinate metadata,
not occupancy responses or relatedness. Reports aggregated CRS/scale diagnostics;
does not repair or rerun the failed ecological analysis.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import runpy
import statistics
import tempfile
import zipfile


def _pearson(a, b):
    if len(a) < 3 or len(a) != len(b):
        return None
    mx, my = statistics.mean(a), statistics.mean(b)
    x2 = sum((x-mx)**2 for x in a)
    y2 = sum((y-my)**2 for y in b)
    if x2 <= 0 or y2 <= 0:
        return None
    return sum((x-mx)*(y-my) for x,y in zip(a,b,strict=True))/math.sqrt(x2*y2)


def _q(vals, p):
    xs = sorted(vals)
    if not xs:
        return None
    k = (len(xs)-1)*p
    i,j=int(math.floor(k)),int(math.ceil(k))
    if i==j:
        return float(xs[i])
    return float(xs[i]*(j-k)+xs[j]*(k-i))


def _readme_clues(z):
    raw = z.read("README.rst").decode("utf-8", errors="replace")
    keys=("coordinate","epsg","etrs","projection","utm","crs","projected","spatial reference")
    return [line.strip()[:250] for line in raw.splitlines()
            if any(key in line.lower() for key in keys)][:25]


def diagnose(source_proto, diagnostic_proto, output):
    script = runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py")
    downloader, rows = script["_download"], script["_rows"]
    result={
        "schema_version":1,
        "status":"STOP_UNSTARTED",
        "source_sha256_expected":diagnostic_proto["source_shas"],
        "original_gate_stop_run_id":diagnostic_proto["parent_failed_run_id"],
        "ecological_response_rows_read":0,
        "source_founding_claims":0,
        "ecological_minrelax_results_scored":0,
        "EOG_WF_new_endpoints":0,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="glanville_crs_audit_") as tmp:
            folder=Path(tmp)
            o=source_proto["source_evidence"]["2019_occupancy_sha256"]
            g=source_proto["source_evidence"]["2017_family_sha256"]
            occ=downloader({
                "archive_url":"https://zenodo.org/records/4987060/files/ECOG-04799.zip?download=1",
                "filename":"ECOG-04799.zip","tag":"schulz2019_occupancy",
                "sha256":o,"max_bytes":5000000},folder)
            gen=downloader({
                "archive_url":"https://zenodo.org/records/5010194/files/supplementary-data-COLONY2.tar.gz?download=1",
                "filename":"supplementary-data-COLONY2.tar.gz","tag":"fountain2017_families",
                "sha256":g,"max_bytes":30000000},folder)
            network={}
            for r in rows(occ,"zip","data/patch_network.tsv","\t"):
                p=script["_str"](r.get("patch"))
                x=script["_number"](r.get("x"))
                y=script["_number"](r.get("y"))
                if p and x is not None and y is not None:
                    network[p]=(x,y)
            genetic=defaultdict(list)
            for r in rows(gen,"tar.gz","master-input.csv",","):
                p=script["_str"](r.get("Patch"))
                x=script["_number"](r.get("Patch Centroid_X (ETRS-TM35FIN)"))
                y=script["_number"](r.get("Patch Centroid_Y (ETRS-TM35FIN)"))
                if p and x is not None and y is not None:
                    genetic[p].append((x,y))
            points=[]
            for patch, values in genetic.items():
                if patch in network:
                    x,y=network[patch]
                    a=statistics.median(z[0] for z in values)
                    b=statistics.median(z[1] for z in values)
                    points.append((x,y,a,b))
            with zipfile.ZipFile(occ) as z:
                result["occupancy_readme_coordinate_mentions"]=_readme_clues(z)
            result["matched_patch_count"]=len(points)
            result["occupancy_spatial_patch_count"]=len(network)
            result["genetic_coordinate_patch_count"]=len(genetic)
            result["coordinate_axes"]={}
            for name, idx in (("2019_x",0),("2019_y",1),("2017_x",2),("2017_y",3)):
                vals=[p[idx] for p in points]
                result["coordinate_axes"][name]={
                    "min":min(vals) if vals else None,
                    "median":_q(vals,.5),
                    "max":max(vals) if vals else None,
                }
            if points:
                gx=[p[2] for p in points]; gy=[p[3] for p in points]
                xx=[p[0] for p in points]; yy=[p[1] for p in points]
                result["pearson"]={
                    "x2019_vs_x2017":_pearson(xx,gx),
                    "y2019_vs_y2017":_pearson(yy,gy),
                    "x2019_vs_y2017":_pearson(xx,gy),
                    "y2019_vs_x2017":_pearson(yy,gx),
                }
                dx=[p[2]-p[0] for p in points]
                dy=[p[3]-p[1] for p in points]
                mx,my=_q(dx,.5),_q(dy,.5)
                result["median_coordinate_offsets"]={"x":mx,"y":my}
                candidates={
                    "identity":lambda x,y:(x,y),
                    "swap_xy":lambda x,y:(y,x),
                    "scale_1000":lambda x,y:(1000*x,1000*y),
                    "scale_0.001":lambda x,y:(x/1000,y/1000),
                    "median_translation_diagnostic_only":lambda x,y:(x+mx,y+my),
                }
                result["representation_diagnostics"]={}
                for label,transform in candidates.items():
                    dist=[math.hypot(transform(x,y)[0]-a,transform(x,y)[1]-b)
                          for x,y,a,b in points]
                    result["representation_diagnostics"][label]={
                        "median_coordinate_difference":_q(dist,.5),
                        "p95_coordinate_difference":_q(dist,.95),
                        "max_coordinate_difference":max(dist),
                    }
            result["status"]="COORDINATE_DIAGNOSTIC_COMPLETED_NO_ECOLOGICAL_RESCORING"
    except (OSError,ValueError,KeyError,zipfile.BadZipFile,script["SourceStop"]) as exc:
        result["status"]=str(exc) if isinstance(exc,script["SourceStop"]) else "STOP_COORDINATE_DIAGNOSTIC_SOURCE_ERROR"
        result["error_type"]=type(exc).__name__
    output.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    result["fingerprint_without_self_hash"]=hashlib.sha256(raw.encode()).hexdigest()
    output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"matched_patches":result.get("matched_patch_count"),"result_file":str(output)},sort_keys=True))
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-protocol",type=Path,default=Path("validation/glanville_minrelax_empirical_v1/protocol_v1.json"))
    ap.add_argument("--diagnostic-protocol",type=Path,default=Path("validation/glanville_coordinate_diagnosis_v1/protocol_v1.json"))
    ap.add_argument("--output",type=Path,default=Path("results/glanville_coordinate_diagnosis_v1/receipt.json"))
    args=ap.parse_args()
    diagnose(json.loads(args.source_protocol.read_text()),
             json.loads(args.diagnostic_protocol.read_text()),args.output)


if __name__=="__main__":
    main()
