from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
EARTH_RADIUS_KM = 6371.0088


class PreResponseStop(RuntimeError):
    """Terminal response-blind source/registry/geometry STOP."""


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("source contract must contain a JSON object")
    return value


def _finite_float(value: str, label: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise PreResponseStop(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise PreResponseStop(f"{label} is not finite")
    return result


def _site_integer(value: str) -> int:
    if not value.isdigit():
        raise PreResponseStop(f"site value is not a positive decimal integer: {value!r}")
    result = int(value)
    if result <= 0 or str(result) != value:
        raise PreResponseStop(f"site value has noncanonical integer spelling: {value!r}")
    return result


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = p2 - p1
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def linear_quantile(sorted_values: list[float], q: float) -> float:
    """NumPy-compatible linear quantile for a non-empty sorted 1-D sample."""
    if not sorted_values:
        raise PreResponseStop("cannot compute structural quantiles from zero pair distances")
    if not 0.0 <= q <= 1.0:
        raise ValueError("quantile must be in [0, 1]")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return float(
        sorted_values[lower]
        + fraction * (sorted_values[upper] - sorted_values[lower])
    )


def parse_coordinate_registry(
    raw: bytes,
    contract: dict[str, object],
) -> tuple[list[dict[str, object]], list[str]]:
    registry = contract["pre_response_registry"]
    source = contract["source"]["coordinate_registry"]
    if git_blob_sha1(raw) != source["git_blob_sha1"]:
        raise PreResponseStop("coordinate registry Git blob SHA-1 drift")
    if len(raw) != int(source["size_bytes"]):
        raise PreResponseStop("coordinate registry byte-size drift")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreResponseStop("coordinate registry is not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_columns = list(registry["required_columns_exact_order"])
    if reader.fieldnames != expected_columns:
        raise PreResponseStop(
            f"coordinate header drift: {reader.fieldnames!r} != {expected_columns!r}"
        )
    physical = list(reader)
    if len(physical) != int(registry["expected_physical_rows"]):
        raise PreResponseStop(
            f"coordinate row count drift: {len(physical)} != {registry['expected_physical_rows']}"
        )

    seen_ids: set[int] = set()
    seen_sites: set[str] = set()
    missing_sites: list[str] = []
    valid: list[dict[str, object]] = []
    for row_number, row in enumerate(physical, start=2):
        raw_id = row["ID"]
        if not raw_id.isdigit() or int(raw_id) <= 0:
            raise PreResponseStop(f"invalid ID at physical row {row_number}")
        numeric_id = int(raw_id)
        if numeric_id in seen_ids:
            raise PreResponseStop(f"duplicate ID {numeric_id}")
        seen_ids.add(numeric_id)
        river = row["river"].strip()
        if not river or river != row["river"]:
            raise PreResponseStop(f"invalid river spelling at physical row {row_number}")
        site = _site_integer(row["site"])
        site_id = f"{river}{site}"
        if site_id in seen_sites:
            raise PreResponseStop(f"duplicate site_id {site_id!r}")
        seen_sites.add(site_id)
        lon_raw = row["longitude"].strip()
        lat_raw = row["latitude"].strip()
        if lon_raw == "NA" or lat_raw == "NA":
            if not (lon_raw == "NA" and lat_raw == "NA"):
                raise PreResponseStop(f"partial coordinate missingness at {site_id}")
            missing_sites.append(site_id)
            continue
        lon = _finite_float(lon_raw, f"longitude for {site_id}")
        lat = _finite_float(lat_raw, f"latitude for {site_id}")
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise PreResponseStop(f"invalid geographic coordinate at {site_id}")
        valid.append(
            {
                "source_row_id": numeric_id,
                "river": river,
                "site_integer": site,
                "site_id": site_id,
                "longitude": lon,
                "latitude": lat,
                "coordinate_source": row["source"].strip(),
                "fold": ((site - 1) % 5) + 1,
            }
        )

    expected_missing = sorted(str(v) for v in registry["expected_missing_coordinate_site_ids"])
    if sorted(missing_sites) != expected_missing:
        raise PreResponseStop(
            f"missing-coordinate site set drift: {sorted(missing_sites)!r} != {expected_missing!r}"
        )
    if len(valid) != int(registry["expected_valid_coordinate_nodes"]):
        raise PreResponseStop(
            f"valid-coordinate node count drift: {len(valid)} != {registry['expected_valid_coordinate_nodes']}"
        )
    valid.sort(key=lambda row: str(row["site_id"]))
    return valid, sorted(missing_sites)


def validate_formatting_code(raw: bytes, contract: dict[str, object]) -> dict[str, object]:
    source = contract["source"]["formatting_code"]
    if git_blob_sha1(raw) != source["git_blob_sha1"]:
        raise PreResponseStop("formatting-code Git blob SHA-1 drift")
    if len(raw) != int(source["size_bytes"]):
        raise PreResponseStop("formatting-code byte-size drift")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreResponseStop("formatting code is not UTF-8") from exc
    required_literals = (
        'site_id = paste0(river, site)',
        'latin == "Noemacheilus_barbatulus" ~ "Barbatula_oreas"',
        '"usubetsu4", "atsuta6", "kokamotsu4"',
        'read_csv(here::here("data_fmt/data_hkd_prtwsd_fmt.csv"))',
    )
    missing = [value for value in required_literals if value not in text]
    if missing:
        raise PreResponseStop(f"published formatting-code literals drifted: {missing!r}")
    return {
        "git_blob_sha1": source["git_blob_sha1"],
        "size_bytes": len(raw),
        "required_literal_count": len(required_literals),
    }


def _same_river_pairs(nodes: list[dict[str, object]]) -> list[tuple[str, str, float]]:
    by_river: dict[str, list[dict[str, object]]] = defaultdict(list)
    for node in nodes:
        by_river[str(node["river"])].append(node)
    pairs: list[tuple[str, str, float]] = []
    for river in sorted(by_river):
        river_nodes = sorted(by_river[river], key=lambda row: str(row["site_id"]))
        for i, left in enumerate(river_nodes):
            for right in river_nodes[i + 1 :]:
                distance = haversine_km(
                    float(left["longitude"]),
                    float(left["latitude"]),
                    float(right["longitude"]),
                    float(right["latitude"]),
                )
                if not math.isfinite(distance) or distance <= 0.0:
                    raise PreResponseStop(
                        f"same-river node pair has nonpositive distance: {left['site_id']}, {right['site_id']}"
                    )
                pairs.append((str(left["site_id"]), str(right["site_id"]), distance))
    if not pairs:
        raise PreResponseStop("no same-river pairs available for world construction")
    return pairs


def derive_worlds(
    nodes: list[dict[str, object]],
    contract: dict[str, object],
) -> dict[str, object]:
    geometry = contract["response_blind_world_geometry"]
    pairs = _same_river_pairs(nodes)
    distances = sorted(distance for _, _, distance in pairs)
    local_rows: list[dict[str, object]] = []
    seen_graphs: set[str] = set()
    for raw_q in geometry["threshold_quantiles"]:
        q = float(raw_q)
        threshold = linear_quantile(distances, q)
        edges = sorted(
            [
                [left, right]
                for left, right, distance in pairs
                if distance <= threshold
            ]
        )
        graph_payload = {
            "node_ids": [str(row["site_id"]) for row in nodes],
            "edge_scope": "same_river_only",
            "edges": edges,
        }
        graph_fingerprint = canonical_sha256(graph_payload)
        if graph_fingerprint in seen_graphs:
            continue
        seen_graphs.add(graph_fingerprint)
        local_rows.append(
            {
                "world_id": f"same_river_q{int(round(q * 100)):02d}",
                "quantile": q,
                "threshold_km": threshold,
                "edge_count": len(edges),
                "graph_fingerprint": graph_fingerprint,
            }
        )
    minimum = int(geometry["minimum_distinct_positive_local_worlds"])
    if len(local_rows) < minimum:
        raise PreResponseStop(
            f"only {len(local_rows)} distinct local adjacency worlds; require >= {minimum}"
        )
    if any(int(row["edge_count"]) <= 0 for row in local_rows):
        raise PreResponseStop("a retained local world has zero edges")

    all_node_ids = [str(row["site_id"]) for row in nodes]
    external_edge_count = len(all_node_ids) * (len(all_node_ids) - 1) // 2
    external_graph_fingerprint = canonical_sha256(
        {
            "node_ids": all_node_ids,
            "edge_scope": "explicit_external_open_complete_graph",
            "edge_count": external_edge_count,
        }
    )
    return {
        "same_river_pair_count": len(pairs),
        "distance_sample_sha256": canonical_sha256(
            [[left, right, distance] for left, right, distance in pairs]
        ),
        "local_worlds": local_rows,
        "external_open": {
            "world_id": "external_open",
            "edge_scope": "explicit_cross_watershed_permissive_analytical_alternative",
            "edge_count": external_edge_count,
            "graph_fingerprint": external_graph_fingerprint,
        },
    }


def derive_baseline_features(nodes: list[dict[str, object]]) -> dict[str, object]:
    by_river: dict[str, list[dict[str, object]]] = defaultdict(list)
    for node in nodes:
        by_river[str(node["river"])].append(node)
    categories = tuple(sorted(by_river))
    feature_names = [
        "longitude",
        "latitude",
        "site_integer",
        "within_river_site_rank_fraction",
        "river_node_count",
        "distance_to_river_centroid_km",
        "nearest_same_river_neighbor_distance_km",
        *[f"river__{river}" for river in categories],
    ]
    rows: list[list[object]] = []
    for river in categories:
        river_nodes = sorted(
            by_river[river],
            key=lambda row: (int(row["site_integer"]), str(row["site_id"])),
        )
        count = len(river_nodes)
        centroid_lon = sum(float(row["longitude"]) for row in river_nodes) / count
        centroid_lat = sum(float(row["latitude"]) for row in river_nodes) / count
        for rank, node in enumerate(river_nodes):
            rank_fraction = 0.0 if count == 1 else rank / (count - 1)
            centroid_distance = haversine_km(
                float(node["longitude"]),
                float(node["latitude"]),
                centroid_lon,
                centroid_lat,
            )
            neighbor_distances = [
                haversine_km(
                    float(node["longitude"]),
                    float(node["latitude"]),
                    float(other["longitude"]),
                    float(other["latitude"]),
                )
                for other in river_nodes
                if other["site_id"] != node["site_id"]
            ]
            nearest = min(neighbor_distances) if neighbor_distances else 0.0
            one_hot = [1.0 if river == category else 0.0 for category in categories]
            rows.append(
                [
                    str(node["site_id"]),
                    float(node["longitude"]),
                    float(node["latitude"]),
                    int(node["site_integer"]),
                    float(rank_fraction),
                    count,
                    float(centroid_distance),
                    float(nearest),
                    *one_hot,
                ]
            )
    rows.sort(key=lambda row: str(row[0]))
    return {
        "river_categories": list(categories),
        "feature_names": feature_names,
        "rows": rows,
        "matrix_fingerprint": canonical_sha256(
            {"feature_names": feature_names, "rows": rows}
        ),
    }


def evaluate_pre_response(
    coordinate_bytes: bytes,
    formatting_code_bytes: bytes,
    contract: dict[str, object],
) -> dict[str, object]:
    nodes, missing_sites = parse_coordinate_registry(coordinate_bytes, contract)
    code_evidence = validate_formatting_code(formatting_code_bytes, contract)
    worlds = derive_worlds(nodes, contract)
    baseline = derive_baseline_features(nodes)
    fold_counts = Counter(int(row["fold"]) for row in nodes)
    if sorted(fold_counts) != [1, 2, 3, 4, 5]:
        raise PreResponseStop("frozen five-fold rule did not produce all five folds")
    result: dict[str, object] = {
        "schema": "eog.hokkaido_streamfish_endpoint3.pre_response_geometry.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "pre_response_geometry_ready",
        "source_commit": contract["source"]["commit"],
        "physical_coordinate_rows": 129,
        "missing_coordinate_site_ids": missing_sites,
        "valid_node_count": len(nodes),
        "node_ids": [str(row["site_id"]) for row in nodes],
        "node_registry_fingerprint": canonical_sha256(nodes),
        "fold_counts": {str(key): fold_counts[key] for key in sorted(fold_counts)},
        "fold_assignment_fingerprint": canonical_sha256(
            [[row["site_id"], row["fold"]] for row in nodes]
        ),
        "world_geometry": worlds,
        "conventional_baseline": baseline,
        "formatting_code_evidence": code_evidence,
        "response_table_requests": 0,
        "response_table_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_stop_result(contract: dict[str, object], reason: str) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.hokkaido_streamfish_endpoint3.pre_response_geometry.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_source_registry_or_geometry",
        "reason": str(reason),
        "response_table_requests": 0,
        "response_table_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result
