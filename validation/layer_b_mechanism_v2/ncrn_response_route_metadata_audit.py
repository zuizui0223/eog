#!/usr/bin/env python3
"""Metadata-only NCRN response-route audit.

This audit requests only the already qualified EML metadata resource and compares
published schemas for three response-bearing files. It never requests any response
CSV bytes. The purpose is to choose and freeze a joinable response route before
biological response access.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "build" / "layer_b_mechanism_v2" / "ncrn_response_route_metadata_audit"
OUTPUT = OUTDIR / "route_audit.json"
METADATA_URL = "https://irma.nps.gov/DataStore/DownloadFile/756926?Reference=2317363"
EXPECTED_METADATA_SHA256 = "a6c2d29be41332e9b1a35bc2a4252ca4a43148e38579f2b79959d4b6709fcef3"
AMENDMENT = "validation/layer_b_mechanism_v2/ncrn_pre_response_audit_corrections_v1.json"
ROUTES = {
    "counts": {
        "filename": "ncrn_birds_forest_counts.csv",
        "file_id": 757399,
    },
    "fielddata": {
        "filename": "ncrn_birds_forest_fielddata.csv",
        "file_id": 757400,
    },
    "R1": {
        "filename": "ncrn_birds_forest_R1_BirdDataStandard.csv",
        "file_id": 757402,
    },
}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "eog-response-route-metadata-audit/2"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(node: ET.Element, name: str) -> str | None:
    for child in list(node):
        if _local(child.tag) == name:
            value = "".join(child.itertext()).strip()
            return value or None
    return None


def _tables(data: bytes) -> dict[str, dict]:
    root = ET.fromstring(data)
    out = {}
    for node in root.iter():
        if _local(node.tag) != "dataTable":
            continue
        entity = _child_text(node, "entityName")
        object_name = None
        for d in node.iter():
            if _local(d.tag) == "objectName":
                object_name = "".join(d.itertext()).strip() or None
                if object_name:
                    break
        attrs = []
        for a in node.iter():
            if _local(a.tag) != "attribute":
                continue
            name = _child_text(a, "attributeName")
            if name:
                attrs.append({
                    "name": name,
                    "definition": _child_text(a, "attributeDefinition"),
                    "storage_type": _child_text(a, "storageType"),
                })
        key = object_name or entity or f"table_{len(out)+1}"
        out[str(key)] = {"entity_name": entity, "object_name": object_name, "attributes": attrs}
    return out


def _find(tables: dict[str, dict], filename: str) -> dict:
    for key, table in tables.items():
        if filename.lower() in str(key).lower() or filename.lower() in str(table.get("object_name") or "").lower():
            return table
    raise RuntimeError(f"metadata table missing for {filename}")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "eog.layer_b_mechanism_v2.ncrn_response_route_metadata_audit.v2",
        "pre_response_correction_amendment": AMENDMENT,
        "metadata_payload_requests": 1,
        "response_payload_requests": 0,
        "counts_payload_requests": 0,
        "fielddata_payload_requests": 0,
        "R1_payload_requests": 0,
        "response_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "response_open_authorized": False,
        "routes": {},
    }
    try:
        metadata = _get(METADATA_URL)
        digest = hashlib.sha256(metadata).hexdigest()
        if digest != EXPECTED_METADATA_SHA256:
            raise RuntimeError(f"metadata SHA256 changed: expected {EXPECTED_METADATA_SHA256}, got {digest}")
        result["metadata_sha256"] = digest
        tables = _tables(metadata)
        for label, route in ROUTES.items():
            table = _find(tables, route["filename"])
            names = [a["name"] for a in table["attributes"]]
            normalized = {_norm(n): n for n in names}
            has_species = any(k in normalized for k in ("sppcode", "speciescode", "scientificname", "commonname", "aoucode"))
            has_event = any("event" in _norm(n) or "visit" in _norm(n) for n in names)
            has_site = any("point" in _norm(n) or "site" in _norm(n) or "grts" in _norm(n) for n in names)
            has_date = any("date" in _norm(n) or "year" in _norm(n) for n in names)
            has_count = any(_norm(n) in {"numind", "birdcount", "count", "abundance"} or "count" in _norm(n) for n in names)
            result["routes"][label] = {
                "file_id": route["file_id"],
                "filename": route["filename"],
                "payload_requested": False,
                "table": table,
                "schema_flags": {
                    "has_species_identity": has_species,
                    "has_event_or_visit_key": has_event,
                    "has_site_key": has_site,
                    "has_date_or_year": has_date,
                    "has_count": has_count,
                },
                "site_year_detection_route_candidate": bool(has_species and (has_event or (has_site and has_date))),
            }
        candidates = [k for k, v in result["routes"].items() if v["site_year_detection_route_candidate"]]
        result["joinable_route_candidates_from_metadata"] = candidates
        if not candidates:
            raise RuntimeError("no published response-bearing schema can be joined to site/year without response-payload alias discovery")
        result["status"] = "metadata_response_route_candidates_identified"
        result["next_gate"] = "freeze exactly one response route and explicit site-year algebra from metadata before response payload"
        rc = 0
    except Exception as exc:
        result["status"] = "terminal_pre_response_response_semantics_stop"
        result["error"] = f"{type(exc).__name__}: {exc}"
        rc = 2
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
