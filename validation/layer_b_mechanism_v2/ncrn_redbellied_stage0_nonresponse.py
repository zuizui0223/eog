#!/usr/bin/env python3
"""Response-blind Stage0 for NCRN Red-bellied Woodpecker.

Only NPS metadata XML, forest points and forest visits may be requested.
The forest counts response, analysis-ready flattened table and fielddata are never
requested here. The goal is to qualify source transport, exact nonresponse schema,
station geometry and temporal survey opportunity before any biological response byte.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "build" / "layer_b_mechanism_v2" / "ncrn_redbellied_stage0"
OUTPUT = OUTDIR / "stage0_nonresponse.json"
REFERENCE = 2317363
BASE = "https://irma.nps.gov/DataStore/DownloadFile/{file_id}?Reference=2317363"
AMENDMENT = "validation/layer_b_mechanism_v2/ncrn_pre_response_audit_corrections_v1.json"
ALLOWED = {
    "metadata": (756926, "ncrn_birds_cumulative_through2025_metadata.xml"),
    "points": (757401, "ncrn_birds_forest_points.csv"),
    "visits": (757403, "ncrn_birds_forest_visits.csv"),
}
FORBIDDEN = {
    "response_counts": (757399, "ncrn_birds_forest_counts.csv"),
    "flattened_response": (757402, "ncrn_birds_forest_R1_BirdDataStandard.csv"),
    "fielddata": (757400, "ncrn_birds_forest_fielddata.csv"),
}
FROZEN_YEARS = set(range(2007, 2020))


def _get(url: str) -> tuple[bytes, str, str | None, str | None]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "eog-qualification-v2-response-blind/2",
            "Accept": "text/csv,application/xml,text/xml,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return data, r.geturl(), r.headers.get("ETag"), r.headers.get("Last-Modified")


def _decode(data: bytes, label: str) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    raise RuntimeError(f"{label} is not decodable as expected public text")


def _csv(data: bytes, label: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(_decode(data, label)))
    if reader.fieldnames is None:
        raise RuntimeError(f"{label} has no CSV header")
    return [str(x) for x in reader.fieldnames], list(reader)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(node: ET.Element, name: str) -> str | None:
    for child in list(node):
        if _local(child.tag) == name:
            text = "".join(child.itertext()).strip()
            return text or None
    return None


def _eml_tables(xml_bytes: bytes) -> dict[str, dict]:
    root = ET.fromstring(xml_bytes)
    tables: dict[str, dict] = {}
    for node in root.iter():
        if _local(node.tag) != "dataTable":
            continue
        entity = _child_text(node, "entityName") or _child_text(node, "entityDescription")
        object_name = None
        for descendant in node.iter():
            if _local(descendant.tag) == "objectName":
                object_name = "".join(descendant.itertext()).strip() or None
                if object_name:
                    break
        key = object_name or entity or f"table_{len(tables)+1}"
        attrs = []
        for attr in node.iter():
            if _local(attr.tag) != "attribute":
                continue
            name = _child_text(attr, "attributeName")
            definition = _child_text(attr, "attributeDefinition")
            storage = _child_text(attr, "storageType")
            if name:
                attrs.append({"name": name, "definition": definition, "storage_type": storage})
        tables[str(key)] = {
            "entity_name": entity,
            "object_name": object_name,
            "attributes": attrs,
        }
    return tables


def _find_table(tables: dict[str, dict], filename: str) -> dict | None:
    target = filename.lower()
    for key, table in tables.items():
        fields = [key, table.get("entity_name"), table.get("object_name")]
        if any(target in str(x or "").lower() for x in fields):
            return table
    return None


def _numeric_column(rows: list[dict[str, str]], column: str) -> list[float]:
    out = []
    for row in rows:
        raw = str(row.get(column, "")).strip()
        if not raw or raw.lower() in {"na", "n/a", "nan", "null", "none"}:
            continue
        try:
            x = float(raw)
        except ValueError:
            continue
        if math.isfinite(x):
            out.append(x)
    return out


def _lat_lon_columns(header: list[str], rows: list[dict[str, str]]) -> tuple[str, str]:
    lat_candidates = [h for h in header if "lat" in h.lower()]
    lon_candidates = [h for h in header if "lon" in h.lower() or "lng" in h.lower()]
    for lat in lat_candidates:
        latvals = _numeric_column(rows, lat)
        if not latvals or not all(-90 <= x <= 90 for x in latvals):
            continue
        for lon in lon_candidates:
            lonvals = _numeric_column(rows, lon)
            if lonvals and all(-180 <= x <= 180 for x in lonvals):
                return lat, lon
    raise RuntimeError(f"could not identify public latitude/longitude columns from header {header}")


def _site_key(points_header: list[str], visits_header: list[str], points_rows: list[dict[str, str]], visits_rows: list[dict[str, str]]) -> str:
    common = [h for h in points_header if h in visits_header]
    preferred = [h for h in common if any(token in h.lower() for token in ("site", "point", "location", "plot"))]
    for h in preferred + common:
        p = {str(r.get(h, "")).strip() for r in points_rows if str(r.get(h, "")).strip()}
        v = {str(r.get(h, "")).strip() for r in visits_rows if str(r.get(h, "")).strip()}
        if len(p) >= 50 and len(p & v) >= 50:
            return h
    raise RuntimeError("no response-independent site key joins >=50 forest points to visits")


def _parse_event_year(raw: str) -> int | None:
    raw = str(raw).strip()
    if not raw:
        return None
    m = re.search(r"\b(20\d{2}|19\d{2})\b", raw)
    if m:
        return int(m.group(1))
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).year
        except ValueError:
            pass
    return None


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "eog.layer_b_mechanism_v2.ncrn_redbellied_stage0_nonresponse.v2",
        "pre_response_correction_amendment": AMENDMENT,
        "candidate": "ncrn_red_bellied_woodpecker_2007_2019",
        "nps_reference": REFERENCE,
        "response_payload_requests": 0,
        "response_header_bytes_opened": 0,
        "response_bytes_opened": 0,
        "response_values_opened": False,
        "flattened_response_requests": 0,
        "fielddata_requests": 0,
        "model_fits": 0,
        "inner_selection_decisions": 0,
        "heldout_scores": 0,
        "response_open_authorized": False,
        "forbidden_resources": {
            name: {"file_id": fid, "filename": filename, "requested": False}
            for name, (fid, filename) in FORBIDDEN.items()
        },
        "allowed_resources": {},
    }
    try:
        payloads = {}
        for role, (fid, filename) in ALLOWED.items():
            url = BASE.format(file_id=fid)
            data, final_url, etag, last_modified = _get(url)
            if not data:
                raise RuntimeError(f"empty allowed resource: {filename}")
            payloads[role] = data
            result["allowed_resources"][role] = {
                "file_id": fid,
                "filename": filename,
                "requested": True,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "final_url": final_url,
                "etag": etag,
                "last_modified": last_modified,
            }

        tables = _eml_tables(payloads["metadata"])
        response_table = _find_table(tables, FORBIDDEN["response_counts"][1])
        visits_table = _find_table(tables, ALLOWED["visits"][1])
        points_table = _find_table(tables, ALLOWED["points"][1])
        if response_table is None:
            raise RuntimeError("EML metadata does not expose an exact forest-counts data-table entity")
        if visits_table is None or points_table is None:
            raise RuntimeError("EML metadata does not expose exact forest points/visits data-table entities")
        response_attrs = response_table.get("attributes", [])
        if len(response_attrs) < 3:
            raise RuntimeError("forest counts metadata exposes too few attributes to freeze response schema")
        result["metadata_dictionary"] = {
            "table_names": sorted(tables),
            "response_table": response_table,
            "visits_table": visits_table,
            "points_table": points_table,
        }

        points_header, points_rows = _csv(payloads["points"], ALLOWED["points"][1])
        visits_header, visits_rows = _csv(payloads["visits"], ALLOWED["visits"][1])
        lat_col, lon_col = _lat_lon_columns(points_header, points_rows)
        site_key = _site_key(points_header, visits_header, points_rows, visits_rows)
        coords = set()
        point_ids = set()
        for row in points_rows:
            sid = str(row.get(site_key, "")).strip()
            if not sid:
                continue
            lat_raw, lon_raw = str(row.get(lat_col, "")).strip(), str(row.get(lon_col, "")).strip()
            try:
                lat, lon = float(lat_raw), float(lon_raw)
            except ValueError:
                continue
            if math.isfinite(lat) and math.isfinite(lon):
                point_ids.add(sid)
                coords.add((lat, lon))
        if len(point_ids) < 50 or len(coords) < 50:
            raise RuntimeError(f"forest points yield only {len(point_ids)} site IDs / {len(coords)} unique coordinates")

        if "EventDate" not in visits_header:
            raise RuntimeError("forest visits lacks frozen survey-year source EventDate")
        survey_years = set()
        counts_by_year = Counter()
        visit_site_ids = set()
        for row in visits_rows:
            sid = str(row.get(site_key, "")).strip()
            if sid:
                visit_site_ids.add(sid)
            year = _parse_event_year(row.get("EventDate", ""))
            if year is not None:
                survey_years.add(year)
                if sid in point_ids:
                    counts_by_year[year] += 1
        missing_years = sorted(FROZEN_YEARS - survey_years)
        if missing_years:
            raise RuntimeError(f"forest visits do not cover frozen years: {missing_years}")
        joined_sites = point_ids & visit_site_ids
        if len(joined_sites) < 50:
            raise RuntimeError(f"only {len(joined_sites)} point IDs are represented in forest visits")

        export_years = sorted({y for y in (_parse_event_year(r.get("ExportDate", "")) for r in visits_rows) if y is not None}) if "ExportDate" in visits_header else []

        result["points"] = {
            "exact_header": points_header,
            "row_count": len(points_rows),
            "site_key": site_key,
            "latitude_column": lat_col,
            "longitude_column": lon_col,
            "unique_site_ids": len(point_ids),
            "unique_coordinate_pairs": len(coords),
        }
        result["visits"] = {
            "exact_header": visits_header,
            "row_count": len(visits_rows),
            "site_key": site_key,
            "survey_year_source_column": "EventDate",
            "survey_years": sorted(survey_years),
            "export_years_provenance_only": export_years,
            "joined_unique_site_ids": len(joined_sites),
            "visit_rows_by_survey_year": {str(y): counts_by_year[y] for y in sorted(counts_by_year)},
        }
        result["status"] = "stage0_nonresponse_qualified_pending_exact_response_algebra_contract"
        result["source_identity_gate"] = "pass_fixed_reference_and_resource_ids_with_live_transport"
        result["geometry_and_effort_gate"] = "pass_points_and_visits_response_independent"
        result["target_estimability_gate"] = "prequalified_independent_publication_bounds_pending_contract_sync"
        result["response_semantics_gate"] = "metadata_dictionary_recovered_pending_explicit_algebra_and_missing_semantics_freeze"
        result["next_gate"] = "freeze_exact_response_algebra_join_missing_semantics_and_full_execution_contract_from_stage0_receipt"
        rc = 0
    except Exception as exc:
        result["status"] = "terminal_pre_response_ncrn_stage0_stop"
        result["error"] = f"{type(exc).__name__}: {exc}"
        rc = 2

    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
