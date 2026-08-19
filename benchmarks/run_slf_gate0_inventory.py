#!/usr/bin/env python3
"""Run spotted-lanternfly Gate 0 without opening county response rows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)
from eog.v2.response_firewall import read_bounded_first_record_text

SLF_BLOB_SHA1 = "e845dcc72080089d11c3f1078766cc14cdeb2340"
EXCLUDED_USPS = {"AK", "HI", "PR"}
EXPECTED_RESPONSE_FIELDS = {"year", "infested", "fips"}


def canonical_sha256(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload).hexdigest()


def normalize(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip(): str(value).strip() for key, value in row.items()}


def read_census_counties(zip_path: Path) -> tuple[list[dict[str, object]], str, str]:
    with zipfile.ZipFile(zip_path) as zf:
        names = [name for name in zf.namelist() if name.lower().endswith(".txt")]
        if len(names) != 1:
            raise ValueError(f"expected one national county text member, found {names!r}")
        member = names[0]
        data = zf.read(member)
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    fields = tuple(str(value).strip() for value in (reader.fieldnames or ()))
    required = {"USPS", "GEOID", "NAME", "INTPTLAT", "INTPTLONG"}
    if not required.issubset(fields):
        raise ValueError(f"Census county schema missing required fields: {fields!r}")

    nodes: list[dict[str, object]] = []
    for raw in reader:
        row = normalize(raw)
        if row["USPS"] in EXCLUDED_USPS:
            continue
        geoid = row["GEOID"]
        if len(geoid) != 5 or not geoid.isdigit():
            raise ValueError(f"invalid county GEOID {geoid!r}")
        lat = float(row["INTPTLAT"])
        lon = float(row["INTPTLONG"])
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValueError(f"invalid county coordinate for {geoid}")
        nodes.append({"geoid": geoid, "usps": row["USPS"], "name": row["NAME"], "lat": lat, "lon": lon})

    geoids = [row["geoid"] for row in nodes]
    if len(set(geoids)) != len(geoids):
        raise ValueError("duplicate Census GEOID in frozen node universe")
    if len(nodes) < 2500:
        raise ValueError(f"unexpectedly small conterminous county universe: {len(nodes)}")
    geometry_payload = [[row["geoid"], row["lat"], row["lon"]] for row in sorted(nodes, key=lambda row: row["geoid"])]
    return nodes, member, canonical_sha256(geometry_payload)


def response_header(path: Path) -> tuple[list[str], int, str]:
    bounded = read_bounded_first_record_text(path, max_record_bytes=16_384)
    fields = [value.strip().lower() for value in next(csv.reader([bounded.text]))]
    if not EXPECTED_RESPONSE_FIELDS.issubset(set(fields)):
        raise ValueError(f"response header lacks required fields: {fields!r}")
    return fields, bounded.bytes_consumed, bounded.terminator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census-zip", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not zipfile.is_zipfile(args.census_zip):
        raise SystemExit("Census source is not a ZIP archive")
    if git_blob_sha1(args.response) != SLF_BLOB_SHA1:
        raise SystemExit("SLFS response Git blob identity mismatch")

    nodes, census_member, geometry_fingerprint = read_census_counties(args.census_zip)
    fields, header_bytes, header_terminator = response_header(args.response)
    n_nodes = len(nodes)

    declaration = ProspectiveEstimabilityDeclaration(
        calibration_events=10,
        calibration_non_events=40,
        heldout_events=10,
        heldout_non_events=40,
        heldout_outer_units_with_both_classes=3,
    )
    evidence = AggregateEstimabilityEvidence(
        source_label="published SLF cumulative county counts 2014-2021 + response-free Census node count",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(lower=44, upper=44),
            "calibration_non_events": AggregateCountInterval(lower=n_nodes - 45),
            "heldout_events": AggregateCountInterval(lower=85, upper=85),
            "heldout_non_events": AggregateCountInterval(lower=n_nodes - 130),
            "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=3, upper=3),
        },
        note="County zero means no official infestation designation through the target year, not latent biological absence.",
    )
    estimability = evaluate_prospective_estimability(declaration, evidence)

    result = {
        "status": "gate0_pass_source_estimability_response_free_geometry" if estimability.status == "plausibly_eligible_pre_response" else "gate0_stop_estimability",
        "candidate": "Spotted lanternfly US county invasion 2014-2021",
        "census_source": {
            "archive_sha256": sha256_file(args.census_zip),
            "member": census_member,
            "conterminous_node_count": n_nodes,
            "geometry_fingerprint": geometry_fingerprint,
            "excluded_usps": sorted(EXCLUDED_USPS),
        },
        "response_source": {
            "git_blob_sha1": git_blob_sha1(args.response),
            "file_sha256": sha256_file(args.response),
            "header_fields": fields,
            "header_bytes_consumed": header_bytes,
            "header_terminator": header_terminator,
            "response_rows_opened": False,
            "response_values_parsed": False,
            "data_rows_after_first_physical_record_opened": False,
        },
        "prospective_estimability": {
            "status": estimability.status,
            "failing_keys": list(estimability.failing_keys),
            "unresolved_keys": list(estimability.unresolved_keys),
            "fingerprint": estimability.fingerprint,
            "calibration_events": 44,
            "heldout_events": 85,
            "calibration_non_events_lower_bound": n_nodes - 45,
            "heldout_non_events_lower_bound": n_nodes - 130,
            "heldout_outer_units_with_both_classes": 3,
        },
        "next": "run response-blind structural scale ladder on Census county geometry only" if estimability.status == "plausibly_eligible_pre_response" else "stop before structural worlds",
    }
    result["fingerprint"] = canonical_sha256(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "node_count": n_nodes,
        "estimability": estimability.status,
        "response_rows_opened": False,
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))

    if estimability.status != "plausibly_eligible_pre_response":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
