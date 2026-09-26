from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np

from eog.v2.adequacy_complete_ladder import plan_adequacy_complete_lcc_targets
from eog.v2.metacommunity_connectivity import (
    aggregate_emergence_test,
    assemblage_row_permutation_null,
    calculate_metacommunity_connectivity,
    deterministic_site_seed,
)
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
RESPONSE_PROTOCOL_PATH = BASE / "response_protocol_v1.json"
RESPONSE_LOCK_PATH = BASE / "response_protocol_lock_v1.json"
ROSTER_LOCK_PATH = BASE / "fresh_roster_lock_v1.json"
OUTPUT_PATH = BASE / "response_result_v1.json"

TOKEN_ENV = "NEON_API_TOKEN"
DATA_QUERY_URL = "https://data.neonscience.org/api/v0/data/query"
TAXONOMY_URL = (
    "https://data.neonscience.org/api/v0/taxonomy?"
    "taxonTypeCode=SMALL_MAMMAL&verbose=true&offset=0&limit=1000"
)
USER_AGENT = "eog-neon-metacommunity-connectivity-response/1.0"


def canonical_sha256(payload: object) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def get_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def post_graphql(query: str, variables: dict[str, object]) -> object:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        "https://data.neonscience.org/graphql",
        data=body,
        method="POST",
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


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


def is_geolocatable_trap(site_code: str, name: str) -> bool:
    marker = ".mammalGrid.mam."
    if not name.startswith(f"{site_code}_") or marker not in name:
        return False
    coordinate = name.rsplit(".", 1)[-1].strip().upper()
    return "X" not in coordinate and bool(re.fullmatch(r"[A-Z][0-9]+", coordinate))


