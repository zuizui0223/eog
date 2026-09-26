from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

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
PROTOCOL_PATH = BASE / "neon_small_mammal_response_protocol_v2_1.json"
PROTOCOL_LOCK_PATH = BASE / "neon_small_mammal_response_protocol_lock_v2_1.json"
NEON_PROTOCOL_PATH = BASE / "neon_small_mammal_protocol_v2.json"
ROSTER_PATH = BASE / "neon_small_mammal_roster_lock_v2.json"
FORECAST_LOCK_PATH = BASE / "neon_small_mammal_forecast_lock_v2.json"
OUTPUT_PATH = BASE / "neon_small_mammal_response_result_v2_3.json"

USER_AGENT = "eog-world-survival-regime-v2-response/1.0"
TOKEN_ENV = "NEON_API_TOKEN"
DATA_QUERY_URL = "https://data.neonscience.org/api/v0/data/query"
TAXONOMY_URL = (
    "https://data.neonscience.org/api/v0/taxonomy?"
    "taxonTypeCode=SMALL_MAMMAL&verbose=true&offset=0&limit=1000"
)
TRAP_PATTERN = re.compile(r"^[A-Z0-9]{4}_.+\.mammalGrid\.mam\.[A-Z][0-9]+$")


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def get_json(url: str) -> object:
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


def registry_for_site(
    site_code: str,
) -> tuple[tuple[str, ...], dict[str, dict[str, object]], str]:
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
    trap_set = set(trap_names)
    for row in location_rows:
        name = str(row.get("locationName", "")).strip()
        if name not in trap_set:
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

    missing = sorted(trap_set - set(by_name))
    if missing:
        raise RuntimeError(f"{site_code}: missing {len(missing)} frozen trap coordinates")
    node_ids = tuple(sorted(by_name))
    fingerprint = canonical_sha256([by_name[node] for node in node_ids])
    return node_ids, by_name, fingerprint


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


