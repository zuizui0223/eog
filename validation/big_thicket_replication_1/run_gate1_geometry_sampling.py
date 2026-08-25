from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import urllib.request

import numpy as np

from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
OUT = Path("build/big_thicket_replication_1/gate1_geometry_sampling.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

AUDIT = {
    "sciencebase_metadata_requests": 0,
    "sciencebase_metadata_bytes_opened": 0,
    "response_independent_payload_requests": 0,
    "response_independent_payload_bytes_opened": 0,
    "biological_response_payload_requests": 0,
    "biological_response_payload_bytes_opened": 0,
    "biological_response_header_bytes_opened": 0,
    "biological_response_rows_opened": False,
    "biological_response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def sciencebase_item() -> dict:
    item_id = CONTRACT["official_source"]["sciencebase_item_id"]
    req = urllib.request.Request(
        f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json",
        headers={"User-Agent": "EOG-Big-Thicket-Gate1/1.0", "Accept": "application/json"},
    )
    AUDIT["sciencebase_metadata_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["sciencebase_metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise RuntimeError(f"ScienceBase metadata transport failure: status={status}, bytes={len(body)}")
    observed = hashlib.sha256(body).hexdigest()
    expected = CONTRACT["official_source"]["sciencebase_item_metadata_sha256"]
    if observed != expected:
        raise RuntimeError(f"ScienceBase item metadata changed: {observed} != {expected}")
    return json.loads(body.decode("utf-8"))


def frozen_files(metadata: dict) -> dict[str, dict]:
    files = {str(row.get("name") or ""): row for row in (metadata.get("files") or [])}
    for name, frozen in CONTRACT["pre_response_asset_identities"].items():
        if name not in files:
            raise RuntimeError(f"frozen file missing: {name}")
        row = files[name]
        checksum = row.get("checksum") or {}
        if isinstance(checksum, dict):
            md5 = str(checksum.get("value") or checksum.get("checksum") or "")
        else:
            md5 = str(checksum)
        if md5 != frozen["md5"] or int(row.get("size") or 0) != int(frozen["bytes"]):
            raise RuntimeError(f"frozen file identity drift: {name}")
    return files


def download_frozen(files: dict[str, dict], name: str) -> bytes:
    frozen = CONTRACT["pre_response_asset_identities"][name]
    if frozen["access"] != "full payload allowed" and "full payload allowed after Gate0" not in frozen["access"]:
        raise RuntimeError(f"full payload not authorized by contract: {name}")
    url = files[name].get("downloadUri") or files[name].get("url")
    if not url:
        raise RuntimeError(f"download URI missing: {name}")
    req = urllib.request.Request(str(url), headers={"User-Agent": "EOG-Big-Thicket-Gate1/1.0", "Accept-Encoding": "identity"})
    AUDIT["response_independent_payload_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(int(frozen["bytes"]) + 1)
        status = int(getattr(response, "status", 200))
    AUDIT["response_independent_payload_bytes_opened"] += len(body)
    if status != 200 or len(body) != int(frozen["bytes"]):
        raise RuntimeError(f"{name} size/transport mismatch: status={status}, bytes={len(body)}")
    md5 = hashlib.md5(body).hexdigest()
    if md5 != frozen["md5"]:
        raise RuntimeError(f"{name} MD5 mismatch: {md5}")
    return body


def parse_csv(payload: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(payload.decode("utf-8-sig"))))


def parse_date_token(token: str) -> date:
    value = token.strip()
    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", value) or re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", value)
    if match:
        y, m, d = map(int, match.groups())
        return date(y, m, d)
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})", value)
    if match:
        m, d, y = map(int, match.groups())
        if y < 100:
            y += 2000
        return date(y, m, d)
    raise ValueError(f"unrecognized frozen date token: {token!r}")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main() -> None:
    metadata = sciencebase_item()
    files = frozen_files(metadata)
    site_bytes = download_frozen(files, "Site Locations.csv")
    matrix_bytes = download_frozen(files, "Sample Matrix.csv")
    sample_bytes = download_frozen(files, "Sample Data.csv")

    # Closed site registry and geometry.
    site_table = parse_csv(site_bytes)
    expected_site_header = ["Site_Number", "Management_Unit", "Latitude", "Longitude"]
    if not site_table or site_table[0] != expected_site_header:
        raise RuntimeError(f"Site Locations header drift: {site_table[0] if site_table else None}")
    site_rows = site_table[1:]
    if len(site_rows) != 52 or any(len(row) != 4 for row in site_rows):
        raise RuntimeError(f"closed 52-site registry changed: rows={len(site_rows)}")
    observed_registry_fp = canonical_sha256({"header": expected_site_header, "rows": site_rows})
    expected_registry_fp = CONTRACT["geometry_semantics_frozen_after_gate0_before_gate1"]["site_registry_row_fingerprint"]
    if observed_registry_fp != expected_registry_fp:
        raise RuntimeError(f"site registry fingerprint changed: {observed_registry_fp} != {expected_registry_fp}")

    node_ids = []
    coordinates: dict[str, tuple[float, float]] = {}
    management_units: dict[str, str] = {}
    for row in site_rows:
        site = row[0].strip()
        if not site or site in coordinates:
            raise RuntimeError(f"duplicate/empty Site_Number: {site!r}")
        lat = float(row[2])
        lon = float(row[3])
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise RuntimeError(f"invalid coordinates for site {site}")
        node_ids.append(site)
        coordinates[site] = (lat, lon)
        management_units[site] = row[1].strip()
    if set(node_ids) != {str(i) for i in range(1, 53)}:
        raise RuntimeError("Site_Number registry is not exactly 1..52")

    n = len(node_ids)
    matrix = np.zeros((n, n), dtype=float)
    for i, a in enumerate(node_ids):
        for j in range(i + 1, n):
            b = node_ids[j]
            d = haversine_km(*coordinates[a], *coordinates[b])
            matrix[i, j] = matrix[j, i] = d
    declaration = StructuralScaleLadderDeclaration(
        axis_id="big_thicket_haversine_km",
        target_largest_component_fractions=tuple(CONTRACT["geometry_semantics_frozen_after_gate0_before_gate1"]["structural_lcc_targets"]),
    )
    ladder = build_structural_scale_ladder(node_ids, matrix, declaration)
    distinct_positive_thresholds = sorted({float(level.distance_threshold) for level in ladder.levels if level.distance_threshold > 0})
    if len(distinct_positive_thresholds) < int(CONTRACT["geometry_semantics_frozen_after_gate0_before_gate1"]["minimum_distinct_positive_structural_scales"]):
        raise RuntimeError(f"insufficient distinct positive structural scales: {distinct_positive_thresholds}")

    # Annual survey availability matrix.
    matrix_table = parse_csv(matrix_bytes)
    expected_matrix_header = CONTRACT["sampling_row_semantics_frozen_before_gate1"]["sample_matrix_expected_physical_header"]
    if not matrix_table or matrix_table[0] != expected_matrix_header:
        raise RuntimeError(f"Sample Matrix header drift: {matrix_table[0] if matrix_table else None}")
    matrix_rows = matrix_table[1:]
    year_labels = [str(year) for year in range(2010, 2019)]
    matrix_by_site: dict[str, dict[str, int]] = {}
    for row in matrix_rows:
        if len(row) != len(expected_matrix_header):
            raise RuntimeError("Sample Matrix row width mismatch")
        site = row[0].strip()
        if site not in coordinates or site in matrix_by_site:
            raise RuntimeError(f"Sample Matrix unknown/duplicate site: {site!r}")
        values: dict[str, int] = {}
        for offset, year in enumerate(year_labels, start=1):
            token = row[offset].strip()
            if not re.fullmatch(r"\d+", token):
                raise RuntimeError(f"Sample Matrix non-integer/blank count at site={site}, year={year}: {token!r}")
            values[year] = int(token)
        matrix_by_site[site] = values
    missing_matrix_sites = sorted(set(node_ids) - set(matrix_by_site), key=int)
    annual_matrix_summary = {
        year: {
            "total_samples": sum(values[year] for values in matrix_by_site.values()),
            "active_site_count": sum(values[year] > 0 for values in matrix_by_site.values()),
            "zero_sample_site_count_among_matrix_rows": sum(values[year] == 0 for values in matrix_by_site.values()),
        }
        for year in year_labels
    }

    # Survey effort/covariate rows; parse positionally because the physical header has duplicate names.
    sample_table = parse_csv(sample_bytes)
    expected_sample_header = CONTRACT["sampling_row_semantics_frozen_before_gate1"]["sample_data_expected_physical_header"]
    if not sample_table or sample_table[0] != expected_sample_header:
        raise RuntimeError(f"Sample Data header drift: {sample_table[0] if sample_table else None}")
    sample_rows = sample_table[1:]
    internal_names = CONTRACT["sampling_row_semantics_frozen_before_gate1"]["sample_data_internal_positional_names"]
    if len(internal_names) != len(expected_sample_header):
        raise RuntimeError("internal positional labels do not match Sample Data width")
    sample_year_counts = Counter()
    sample_year_sites: dict[str, set[str]] = defaultdict(set)
    sample_token_counts = Counter()
    date_values = []
    unknown_site_rows = []
    duplicate_survey_ids = []
    seen_survey_ids = set()
    missingness = Counter()
    for row_index, row in enumerate(sample_rows, start=2):
        if len(row) != len(expected_sample_header):
            raise RuntimeError(f"Sample Data row width mismatch at physical row {row_index}: {len(row)}")
        record = dict(zip(internal_names, row, strict=True))
        survey_id = record["Survey_ID"].strip()
        if not survey_id:
            raise RuntimeError(f"empty Survey_ID at physical row {row_index}")
        if survey_id in seen_survey_ids:
            duplicate_survey_ids.append(survey_id)
        seen_survey_ids.add(survey_id)
        site = record["Site_Number"].strip()
        if site and site not in coordinates:
            unknown_site_rows.append({"physical_row": row_index, "site": site})
        if not site:
            raise RuntimeError(f"empty Site_Number at physical row {row_index}")
        parsed_date = parse_date_token(record["Date"])
        date_values.append(parsed_date)
        year = str(parsed_date.year)
        sample_year_counts[year] += 1
        sample_year_sites[year].add(site)
        sample_token_counts[record["Sample"].strip()] += 1
        for key, value in record.items():
            if not value.strip():
                missingness[key] += 1
    if unknown_site_rows:
        raise RuntimeError(f"Sample Data contains sites outside frozen registry: {unknown_site_rows[:5]}")

    payload = {
        "schema": "eog.big_thicket_gate1_geometry_sampling.v1",
        "replication_id": CONTRACT["replication_id"],
        "status": "response_blind_geometry_and_sampling_pass",
        "site_registry": {
            "site_count": 52,
            "registry_row_fingerprint": observed_registry_fp,
            "management_unit_counts": dict(sorted(Counter(management_units.values()).items())),
        },
        "geometry": {
            "axis_id": ladder.axis_id,
            "distance_matrix_fingerprint": ladder.distance_matrix_fingerprint,
            "structural_ladder_fingerprint": ladder.fingerprint,
            "levels": [
                {
                    "level_id": level.level_id,
                    "target_lcc": level.target_largest_component_fraction,
                    "threshold_km": level.distance_threshold,
                    "achieved_lcc": level.achieved_largest_component_fraction,
                    "weak_component_count": level.weak_component_count,
                    "isolated_node_fraction": level.isolated_node_fraction,
                    "directed_edge_count": level.directed_edge_count,
                    "fingerprint": level.fingerprint,
                }
                for level in ladder.levels
            ],
            "distinct_positive_thresholds_km": distinct_positive_thresholds,
        },
        "sample_matrix": {
            "row_count": len(matrix_rows),
            "represented_site_count": len(matrix_by_site),
            "missing_frozen_registry_sites": missing_matrix_sites,
            "annual_summary": annual_matrix_summary,
        },
        "sample_data": {
            "row_count": len(sample_rows),
            "unique_survey_id_count": len(seen_survey_ids),
            "duplicate_survey_id_count": len(duplicate_survey_ids),
            "date_min": min(date_values).isoformat() if date_values else None,
            "date_max": max(date_values).isoformat() if date_values else None,
            "rows_by_year": dict(sorted(sample_year_counts.items())),
            "active_sites_by_year": {year: len(sites) for year, sites in sorted(sample_year_sites.items())},
            "sample_token_counts": dict(sorted(sample_token_counts.items())),
            "missing_field_counts": dict(sorted(missingness.items())),
        },
        "audit": dict(AUDIT),
    }
    if AUDIT["biological_response_payload_requests"] or AUDIT["biological_response_payload_bytes_opened"]:
        raise RuntimeError("biological response firewall violated")
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
