from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

from eog.v2.adequacy_complete_ladder import plan_adequacy_complete_lcc_targets
from eog.v2.world_adequacy import StructuralAdequacyDeclaration
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)
from eog.v2.world_survival_regime_v2 import prepare_world_survival_regime_v2


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "validation" / "world_survival_regime_v2"
PROTOCOL_PATH = BASE / "neon_small_mammal_protocol_v2.json"
ROSTER_PATH = BASE / "neon_small_mammal_roster_lock_v2.json"
OUTPUT_PATH = BASE / "neon_small_mammal_forecast_result_v2.json"

USER_AGENT = "eog-world-survival-regime-v2-metadata/1.0"
TRAP_PATTERN = re.compile(r"^[A-Z0-9]{4}_.+\.mammalGrid\.mam\.[A-Z][0-9]+$")
FORBIDDEN_URL_FRAGMENTS = (
    "/api/v0/data/",
    "/api/v0/data?",
    "/api/v0/data/query",
)


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_json(url: str) -> object:
    if any(fragment in url for fragment in FORBIDDEN_URL_FRAGMENTS):
        raise RuntimeError(f"biological data endpoint forbidden before forecast lock: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def post_graphql(query: str, variables: dict[str, object]) -> object:
    url = "https://data.neonscience.org/graphql"
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def collect_location_names(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        name = value.get("locationName")
        if isinstance(name, str):
            result.add(name)
        for child in value.values():
            result.update(collect_location_names(child))
    elif isinstance(value, list):
        for child in value:
            result.update(collect_location_names(child))
    return result


def fetch_locations(names: list[str]) -> list[dict[str, object]]:
    query = """
    query FindLocations($query: LocationQuery!) {
      locations: findLocations(query: $query) {
        locationName
        locationDescription
        locationType
        domainCode
        siteCode
        locationDecimalLatitude
        locationDecimalLongitude
        locationElevation
      }
    }
    """
    rows: list[dict[str, object]] = []
    for start in range(0, len(names), 500):
        batch = names[start : start + 500]
        payload = post_graphql(query, {"query": {"locationNames": batch}})
        if not isinstance(payload, dict) or payload.get("errors"):
            raise RuntimeError(f"GraphQL location lookup failed: {payload!r}")
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("locations"), list):
            raise RuntimeError("GraphQL location lookup returned unexpected schema")
        rows.extend(row for row in data["locations"] if isinstance(row, dict))
    return rows


def haversine_matrix(latitudes: list[float], longitudes: list[float]) -> np.ndarray:
    lat = np.radians(np.asarray(latitudes, dtype=float))
    lon = np.radians(np.asarray(longitudes, dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    return 6371.0088 * 2.0 * np.arcsin(np.sqrt(a))


def registry_for_site(site_code: str) -> tuple[tuple[str, ...], dict[str, dict[str, object]], str]:
    hierarchy_url = (
        "https://data.neonscience.org/api/v0/locations/"
        f"{site_code}?hierarchy=true"
    )
    hierarchy_payload = get_json(hierarchy_url)
    names = sorted(collect_location_names(hierarchy_payload))
    trap_names = [
        name
        for name in names
        if name.startswith(f"{site_code}_") and TRAP_PATTERN.fullmatch(name)
    ]
    if not trap_names:
        raise RuntimeError(f"{site_code}: no trap names found")

    location_rows = fetch_locations(trap_names)
    by_name: dict[str, dict[str, object]] = {}
    for row in location_rows:
        name = str(row.get("locationName", "")).strip()
        if name not in set(trap_names):
            continue
        try:
            latitude = float(row.get("locationDecimalLatitude"))
            longitude = float(row.get("locationDecimalLongitude"))
        except (TypeError, ValueError) as error:
            raise RuntimeError(f"{site_code}: nonnumeric coordinate for {name}") from error
        if not math.isfinite(latitude) or not math.isfinite(longitude):
            raise RuntimeError(f"{site_code}: nonfinite coordinate for {name}")
        if name in by_name:
            raise RuntimeError(f"{site_code}: duplicate GraphQL location {name}")
        by_name[name] = {
            "locationName": name,
            "latitude": latitude,
            "longitude": longitude,
            "locationType": row.get("locationType"),
            "domainCode": row.get("domainCode"),
            "siteCode": row.get("siteCode"),
        }

    missing = sorted(set(trap_names) - set(by_name))
    if missing:
        raise RuntimeError(f"{site_code}: missing {len(missing)} frozen trap coordinates")
    node_ids = tuple(sorted(by_name))
    fingerprint = canonical_sha256([by_name[node] for node in node_ids])
    return node_ids, by_name, fingerprint


def main() -> int:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))

    site_codes = tuple(protocol["candidate_roster"]["fixed_site_codes"])
    if list(site_codes) != roster["site_order"]:
        raise RuntimeError("protocol site roster differs from response-blind roster lock")

    adequacy_spec = protocol["worlds"]["adequacy"]
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(
            adequacy_spec["min_largest_weak_component_fraction"]
        ),
        max_isolated_node_fraction=float(adequacy_spec["max_isolated_node_fraction"]),
        min_median_horizon_reachable_fraction=None,
        require_at_least_one_world_pass=bool(
            adequacy_spec["require_at_least_one_world_pass"]
        ),
    )

    systems: list[dict[str, object]] = []
    for site_code in site_codes:
        expected_count, expected_fingerprint = roster["site_node_registry"][site_code]
        node_ids, by_name, registry_fingerprint = registry_for_site(site_code)
        if len(node_ids) != int(expected_count):
            systems.append(
                {
                    "site_code": site_code,
                    "status": "pre_response_stop_node_count_drift",
                    "expected_node_count": int(expected_count),
                    "observed_node_count": len(node_ids),
                    "response_opened": False,
                }
            )
            continue
        if registry_fingerprint != expected_fingerprint:
            systems.append(
                {
                    "site_code": site_code,
                    "status": "pre_response_stop_node_registry_fingerprint_drift",
                    "expected_node_registry_fingerprint": expected_fingerprint,
                    "observed_node_registry_fingerprint": registry_fingerprint,
                    "response_opened": False,
                }
            )
            continue

        latitudes = [float(by_name[node]["latitude"]) for node in node_ids]
        longitudes = [float(by_name[node]["longitude"]) for node in node_ids]
        distance_matrix = haversine_matrix(latitudes, longitudes)

        plan = plan_adequacy_complete_lcc_targets(
            len(node_ids),
            tuple(float(value) for value in protocol["worlds"]["base_lcc_targets"]),
            adequacy,
        )
        declaration = StructuralScaleLadderDeclaration(
            axis_id=f"{site_code.lower()}_trap_haversine_km",
            target_largest_component_fractions=plan.completed_targets,
        )
        ladder = build_structural_scale_ladder(
            node_ids,
            distance_matrix,
            declaration,
        )
        adjacencies = structural_scale_adjacencies(ladder, distance_matrix)

        prepared = prepare_world_survival_regime_v2(
            node_ids,
            adjacencies,
            adequacy=adequacy,
            horizon_realization_cutoff=float(protocol["forecast"]["cutoff"]),
        )

        systems.append(
            {
                "site_code": site_code,
                "status": "v2_forecast_locked_response_unopened",
                "node_count": len(node_ids),
                "node_registry_fingerprint": registry_fingerprint,
                "declared_ladder_target_count": len(ladder.levels),
                "distinct_world_count": prepared.deduplication.distinct_world_count,
                "alias_groups": [
                    {
                        "canonical_world_id": row.canonical_world_id,
                        "alias_world_ids": list(row.alias_world_ids),
                        "adjacency_fingerprint": row.adjacency_fingerprint,
                    }
                    for row in prepared.deduplication.alias_groups
                ],
                "deduplication_fingerprint": prepared.deduplication.fingerprint,
                "audit_fingerprint": prepared.audit.fingerprint,
                "gate_fingerprint": prepared.gate.fingerprint,
                "forecast_regime": prepared.forecast.regime,
                "predicted_surviving_world_fraction": (
                    prepared.forecast.predicted_surviving_world_fraction
                ),
                "predicted_surviving_world_ids": list(
                    prepared.forecast.predicted_surviving_world_ids
                ),
                "predicted_failing_world_ids": list(
                    prepared.forecast.predicted_failing_world_ids
                ),
                "structural_rows": [
                    {
                        "world_id": row.world_id,
                        "largest_weak_component_fraction": (
                            row.largest_weak_component_fraction
                        ),
                        "median_one_step_reachable_fraction": (
                            row.median_horizon_reachable_fraction
                        ),
                        "horizon_realization_ratio": row.horizon_realization_ratio,
                        "predicted_survives": row.predicted_survives,
                    }
                    for row in prepared.forecast.structural_rows
                ],
                "forecast_fingerprint": prepared.forecast.fingerprint,
                "preparation_fingerprint": prepared.fingerprint,
                "response_opened": False,
                "biological_response_bytes_opened": 0,
                "model_fits": 0,
            }
        )

    payload: dict[str, object] = {
        "schema": "eog.world_survival_regime.neon_small_mammal.forecast_result.v2",
        "programme": protocol["programme"],
        "generic_protocol_fingerprint": canonical_sha256(
            json.loads(
                (BASE / "protocol_v2.json").read_text(encoding="utf-8")
            )
        ),
        "neon_protocol_fingerprint": canonical_sha256(protocol),
        "roster_lock_fingerprint": canonical_sha256(roster),
        "site_codes": list(site_codes),
        "systems": systems,
        "forecast_locked_system_count": sum(
            row.get("status") == "v2_forecast_locked_response_unopened"
            for row in systems
        ),
        "registry_drift_stop_count": sum(
            str(row.get("status", "")).startswith("pre_response_stop_")
            for row in systems
        ),
        "response_endpoint_requests": 0,
        "biological_response_bytes_opened": 0,
        "model_fits": 0,
    }
    payload["fingerprint"] = canonical_sha256(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as error:
        print(f"HTTP error: {error.code} {error.reason}", file=sys.stderr)
        raise
