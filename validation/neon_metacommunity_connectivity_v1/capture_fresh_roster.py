from __future__ import annotations

import hashlib
import json
import math
import re
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
from eog.v2.world_survival_regime_v2 import deduplicate_structural_worlds


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "validation" / "neon_metacommunity_connectivity_v1"
PROTOCOL_PATH = BASE / "protocol_v1.json"
OUTPUT_PATH = BASE / "fresh_roster_result_v1.json"

USER_AGENT = "eog-neon-metacommunity-connectivity-metadata/1.0"
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
        raise RuntimeError(f"biological response endpoint forbidden during roster capture: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
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
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def collect_site_codes(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        code = value.get("siteCode")
        if isinstance(code, str) and re.fullmatch(r"[A-Z0-9]{4}", code):
            result.add(code)
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


def is_geolocatable_mammal_trap(site_code: str, name: str) -> bool:
    prefix = f"{site_code}_"
    marker = ".mammalGrid.mam."
    if not name.startswith(prefix) or marker not in name:
        return False
    coordinate = name.rsplit(".", 1)[-1].strip().upper()
    if "X" in coordinate:
        return False
    return bool(re.fullmatch(r"[A-Z][0-9]+", coordinate))


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
        f"{urllib.parse.quote(site_code)}?hierarchy=true"
    )
    hierarchy = get_json(hierarchy_url)
    names = sorted(collect_location_names(hierarchy))
    trap_names = [name for name in names if is_geolocatable_mammal_trap(site_code, name)]
    if not trap_names:
        return (), {}, canonical_sha256([])

    location_rows = fetch_locations(trap_names)
    by_name: dict[str, dict[str, object]] = {}
    for row in location_rows:
        name = str(row.get("locationName", "")).strip()
        if name not in set(trap_names):
            continue
        try:
            latitude = float(row.get("locationDecimalLatitude"))
            longitude = float(row.get("locationDecimalLongitude"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(latitude) or not math.isfinite(longitude):
            continue
        if name in by_name:
            raise RuntimeError(f"{site_code}: duplicate location row {name}")
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
        raise RuntimeError(f"{site_code}: {len(missing)} geolocatable trap names lack coordinates")
    node_ids = tuple(sorted(by_name))
    fingerprint = canonical_sha256([by_name[node] for node in node_ids])
    return node_ids, by_name, fingerprint


def target_taxa(protocol: dict[str, object]) -> tuple[list[dict[str, str]], str]:
    taxonomy_url = (
        "https://data.neonscience.org/api/v0/taxonomy?"
        "taxonTypeCode=SMALL_MAMMAL&verbose=true&offset=0&limit=1000"
    )
    payload = get_json(taxonomy_url)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise RuntimeError("taxonomy endpoint returned unexpected schema")
    excluded = {
        str(row["scientific_name"])
        for row in protocol["target_taxa"]["design_contamination_exclusions"]
    }
    taxa: list[dict[str, str]] = []
    for row in payload["data"]:
        if not isinstance(row, dict):
            continue
        if str(row.get("dwc:taxonRank", "")).lower() != "species":
            continue
        if str(row.get("taxonProtocolCategory", "")).lower() != "target":
            continue
        taxon_id = str(row.get("taxonID", "")).strip()
        name = str(row.get("dwc:scientificName", "")).strip()
        if not taxon_id or not name or name in excluded:
            continue
        taxa.append({"taxon_id": taxon_id, "scientific_name": name})
    taxa.sort(key=lambda row: (row["scientific_name"], row["taxon_id"]))
    return taxa, canonical_sha256(payload)


def main() -> int:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    release = str(protocol["data_source"]["release"])
    product = str(protocol["data_source"]["product_code"])

    product_url = (
        "https://data.neonscience.org/api/v0/products/"
        f"{urllib.parse.quote(product)}?release={urllib.parse.quote(release)}"
    )
    product_payload = get_json(product_url)
    site_codes = sorted(collect_site_codes(product_payload))

    excluded = set(protocol["fresh_site_selection"]["excluded_consumed_sites"])
    excluded.update(
        row["site_code"]
        for row in protocol["fresh_site_selection"]["excluded_design_contaminated_sites"]
    )
    candidate_codes = [site for site in site_codes if site not in excluded]

    taxa, taxonomy_fp = target_taxa(protocol)

    adequacy_spec = protocol["world_family"]["adequacy"]
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(
            adequacy_spec["min_largest_weak_component_fraction"]
        ),
        max_isolated_node_fraction=float(adequacy_spec["max_isolated_node_fraction"]),
        min_median_horizon_reachable_fraction=None,
        require_at_least_one_world_pass=True,
    )

    target_count = int(protocol["fresh_site_selection"]["target_site_count"])
    minimum_nodes = int(protocol["node_registry"]["minimum_nodes"])
    selected: list[dict[str, object]] = []
    stops: list[dict[str, object]] = []

    for site_code in candidate_codes:
        if len(selected) >= target_count:
            break
        try:
            node_ids, by_name, registry_fp = registry_for_site(site_code)
        except Exception as error:
            stops.append({
                "site_code": site_code,
                "status": "pre_response_metadata_stop",
                "detail": f"{type(error).__name__}: {error}",
            })
            continue

        if len(node_ids) < minimum_nodes:
            stops.append({
                "site_code": site_code,
                "status": "pre_response_insufficient_geolocatable_traps",
                "node_count": len(node_ids),
            })
            continue

        latitudes = [float(by_name[node]["latitude"]) for node in node_ids]
        longitudes = [float(by_name[node]["longitude"]) for node in node_ids]
        distances = haversine_matrix(latitudes, longitudes)

        plan = plan_adequacy_complete_lcc_targets(
            len(node_ids),
            tuple(float(v) for v in protocol["world_family"]["base_lcc_targets"]),
            adequacy,
        )
        declaration = StructuralScaleLadderDeclaration(
            axis_id=f"{site_code.lower()}_trap_haversine_km",
            target_largest_component_fractions=plan.completed_targets,
        )
        ladder = build_structural_scale_ladder(node_ids, distances, declaration)
        adjacencies = structural_scale_adjacencies(ladder, distances)
        dedup = deduplicate_structural_worlds(adjacencies)
        audit = audit_world_universe_structure(
            node_ids,
            dedup.world_adjacencies,
            horizon=1,
        )
        gate = apply_structural_adequacy_gate(audit, adequacy)
        if not gate.passed:
            stops.append({
                "site_code": site_code,
                "status": "pre_response_structural_adequacy_stop",
                "node_count": len(node_ids),
                "audit_fingerprint": audit.fingerprint,
                "gate_fingerprint": gate.fingerprint,
            })
            continue

        selected.append({
            "site_code": site_code,
            "node_count": len(node_ids),
            "node_registry_fingerprint": registry_fp,
            "node_ids": list(node_ids),
            "completed_lcc_targets": list(plan.completed_targets),
            "declared_world_count": dedup.declared_world_count,
            "distinct_world_count": dedup.distinct_world_count,
            "deduplication_fingerprint": dedup.fingerprint,
            "alias_groups": [
                {
                    "canonical_world_id": row.canonical_world_id,
                    "alias_world_ids": list(row.alias_world_ids),
                    "adjacency_fingerprint": row.adjacency_fingerprint,
                }
                for row in dedup.alias_groups
            ],
            "audit_fingerprint": audit.fingerprint,
            "gate_fingerprint": gate.fingerprint,
            "world_universe_fingerprint": canonical_sha256({
                "deduplication_fingerprint": dedup.fingerprint,
                "audit_fingerprint": audit.fingerprint,
                "gate_fingerprint": gate.fingerprint,
                "horizon": 1,
            }),
        })

    payload: dict[str, object] = {
        "schema":"eog.neon_metacommunity_connectivity.fresh_roster.v1",
        "programme":protocol["programme"],
        "product_code":product,
        "release":release,
        "product_metadata_fingerprint":canonical_sha256(product_payload),
        "taxonomy_metadata_fingerprint":taxonomy_fp,
        "eligible_target_taxon_count":len(taxa),
        "eligible_target_taxa":taxa,
        "available_site_count":len(site_codes),
        "candidate_site_count_after_exclusions":len(candidate_codes),
        "selected_site_count":len(selected),
        "selected_site_codes":[row["site_code"] for row in selected],
        "selected_sites":selected,
        "pre_response_stops":stops,
        "response_endpoint_requests":0,
        "biological_response_bytes_opened":0,
        "model_fits":0,
    }
    if len(selected) != target_count:
        payload["status"] = "terminal_pre_response_insufficient_fresh_sites"
    else:
        payload["status"] = "fresh_roster_locked_response_unopened"
    payload["fingerprint"] = canonical_sha256(payload)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if len(selected) == target_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