def frozen_site_geometry(
    site_code: str,
    *,
    neon_protocol: dict[str, Any],
    roster: dict[str, Any],
    forecast_lock: dict[str, Any],
) -> dict[str, Any]:
    expected_count, expected_fingerprint = roster["site_node_registry"][site_code]
    node_ids, by_name, registry_fingerprint = registry_for_site(site_code)
    if len(node_ids) != int(expected_count):
        raise RuntimeError(
            f"{site_code}: node count drift before response "
            f"({len(node_ids)} != {expected_count})"
        )
    if registry_fingerprint != expected_fingerprint:
        raise RuntimeError(f"{site_code}: node registry fingerprint drift before response")

    latitudes = [float(by_name[node]["latitude"]) for node in node_ids]
    longitudes = [float(by_name[node]["longitude"]) for node in node_ids]
    distance_matrix = haversine_matrix(latitudes, longitudes)

    adequacy_spec = neon_protocol["worlds"]["adequacy"]
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(
            adequacy_spec["min_largest_weak_component_fraction"]
        ),
        max_isolated_node_fraction=float(
            adequacy_spec["max_isolated_node_fraction"]
        ),
        min_median_horizon_reachable_fraction=None,
        require_at_least_one_world_pass=bool(
            adequacy_spec["require_at_least_one_world_pass"]
        ),
    )
    plan = plan_adequacy_complete_lcc_targets(
        len(node_ids),
        tuple(float(value) for value in neon_protocol["worlds"]["base_lcc_targets"]),
        adequacy,
    )
    declaration = StructuralScaleLadderDeclaration(
        axis_id=f"{site_code.lower()}_trap_haversine_km",
        target_largest_component_fractions=plan.completed_targets,
    )
    ladder = build_structural_scale_ladder(node_ids, distance_matrix, declaration)
    adjacencies = structural_scale_adjacencies(ladder, distance_matrix)
    prepared = prepare_world_survival_regime_v2(
        node_ids,
        adjacencies,
        adequacy=adequacy,
        horizon_realization_cutoff=float(neon_protocol["forecast"]["cutoff"]),
    )

    forecast_rows = {
        str(row[0]): row
        for row in forecast_lock["systems"]
    }
    locked = forecast_rows[site_code]
    if int(locked[1]) != prepared.deduplication.distinct_world_count:
        raise RuntimeError(f"{site_code}: distinct-world count differs from forecast lock")
    if str(locked[2]) != prepared.forecast.regime:
        raise RuntimeError(f"{site_code}: forecast regime differs from forecast lock")
    if not math.isclose(
        float(locked[3]),
        prepared.forecast.predicted_surviving_world_fraction,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        raise RuntimeError(f"{site_code}: forecast fraction differs from forecast lock")
    if str(locked[4]) != prepared.forecast.fingerprint:
        raise RuntimeError(f"{site_code}: forecast fingerprint differs from forecast lock")

    return {
        "site_code": site_code,
        "node_ids": node_ids,
        "node_index": {node_id: index for index, node_id in enumerate(node_ids)},
        "registry_fingerprint": registry_fingerprint,
        "canonical_worlds": {
            world_id: np.asarray(adjacency, dtype=bool)
            for world_id, adjacency in prepared.deduplication.world_adjacencies.items()
        },
        "alias_groups": [
            {
                "canonical_world_id": row.canonical_world_id,
                "alias_world_ids": list(row.alias_world_ids),
                "adjacency_fingerprint": row.adjacency_fingerprint,
            }
            for row in prepared.deduplication.alias_groups
        ],
        "forecast_regime": prepared.forecast.regime,
        "forecast_fraction": prepared.forecast.predicted_surviving_world_fraction,
        "forecast_fingerprint": prepared.forecast.fingerprint,
        "preparation_fingerprint": prepared.fingerprint,
    }


def validate_response_protocol_contract(protocol: dict[str, Any]) -> None:
    required_top = {
        "schema",
        "programme",
        "state",
        "unchanged",
        "authentication",
        "response_query",
        "file_selection",
        "required_columns",
        "row_semantics",
        "site_estimability",
        "observed_world_rule",
        "scoring",
        "integrity",
    }
    missing_top = sorted(required_top - set(protocol))
    if missing_top:
        raise RuntimeError(
            f"response protocol missing required top-level keys: {missing_top}"
        )

    unchanged = protocol["unchanged"]
    if not isinstance(unchanged, dict):
        raise RuntimeError("response protocol unchanged block must be an object")
    required_unchanged = {
        "prerequisite_forecast_result_fingerprint",
        "fixed_site_codes",
        "forecast_regime_counts",
        "productCode",
        "release",
        "package",
        "target_taxonomy_fingerprint",
        "target_taxon_count",
        "target_exclusions",
        "compatibility_max_steps",
        "source_policy",
        "survival_denominator",
    }
    missing_unchanged = sorted(required_unchanged - set(unchanged))
    if missing_unchanged:
        raise RuntimeError(
            f"response protocol unchanged block missing keys: {missing_unchanged}"
        )

    query = protocol["response_query"]
    if not isinstance(query, dict) or not isinstance(query.get("body"), dict):
        raise RuntimeError("response protocol response_query.body must be an object")
    body = query["body"]
    if body.get("siteCodes") != unchanged["fixed_site_codes"]:
        raise RuntimeError("response query siteCodes differ from frozen unchanged site list")
    if body.get("productCode") != unchanged["productCode"]:
        raise RuntimeError("response query productCode differs from frozen unchanged value")
    if body.get("release") != unchanged["release"]:
        raise RuntimeError("response query release differs from frozen unchanged value")
    if body.get("package") != unchanged["package"]:
        raise RuntimeError("response query package differs from frozen unchanged value")

    if int(unchanged["compatibility_max_steps"]) != 1:
        raise RuntimeError("v2.1 response protocol compatibility_max_steps must equal 1")
    if protocol["required_columns"] != [
        "namedLocation",
        "trapCoordinate",
        "trapStatus",
        "taxonID",
    ]:
        raise RuntimeError("response protocol required_columns drifted")


def eligible_target_taxa(protocol: dict[str, Any]) -> tuple[set[str], dict[str, str], str]:
    unchanged = protocol["unchanged"]
    taxonomy_payload = get_json(TAXONOMY_URL)
    taxonomy_fp = canonical_sha256(taxonomy_payload)
    expected_fp = str(unchanged["target_taxonomy_fingerprint"])
    if taxonomy_fp != expected_fp:
        raise RuntimeError("taxonomy metadata fingerprint drift before response query")
    if not isinstance(taxonomy_payload, dict) or not isinstance(
        taxonomy_payload.get("data"), list
    ):
        raise RuntimeError("taxonomy endpoint returned unexpected schema")

    exclusions = set(str(value) for value in unchanged["target_exclusions"])
    ids: set[str] = set()
    names: dict[str, str] = {}
    for row in taxonomy_payload["data"]:
        if not isinstance(row, dict):
            continue
        if str(row.get("dwc:taxonRank", "")).lower() != "species":
            continue
        if str(row.get("taxonProtocolCategory", "")).lower() != "target":
            continue
        scientific_name = str(row.get("dwc:scientificName", "")).strip()
        taxon_id = str(row.get("taxonID", "")).strip()
        if not scientific_name or not taxon_id or scientific_name in exclusions:
            continue
        ids.add(taxon_id)
        names[taxon_id] = scientific_name

    expected_count = int(unchanged["target_taxon_count"])
    if len(ids) != expected_count:
        raise RuntimeError(
            f"eligible target-taxon count drift before response query "
            f"({len(ids)} != {expected_count})"
        )
    return ids, names, taxonomy_fp


def post_data_query(
    body: dict[str, Any],
    token: str,
    counters: dict[str, int],
) -> dict[str, Any]:
    raw_body = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        DATA_QUERY_URL,
        data=raw_body,
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "X-API-Token": token,
        },
    )
    counters["response_endpoint_requests"] += 1
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
    counters["response_query_bytes_opened"] += len(raw)
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise RuntimeError("NEON data query returned unexpected schema")
    return payload


