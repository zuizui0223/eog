from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from statistics import median
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1_nonresponse_contract.json"
OUTPUT = ROOT / "build/neon_camera_selective_promotion/stage1_nonresponse.json"
URLS = {
    "camera_trap_deployments.csv": "https://zenodo.org/api/records/20826511/files/camera_trap_deployments.csv/content",
    "subproject_descriptions.csv": "https://zenodo.org/api/records/20826511/files/subproject_descriptions.csv/content",
}


def _get(name: str) -> bytes:
    req = Request(URLS[name], headers={"User-Agent": "eog-response-blind-neon-stage1/1.0"})
    with urlopen(req, timeout=60) as r:  # noqa: S310
        raw = r.read()
    return raw


def _parse_csv(raw: bytes):
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def _find(cols, candidates):
    low = {c.lower(): c for c in cols}
    for k in candidates:
        if k.lower() in low:
            return low[k.lower()]
    for c in cols:
        lc = c.lower()
        if any(k.lower() in lc for k in candidates):
            return c
    return None


def _parse_dt(value: str):
    if not value:
        return None
    v = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(v)
    except Exception:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except Exception:
                pass
    return None


def main() -> int:
    contract = json.loads(CONTRACT.read_text())
    base = {
        "schema": "eog.neon_camera_selective_promotion.stage1_nonresponse.v1",
        "attempt_id": contract["attempt_id"],
        "response_file_requests": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        parsed = {}
        for name, spec in contract["authorized_payloads"].items():
            raw = _get(name)
            if len(raw) != spec["exact_size"]:
                raise RuntimeError(f"size drift for {name}: {len(raw)}")
            md5 = hashlib.md5(raw).hexdigest()  # noqa: S324 - provenance checksum only
            if md5 != spec["md5"]:
                raise RuntimeError(f"checksum drift for {name}: {md5}")
            cols, rows = _parse_csv(raw)
            parsed[name] = {"columns": cols, "rows": rows, "bytes": len(raw), "md5": md5}

        dep = parsed["camera_trap_deployments.csv"]
        sub = parsed["subproject_descriptions.csv"]
        cols = dep["columns"]

        suspicious = [c for c in cols if any(k in c.lower() for k in ("species", "taxon", "detection", "scientificname", "commonname", "sequence"))]
        if suspicious:
            raise RuntimeError(f"deployment table contains biological-response-like columns: {suspicious}")

        id_col = _find(cols, ["deploymentID", "deployment_id", "deployment"])
        lat_col = _find(cols, ["latitude", "lat"])
        lon_col = _find(cols, ["longitude", "lon", "lng"])
        start_col = _find(cols, ["deploymentStart", "start", "startDate"])
        end_col = _find(cols, ["deploymentEnd", "end", "endDate"])
        sub_col = _find(cols, ["subproject", "project"])

        starts = [_parse_dt(r.get(start_col, "")) for r in dep["rows"]] if start_col else []
        ends = [_parse_dt(r.get(end_col, "")) for r in dep["rows"]] if end_col else []
        starts = [x for x in starts if x]
        ends = [x for x in ends if x]
        durations = []
        if start_col and end_col:
            for r in dep["rows"]:
                a, b = _parse_dt(r.get(start_col, "")), _parse_dt(r.get(end_col, ""))
                if a and b:
                    durations.append((b - a).total_seconds() / 86400)

        coords = []
        if lat_col and lon_col:
            for r in dep["rows"]:
                try:
                    coords.append((round(float(r[lat_col]), 6), round(float(r[lon_col]), 6)))
                except Exception:
                    pass

        result = {
            **base,
            "status": "stage1_nonresponse_ready_for_target_and_split_freeze",
            "opened_nonresponse_files": {
                name: {"bytes": v["bytes"], "md5": v["md5"], "columns": v["columns"], "row_count": len(v["rows"])}
                for name, v in parsed.items()
            },
            "deployment_schema": {
                "deployment_id_column": id_col,
                "latitude_column": lat_col,
                "longitude_column": lon_col,
                "start_column": start_col,
                "end_column": end_col,
                "subproject_column": sub_col,
                "biological_response_like_columns": suspicious,
            },
            "deployment_summary": {
                "row_count": len(dep["rows"]),
                "unique_deployment_ids": len({r.get(id_col) for r in dep["rows"] if id_col and r.get(id_col)}),
                "coordinate_complete_rows": len(coords),
                "unique_coordinate_nodes": len(set(coords)),
                "date_min": min(starts).isoformat() if starts else None,
                "date_max": max(ends).isoformat() if ends else None,
                "duration_days_min": min(durations) if durations else None,
                "duration_days_median": median(durations) if durations else None,
                "duration_days_max": max(durations) if durations else None,
                "unique_subprojects": len({r.get(sub_col) for r in dep["rows"] if sub_col and r.get(sub_col)}),
            },
            "subproject_row_count": len(sub["rows"]),
            "next_gate": "Freeze target taxon independently of response values, then freeze temporal inner/outer split and model/selector contracts before opening camera_trap_sequences.csv.",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_nonresponse_schema_or_transport",
            "reason": str(exc),
            "next_gate": "none; no repair within this attempt after live Stage1",
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
