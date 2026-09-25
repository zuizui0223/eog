from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

from eog.v2.adequacy_complete_ladder import plan_adequacy_complete_lcc_targets
from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)
from eog.v2.world_survival_regime import (
    RegimeForecastDeclaration,
    forecast_world_survival_regime,
)


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "validation" / "world_survival_regime_v1"
PROTOCOL_PATH = BASE / "neon_small_mammal_protocol_v1.json"
OUTPUT_PATH = BASE / "neon_small_mammal_metadata_capture_result_v1.json"

USER_AGENT = "eog-world-survival-regime-metadata/1.0"
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


def collect_site_codes(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        site = value.get("siteCode")
        if isinstance(site, str) and re.fullmatch(r"[A-Z0-9]{4}", site):
            result.add(site)
        for child in value.values():
            result.update(collect_site_codes(child))
    elif isinstance(value, list):
        for child in value:
            result.update(collect_site_codes(child))
    return result


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


def main() -> int:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    source = protocol["source"]
    release = str(source["release"])
    product_code = str(source["product_code"])
    max_sites = int(protocol["candidate_sites"]["maximum_sites"])
    minimum_nodes = int(protocol["node_registry"]["minimum_nodes"])

    product_url = (
        "https://data.neonscience.org/api/v0/products/"
        f"{urllib.parse.quote(product_code)}?release={urllib.parse.quote(release)}"
    )
    taxonomy_url = (
        "https://data.neonscience.org/api/v0/taxonomy?"
        "taxonTypeCode=SMALL_MAMMAL&verbose=true&offset=0&limit=1000"
    )

    product_payload = get_json(product_url)
    taxonomy_payload = get_json(taxonomy_url)

    site_codes = sorted(collect_site_codes(product_payload))
    selected_sites = site_codes[:max_sites]
    if not selected_sites:
        raise RuntimeError("product metadata yielded no site codes")

    if not isinstance(taxonomy_payload, dict) or not isinstance(
        taxonomy_payload.get("data"), list
    ):
        raise RuntimeError("taxonomy endpoint returned unexpected schema")

    excluded_names = {
        row["scientific_name"]
        for row in protocol["response_target"]["design_contamination_exclusions"]
    }
    target_taxa: list[dict[str, str]] = []
    for row in taxonomy_payload["data"]:
        if not isinstance(row, dict):
            continue
        if str(row.get("dwc:taxonRank", "")).lower() != "species":
            continue
        if str(row.get("taxonProtocolCategory", "")).lower() != "target":
            continue
        name = str(row.get("dwc:scientificName", "")).strip()
        taxon_id = str(row.get("taxonID", "")).strip()
        if not name or not taxon_id or name in excluded_names:
            continue
        target_taxa.append({"taxon_id": taxon_id, "scientific_name": name})
    target_taxa.sort(key=lambda row: (row["scientific_name"], row["taxon_id"]))
    if not target_taxa:
        raise RuntimeError("no eligible target small-mammal taxa remained")

    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.90,
        max_isolated_node_fraction=0.05,
        min_median_horizon_reachable_fraction=None,
        require_at_least_one_world_pass=True,
    )

    systems: list[dict[str, object]] = []
    for site_code in selected_sites:
        site_url = (
            "https://data.neonscience.org/api/v0/sites/"
            f"{urllib.parse.quote(site_code)}?release={urllib.parse.quote(release)}"
        )
        hierarchy_url = (
            "https://data.neonscience.org/api/v0/locations/"
            f"{urllib.parse.quote(site_code)}?hierarchy=true"
        )
        site_payload = get_json(site_url)
        hierarchy_payload = get_json(hierarchy_url)
        all_names = sorted(collect_location_names(hierarchy_payload))
        trap_names = [
            name for name in all_names
            if name.startswith(f"{site_code}_") and TRAP_PATTERN.fullmatch(name)
        ]

        system: dict[str, object] = {
            "site_code": site_code,
            "site_metadata_fingerprint": canonical_sha256(site_payload),
            "location_hierarchy_fingerprint": canonical_sha256(hierarchy_payload),
            "discovered_trap_name_count": len(trap_names),
            "response_opened": False,
            "model_fits": 0,
        }
        if len(trap_names) < minimum_nodes:
            system["status"] = "pre_response_stop_insufficient_trap_registry"
            systems.append(system)
            continue

        location_rows = fetch_locations(trap_names)
        by_name: dict[str, dict[str, object]] = {}
        invalid_names: list[str] = []
        for row in location_rows:
            name = str(row.get("locationName", "")).strip()
            try:
                latitude = float(row.get("locationDecimalLatitude"))
                longitude = float(row.get("locationDecimalLongitude"))
            except (TypeError, ValueError):
                invalid_names.append(name)
                continue
            if not math.isfinite(latitude) or not math.isfinite(longitude):
                invalid_names.append(name)
                continue
            if name in by_name:
                invalid_names.append(name)
                continue
            by_name[name] = {
                "locationName": name,
                "latitude": latitude,
                "longitude": longitude,
                "locationType": row.get("locationType"),
                "domainCode": row.get("domainCode"),
                "siteCode": row.get("siteCode"),
            }

        missing_names = sorted(set(trap_names) - set(by_name))
        if invalid_names or missing_names or len(by_name) < minimum_nodes:
            system.update(
                {
                    "status": "pre_response_stop_invalid_or_incomplete_trap_coordinates",
                    "invalid_location_names": sorted(set(invalid_names)),
                    "missing_location_names": missing_names,
                    "valid_node_count": len(by_name),
                }
            )
            systems.append(system)
            continue

        node_ids = tuple(sorted(by_name))
        latitudes = [float(by_name[node]["latitude"]) for node in node_ids]
        longitudes = [float(by_name[node]["longitude"]) for node in node_ids]
        distance_matrix = haversine_matrix(latitudes, longitudes)

        plan = plan_adequacy_complete_lcc_targets(
            len(node_ids),
            tuple(float(v) for v in protocol["worlds"]["base_lcc_targets"]),
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
        audit = audit_world_universe_structure(
            node_ids,
            adjacencies,
            horizon=len(node_ids) - 1,
        )
        gate = apply_structural_adequacy_gate(audit, adequacy)
        if not gate.passed:
            system.update(
                {
                    "status": "pre_response_stop_structural_adequacy",
                    "node_count": len(node_ids),
                    "ladder_fingerprint": ladder.fingerprint,
                    "audit_fingerprint": audit.fingerprint,
                    "gate_fingerprint": gate.fingerprint,
                    "passing_world_ids": list(gate.passing_world_ids),
                }
            )
            systems.append(system)
            continue

        forecast = forecast_world_survival_regime(
            audit,
            gate,
            RegimeForecastDeclaration(horizon_realization_cutoff=0.5),
        )
        system.update(
            {
                "status": "forecast_locked_response_unopened",
                "node_count": len(node_ids),
                "node_registry_fingerprint": canonical_sha256(
                    [by_name[node] for node in node_ids]
                ),
                "node_ids": list(node_ids),
                "ladder_targets": list(plan.completed_targets),
                "ladder_levels": [
                    {
                        "world_id": row.level_id,
                        "target_lcc_fraction": row.target_largest_component_fraction,
                        "distance_threshold_km": row.distance_threshold,
                        "achieved_lcc_fraction": row.achieved_largest_component_fraction,
                        "isolated_node_fraction": row.isolated_node_fraction,
                    }
                    for row in ladder.levels
                ],
                "ladder_fingerprint": ladder.fingerprint,
                "audit_fingerprint": audit.fingerprint,
                "gate_fingerprint": gate.fingerprint,
                "forecast_regime": forecast.regime,
                "predicted_surviving_world_fraction": (
                    forecast.predicted_surviving_world_fraction
                ),
                "predicted_surviving_world_ids": list(
                    forecast.predicted_surviving_world_ids
                ),
                "forecast_fingerprint": forecast.fingerprint,
            }
        )
        systems.append(system)

    payload: dict[str, object] = {
        "schema": "eog.world_survival_regime.neon_small_mammal.metadata_capture.v1",
        "programme": protocol["programme"],
        "protocol_fingerprint": canonical_sha256(protocol),
        "product_code": product_code,
        "release": release,
        "product_metadata_fingerprint": canonical_sha256(product_payload),
        "taxonomy_metadata_fingerprint": canonical_sha256(taxonomy_payload),
        "available_site_count": len(site_codes),
        "selected_site_codes": selected_sites,
        "eligible_target_taxon_count": len(target_taxa),
        "eligible_target_taxa": target_taxa,
        "design_contamination_exclusions": sorted(excluded_names),
        "systems": systems,
        "response_endpoint_requests": 0,
        "biological_response_bytes_opened": 0,
        "model_fits": 0,
    }
    payload["forecast_locked_system_count"] = sum(
        row.get("status") == "forecast_locked_response_unopened" for row in systems
    )
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