def response_file_inventory(
    query_payload: dict[str, Any],
    fixed_sites: tuple[str, ...],
) -> list[dict[str, Any]]:
    data = query_payload["data"]
    if str(data.get("productCode", "")) != "DP1.10072.001":
        raise RuntimeError("data query productCode drift")
    returned_sites = tuple(str(value) for value in data.get("siteCodes", []))
    if set(returned_sites) - set(fixed_sites):
        raise RuntimeError("data query returned an undeclared site")

    releases = data.get("releases")
    if not isinstance(releases, list):
        raise RuntimeError("data query releases field is missing")
    matching = [
        row
        for row in releases
        if isinstance(row, dict) and row.get("release") == "RELEASE-2026"
    ]
    if len(matching) != 1:
        raise RuntimeError("data query did not return exactly one RELEASE-2026 block")

    inventory: dict[tuple[str, str, str], dict[str, Any]] = {}
    for package in matching[0].get("packages", []):
        if not isinstance(package, dict):
            continue
        site_code = str(package.get("siteCode", ""))
        month = str(package.get("month", ""))
        if site_code not in fixed_sites:
            raise RuntimeError(f"undeclared site in package inventory: {site_code}")
        if str(package.get("packageType", "")) != "basic":
            raise RuntimeError("data query returned non-basic package")
        files = package.get("files")
        if not isinstance(files, list):
            raise RuntimeError("package files field is missing")
        for row in files:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", ""))
            if "mam_pertrapnight" not in name or not name.lower().endswith(".csv"):
                continue
            md5 = str(row.get("md5", "")).lower()
            url = str(row.get("url", ""))
            size = row.get("size")
            if not re.fullmatch(r"[0-9a-f]{32}", md5):
                raise RuntimeError(f"missing/invalid MD5 for {site_code}/{month}/{name}")
            if not url.startswith("https://"):
                raise RuntimeError(f"invalid response file URL for {name}")
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise RuntimeError(f"invalid response file size for {name}")
            key = (site_code, month, name)
            normalized = {
                "site_code": site_code,
                "month": month,
                "name": name,
                "size": size,
                "md5": md5,
                "url": url,
            }
            if key in inventory and inventory[key] != normalized:
                raise RuntimeError(f"conflicting duplicate response file inventory: {key}")
            inventory[key] = normalized

    rows = [inventory[key] for key in sorted(inventory)]
    if not rows:
        raise RuntimeError("data query returned no mam_pertrapnight CSV files")
    return rows