def fetch_locations(names: list[str]) -> list[dict[str, object]]:
    query = """
    query FindLocations($query: LocationQuery!) {
      locations: findLocations(query: $query) {
        locationName
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
        payload = post_graphql(query, {"query": {"locationNames": names[start:start+500]}})
        if not isinstance(payload, dict) or payload.get("errors"):
            raise RuntimeError(f"GraphQL location lookup failed: {payload!r}")
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("locations"), list):
            raise RuntimeError("GraphQL location lookup returned unexpected schema")
        rows.extend(row for row in data["locations"] if isinstance(row, dict))
    return rows


def registry_for_site(site_code: str) -> tuple[tuple[str, ...], dict[str, dict[str, object]], str]:
    hierarchy = get_json(
        f"https://data.neonscience.org/api/v0/locations/{site_code}?hierarchy=true"
    )
    names = sorted(collect_location_names(hierarchy))
    traps = [name for name in names if is_geolocatable_trap(site_code, name)]
    rows = fetch_locations(traps)
    by_name: dict[str, dict[str, object]] = {}
    trap_set = set(traps)
    for row in rows:
        name = str(row.get("locationName", "")).strip()
        if name not in trap_set:
            continue
        try:
            lat = float(row.get("locationDecimalLatitude"))
            lon = float(row.get("locationDecimalLongitude"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(lat) or not math.isfinite(lon):
            continue
        if name in by_name:
            raise RuntimeError(f"{site_code}: duplicate location {name}")
        by_name[name] = {
            "locationName": name,
            "latitude": lat,
            "longitude": lon,
            "locationType": row.get("locationType"),
            "domainCode": row.get("domainCode"),
            "siteCode": row.get("siteCode"),
        }
    missing = sorted(trap_set - set(by_name))
    if missing:
        raise RuntimeError(f"{site_code}: missing coordinates for {len(missing)} frozen traps")
    node_ids = tuple(sorted(by_name))
    fp = canonical_sha256([by_name[node] for node in node_ids])
    return node_ids, by_name, fp


def haversine_matrix(latitudes: list[float], longitudes: list[float]) -> np.ndarray:
    lat = np.radians(np.asarray(latitudes, dtype=float))
    lon = np.radians(np.asarray(longitudes, dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    )
    return 6371.0088 * 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def frozen_geometry(
    site_code: str,
    protocol: dict[str, Any],
    roster: dict[str, Any],
) -> dict[str, Any]:
    locked = roster["site_locks"][site_code]
    node_ids, by_name, registry_fp = registry_for_site(site_code)
    if len(node_ids) != int(locked["node_count"]):
        raise RuntimeError(f"{site_code}: node count drift before response")
    if registry_fp != locked["node_registry_fingerprint"]:
        raise RuntimeError(f"{site_code}: node registry fingerprint drift before response")

    distances = haversine_matrix(
        [float(by_name[node]["latitude"]) for node in node_ids],
        [float(by_name[node]["longitude"]) for node in node_ids],
    )
    adequacy_spec = protocol["world_family"]["adequacy"]
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(
            adequacy_spec["min_largest_weak_component_fraction"]
        ),
        max_isolated_node_fraction=float(adequacy_spec["max_isolated_node_fraction"]),
        min_median_horizon_reachable_fraction=None,
        require_at_least_one_world_pass=True,
    )
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
    adj = structural_scale_adjacencies(ladder, distances)
    dedup = deduplicate_structural_worlds(adj)
    audit = audit_world_universe_structure(node_ids, dedup.world_adjacencies, horizon=1)
    gate = apply_structural_adequacy_gate(audit, adequacy)
    if not gate.passed:
        raise RuntimeError(f"{site_code}: structural adequacy drift before response")
    world_fp = canonical_sha256({
        "deduplication_fingerprint":dedup.fingerprint,
        "audit_fingerprint":audit.fingerprint,
        "gate_fingerprint":gate.fingerprint,
        "horizon":1,
    })
    if dedup.distinct_world_count != int(locked["distinct_world_count"]):
        raise RuntimeError(f"{site_code}: distinct world count drift")
    if world_fp != locked["world_universe_fingerprint"]:
        raise RuntimeError(f"{site_code}: world-universe fingerprint drift")
    return {
        "site_code":site_code,
        "node_ids":node_ids,
        "node_index":{node:i for i,node in enumerate(node_ids)},
        "canonical_worlds":{
            world_id:np.asarray(matrix,dtype=bool)
            for world_id,matrix in dedup.world_adjacencies.items()
        },
        "node_registry_fingerprint":registry_fp,
        "world_universe_fingerprint":world_fp,
    }


def eligible_target_taxa(response_protocol: dict[str, Any]) -> tuple[tuple[str, ...], dict[str,str], str]:
    payload = get_json(TAXONOMY_URL)
    fp = canonical_sha256(payload)
    target = response_protocol["target_taxonomy"]
    if fp != target["fingerprint"]:
        raise RuntimeError("taxonomy metadata fingerprint drift before response")
    excluded = set(target["excluded_scientific_names"])
    ids: list[str] = []
    names: dict[str,str] = {}
    for row in payload.get("data", []):
        if not isinstance(row, dict):
            continue
        if str(row.get("dwc:taxonRank","")).lower() != "species":
            continue
        if str(row.get("taxonProtocolCategory","")).lower() != "target":
            continue
        taxon_id = str(row.get("taxonID","")).strip()
        name = str(row.get("dwc:scientificName","")).strip()
        if not taxon_id or not name or name in excluded:
            continue
        ids.append(taxon_id)
        names[taxon_id] = name
    ids = sorted(set(ids))
    if len(ids) != int(target["expected_target_taxon_count"]):
        raise RuntimeError("eligible target taxon count drift before response")
    return tuple(ids), names, fp


def post_data_query(body: dict[str,Any], token: str, counters: dict[str,int]) -> dict[str,Any]:
    request = urllib.request.Request(
        DATA_QUERY_URL,
        data=json.dumps(body,sort_keys=True,separators=(",",":")).encode("utf-8"),
        method="POST",
        headers={
            "User-Agent":USER_AGENT,
            "Content-Type":"application/json",
            "X-API-Token":token,
        },
    )
    counters["response_endpoint_requests"] += 1
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
    counters["response_query_bytes_opened"] += len(raw)
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),dict):
        raise RuntimeError("NEON data query returned unexpected schema")
    return payload


def response_inventory(payload: dict[str,Any], fixed_sites: tuple[str,...]) -> list[dict[str,Any]]:
    data = payload["data"]
    if str(data.get("productCode","")) != "DP1.10072.001":
        raise RuntimeError("response product drift")
    releases = data.get("releases")
    if not isinstance(releases,list):
        raise RuntimeError("response releases missing")
    blocks=[r for r in releases if isinstance(r,dict) and r.get("release")=="RELEASE-2026"]
    if len(blocks)!=1:
        raise RuntimeError("expected exactly one RELEASE-2026 response block")
    inventory: dict[tuple[str,str,str],dict[str,Any]]={}
    for package in blocks[0].get("packages",[]):
        if not isinstance(package,dict):
            continue
        site=str(package.get("siteCode",""))
        if site not in fixed_sites:
            raise RuntimeError(f"undeclared response site {site}")
        if str(package.get("packageType",""))!="basic":
            raise RuntimeError("non-basic response package")
        month=str(package.get("month",""))
        for row in package.get("files",[]):
            if not isinstance(row,dict):
                continue
            name=str(row.get("name",""))
            if "mam_pertrapnight" not in name or not name.lower().endswith(".csv"):
                continue
            md5=str(row.get("md5","")).lower()
            url=str(row.get("url",""))
            size=row.get("size")
            if not re.fullmatch(r"[0-9a-f]{32}",md5):
                raise RuntimeError(f"invalid md5 for {name}")
            if not url.startswith("https://"):
                raise RuntimeError(f"invalid URL for {name}")
            if isinstance(size,bool) or not isinstance(size,int) or size<0:
                raise RuntimeError(f"invalid size for {name}")
            key=(site,month,name)
            norm={"site_code":site,"month":month,"name":name,"md5":md5,"url":url,"size":size}
            if key in inventory and inventory[key]!=norm:
                raise RuntimeError(f"conflicting duplicate file {key}")
            inventory[key]=norm
    rows=[inventory[key] for key in sorted(inventory)]
    if not rows:
        raise RuntimeError("no mam_pertrapnight response files")
    return rows


def download(row: dict[str,Any], token: str, counters: dict[str,int]) -> bytes:
    request=urllib.request.Request(
        str(row["url"]),
        headers={"User-Agent":USER_AGENT,"X-API-Token":token},
    )
    counters["response_file_requests"] += 1
    with urllib.request.urlopen(request, timeout=180) as response:
        raw=response.read()
    counters["biological_response_bytes_opened"] += len(raw)
    if len(raw)!=int(row["size"]):
        raise RuntimeError(f"size mismatch for {row['name']}")
    if hashlib.md5(raw).hexdigest()!=row["md5"]:
        raise RuntimeError(f"md5 mismatch for {row['name']}")
    return raw


def parse_response_file(
    raw: bytes,
    row: dict[str,Any],
    *,
    target_taxa: set[str],
    geometries: dict[str,dict[str,Any]],
    species_by_node: dict[str,dict[str,set[str]]],
    unknown_non_x: dict[str,set[str]],
    x_positive_nodes: dict[str,set[str]],
    counters_by_site: dict[str,dict[str,int]],
) -> None:
    site=str(row["site_code"])
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"non-UTF8 response CSV {row['name']}") from error
    reader=csv.DictReader(io.StringIO(text))
    required={"namedLocation","trapCoordinate","trapStatus","taxonID"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise RuntimeError(f"required columns missing in {row['name']}")
    node_set=set(geometries[site]["node_ids"])
    for record in reader:
        counters_by_site[site]["rows"] += 1
        status=str(record.get("trapStatus","")).strip().lower()
        if "capture" not in status or "no capture" in status:
            continue
        taxon=str(record.get("taxonID","")).strip()
        if taxon not in target_taxa:
            continue
        counters_by_site[site]["target_capture_rows"] += 1
        named=str(record.get("namedLocation","")).strip()
        coord=str(record.get("trapCoordinate","")).strip()
        node=f"{named}.{coord}"
        if "X" in coord.upper():
            counters_by_site[site]["x_excluded_rows"] += 1
            x_positive_nodes[site].add(node)
            continue
        if node not in node_set:
            unknown_non_x[site].add(node)
            continue
        species_by_node[site].setdefault(node,set()).add(taxon)


def rankdata(values: list[float]) -> np.ndarray:
    array=np.asarray(values,dtype=float)
    order=np.argsort(array,kind="mergesort")
    ranks=np.empty(len(array),dtype=float)
    i=0
    while i<len(array):
        j=i+1
        while j<len(array) and array[order[j]]==array[order[i]]:
            j+=1
        rank=(i+1+j)/2.0
        ranks[order[i:j]]=rank
        i=j
    return ranks


def spearman(values_a: list[float], values_b: list[float]) -> float | None:
    if len(values_a)<3 or len(values_a)!=len(values_b):
        return None
    ra=rankdata(values_a)
    rb=rankdata(values_b)
    if float(np.std(ra))==0.0 or float(np.std(rb))==0.0:
        return None
    return float(np.corrcoef(ra,rb)[0,1])


def main() -> int:
    protocol=json.loads(PROTOCOL_PATH.read_text())
    response_protocol=json.loads(RESPONSE_PROTOCOL_PATH.read_text())
    response_lock=json.loads(RESPONSE_LOCK_PATH.read_text())
    roster=json.loads(ROSTER_LOCK_PATH.read_text())

    counters={
        "response_endpoint_requests":0,
        "response_query_bytes_opened":0,
        "response_file_requests":0,
        "biological_response_bytes_opened":0,
    }
    response_consumed=False
    try:
        if git_blob_sha1(RESPONSE_PROTOCOL_PATH)!=response_lock["protocol_git_blob_sha1"]:
            raise RuntimeError("response protocol blob differs from lock")
        if roster["result_fingerprint"]!=response_protocol["prerequisite_roster_result_fingerprint"]:
            raise RuntimeError("roster prerequisite mismatch")
        fixed_sites=tuple(response_protocol["fixed_site_codes"])
        if list(fixed_sites)!=roster["selected_site_codes"]:
            raise RuntimeError("fixed response sites differ from roster lock")
        if response_protocol["response_query"]["body"]["siteCodes"]!=list(fixed_sites):
            raise RuntimeError("response query site order differs from frozen sites")

        taxa,taxon_names,taxonomy_fp=eligible_target_taxa(response_protocol)
        taxon_set=set(taxa)

        geometries={}
        for site in fixed_sites:
            geometries[site]=frozen_geometry(site,protocol,roster)

        token=os.environ.get(TOKEN_ENV,"").strip()
        if not token:
            raise RuntimeError("NEON_API_TOKEN is missing before response access")

        query=post_data_query(response_protocol["response_query"]["body"],token,counters)
        response_consumed=True
        inventory=response_inventory(query,fixed_sites)

        species_by_node={site:{} for site in fixed_sites}
        unknown={site:set() for site in fixed_sites}
        x_nodes={site:set() for site in fixed_sites}
        site_counts={
            site:{"rows":0,"target_capture_rows":0,"x_excluded_rows":0}
            for site in fixed_sites
        }
        receipts=[]
        for row in inventory:
            raw=download(row,token,counters)
            parse_response_file(
                raw,row,
                target_taxa=taxon_set,
                geometries=geometries,
                species_by_node=species_by_node,
                unknown_non_x=unknown,
                x_positive_nodes=x_nodes,
                counters_by_site=site_counts,
            )
            receipts.append({
                "site_code":row["site_code"],
                "month":row["month"],
                "name":row["name"],
                "size":row["size"],
                "md5":row["md5"],
            })

        site_results=[]
        observed_gains=[]
        adjusted_gains=[]
        rescue_values=[]
        dominance_values=[]
        stops=[]
        for site in fixed_sites:
            if unknown[site]:
                stops.append({
                    "site_code":site,
                    "status":"response_consumed_unknown_non_x_positive_node",
                    "unknown_non_x_count":len(unknown[site]),
                    "examples":sorted(unknown[site])[:10],
                    "x_excluded_positive_node_count":len(x_nodes[site]),
                })
                continue

            node_ids=geometries[site]["node_ids"]
            observed_species=sorted({
                species
                for values in species_by_node[site].values()
                for species in values
            })
            guild_positive_nodes=sorted(species_by_node[site])
            counts={
                species:sum(species in values for values in species_by_node[site].values())
                for species in observed_species
            }
            species_two=[species for species,count in counts.items() if count>=2]
            if (
                len(guild_positive_nodes)
                < int(protocol["site_response_estimability"]["minimum_guild_positive_nodes"])
                or len(species_two)
                < int(protocol["site_response_estimability"]["minimum_species_with_at_least_two_positive_nodes"])
            ):
                stops.append({
                    "site_code":site,
                    "status":"response_consumed_non_estimable_metacommunity",
                    "guild_positive_node_count":len(guild_positive_nodes),
                    "observed_target_species_count":len(observed_species),
                    "species_with_two_positive_nodes":len(species_two),
                    "x_excluded_positive_node_count":len(x_nodes[site]),
                })
                continue

            species_index={species:i for i,species in enumerate(taxa)}
            incidence=np.zeros((len(node_ids),len(taxa)),dtype=bool)
            node_index=geometries[site]["node_index"]
            for node,values in species_by_node[site].items():
                i=node_index[node]
                for species in values:
                    incidence[i,species_index[species]]=True

            metric=calculate_metacommunity_connectivity(
                geometries[site]["canonical_worlds"],
                incidence,
                species_ids=taxa,
            )
            seed=deterministic_site_seed(protocol["programme"],site)
            null=assemblage_row_permutation_null(
                geometries[site]["canonical_worlds"],
                incidence,
                species_ids=taxa,
                replicates=int(protocol["assemblage_permutation_null"]["replicates"]),
                seed=seed,
            )
            best_names=[taxon_names.get(s,s) for s in metric.best_species_ids]
            site_result={
                "site_code":site,
                "status":"scored_metacommunity_connectivity",
                "node_count":len(node_ids),
                "guild_positive_node_count":metric.guild_positive_node_count,
                "observed_target_species_count":len(observed_species),
                "species_with_two_positive_nodes":len(metric.species_with_two_positive_nodes),
                "community_survival_fraction":metric.community_survival_fraction,
                "max_species_survival_fraction":metric.max_species_survival_fraction,
                "best_species_ids":list(metric.best_species_ids),
                "best_species_names":best_names,
                "emergent_connectivity_gain":metric.emergent_connectivity_gain,
                "strict_emergent_world_fraction":metric.strict_emergent_world_fraction,
                "cross_species_rescue_fraction":metric.cross_species_rescue_fraction,
                "dominance_coverage":metric.dominance_coverage,
                "permutation_seed":seed,
                "permutation_replicates":null.replicates,
                "null_median_gain":null.null_median_gain,
                "null_adjusted_gain":null.null_adjusted_gain,
                "site_upper_tail_p":null.upper_tail_p,
                "null_gain_min":min(null.null_gains),
                "null_gain_max":max(null.null_gains),
                "null_gains":list(null.null_gains),
                "row_sum_preserved":null.row_sum_preserved,
                "column_sum_preserved":null.column_sum_preserved,
                "guild_positive_set_preserved":null.guild_positive_set_preserved,
                "x_excluded_positive_node_count":len(x_nodes[site]),
                "x_excluded_positive_row_count":site_counts[site]["x_excluded_rows"],
                "metric_fingerprint":metric.fingerprint,
                "null_fingerprint":null.fingerprint,
                "world_universe_fingerprint":geometries[site]["world_universe_fingerprint"],
                "node_registry_fingerprint":geometries[site]["node_registry_fingerprint"],
            }
            site_result["fingerprint"]=canonical_sha256(site_result)
            site_results.append(site_result)
            observed_gains.append(metric.emergent_connectivity_gain)
            adjusted_gains.append(null.null_adjusted_gain)
            rescue_values.append(metric.cross_species_rescue_fraction)
            dominance_values.append(metric.dominance_coverage)

        aggregate=None
        if site_results:
            aggregate_result=aggregate_emergence_test(
                observed_gains,
                adjusted_gains,
                minimum_sites=int(protocol["primary_hypothesis"]["minimum_scored_sites"]),
                alpha=0.05,
            )
            aggregate={
                "site_count":aggregate_result.site_count,
                "positive_null_adjusted_site_count":aggregate_result.positive_null_adjusted_site_count,
                "median_observed_gain":aggregate_result.median_observed_gain,
                "median_null_adjusted_gain":aggregate_result.median_null_adjusted_gain,
                "one_sided_sign_test_p":aggregate_result.one_sided_sign_test_p,
                "confirmatory_estimable":aggregate_result.confirmatory_estimable,
                "primary_supported":aggregate_result.primary_supported,
                "gain_vs_cross_species_rescue_spearman_rho":spearman(observed_gains,rescue_values),
                "gain_vs_dominance_spearman_rho":spearman(observed_gains,dominance_values),
                "fingerprint":aggregate_result.fingerprint,
            }

        status=(
            "completed_scored_metacommunity_programme"
            if aggregate is not None and aggregate["confirmatory_estimable"]
            else "completed_non_estimable_metacommunity_programme"
        )
        payload={
            "schema":"eog.neon_metacommunity_connectivity.response_result.v1",
            "programme":protocol["programme"],
            "status":status,
            "roster_result_fingerprint":roster["result_fingerprint"],
            "taxonomy_metadata_fingerprint":taxonomy_fp,
            "fixed_site_count":len(fixed_sites),
            "scored_site_count":len(site_results),
            "stopped_site_count":len(stops),
            "site_results":site_results,
            "response_consumed_stops":stops,
            "aggregate_primary":aggregate,
            "response_file_count":len(inventory),
            "response_file_inventory_fingerprint":canonical_sha256(receipts),
            **counters,
            "model_fits":0,
            "rerun_authorized":False,
        }
        payload["fingerprint"]=canonical_sha256(payload)
        OUTPUT_PATH.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
        return 0
    except Exception as error:
        payload={
            "schema":"eog.neon_metacommunity_connectivity.response_result.v1",
            "programme":json.loads(PROTOCOL_PATH.read_text())["programme"],
            "status":(
                "terminal_response_consumed_failure"
                if response_consumed
                else "terminal_pre_response_failure"
            ),
            "failure_detail":f"{type(error).__name__}: {error}",
            **counters,
            "model_fits":0,
            "rerun_authorized":not response_consumed,
        }
        payload["fingerprint"]=canonical_sha256(payload)
        OUTPUT_PATH.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
