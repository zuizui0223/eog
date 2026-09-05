from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_pre_response_certificate.json"
EARTH_RADIUS_KM = 6371.0088
USER_AGENT = "EOG-UWIN-Multicity-Endpoint3-Gate0/1.0"
ByteFetcher = Callable[[str, int], bytes]


class Gate0Stop(RuntimeError):
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
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _finite_float(value: str, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise Gate0Stop(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise Gate0Stop(f"{label} is not finite")
    return result


def _csv_rows(raw: bytes, label: str) -> tuple[list[str], list[dict[str, str]]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Gate0Stop(f"{label} is not UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise Gate0Stop(f"{label} is empty") from exc
    if not header or len(set(header)) != len(header):
        raise Gate0Stop(f"{label} has empty/duplicate physical columns")
    physical: list[dict[str, str]] = []
    for row_number, row in enumerate(reader, start=2):
        if len(row) != len(header):
            raise Gate0Stop(
                f"{label} row {row_number} has {len(row)} cells for {len(header)} columns"
            )
        physical.append(dict(zip(header, row, strict=True)))
    if not physical:
        raise Gate0Stop(f"{label} has no data rows")
    return header, physical


def _verify_source_bytes(
    raw: bytes,
    source: dict[str, object],
    label: str,
) -> None:
    if len(raw) != int(source["size_bytes"]):
        raise Gate0Stop(f"{label} byte-size drift")
    if git_blob_sha1(raw) != str(source["git_blob_sha1"]):
        raise Gate0Stop(f"{label} Git blob SHA-1 drift")


def parse_coordinates(
    raw: bytes,
    contract: dict[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    source = contract["source"]["safe_files"]["site_coordinates"]
    _verify_source_bytes(raw, source, "site coordinates")
    header, rows = _csv_rows(raw, "site coordinates")
    expected = list(contract["safe_schema"]["site_coordinates_required_columns"])
    if header != expected:
        raise Gate0Stop(f"coordinate header drift: {header!r} != {expected!r}")
    allowed_cities = set(contract["city_codes"])
    out: dict[tuple[str, str], dict[str, object]] = {}
    for i, row in enumerate(rows, start=2):
        site = row["Site"].strip()
        city = row["City"].strip()
        if not site or site != row["Site"]:
            raise Gate0Stop(f"invalid Site spelling in coordinates row {i}")
        if city not in allowed_cities:
            raise Gate0Stop(f"unknown City {city!r} in coordinates row {i}")
        if row["Crs"].strip() not in {"4326", "4326.0"}:
            raise Gate0Stop(f"coordinate CRS is not 4326 for {city}|{site}")
        lon = _finite_float(row["Long"], f"longitude for {city}|{site}")
        lat = _finite_float(row["Lat"], f"latitude for {city}|{site}")
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise Gate0Stop(f"invalid WGS84 coordinate for {city}|{site}")
        key = (city, site)
        if key in out:
            raise Gate0Stop(f"duplicate coordinate key {city}|{site}")
        out[key] = {"city": city, "site": site, "longitude": lon, "latitude": lat}
    return out


def parse_range_availability(
    raw: bytes,
    contract: dict[str, object],
) -> tuple[str, dict[str, float], list[str], dict[str, int]]:
    source = contract["source"]["safe_files"]["range_availability"]
    _verify_source_bytes(raw, source, "range availability")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Gate0Stop("range availability is not UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise Gate0Stop("range availability is empty") from exc
    expected_cities = set(contract["safe_schema"]["range_city_columns_exact_set"])
    if len(header) != len(expected_cities) + 1 or len(set(header[1:])) != len(header[1:]):
        raise Gate0Stop("range availability header width/uniqueness drift")
    if set(header[1:]) != expected_cities:
        raise Gate0Stop("range availability city columns drifted")
    species_rows: dict[str, dict[str, float]] = {}
    for row_number, row in enumerate(reader, start=2):
        if len(row) != len(header):
            raise Gate0Stop(f"range row {row_number} width drift")
        species = row[0].strip()
        if not species or species != row[0] or species in species_rows:
            raise Gate0Stop(f"invalid/duplicate species identifier at range row {row_number}")
        values = {
            city: _finite_float(value, f"range distance {species}/{city}")
            for city, value in zip(header[1:], row[1:], strict=True)
        }
        species_rows[species] = values
    if not species_rows:
        raise Gate0Stop("range availability contains no species")
    counts = {
        species: sum(value >= 0.0 for value in values.values())
        for species, values in species_rows.items()
    }
    best = max(counts.values())
    if best < int(contract["focal_selection"]["minimum_in_range_cities"]):
        raise Gate0Stop(f"best response-independent range coverage is only {best} cities")
    focal = sorted(species for species, count in counts.items() if count == best)[0]
    distances = species_rows[focal]
    in_range = sorted(city for city, value in distances.items() if value >= 0.0)
    return focal, distances, in_range, counts


def parse_site_covariates(
    raw: bytes,
    contract: dict[str, object],
    coordinates: dict[tuple[str, str], dict[str, object]],
    in_range_cities: set[str],
) -> list[dict[str, object]]:
    source = contract["source"]["safe_files"]["site_covariates"]
    _verify_source_bytes(raw, source, "site covariates")
    header, rows = _csv_rows(raw, "site covariates")
    required = list(contract["safe_schema"]["site_covariates_required_columns"])
    missing = [name for name in required if name not in header]
    if missing:
        raise Gate0Stop(f"site covariates missing required columns: {missing!r}")
    allowed_cities = set(contract["city_codes"])
    season_re = re.compile(str(contract["candidate_registry"]["season_pattern"]))
    numeric_names = required[3:]
    out: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        site = row["Site"].strip()
        city = row["City"].strip()
        season = row["Season"].strip()
        if not site or site != row["Site"]:
            raise Gate0Stop(f"invalid Site spelling in site covariates row {row_number}")
        if city not in allowed_cities:
            raise Gate0Stop(f"unknown City {city!r} in site covariates row {row_number}")
        if not season_re.fullmatch(season):
            raise Gate0Stop(f"invalid Season {season!r} in site covariates row {row_number}")
        key = (city, site, season)
        if key in seen:
            raise Gate0Stop(f"duplicate candidate source row {city}|{site}|{season}")
        seen.add(key)
        numeric = {
            name: _finite_float(row[name], f"{name} for {city}|{site}|{season}")
            for name in numeric_names
        }
        if city not in in_range_cities:
            continue
        coord = coordinates.get((city, site))
        if coord is None:
            raise Gate0Stop(f"candidate site lacks unique coordinates: {city}|{site}")
        out.append(
            {
                "city": city,
                "site": site,
                "season": season,
                "longitude": coord["longitude"],
                "latitude": coord["latitude"],
                **numeric,
            }
        )
    out.sort(key=lambda row: (str(row["city"]), str(row["site"]), str(row["season"])))
    if len(out) < int(contract["candidate_registry"]["minimum_candidate_site_seasons"]):
        raise Gate0Stop(f"only {len(out)} response-independent candidate site-seasons")
    unique_sites = {(str(row["city"]), str(row["site"])) for row in out}
    if len(unique_sites) < int(contract["candidate_registry"]["minimum_unique_sites"]):
        raise Gate0Stop(f"only {len(unique_sites)} response-independent candidate sites")
    return out


def parse_housing_cost(
    raw: bytes,
    contract: dict[str, object],
    candidate_keys: set[tuple[str, str]],
) -> tuple[bool, dict[tuple[str, str], float], str]:
    source = contract["source"]["safe_files"]["housing_cost"]
    _verify_source_bytes(raw, source, "housing cost")
    header, rows = _csv_rows(raw, "housing cost")
    expected = list(contract["safe_schema"]["housing_cost_required_columns"])
    if header != expected:
        raise Gate0Stop(f"housing-cost header drift: {header!r} != {expected!r}")
    allowed_cities = set(contract["city_codes"])
    mapping: dict[tuple[str, str], float] = {}
    duplicate_keys: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        city = row["City"].strip()
        season = row["Season"].strip()
        if city not in allowed_cities or not season:
            raise Gate0Stop(f"invalid housing City/Season at row {row_number}")
        key = (city, season)
        price = _finite_float(row["Price"], f"housing Price for {city}|{season}")
        if key in mapping:
            duplicate_keys.add(key)
        mapping[key] = price
    if duplicate_keys & candidate_keys:
        return False, {}, "candidate City|Season has duplicate housing-cost rows"
    missing = sorted(candidate_keys - set(mapping))
    if missing:
        return False, {}, f"{len(missing)} candidate City|Season keys lack housing cost"
    return True, {key: mapping[key] for key in candidate_keys}, "complete unique candidate linkage"


def _fold(city: str, site: str) -> int:
    digest = hashlib.sha256(f"{city}|{site}".encode("utf-8")).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 5)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def linear_quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise Gate0Stop("cannot derive worlds from zero positive same-city distances")
    position = (len(sorted_values) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    f = position - lo
    return float(sorted_values[lo] + f * (sorted_values[hi] - sorted_values[lo]))


def derive_geometry(
    candidates: list[dict[str, object]],
    contract: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    site_rows: dict[tuple[str, str], dict[str, object]] = {}
    for row in candidates:
        key = (str(row["city"]), str(row["site"]))
        current = {
            "city": key[0],
            "site": key[1],
            "longitude": float(row["longitude"]),
            "latitude": float(row["latitude"]),
            "fold": _fold(*key),
        }
        previous = site_rows.get(key)
        if previous is not None and previous != current:
            raise Gate0Stop(f"site geometry/fold changed across seasons: {key}")
        site_rows[key] = current
    nodes = sorted(site_rows.values(), key=lambda row: (str(row["city"]), str(row["site"])))
    site_fold_counts = Counter(int(row["fold"]) for row in nodes)
    if sorted(site_fold_counts) != [1, 2, 3, 4, 5]:
        raise Gate0Stop("frozen site-hash rule did not populate all five folds")

    by_city: dict[str, list[dict[str, object]]] = defaultdict(list)
    for node in nodes:
        by_city[str(node["city"])].append(node)
    pairs: list[tuple[str, str, float]] = []
    for city in sorted(by_city):
        city_nodes = sorted(by_city[city], key=lambda row: str(row["site"]))
        for i, left in enumerate(city_nodes):
            for right in city_nodes[i + 1 :]:
                d = haversine_km(
                    float(left["longitude"]), float(left["latitude"]),
                    float(right["longitude"]), float(right["latitude"]),
                )
                if d <= 0.0 or not math.isfinite(d):
                    raise Gate0Stop(f"nonpositive same-city distance in {city}")
                pairs.append((f"{city}|{left['site']}", f"{city}|{right['site']}", d))
    distances = sorted(d for _, _, d in pairs)
    local_worlds: list[dict[str, object]] = []
    seen_graphs: set[str] = set()
    node_ids = [f"{row['city']}|{row['site']}" for row in nodes]
    for raw_q in contract["response_blind_world_geometry"]["threshold_quantiles"]:
        q = float(raw_q)
        threshold = linear_quantile(distances, q)
        edges = sorted([[a, b] for a, b, d in pairs if d <= threshold])
        graph_fp = canonical_sha256({"node_ids": node_ids, "edge_scope": "same_city_only", "edges": edges})
        if graph_fp in seen_graphs:
            continue
        seen_graphs.add(graph_fp)
        local_worlds.append(
            {
                "world_id": f"same_city_q{int(round(q * 100)):02d}",
                "quantile": q,
                "threshold_km": threshold,
                "edge_count": len(edges),
                "graph_fingerprint": graph_fp,
            }
        )
    minimum = int(contract["response_blind_world_geometry"]["minimum_distinct_positive_local_worlds"])
    if len(local_worlds) < minimum or any(int(row["edge_count"]) <= 0 for row in local_worlds):
        raise Gate0Stop(f"only {len(local_worlds)} distinct positive local worlds; require >= {minimum}")
    return nodes, {
        "same_city_pair_count": len(pairs),
        "distance_sample_fingerprint": canonical_sha256([[a, b, d] for a, b, d in pairs]),
        "local_worlds": local_worlds,
        "external_open": {
            "world_id": "external_open",
            "semantics": "explicit permissive analytical alternative that may bridge metropolitan components",
        },
    }


def derive_baseline(
    candidates: list[dict[str, object]],
    focal_distances: dict[str, float],
    housing_included: bool,
    housing: dict[tuple[str, str], float],
) -> dict[str, object]:
    cities = sorted({str(row["city"]) for row in candidates})
    seasons = sorted({str(row["season"]) for row in candidates})
    numeric = ["longitude", "latitude", "Building_age", "Impervious", "Income", "Ndvi", "Population_density", "Vacancy", "focal_city_range_distance"]
    if housing_included:
        numeric.append("housing_cost_price")
    feature_names = [*numeric, *[f"City__{x}" for x in cities], *[f"Season__{x}" for x in seasons]]
    rows: list[list[object]] = []
    for row in candidates:
        city, season = str(row["city"]), str(row["season"])
        values: list[float] = [
            float(row["longitude"]), float(row["latitude"]), float(row["Building_age"]),
            float(row["Impervious"]), float(row["Income"]), float(row["Ndvi"]),
            float(row["Population_density"]), float(row["Vacancy"]), float(focal_distances[city]),
        ]
        if housing_included:
            values.append(float(housing[(city, season)]))
        values.extend(1.0 if city == x else 0.0 for x in cities)
        values.extend(1.0 if season == x else 0.0 for x in seasons)
        rows.append([city, str(row["site"]), season, *values])
    return {
        "city_categories": cities,
        "season_categories": seasons,
        "numeric_roles": numeric,
        "feature_names": feature_names,
        "row_count": len(rows),
        "matrix_fingerprint": canonical_sha256({"feature_names": feature_names, "rows": rows}),
    }


def evaluate_pre_response(
    safe_payloads: dict[str, bytes],
    contract: dict[str, object],
) -> dict[str, object]:
    coordinates = parse_coordinates(safe_payloads["site_coordinates"], contract)
    focal, focal_distances, in_range_cities, range_counts = parse_range_availability(
        safe_payloads["range_availability"], contract
    )
    candidates = parse_site_covariates(
        safe_payloads["site_covariates"], contract, coordinates, set(in_range_cities)
    )
    candidate_city_seasons = {(str(row["city"]), str(row["season"])) for row in candidates}
    housing_included, housing, housing_reason = parse_housing_cost(
        safe_payloads["housing_cost"], contract, candidate_city_seasons
    )
    nodes, geometry = derive_geometry(candidates, contract)
    baseline = derive_baseline(candidates, focal_distances, housing_included, housing)
    site_season_fold_counts = Counter(_fold(str(row["city"]), str(row["site"])) for row in candidates)
    if sorted(site_season_fold_counts) != [1, 2, 3, 4, 5]:
        raise Gate0Stop("candidate site-seasons do not occupy all five heldout folds")

    candidate_registry_rows = [
        [
            str(row["city"]), str(row["site"]), str(row["season"]),
            float(row["longitude"]), float(row["latitude"]),
            _fold(str(row["city"]), str(row["site"])),
        ]
        for row in candidates
    ]
    node_rows = [
        [str(row["city"]), str(row["site"]), float(row["longitude"]), float(row["latitude"]), int(row["fold"])]
        for row in nodes
    ]
    result: dict[str, object] = {
        "schema": "eog.uwin_multicity_endpoint3.gate0_pre_response.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_pre_response_ready",
        "selected_focal_species": focal,
        "focal_in_range_city_count": len(in_range_cities),
        "focal_in_range_cities": in_range_cities,
        "range_selection_tie_count": sum(count == max(range_counts.values()) for count in range_counts.values()),
        "coordinate_registry_count": len(coordinates),
        "candidate_site_count": len(nodes),
        "candidate_site_season_count": len(candidates),
        "candidate_city_count": len({str(row["city"]) for row in candidates}),
        "candidate_seasons": sorted({str(row["season"]) for row in candidates}),
        "site_fold_counts": {str(k): v for k, v in sorted(Counter(int(row["fold"]) for row in nodes).items())},
        "site_season_fold_counts": {str(k): v for k, v in sorted(site_season_fold_counts.items())},
        "candidate_registry_fingerprint": canonical_sha256(candidate_registry_rows),
        "node_registry_fingerprint": canonical_sha256(node_rows),
        "geometry": geometry,
        "baseline": baseline,
        "housing_cost_included": housing_included,
        "housing_cost_decision": housing_reason,
        "normalized_problem_contract": {
            "node_role": "City|Site with WGS84 coordinates",
            "context_role": "Season",
            "candidate_unit_role": "City|Site|Season",
            "effort_role": "reserved for final J > 0 response gate",
            "response_role": "reserved for final focal Y > 0 versus Y == 0 under J > 0",
            "geometry_role": "same-city world family plus external_open",
            "baseline_role": "response-independent site/context covariates only",
        },
        "safe_file_requests": 4,
        "safe_file_bytes_opened": sum(len(value) for value in safe_payloads.values()),
        "response_file_requests": 0,
        "response_header_bytes_opened": 0,
        "response_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "next_gate": "freeze and execute response physical-header-only gate; do not open a capture-history data row",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def _http_fetch_bytes(url: str, maximum: int) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise Gate0Stop("safe source URL left raw.githubusercontent.com")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            status = getattr(response, "status", None) or response.getcode()
            final = response.geturl()
            headers = {key.lower(): value for key, value in response.headers.items()}
            if status != 200:
                raise Gate0Stop(f"safe file returned HTTP {status}")
            if final != url:
                raise Gate0Stop("safe file request changed frozen URL identity")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate0Stop("safe file unexpectedly used content encoding")
            body = response.read(maximum + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise Gate0Stop(f"safe file transport unavailable: {exc}") from exc
    if len(body) > maximum:
        raise Gate0Stop("safe file exceeded frozen byte cap")
    return body


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    fetch_bytes: ByteFetcher = _http_fetch_bytes,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base: dict[str, object] = {
        "schema": "eog.uwin_multicity_endpoint3.gate0_pre_response.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "safe_file_requests": 0,
        "safe_file_bytes_opened": 0,
        "response_file_requests": 0,
        "response_header_bytes_opened": 0,
        "response_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    payloads: dict[str, bytes] = {}
    requests = 0
    opened = 0
    try:
        safe_files = contract["source"]["safe_files"]
        for role in ("site_coordinates", "site_covariates", "range_availability", "housing_cost"):
            source = safe_files[role]
            raw = fetch_bytes(str(source["raw_url"]), int(source["size_bytes"]))
            requests += 1
            opened += len(raw)
            payloads[role] = raw
        if opened > int(contract["gate0_firewall"]["maximum_safe_file_bytes_total"]):
            raise Gate0Stop("safe-file total exceeded frozen Gate0 byte cap")
        result = {**base, **evaluate_pre_response(payloads, contract)}
        result["safe_file_requests"] = requests
        result["safe_file_bytes_opened"] = opened
        result["fingerprint"] = canonical_sha256({k: v for k, v in result.items() if k != "fingerprint"})
    except Gate0Stop as exc:
        result = {
            **base,
            "safe_file_requests": requests,
            "safe_file_bytes_opened": opened,
            "status": "stop_pre_response_source_registry_or_geometry",
            "reason": str(exc),
            "next_gate": "none; do not open the capture-history response and do not repair this attempt post-STOP",
        }
        result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    run()
