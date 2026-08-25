from __future__ import annotations

from collections import Counter
from datetime import datetime
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.request

import numpy as np

from eog.v2.world_scale_ladder import StructuralScaleLadderDeclaration, build_structural_scale_ladder

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
OUT = Path("build/louisiana_marsh_bird_replication_1/gate1_geometry_temporal.json")
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
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def get_item() -> dict:
    item_id = CONTRACT["official_source"]["sciencebase_item_id"]
    req = urllib.request.Request(
        f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json",
        headers={"User-Agent": "EOG-Louisiana-Marsh-Bird-Gate1/1.0", "Accept": "application/json"},
    )
    AUDIT["sciencebase_metadata_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["sciencebase_metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise RuntimeError(f"ScienceBase metadata failure: status={status}, bytes={len(body)}")
    observed = hashlib.sha256(body).hexdigest()
    expected = CONTRACT["official_source"]["sciencebase_item_metadata_sha256"]
    if observed != expected:
        raise RuntimeError(f"ScienceBase metadata changed: {observed} != {expected}")
    return json.loads(body.decode("utf-8"))


def file_map(item: dict) -> dict[str, dict]:
    files = {str(row.get("name") or ""): row for row in (item.get("files") or [])}
    frozen = {**CONTRACT["response_independent_assets"], **CONTRACT["biological_response_assets_forbidden"]}
    for name, identity in frozen.items():
        if name not in files:
            raise RuntimeError(f"frozen asset missing: {name}")
        checksum = files[name].get("checksum") or {}
        md5 = str(checksum.get("value") or checksum.get("checksum") or "") if isinstance(checksum, dict) else str(checksum)
        if md5 != identity["md5"] or int(files[name].get("size") or 0) != int(identity["bytes"]):
            raise RuntimeError(f"asset identity drift: {name}")
    return files


def download(files: dict[str, dict], name: str) -> bytes:
    frozen = CONTRACT["response_independent_assets"][name]
    url = files[name].get("downloadUri") or files[name].get("url")
    if not url:
        raise RuntimeError(f"missing download URI: {name}")
    req = urllib.request.Request(str(url), headers={"User-Agent": "EOG-Louisiana-Marsh-Bird-Gate1/1.0", "Accept-Encoding": "identity"})
    AUDIT["response_independent_payload_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(int(frozen["bytes"]) + 1)
        status = int(getattr(response, "status", 200))
    AUDIT["response_independent_payload_bytes_opened"] += len(body)
    if status != 200 or len(body) != int(frozen["bytes"]):
        raise RuntimeError(f"{name} transport/size mismatch: status={status}, bytes={len(body)}")
    observed = hashlib.md5(body).hexdigest()
    if observed != frozen["md5"]:
        raise RuntimeError(f"{name} MD5 mismatch: {observed}")
    return body


def parse_table(body: bytes, name: str) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(body.decode("utf-8-sig"))))
    if len(rows) < 2:
        raise RuntimeError(f"{name} has no data rows")
    header, data = rows[0], rows[1:]
    if any(len(row) != len(header) for row in data):
        raise RuntimeError(f"{name} row width mismatch")
    expected = CONTRACT["response_independent_assets"][name]
    if header != expected["physical_header"]:
        raise RuntimeError(f"{name} header drift: {header}")
    fingerprint = canonical_sha256({"header": header, "rows": data})
    if fingerprint != expected["table_fingerprint"]:
        raise RuntimeError(f"{name} table fingerprint drift: {fingerprint}")
    return header, data


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371.0088
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def main() -> None:
    item = get_item()
    files = file_map(item)
    _, site_rows = parse_table(download(files, "Sites.csv"), "Sites.csv")
    _, sample_rows = parse_table(download(files, "Samples.csv"), "Samples.csv")

    if len(site_rows) != 33 or len(sample_rows) != 20:
        raise RuntimeError(f"response-independent registry counts changed: sites={len(site_rows)}, samples={len(sample_rows)}")

    node_ids = []
    coords = {}
    marsh = {}
    habitat = {}
    for row in site_rows:
        site = row[0].strip()
        if not site or site in coords:
            raise RuntimeError(f"empty/duplicate Site: {site!r}")
        lat = float(row[1])
        lon = float(row[2])
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise RuntimeError(f"invalid coordinates for {site}")
        node_ids.append(site)
        coords[site] = (lat, lon)
        marsh[site] = row[3].strip()
        habitat[site] = row[4].strip()

    n = len(node_ids)
    distance_matrix = np.zeros((n, n), dtype=float)
    for i, a in enumerate(node_ids):
        for j in range(i + 1, n):
            b = node_ids[j]
            distance_matrix[i, j] = distance_matrix[j, i] = haversine_km(coords[a], coords[b])
    geom = CONTRACT["geometry_semantics_frozen_after_gate0_before_gate1"]
    declaration = StructuralScaleLadderDeclaration(
        axis_id="southwest_louisiana_marsh_site_haversine_km",
        target_largest_component_fractions=tuple(geom["structural_lcc_targets"]),
    )
    ladder = build_structural_scale_ladder(node_ids, distance_matrix, declaration)
    distinct_positive = sorted({float(level.distance_threshold) for level in ladder.levels if level.distance_threshold > 0})
    if len(distinct_positive) < int(geom["minimum_distinct_positive_structural_scales"]):
        raise RuntimeError(f"insufficient structural-scale diversity: {distinct_positive}")

    sampling = CONTRACT["sampling_semantics_frozen_after_gate0"]
    occasions = []
    seen_periods = set()
    for row in sample_rows:
        period = int(row[0].strip())
        if period in seen_periods:
            raise RuntimeError(f"duplicate Sample Period: {period}")
        seen_periods.add(period)
        dt = datetime.strptime(row[1].strip(), "%m/%d/%Y").date()
        precipitation = float(row[2])
        min_air_temp = float(row[3])
        if not all(math.isfinite(v) for v in (precipitation, min_air_temp)):
            raise RuntimeError(f"non-finite sampling covariate at period {period}")
        occasions.append({
            "sample_period": period,
            "date": dt.isoformat(),
            "precipitation": precipitation,
            "min_air_temp": min_air_temp,
        })
    if sorted(seen_periods) != sampling["all_20_sample_period_ids_required_once"]:
        raise RuntimeError(f"sample-period registry mismatch: {sorted(seen_periods)}")
    chronological = sorted(occasions, key=lambda row: (row["date"], row["sample_period"]))
    observed_order = [row["sample_period"] for row in chronological]
    if observed_order != sampling["chronological_sample_period_order"]:
        raise RuntimeError(f"chronological sample-period order drift: {observed_order}")
    if [row["sample_period"] for row in chronological[:12]] != sampling["calibration_sample_periods"]:
        raise RuntimeError("calibration split drift")
    if [row["sample_period"] for row in chronological[12:]] != sampling["heldout_sample_periods"]:
        raise RuntimeError("heldout split drift")

    payload = {
        "schema": "eog.louisiana_marsh_bird_gate1_geometry_temporal.v1",
        "replication_id": CONTRACT["replication_id"],
        "status": "response_blind_geometry_and_temporal_split_pass",
        "site_registry": {
            "site_count": 33,
            "site_ids": node_ids,
            "site_registry_fingerprint": canonical_sha256({"site_ids": node_ids, "coordinates": {site: list(coords[site]) for site in node_ids}}),
            "marsh_counts": dict(sorted(Counter(marsh.values()).items())),
            "habitat_counts": dict(sorted(Counter(habitat.values()).items())),
        },
        "geometry": {
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
            "distinct_positive_thresholds_km": distinct_positive,
        },
        "temporal": {
            "chronological_occasions": chronological,
            "calibration_sample_periods": sampling["calibration_sample_periods"],
            "heldout_sample_periods": sampling["heldout_sample_periods"],
            "primary_outer_units": sampling["primary_outer_units"],
            "calibration_row_capacity_if_complete": 33 * len(sampling["calibration_sample_periods"]),
            "heldout_row_capacity_if_complete": 33 * len(sampling["heldout_sample_periods"]),
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