def download_bytes(
    row: dict[str, Any],
    token: str,
    counters: dict[str, int],
) -> bytes:
    request = urllib.request.Request(
        str(row["url"]),
        headers={
            "User-Agent": USER_AGENT,
            "X-API-Token": token,
        },
    )
    counters["response_file_requests"] += 1
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read()
    counters["biological_response_bytes_opened"] += len(raw)
    if len(raw) != int(row["size"]):
        raise RuntimeError(
            f"response file byte size mismatch for {row['name']}: "
            f"{len(raw)} != {row['size']}"
        )
    observed_md5 = hashlib.md5(raw).hexdigest()
    if observed_md5 != row["md5"]:
        raise RuntimeError(
            f"response file MD5 mismatch for {row['name']}: "
            f"{observed_md5} != {row['md5']}"
        )
    return raw


def update_positive_nodes(
    *,
    raw: bytes,
    row: dict[str, Any],
    target_taxon_ids: set[str],
    geometries: dict[str, dict[str, Any]],
    positive_nodes: dict[str, set[str]],
    unknown_positive_nodes: dict[str, set[str]],
    row_counts: dict[str, int],
) -> None:
    site_code = str(row["site_code"])
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"non-UTF8 response CSV: {row['name']}") from error
    reader = csv.DictReader(io.StringIO(text))
    expected = {"namedLocation", "trapCoordinate", "trapStatus", "taxonID"}
    if reader.fieldnames is None or not expected.issubset(set(reader.fieldnames)):
        raise RuntimeError(
            f"response CSV missing frozen required columns in {row['name']}: "
            f"{reader.fieldnames}"
        )

    node_set = set(geometries[site_code]["node_ids"])
    for record in reader:
        row_counts[site_code] += 1
        trap_status = str(record.get("trapStatus", "")).strip().lower()
        if "capture" not in trap_status or "no capture" in trap_status:
            continue
        taxon_id = str(record.get("taxonID", "")).strip()
        if taxon_id not in target_taxon_ids:
            continue
        named_location = str(record.get("namedLocation", "")).strip()
        trap_coordinate = str(record.get("trapCoordinate", "")).strip()
        if not named_location or not trap_coordinate:
            unknown_positive_nodes[site_code].add(
                f"{named_location}.{trap_coordinate}"
            )
            continue
        node_key = f"{named_location}.{trap_coordinate}"
        if node_key not in node_set:
            unknown_positive_nodes[site_code].add(node_key)
            continue
        positive_nodes[site_code].add(node_key)


