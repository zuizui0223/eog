from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import statistics
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation" / "carrier_prevalence_mechanism_v1"
PROTOCOL_PATH = BASE / "protocol_v1.json"
ROSTER_PATH = BASE / "fresh_roster_lock_v1.json"
TRAIT_LOCK_PATH = BASE / "target_pool_traits_lock_v1.json"
TRAIT_DATA_PATH = ROOT / "data" / "derived" / "combine_target_pool_traits_v1.csv"
RESPONSE_PROTOCOL_PATH = BASE / "response_protocol_v1.json"
AUTHORIZATION_PATH = BASE / "response_authorization_v1.json"
OUTPUT_PATH = ROOT / "results" / "carrier_prevalence_response_v1.json"

DATA_QUERY_URL = "https://data.neonscience.org/api/v0/data/query"
TOKEN_ENV = "NEON_API_TOKEN"
USER_AGENT = "neon-carrier-prevalence-response/1.0"

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

roster_mod = _load_module(
    "carrier_roster",
    ROOT / "analysis" / "capture_carrier_prevalence_fresh_roster_v1.py",
)
null_mod = _load_module(
    "carrier_null",
    ROOT / "analysis" / "count_conditioned_carrier_null_v1.py",
)

def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rank_average(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        r = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = r
        i = j
    return ranks

def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) < 3 or len(x) != len(y):
        return None
    mx, my = statistics.mean(x), statistics.mean(y)
    dx = math.sqrt(sum((v - mx) ** 2 for v in x))
    dy = math.sqrt(sum((v - my) ** 2 for v in y))
    if dx == 0 or dy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (dx * dy)

def spearman(x: list[float], y: list[float]) -> float | None:
    return pearson(rank_average(x), rank_average(y))

def exact_sign_test_greater(positive: int, n: int) -> float | None:
    if n <= 0:
        return None
    return sum(math.comb(n, k) for k in range(positive, n + 1)) / (2 ** n)

def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value

def validate_pre_response_inputs() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    required = [
        PROTOCOL_PATH,
        ROSTER_PATH,
        TRAIT_LOCK_PATH,
        TRAIT_DATA_PATH,
        RESPONSE_PROTOCOL_PATH,
        AUTHORIZATION_PATH,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"response execution not armed; missing frozen inputs: {missing}")
    if OUTPUT_PATH.exists():
        raise RuntimeError("response output already exists; rerun forbidden")

    protocol = load_json(PROTOCOL_PATH)
    roster = load_json(ROSTER_PATH)
    traits = load_json(TRAIT_LOCK_PATH)
    rp = load_json(RESPONSE_PROTOCOL_PATH)
    auth = load_json(AUTHORIZATION_PATH)

    if rp["programme"] != protocol["programme"] or auth["programme"] != protocol["programme"]:
        raise RuntimeError("programme mismatch")
    if rp["fresh_roster_fingerprint"] != roster["fingerprint"]:
        raise RuntimeError("response protocol roster fingerprint mismatch")
    if rp["target_pool_traits_fingerprint"] != traits["fingerprint"]:
        raise RuntimeError("response protocol trait-lock fingerprint mismatch")
    if rp["fixed_site_codes"] != roster["selected_site_codes"]:
        raise RuntimeError("response protocol fixed sites differ from frozen roster")
    if rp["taxonomy_metadata_fingerprint"] != roster["taxonomy_metadata_fingerprint"]:
        raise RuntimeError("taxonomy fingerprint mismatch")
    if int(rp["expected_target_taxon_count"]) != int(roster["eligible_target_taxon_count"]):
        raise RuntimeError("target taxon count mismatch")

    hashes = auth["required_file_sha256"]
    actual = {
        "protocol_v1.json": file_sha256(PROTOCOL_PATH),
        "fresh_roster_lock_v1.json": file_sha256(ROSTER_PATH),
        "target_pool_traits_lock_v1.json": file_sha256(TRAIT_LOCK_PATH),
        "combine_target_pool_traits_v1.csv": file_sha256(TRAIT_DATA_PATH),
        "response_protocol_v1.json": file_sha256(RESPONSE_PROTOCOL_PATH),
        "run_carrier_prevalence_response_once_v1.py": file_sha256(Path(__file__)),
        "count_conditioned_carrier_null_v1.py": file_sha256(
            ROOT / "analysis" / "count_conditioned_carrier_null_v1.py"
        ),
        "capture_carrier_prevalence_fresh_roster_v1.py": file_sha256(
            ROOT / "analysis" / "capture_carrier_prevalence_fresh_roster_v1.py"
        ),
    }
    if hashes != actual:
        raise RuntimeError(
            "authorization file hashes do not match current frozen execution files"
        )
    if auth.get("authorization_state") != "authorized_once_only_biological_response_execution":
        raise RuntimeError("response is not authorized")
    if auth.get("authorization_consumed") is not False:
        raise RuntimeError("authorization is already consumed")

    return protocol, roster, traits, rp, auth

