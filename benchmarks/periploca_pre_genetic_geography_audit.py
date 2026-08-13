"""Stage-1 response-free geography audit for the Periploca candidate.

Only the released population-geography text file is read as structured content. The
microsatellite file is passed only as an opaque byte object for checksum/provenance and
is never decoded or parsed by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re


POP_PATTERN = re.compile(r"pop|population|code|site|locality|location", re.I)
LAT_PATTERN = re.compile(r"(^|[^a-z])lat(?:itude)?([^a-z]|$)", re.I)
LON_PATTERN = re.compile(r"(^|[^a-z])(lon|long|longitude)([^a-z]|$)", re.I)
UTM_PATTERN = re.compile(r"utm", re.I)
ISLAND_PATTERN = re.compile(r"island|mainland|region|country|geogr|position", re.I)
DMS_PATTERN = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?)\s*(?:°|d)?\s*"
    r"(?:(\d+(?:\.\d+)?)\s*(?:['′m])?\s*)?"
    r"(?:(\d+(?:\.\d+)?)\s*(?:[\"″s])?\s*)?"
    r"([NSEW])?\s*$",
    re.I,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _decode(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("Periploca geography file has no supported text encoding")


def _nonempty_lines(text: str) -> list[str]:
    return [line.rstrip("\r\n") for line in text.splitlines() if line.strip()]


def _choose_delimiter(lines: list[str]) -> str:
    sample = "\n".join(lines[: min(len(lines), 30)])
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t,;").delimiter
    except csv.Error:
        counts = {delimiter: sum(line.count(delimiter) for line in lines[:10]) for delimiter in ("\t", ",", ";")}
        delimiter, score = max(counts.items(), key=lambda item: item[1])
        if score > 0:
            return delimiter
        raise ValueError("could not infer tab/comma/semicolon delimiter from Periploca geography file")


def _parse_coordinate(value: object, *, latitude: bool) -> float | None:
    text = str(value or "").strip()
    if not text or text.lower() in {"na", "nan", "n/a", "null", "none", ".", "-"}:
        return None
    normalized = text.replace("º", "°").replace("’", "′")
    try:
        parsed = float(normalized)
    except ValueError:
        match = DMS_PATTERN.match(normalized)
        if not match:
            return None
        degrees = float(match.group(1))
        minutes = float(match.group(2) or 0.0)
        seconds = float(match.group(3) or 0.0)
        hemisphere = (match.group(4) or "").upper()
        sign = -1.0 if degrees < 0 else 1.0
        parsed = abs(degrees) + minutes / 60.0 + seconds / 3600.0
        parsed *= sign
        if hemisphere in {"S", "W"}:
            parsed = -abs(parsed)
        elif hemisphere in {"N", "E"}:
            parsed = abs(parsed)
    if not math.isfinite(parsed):
        return None
    bound = 90.0 if latitude else 180.0
    if not (-bound <= parsed <= bound):
        return None
    return float(parsed)


def audit(geography_path: Path, microsatellite_path: Path) -> dict[str, object]:
    geography_bytes = geography_path.read_bytes()
    text, encoding = _decode(geography_bytes)
    lines = _nonempty_lines(text)
    if len(lines) < 2:
        raise ValueError("Periploca geography file has fewer than two non-empty lines")
    delimiter = _choose_delimiter(lines)
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    headers = tuple((reader.fieldnames or ()))
    rows = list(reader)
    if not headers or not rows:
        raise ValueError("Periploca geography file did not yield a header plus data rows")

    population_candidates = [header for header in headers if POP_PATTERN.search(header or "")]
    latitude_candidates = [header for header in headers if LAT_PATTERN.search(header or "")]
    longitude_candidates = [header for header in headers if LON_PATTERN.search(header or "")]
    utm_candidates = [header for header in headers if UTM_PATTERN.search(header or "")]
    island_region_candidates = [header for header in headers if ISLAND_PATTERN.search(header or "")]

    coordinate_pair_audits: list[dict[str, object]] = []
    for lat_header in latitude_candidates:
        for lon_header in longitude_candidates:
            parsed_pairs: list[tuple[float, float]] = []
            for row in rows:
                latitude = _parse_coordinate(row.get(lat_header), latitude=True)
                longitude = _parse_coordinate(row.get(lon_header), latitude=False)
                if latitude is not None and longitude is not None:
                    parsed_pairs.append((latitude, longitude))
            coordinate_pair_audits.append(
                {
                    "latitude_column": lat_header,
                    "longitude_column": lon_header,
                    "n_finite_coordinate_rows": len(parsed_pairs),
                    "n_unique_coordinate_pairs": len({(round(lat, 8), round(lon, 8)) for lat, lon in parsed_pairs}),
                    "latitude_min": min((pair[0] for pair in parsed_pairs), default=None),
                    "latitude_max": max((pair[0] for pair in parsed_pairs), default=None),
                    "longitude_min": min((pair[1] for pair in parsed_pairs), default=None),
                    "longitude_max": max((pair[1] for pair in parsed_pairs), default=None),
                }
            )

    utm_audits: list[dict[str, object]] = []
    for header in utm_candidates:
        values = [str(row.get(header) or "").strip() for row in rows]
        nonempty = [value for value in values if value]
        # Raw examples are public response-free geography metadata and are retained only
        # to establish the released coordinate syntax before a converter is frozen.
        utm_audits.append(
            {
                "column": header,
                "n_nonempty_rows": len(nonempty),
                "n_unique_values": len(set(nonempty)),
                "raw_examples_first_12": nonempty[:12],
                "contains_zone_like_token_count": sum(bool(re.search(r"\b\d{1,2}\s*[A-Z]\b", value, re.I)) for value in nonempty),
                "contains_two_large_numeric_tokens_count": sum(
                    len(re.findall(r"\d{4,}(?:\.\d+)?", value)) >= 2 for value in nonempty
                ),
            }
        )

    population_distinct_counts: dict[str, int] = {}
    for header in population_candidates:
        population_distinct_counts[header] = len(
            {str(row.get(header) or "").strip() for row in rows if str(row.get(header) or "").strip()}
        )

    island_region_distinct_counts: dict[str, int] = {}
    for header in island_region_candidates:
        island_region_distinct_counts[header] = len(
            {str(row.get(header) or "").strip() for row in rows if str(row.get(header) or "").strip()}
        )

    best_coordinate_rows = max(
        (int(item["n_finite_coordinate_rows"]) for item in coordinate_pair_audits),
        default=0,
    )
    best_population_count = max(population_distinct_counts.values(), default=0)
    direct_latlon_admitted = bool(
        population_candidates
        and coordinate_pair_audits
        and best_coordinate_rows >= 6
        and best_population_count >= 6
    )
    response_free_coordinate_schema_available = bool(direct_latlon_admitted or utm_audits)

    result: dict[str, object] = {
        "status": (
            "periploca-stage1-response-free-direct-coordinate-pass"
            if direct_latlon_admitted
            else "periploca-stage1-response-free-utm-schema-detected"
            if utm_audits
            else "non_estimable_response_free_geography_unavailable"
        ),
        "admitted": direct_latlon_admitted,
        "response_free_coordinate_schema_available": response_free_coordinate_schema_available,
        "geography_file_name": geography_path.name,
        "geography_size_bytes": geography_path.stat().st_size,
        "geography_sha256": hashlib.sha256(geography_bytes).hexdigest(),
        "geography_encoding": encoding,
        "delimiter": delimiter,
        "n_nonempty_lines": len(lines),
        "n_rows": len(rows),
        "headers": list(headers),
        "population_id_candidate_columns": population_candidates,
        "population_candidate_distinct_counts": population_distinct_counts,
        "latitude_candidate_columns": latitude_candidates,
        "longitude_candidate_columns": longitude_candidates,
        "coordinate_pair_audits": coordinate_pair_audits,
        "utm_candidate_columns": utm_candidates,
        "utm_schema_audits": utm_audits,
        "island_region_candidate_columns": island_region_candidates,
        "island_region_candidate_distinct_counts": island_region_distinct_counts,
        "microsatellite_file_name": microsatellite_path.name,
        "microsatellite_size_bytes": microsatellite_path.stat().st_size,
        "microsatellite_sha256": _sha256(microsatellite_path),
        "microsatellite_contents_accessed": False,
        "cpdna_contents_accessed": False,
        "genetic_response_computed": False,
        "claim_boundary": (
            "Only the released population-geography text was decoded/parsed. The microsatellite "
            "file was treated as an opaque byte object for checksum only; cpDNA was not opened. "
            "UTM raw examples are recorded solely to freeze the released response-free coordinate syntax."
        ),
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geography", type=Path, required=True)
    parser.add_argument("--microsatellite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.geography, args.microsatellite)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