def observed_site_result(
    geometry: dict[str, Any],
    positive_nodes: set[str],
) -> dict[str, Any]:
    site_code = str(geometry["site_code"])
    if len(positive_nodes) < 2:
        return {
            "site_code": site_code,
            "status": "response_consumed_non_estimable_positive_support",
            "ever_positive_node_count": len(positive_nodes),
            "forecast_regime": geometry["forecast_regime"],
            "forecast_survival_fraction": geometry["forecast_fraction"],
            "counts_as_scored_system": False,
        }

    indices = np.asarray(
        [geometry["node_index"][node_id] for node_id in sorted(positive_nodes)],
        dtype=int,
    )
    surviving: list[str] = []
    failing: list[str] = []
    for world_id in sorted(geometry["canonical_worlds"]):
        adjacency = geometry["canonical_worlds"][world_id]
        world_survives = True
        for target_index in indices:
            peer_indices = indices[indices != target_index]
            if peer_indices.size == 0 or not bool(
                np.any(adjacency[target_index, peer_indices])
            ):
                world_survives = False
                break
        if world_survives:
            surviving.append(world_id)
        else:
            failing.append(world_id)

    distinct_world_count = len(geometry["canonical_worlds"])
    fraction = len(surviving) / distinct_world_count
    if len(surviving) == 0:
        regime = "falsified_universe"
    elif len(surviving) == distinct_world_count:
        regime = "saturated"
    else:
        regime = "contracting"

    forecast_fraction = float(geometry["forecast_fraction"])
    forecast_regime = str(geometry["forecast_regime"])
    result: dict[str, Any] = {
        "site_code": site_code,
        "status": "scored_world_survival_regime",
        "counts_as_scored_system": True,
        "ever_positive_node_count": len(positive_nodes),
        "ever_positive_node_ids": sorted(positive_nodes),
        "distinct_world_count": distinct_world_count,
        "surviving_world_ids": surviving,
        "failing_world_ids": failing,
        "observed_survival_fraction": fraction,
        "observed_regime": regime,
        "forecast_survival_fraction": forecast_fraction,
        "forecast_regime": forecast_regime,
        "exact_regime_match": regime == forecast_regime,
        "absolute_survival_fraction_error": abs(fraction - forecast_fraction),
        "forecast_fingerprint": geometry["forecast_fingerprint"],
        "preparation_fingerprint": geometry["preparation_fingerprint"],
        "alias_groups": geometry["alias_groups"],
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_payload(
    *,
    protocol: dict[str, Any],
    forecast_lock: dict[str, Any],
    counters: dict[str, int],
    status: str,
    failure_stage: str | None,
    failure_detail: str | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "eog.world_survival_regime.neon_small_mammal.response_result.v2_3",
        "programme": protocol["programme"],
        "status": status,
        "failure_stage": failure_stage,
        "failure_detail": failure_detail,
        "forecast_lock_result_fingerprint": (
            forecast_lock["result_fingerprint"]
        ),
        "forecast_regime_counts": forecast_lock["regime_counts"],
        **counters,
        "model_fits": 0,
        "rerun_authorized": False,
    }
    if extra:
        payload.update(extra)
    payload["fingerprint"] = canonical_sha256(payload)
    return payload


def main() -> int:
    response_protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    response_lock = json.loads(PROTOCOL_LOCK_PATH.read_text(encoding="utf-8"))
    neon_protocol = json.loads(NEON_PROTOCOL_PATH.read_text(encoding="utf-8"))
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    forecast_lock = json.loads(FORECAST_LOCK_PATH.read_text(encoding="utf-8"))

    counters = {
        "response_endpoint_requests": 0,
        "response_query_bytes_opened": 0,
        "response_file_requests": 0,
        "biological_response_bytes_opened": 0,
    }
    response_consumed = False
    query_payload: dict[str, Any] | None = None
    inventory: list[dict[str, Any]] = []
    try:
        if git_blob_sha1(PROTOCOL_PATH) != response_lock["protocol_git_blob_sha1"]:
            raise RuntimeError("response protocol blob differs from response protocol lock")
        if (
            forecast_lock["result_fingerprint"]
            != response_protocol["unchanged"]["prerequisite_forecast_result_fingerprint"]
        ):
            raise RuntimeError("forecast lock prerequisite fingerprint mismatch")
        if forecast_lock["response_endpoint_requests"] != 0:
            raise RuntimeError("forecast lock already records response access")

        validate_response_protocol_contract(response_protocol)
        target_taxon_ids, target_taxon_names, taxonomy_fp = eligible_target_taxa(
            response_protocol
        )
        fixed_sites = tuple(response_protocol["response_query"]["body"]["siteCodes"])
        if list(fixed_sites) != roster["site_order"]:
            raise RuntimeError("response protocol site order differs from frozen roster")

        geometries: dict[str, dict[str, Any]] = {}
        for site_code in fixed_sites:
            geometries[site_code] = frozen_site_geometry(
                site_code,
                neon_protocol=neon_protocol,
                roster=roster,
                forecast_lock=forecast_lock,
            )

        token = os.environ.get(TOKEN_ENV, "").strip()
        if not token:
            payload = terminal_payload(
                protocol=response_protocol,
                forecast_lock=forecast_lock,
                counters=counters,
                status="terminal_no_access_missing_neon_api_token",
                failure_stage="authentication",
                failure_detail=f"{TOKEN_ENV} is empty; no biological response request was made",
                extra={
                    "taxonomy_metadata_fingerprint": taxonomy_fp,
                    "eligible_target_taxon_count": len(target_taxon_ids),
                    "verified_geometry_site_count": len(geometries),
                },
            )
            OUTPUT_PATH.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return 2

        query_payload = post_data_query(
            dict(response_protocol["response_query"]["body"]),
            token,
            counters,
        )
        response_consumed = True
        inventory = response_file_inventory(query_payload, fixed_sites)

        positive_nodes = {site: set() for site in fixed_sites}
        unknown_positive_nodes = {site: set() for site in fixed_sites}
        row_counts = {site: 0 for site in fixed_sites}
        file_receipts: list[dict[str, Any]] = []
        for row in inventory:
            raw = download_bytes(row, token, counters)
            update_positive_nodes(
                raw=raw,
                row=row,
                target_taxon_ids=target_taxon_ids,
                geometries=geometries,
                positive_nodes=positive_nodes,
                unknown_positive_nodes=unknown_positive_nodes,
                row_counts=row_counts,
            )
            file_receipts.append(
                {
                    "site_code": row["site_code"],
                    "month": row["month"],
                    "name": row["name"],
                    "size": row["size"],
                    "md5": row["md5"],
                }
            )

        site_results: list[dict[str, Any]] = []
        for site_code in fixed_sites:
            unknown = sorted(unknown_positive_nodes[site_code])
            if unknown:
                site_results.append(
                    {
                        "site_code": site_code,
                        "status": "response_consumed_registry_mismatch_unknown_positive_node",
                        "counts_as_scored_system": False,
                        "unknown_positive_node_count": len(unknown),
                        "unknown_positive_node_ids": unknown,
                        "ever_positive_known_node_count": len(
                            positive_nodes[site_code]
                        ),
                        "forecast_regime": geometries[site_code]["forecast_regime"],
                        "forecast_survival_fraction": geometries[site_code]["forecast_fraction"],
                    }
                )
                continue
            site_results.append(
                observed_site_result(
                    geometries[site_code],
                    positive_nodes[site_code],
                )
            )

        scored = [row for row in site_results if row["counts_as_scored_system"]]
        exact_matches = sum(bool(row["exact_regime_match"]) for row in scored)
        exact_match_fraction = (
            exact_matches / len(scored) if scored else None
        )
        mae = (
            float(
                np.mean(
                    [
                        float(row["absolute_survival_fraction_error"])
                        for row in scored
                    ]
                )
            )
            if scored
            else None
        )
        observed_counts = {
            "falsified_universe": sum(
                row.get("observed_regime") == "falsified_universe" for row in scored
            ),
            "contracting": sum(
                row.get("observed_regime") == "contracting" for row in scored
            ),
            "saturated": sum(
                row.get("observed_regime") == "saturated" for row in scored
            ),
        }
        terminal = "completed_scored_regime_programme" if scored else (
            "response_consumed_no_estimable_sites"
        )
        payload = terminal_payload(
            protocol=response_protocol,
            forecast_lock=forecast_lock,
            counters=counters,
            status=terminal,
            failure_stage=None,
            failure_detail=None,
            extra={
                "taxonomy_metadata_fingerprint": taxonomy_fp,
                "eligible_target_taxon_count": len(target_taxon_ids),
                "eligible_target_taxa": [
                    {
                        "taxon_id": taxon_id,
                        "scientific_name": target_taxon_names[taxon_id],
                    }
                    for taxon_id in sorted(target_taxon_ids)
                ],
                "query_payload_fingerprint": canonical_sha256(query_payload),
                "selected_response_file_count": len(inventory),
                "response_file_inventory_fingerprint": canonical_sha256(
                    file_receipts
                ),
                "response_file_receipts": file_receipts,
                "response_row_counts_by_site": row_counts,
                "site_results": site_results,
                "fixed_site_count": len(fixed_sites),
                "scored_site_count": len(scored),
                "non_estimable_or_stopped_site_count": len(fixed_sites) - len(scored),
                "exact_regime_match_count": exact_matches,
                "exact_regime_match_fraction": exact_match_fraction,
                "mean_absolute_survival_fraction_error": mae,
                "observed_regime_counts": observed_counts,
                "simple_chance_reference": 1.0 / 3.0,
                "all_forecasts_were_contracting": True,
                "interpretation_guardrail": (
                    "The frozen v2 forecast predicted contracting for all 16 sites; "
                    "therefore exact-match fraction is the observed contracting prevalence "
                    "among estimable fixed sites. No post-response retuning is authorized."
                ),
            },
        )
        OUTPUT_PATH.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 0

    except Exception as error:
        status = (
            "terminal_response_consumed_failure"
            if response_consumed
            else "terminal_pre_response_failure"
        )
        payload = terminal_payload(
            protocol=response_protocol,
            forecast_lock=forecast_lock,
            counters=counters,
            status=status,
            failure_stage="runner",
            failure_detail=f"{type(error).__name__}: {error}",
            extra={
                "query_payload_fingerprint": (
                    canonical_sha256(query_payload)
                    if query_payload is not None
                    else None
                ),
                "selected_response_file_count_before_failure": len(inventory),
            },
        )
        OUTPUT_PATH.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(payload["failure_detail"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