def reconstruct_geometry(
    protocol: dict[str, Any],
    roster: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    by_site = {row["site_code"]: row for row in roster["selected_sites"]}
    out: dict[str, dict[str, Any]] = {}
    for site in roster["selected_site_codes"]:
        locked = by_site[site]
        node_ids, rows, reg_fp = roster_mod.registry(site)
        if node_ids != locked["node_ids"]:
            raise RuntimeError(f"{site}: node IDs drifted before response")
        if reg_fp != locked["node_registry_fingerprint"]:
            raise RuntimeError(f"{site}: node registry fingerprint drifted before response")
        dist = roster_mod.haversine(rows)
        w = roster_mod.worlds(site, dist, protocol)
        if w["world_universe_fingerprint"] != locked["world_universe_fingerprint"]:
            raise RuntimeError(f"{site}: world universe drifted before response")
        if int(w["distinct_world_count"]) != int(locked["distinct_world_count"]):
            raise RuntimeError(f"{site}: distinct world count drifted before response")

        node_index = {node: i for i, node in enumerate(node_ids)}
        edge_worlds: list[set[tuple[int, int]]] = []
        for world in w["canonical_worlds"]:
            a = roster_mod.adjacency(dist, float(world["distance_threshold_km"]))
            edges = {
                (i, j)
                for i in range(len(node_ids))
                for j in range(i + 1, len(node_ids))
                if bool(a[i, j])
            }
            edge_worlds.append(edges)
        out[site] = {
            "node_ids": node_ids,
            "node_index": node_index,
            "edge_worlds": edge_worlds,
            "world_universe_fingerprint": locked["world_universe_fingerprint"],
            "node_registry_fingerprint": reg_fp,
        }
    return out

def post_data_query(
    body: dict[str, Any],
    token: str,
    counters: dict[str, int],
) -> dict[str, Any]:
    request = urllib.request.Request(
        DATA_QUERY_URL,
        data=json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"),
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

def response_inventory(
    payload: dict[str, Any],
    fixed_sites: tuple[str, ...],
) -> list[dict[str, Any]]:
    data = payload["data"]
    if str(data.get("productCode", "")) != "DP1.10072.001":
        raise RuntimeError("response product drift")
    releases = data.get("releases")
    if not isinstance(releases, list):
        raise RuntimeError("response releases missing")
    blocks = [
        r for r in releases
        if isinstance(r, dict) and r.get("release") == "RELEASE-2026"
    ]
    if len(blocks) != 1:
        raise RuntimeError("expected exactly one RELEASE-2026 response block")

    inventory: dict[tuple[str, str, str], dict[str, Any]] = {}
    for package in blocks[0].get("packages", []):
        if not isinstance(package, dict):
            continue
        site = str(package.get("siteCode", ""))
        if site not in fixed_sites:
            raise RuntimeError(f"undeclared response site {site}")
        if str(package.get("packageType", "")) != "basic":
            raise RuntimeError("non-basic response package")
        month = str(package.get("month", ""))
        for row in package.get("files", []):
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", ""))
            if "mam_pertrapnight" not in name or not name.lower().endswith(".csv"):
                continue
            md5 = str(row.get("md5", "")).lower()
            url = str(row.get("url", ""))
            size = row.get("size")
            if not md5 or len(md5) != 32:
                raise RuntimeError(f"invalid md5 for {name}")
            if not url.startswith("https://"):
                raise RuntimeError(f"invalid URL for {name}")
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise RuntimeError(f"invalid size for {name}")
            key = (site, month, name)
            norm = {
                "site_code": site,
                "month": month,
                "name": name,
                "md5": md5,
                "url": url,
                "size": size,
            }
            if key in inventory and inventory[key] != norm:
                raise RuntimeError(f"conflicting duplicate response file {key}")
            inventory[key] = norm
    rows = [inventory[k] for k in sorted(inventory)]
    if not rows:
        raise RuntimeError("no mam_pertrapnight response files found")
    return rows

def download_response_file(
    row: dict[str, Any],
    token: str,
    counters: dict[str, int],
) -> bytes:
    request = urllib.request.Request(
        str(row["url"]),
        headers={"User-Agent": USER_AGENT, "X-API-Token": token},
    )
    counters["response_file_requests"] += 1
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read()
    counters["biological_response_bytes_opened"] += len(raw)
    if len(raw) != int(row["size"]):
        raise RuntimeError(f"size mismatch for {row['name']}")
    if hashlib.md5(raw).hexdigest() != row["md5"]:
        raise RuntimeError(f"md5 mismatch for {row['name']}")
    return raw

def parse_response_file(
    raw: bytes,
    row: dict[str, Any],
    *,
    target_taxa: set[str],
    geometry: dict[str, dict[str, Any]],
    species_by_node: dict[str, dict[str, set[str]]],
    unknown_non_x: dict[str, set[str]],
    x_positive_nodes: dict[str, set[str]],
    site_counts: dict[str, dict[str, int]],
) -> None:
    site = str(row["site_code"])
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"namedLocation", "trapCoordinate", "trapStatus", "taxonID"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise RuntimeError(f"required columns missing in {row['name']}")
    node_set = set(geometry[site]["node_ids"])
    for record in reader:
        site_counts[site]["rows"] += 1
        status = str(record.get("trapStatus", "")).strip().lower()
        if "capture" not in status or "no capture" in status:
            continue
        taxon = str(record.get("taxonID", "")).strip()
        if taxon not in target_taxa:
            continue
        site_counts[site]["target_capture_rows"] += 1
        named = str(record.get("namedLocation", "")).strip()
        coord = str(record.get("trapCoordinate", "")).strip()
        node = f"{named}.{coord}"
        if "X" in coord.upper():
            site_counts[site]["x_excluded_rows"] += 1
            x_positive_nodes[site].add(node)
            continue
        if node not in node_set:
            unknown_non_x[site].add(node)
            continue
        species_by_node[site].setdefault(node, set()).add(taxon)

def load_trait_table() -> dict[str, dict[str, float | None]]:
    with TRAIT_DATA_PATH.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    traits = [
        "adult_mass_g",
        "dispersal_km",
        "habitat_breadth_n",
        "det_diet_breadth_n",
        "home_range_km2",
        "density_n_km2",
        "trophic_level",
    ]
    out: dict[str, dict[str, float | None]] = {}
    for row in rows:
        species = row["species_name"]
        values: dict[str, float | None] = {}
        for trait in traits:
            raw = row.get(trait, "")
            values[trait] = None if raw in (None, "") else float(raw)
        out[species] = values
    return out

def secondary_trait_summary(
    site_results: list[dict[str, Any]],
    trait_by_species: dict[str, dict[str, float | None]],
) -> dict[str, Any]:
    traits = [
        "adult_mass_g",
        "dispersal_km",
        "habitat_breadth_n",
        "det_diet_breadth_n",
        "home_range_km2",
        "density_n_km2",
        "trophic_level",
    ]
    result: dict[str, Any] = {}
    for trait in traits:
        site_rhos: list[dict[str, Any]] = []
        for site in site_results:
            pairs: list[tuple[float, float]] = []
            for species in site["species_results"]:
                t = trait_by_species.get(species["scientific_name"], {}).get(trait)
                if t is None:
                    continue
                pairs.append((float(t), float(species["carrier_excess"])))
            if len(pairs) < 3:
                continue
            x = [a for a, _ in pairs]
            y = [b for _, b in pairs]
            rho = spearman(x, y)
            if rho is None:
                continue
            site_rhos.append({"site_code": site["site_code"], "n": len(pairs), "rho": rho})
        values = [r["rho"] for r in site_rhos]
        result[trait] = {
            "estimable_site_count": len(values),
            "median_within_site_spearman_rho": (
                statistics.median(values) if values else None
            ),
            "positive_site_rho_count": sum(v > 0 for v in values),
            "zero_site_rho_count": sum(v == 0 for v in values),
            "negative_site_rho_count": sum(v < 0 for v in values),
            "site_rhos": site_rhos,
        }
    return result

def main() -> int:
    counters = {
        "response_endpoint_requests": 0,
        "response_query_bytes_opened": 0,
        "response_file_requests": 0,
        "biological_response_bytes_opened": 0,
    }
    response_consumed = False
    try:
        protocol, roster, trait_lock, rp, auth = validate_pre_response_inputs()
        geometry = reconstruct_geometry(protocol, roster)

        token = os.environ.get(TOKEN_ENV, "").strip()
        if not token:
            raise RuntimeError("NEON_API_TOKEN is missing before response access")

        fixed_sites = tuple(rp["fixed_site_codes"])
        target_rows = roster["eligible_target_taxa"]
        taxon_names = {str(r["taxon_id"]): str(r["scientific_name"]) for r in target_rows}
        target_taxa = set(taxon_names)

        query = post_data_query(rp["response_query"]["body"], token, counters)
        response_consumed = True
        inventory = response_inventory(query, fixed_sites)

        species_by_node = {site: {} for site in fixed_sites}
        unknown_non_x = {site: set() for site in fixed_sites}
        x_positive_nodes = {site: set() for site in fixed_sites}
        site_counts = {
            site: {"rows": 0, "target_capture_rows": 0, "x_excluded_rows": 0}
            for site in fixed_sites
        }
        receipts = []
        for row in inventory:
            raw = download_response_file(row, token, counters)
            parse_response_file(
                raw,
                row,
                target_taxa=target_taxa,
                geometry=geometry,
                species_by_node=species_by_node,
                unknown_non_x=unknown_non_x,
                x_positive_nodes=x_positive_nodes,
                site_counts=site_counts,
            )
            receipts.append({
                "site_code": row["site_code"],
                "month": row["month"],
                "name": row["name"],
                "size": row["size"],
                "md5": row["md5"],
            })

        site_results: list[dict[str, Any]] = []
        stops: list[dict[str, Any]] = []
        replicates = int(protocol["count_conditioned_null"]["replicates"])
        min_positive = int(protocol["site_estimability"]["minimum_guild_positive_nodes"])
        min_species = int(
            protocol["site_estimability"][
                "minimum_eligible_species_with_at_least_two_positive_nodes"
            ]
        )

        for site in fixed_sites:
            if unknown_non_x[site]:
                stops.append({
                    "site_code": site,
                    "status": "response_consumed_unknown_non_x_positive_node",
                    "unknown_non_x_count": len(unknown_non_x[site]),
                    "examples": sorted(unknown_non_x[site])[:10],
                    "x_excluded_positive_node_count": len(x_positive_nodes[site]),
                })
                continue

            node_ids = geometry[site]["node_ids"]
            node_index = geometry[site]["node_index"]
            guild_positive_nodes = sorted(species_by_node[site])
            species_ids = sorted({
                species
                for values in species_by_node[site].values()
                for species in values
            })
            positive_by_species = {
                species: {
                    node_index[node]
                    for node, values in species_by_node[site].items()
                    if species in values
                }
                for species in species_ids
            }
            eligible = [
                species for species in species_ids
                if len(positive_by_species[species]) >= 2
            ]
            if len(guild_positive_nodes) < min_positive or len(eligible) < min_species:
                stops.append({
                    "site_code": site,
                    "status": "response_consumed_non_estimable_site",
                    "guild_positive_node_count": len(guild_positive_nodes),
                    "eligible_species_count": len(eligible),
                    "observed_target_species_count": len(species_ids),
                    "x_excluded_positive_node_count": len(x_positive_nodes[site]),
                })
                continue

            candidate_nodes = [node_index[node] for node in guild_positive_nodes]
            species_results = []
            for species in eligible:
                name = taxon_names.get(species, species)
                seed = null_mod.deterministic_seed(site, name)
                grid_seed = null_mod.deterministic_grid_seed(site, name)
                grid_by_node = {
                    node_index[node]: node.rsplit(".", 1)[0]
                    for node in guild_positive_nodes
                }
                decomposition = null_mod.grid_conditioned_decomposition(
                    positive_by_species[species],
                    candidate_nodes,
                    grid_by_node,
                    geometry[site]["edge_worlds"],
                    replicates=replicates,
                    sitewide_seed=seed,
                    grid_seed=grid_seed,
                )
                species_results.append({
                    "taxon_id": species,
                    "scientific_name": name,
                    "positive_node_count": len(positive_by_species[species]),
                    "positive_node_fraction_of_guild": (
                        len(positive_by_species[species]) / len(candidate_nodes)
                    ),
                    "observed_grid_count": len({
                        grid_by_node[node] for node in positive_by_species[species]
                    }),
                    "observed_carrier": decomposition["observed_carrier"],
                    "expected_carrier_probability_count_conditioned": (
                        decomposition["expected_sitewide"]
                    ),
                    "expected_carrier_probability_grid_conditioned": (
                        decomposition["expected_grid_conditioned"]
                    ),
                    "carrier_excess": decomposition["sitewide_excess"],
                    "between_grid_allocation_component": (
                        decomposition["between_grid_allocation_component"]
                    ),
                    "within_grid_organization_component": (
                        decomposition["within_grid_organization_component"]
                    ),
                    "decomposition_reconstruction_error": (
                        decomposition["reconstruction_error"]
                    ),
                    "null_seed": seed,
                    "grid_null_seed": grid_seed,
                })

            effects = [float(r["carrier_excess"]) for r in species_results]
            between_grid = [
                float(r["between_grid_allocation_component"]) for r in species_results
            ]
            within_grid = [
                float(r["within_grid_organization_component"]) for r in species_results
            ]
            reconstruction = [
                abs(float(r["decomposition_reconstruction_error"])) for r in species_results
            ]
            site_result = {
                "site_code": site,
                "status": "scored_carrier_prevalence_mechanism",
                "guild_positive_node_count": len(candidate_nodes),
                "observed_target_species_count": len(species_ids),
                "eligible_species_count": len(eligible),
                "observed_carrier_count": sum(r["observed_carrier"] for r in species_results),
                "expected_carrier_count_count_conditioned": sum(
                    r["expected_carrier_probability_count_conditioned"]
                    for r in species_results
                ),
                "mean_species_carrier_excess": statistics.mean(effects),
                "median_species_carrier_excess": statistics.median(effects),
                "mean_between_grid_allocation_component": statistics.mean(between_grid),
                "mean_within_grid_organization_component": statistics.mean(within_grid),
                "max_abs_decomposition_reconstruction_error": max(reconstruction),
                "species_results": species_results,
                "x_excluded_positive_node_count": len(x_positive_nodes[site]),
                "x_excluded_positive_row_count": site_counts[site]["x_excluded_rows"],
                "node_registry_fingerprint": geometry[site]["node_registry_fingerprint"],
                "world_universe_fingerprint": geometry[site]["world_universe_fingerprint"],
            }
            site_result["fingerprint"] = canonical_sha256(site_result)
            site_results.append(site_result)

        effects = [float(r["mean_species_carrier_excess"]) for r in site_results]
        positive = sum(v > 0 for v in effects)
        n = len(effects)
        p_value = exact_sign_test_greater(positive, n) if n else None
        min_sites = int(protocol["aggregate_test"]["minimum_scored_sites"])
        estimable = n >= min_sites
        median_effect = statistics.median(effects) if effects else None
        primary_supported = bool(
            estimable
            and median_effect is not None
            and median_effect > 0
            and p_value is not None
            and p_value < 0.05
        )

        grid_effects = [
            float(r["mean_within_grid_organization_component"]) for r in site_results
        ]
        grid_positive = sum(v > 0 for v in grid_effects)
        grid_p = exact_sign_test_greater(grid_positive, len(grid_effects)) if grid_effects else None
        grid_median = statistics.median(grid_effects) if grid_effects else None
        between_effects = [
            float(r["mean_between_grid_allocation_component"]) for r in site_results
        ]

        trait_by_species = load_trait_table()
        secondary = secondary_trait_summary(site_results, trait_by_species)

        payload = {
            "schema": "neon.carrier_prevalence_mechanism.response.v1",
            "programme": protocol["programme"],
            "status": (
                "completed_estimable_once_only_response"
                if estimable
                else "completed_non_estimable_once_only_response"
            ),
            "fresh_roster_fingerprint": roster["fingerprint"],
            "target_pool_traits_fingerprint": trait_lock["fingerprint"],
            "fixed_site_count": len(fixed_sites),
            "scored_site_count": n,
            "stopped_site_count": len(stops),
            "site_results": site_results,
            "response_consumed_stops": stops,
            "aggregate_primary": {
                "site_count": n,
                "minimum_scored_sites": min_sites,
                "positive_site_effect_count": positive,
                "median_site_effect": median_effect,
                "one_sided_exact_sign_test_p": p_value,
                "confirmatory_estimable": estimable,
                "primary_spatial_organization_supported": primary_supported,
                "interpretation": (
                    "spatial organization contributes beyond prevalence"
                    if primary_supported
                    else (
                        "prevalence-only explanation sufficient at declared resolution"
                        if estimable
                        else "primary non-estimable under frozen minimum-site rule"
                    )
                ),
            },
            "secondary_grid_decomposition": {
                "site_count": len(grid_effects),
                "median_between_grid_allocation_component": (
                    statistics.median(between_effects) if between_effects else None
                ),
                "median_within_grid_organization_component": grid_median,
                "positive_within_grid_site_count": grid_positive,
                "one_sided_exact_sign_test_p_within_grid": grid_p,
                "interpretation_rule": (
                    "diagnostic only; cannot alter the primary site-wide count-conditioned decision"
                ),
                "identity": (
                    "site-wide carrier excess = between-grid allocation component + "
                    "within-grid organization component"
                ),
            },
            "secondary_frozen_traits": secondary,
            "response_file_count": len(inventory),
            "response_file_inventory_fingerprint": canonical_sha256(receipts),
            **counters,
            "model_fits": 0,
            "rerun_allowed": False,
            "post_response_site_change_allowed": False,
            "post_response_metric_change_allowed": False,
        }
        payload["fingerprint"] = canonical_sha256(payload)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("RESPONSE_SUMMARY " + json.dumps({
            "status": payload["status"],
            "fixed_sites": len(fixed_sites),
            "scored_sites": n,
            "stopped_sites": len(stops),
            "positive_site_effect_count": positive,
            "median_site_effect": median_effect,
            "one_sided_exact_sign_test_p": p_value,
            "primary_supported": primary_supported,
            "response_endpoint_requests": counters["response_endpoint_requests"],
            "biological_response_bytes_opened": counters["biological_response_bytes_opened"],
            "fingerprint": payload["fingerprint"],
        }, sort_keys=True))
        return 0
    except Exception as error:
        payload = {
            "schema": "neon.carrier_prevalence_mechanism.response.v1",
            "status": (
                "terminal_response_consumed_failure"
                if response_consumed
                else "terminal_pre_response_failure"
            ),
            "failure_detail": f"{type(error).__name__}: {error}",
            **counters,
            "model_fits": 0,
            "rerun_allowed": not response_consumed,
        }
        payload["fingerprint"] = canonical_sha256(payload)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("RESPONSE_FAILURE " + json.dumps(payload, sort_keys=True))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
