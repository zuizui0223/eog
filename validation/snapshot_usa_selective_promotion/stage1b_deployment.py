from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1b_deployment_contract.json"
OUTPUT = ROOT / "build/snapshot_usa_selective_promotion/stage1b_deployment.json"


def _fp(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _parse_iso(value: str) -> date:
    return date.fromisoformat(value.strip())


def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.snapshot_usa_selective_promotion.stage1b_deployment.v1",
        "attempt_id": c["attempt_id"],
        "deployment_payload_requests": 0,
        "sequence_payload_requests": 0,
        "sequence_header_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(c["authorized_deployment_url"], headers={"User-Agent": "eog-response-blind-stage1b/1.0"})
        with urlopen(req, timeout=60) as response:  # noqa: S310 exact frozen deployment URL
            raw = response.read()
            status = int(getattr(response, "status", 200))
            final_url = response.geturl()
        base["deployment_payload_requests"] = 1
        if status != 200:
            raise RuntimeError(f"deployment HTTP status {status}")
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames != c["required_header"]:
            raise RuntimeError(f"deployment header drift: {reader.fieldnames}")
        rows = []
        allowed_years = set(int(x) for x in c["allowed_years"])
        ids = set()
        for line_no, row in enumerate(reader, start=2):
            try:
                year = int(row["Year"])
                if year not in allowed_years:
                    raise ValueError("year")
                array = row["Camera_Trap_Array"].strip()
                site = row["Site_Name"].strip()
                dep = row["Deployment_ID"].strip()
                if not array or not site or not dep or dep in ids:
                    raise ValueError("identity")
                ids.add(dep)
                nights = float(row["Survey_Nights"])
                lat = float(row["Latitude"])
                lon = float(row["Longitude"])
                if not math.isfinite(nights) or nights <= 0:
                    raise ValueError("survey nights")
                if not math.isfinite(lat) or not -90 <= lat <= 90:
                    raise ValueError("latitude")
                if not math.isfinite(lon) or not -180 <= lon <= 180:
                    raise ValueError("longitude")
                start = _parse_iso(row["Start_Date"])
                end = _parse_iso(row["End_Date"])
                if end < start:
                    raise ValueError("date order")
            except Exception as exc:
                raise RuntimeError(f"invalid deployment row {line_no}: {exc}") from exc
            rows.append({
                "year": year, "array": array, "site": site, "deployment_id": dep,
                "start_date": start.isoformat(), "end_date": end.isoformat(),
                "survey_nights": nights, "latitude": lat, "longitude": lon,
                "habitat": row["Habitat"].strip(), "development_level": row["Development_Level"].strip(),
                "feature_type": row["Feature_Type"].strip(), "project": row["Project"].strip(),
            })
        if not rows:
            raise RuntimeError("deployment file has zero rows")
        by_array_year: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for row in rows:
            by_array_year[row["array"]][row["year"]].append(row)
        ranked = []
        years = sorted(allowed_years)
        for array, year_rows in by_array_year.items():
            if set(year_rows) != allowed_years:
                continue
            annual_sites = {year: len({r["site"] for r in year_rows[year]}) for year in years}
            if min(annual_sites.values()) < 7:
                continue
            total_nights = sum(r["survey_nights"] for year in years for r in year_rows[year])
            ranked.append((min(annual_sites.values()), total_nights, array, annual_sites))
        if not ranked:
            raise RuntimeError("no focal array satisfies frozen five-year >=7-sites rule")
        ranked.sort(key=lambda x: (-x[0], -x[1], x[2]))
        best = ranked[0]
        selected_array = best[2]
        selected_rows = [r for r in rows if r["array"] == selected_array]
        annual_summary = {}
        for year in years:
            yr = [r for r in selected_rows if r["year"] == year]
            annual_summary[str(year)] = {
                "distinct_sites": len({r["site"] for r in yr}),
                "deployment_rows": len(yr),
                "survey_nights": sum(r["survey_nights"] for r in yr),
                "start_min": min(r["start_date"] for r in yr),
                "end_max": max(r["end_date"] for r in yr),
            }
        result = {
            **base,
            "status": "stage1b_deployment_qualified_and_focal_array_selected",
            "deployment_final_url": final_url,
            "deployment_bytes_opened": len(raw),
            "deployment_md5": hashlib.md5(raw).hexdigest(),  # noqa: S324 provenance only
            "deployment_sha256": hashlib.sha256(raw).hexdigest(),
            "deployment_row_count": len(rows),
            "eligible_array_count": len(ranked),
            "selected_array": selected_array,
            "selected_array_rank_key": {
                "minimum_annual_distinct_sites": best[0],
                "total_survey_nights": best[1],
            },
            "selected_array_annual_summary": annual_summary,
            "selected_array_rows": selected_rows,
            "selected_array_rows_fingerprint": _fp(selected_rows),
            "next_gate": "freeze selected array geometry/time grid/world universe/target species/header-only response contract before sequence bytes",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_deployment_transport_schema_or_structure",
            "reason": str(exc),
            "next_gate": "none; no deployment or selection repair within this attempt",
        }
    result["fingerprint"] = _fp(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    printable = {k: v for k, v in result.items() if k != "selected_array_rows"}
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
