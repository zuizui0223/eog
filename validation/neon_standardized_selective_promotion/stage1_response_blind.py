from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "stage1_response_blind_contract.json"
OUTPUT = Path("build/neon_standardized_selective_promotion/stage1_response_blind.json")
BASE = "https://zenodo.org/api/records/20826511/files/{name}/content"


def get_file(name: str, expected_md5: str, expected_size: int) -> bytes:
    req = Request(BASE.format(name=name), headers={"User-Agent": "eog-fresh-stage1/1"})
    with urlopen(req, timeout=30) as r:
        raw = r.read()
    if len(raw) != expected_size:
        raise RuntimeError(f"size mismatch for {name}: {len(raw)}")
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != expected_md5:
        raise RuntimeError(f"md5 mismatch for {name}: {md5}")
    return raw


def parse_csv(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader.fieldnames or []), list(reader)


def numeric_extent(rows, columns, needles):
    out = {}
    for c in columns:
        lc = c.lower()
        if not any(n in lc for n in needles):
            continue
        vals=[]
        for r in rows:
            try:
                vals.append(float(r.get(c, "")))
            except (TypeError, ValueError):
                pass
        if vals:
            out[c] = {"min": min(vals), "max": max(vals), "n_numeric": len(vals)}
    return out


def unique_counts(rows, columns):
    out={}
    for c in columns:
        lc=c.lower()
        if any(x in lc for x in ("deployment", "location", "site", "subproject", "project")) and not any(x in lc for x in ("latitude", "longitude")):
            out[c] = len({r.get(c, "") for r in rows if r.get(c, "") != ""})
    return out


def temporal_extent(rows, columns):
    out={}
    for c in columns:
        lc=c.lower()
        if not any(x in lc for x in ("start", "end", "date", "time")):
            continue
        vals=[r.get(c, "") for r in rows if r.get(c, "")]
        if vals:
            out[c]={"min_lexical": min(vals), "max_lexical": max(vals), "n_nonempty": len(vals)}
    return out


def run() -> dict:
    c=json.loads(CONTRACT.read_text())
    base={
        "schema":"eog.neon_standardized_selective_promotion.stage1_response_blind.v1",
        "attempt_id":c["attempt_id"],
        "authorized_payload_requests":0,
        "authorized_payload_bytes_opened":0,
        "response_payload_requests":0,
        "response_payload_bytes_opened":0,
        "biological_response_values_opened":False,
        "model_fits":0,
        "heldout_scores":0,
        "counts_as_predictive_evidence":False,
    }
    try:
        summaries={}
        for name, spec in c["authorized_payloads"].items():
            raw=get_file(name, spec["md5"], spec["size"])
            base["authorized_payload_requests"] += 1
            base["authorized_payload_bytes_opened"] += len(raw)
            cols, rows=parse_csv(raw)
            summaries[name]={
                "columns":cols,
                "row_count":len(rows),
                "unique_identifier_counts":unique_counts(rows, cols),
                "coordinate_extents":numeric_extent(rows, cols, ("lat", "lon", "long")),
                "temporal_extents":temporal_extent(rows, cols),
            }
        result={**base,"status":"stage1_response_blind_ready_for_endpoint_freeze","summaries":summaries,"next_gate":c["next_if_ready"]}
    except Exception as exc:
        result={**base,"status":"stop_pre_response_stage1_transport_schema_or_geometry","reason":str(exc),"next_gate":"none; no repair within this attempt"}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return result

if __name__ == "__main__":
    run()
