from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

import gate1_registry_effort as g1
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "bbs_northern_bobwhite_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate2_structural_contract.json").read_text())
OUT = BUILD / "gate2_structural.json"


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fp(o):
    return hashlib.sha256(canon(o)).hexdigest()


def fetch_allowed(name: str):
    item = g1.get_json(g1.SOURCE["source"]["metadata_item_url"])
    files = {str(f.get("name")): f for f in (item.get("files") or []) if isinstance(f, dict)}
    f = files.get(name)
    if f is None:
        raise RuntimeError(f"allowed file absent from ScienceBase metadata: {name}")
    spec = g1.CONTRACT["allowed_payloads"][name]
    size = int(f.get("size"))
    md5 = g1.checksum_md5(f)
    if size != int(spec["size"]) or md5 != spec["md5"]:
        raise RuntimeError(f"metadata identity mismatch for {name}: size={size}, md5={md5}")
    uri = f.get("downloadUri") or f.get("url")
    if not uri:
        raise RuntimeError(f"no individual download URI for {name}")
    raw, final_url, ctype = g1.get_bytes(uri)
    if len(raw) != int(spec["size"]):
        raise RuntimeError(f"byte-size mismatch for {name}: {len(raw)} != {spec['size']}")
    actual = hashlib.md5(raw).hexdigest()
    if actual != spec["md5"]:
        raise RuntimeError(f"MD5 mismatch for {name}: {actual} != {spec['md5']}")
    header, rows, enc, delim = g1.decode_csv(raw, name)
    return header, rows, {"size": len(raw), "md5": actual, "encoding": enc, "delimiter": delim, "content_type": ctype}


def reconstruct_registry(route_rows, route_header, weather_rows, weather_header):
    rsem = g1.resolve_semantics(
        route_header,
        g1.CONTRACT["semantic_aliases"]["routes"],
        {"country_num", "state_num", "route", "latitude", "longitude"},
    )
    wsem = g1.resolve_semantics(
        weather_header,
        g1.CONTRACT["semantic_aliases"]["weather"],
        {"country_num", "state_num", "route", "year", "quality_current_id", "run_type"},
    )
    usa = int(g1.CONTRACT["eligibility"]["usa_country_num"])
    route_by_key = {}
    for r in route_rows:
        key = (
            g1.intval(r.get(rsem["country_num"]), "route.country"),
            g1.intval(r.get(rsem["state_num"]), "route.state"),
            g1.intval(r.get(rsem["route"]), "route.route"),
        )
        if key in route_by_key:
            raise RuntimeError(f"duplicate Routes.csv key during Gate2 reconstruction: {key}")
        lat = g1.floatval(r.get(rsem["latitude"]), f"latitude {key}")
        lon = g1.floatval(r.get(rsem["longitude"]), f"longitude {key}")
        route_by_key[key] = {"latitude": lat, "longitude": lon}
    usa_routes = {k: v for k, v in route_by_key.items() if k[0] == usa}

    modeled_years = set(map(int, g1.CONTRACT["eligibility"]["modeled_years"]))
    run_type = int(g1.CONTRACT["eligibility"]["acceptable_run_type"])
    qid = int(g1.CONTRACT["eligibility"]["acceptable_quality_current_id"])
    eligible_by_route = {}
    seen = set()
    for w in weather_rows:
        country = g1.intval(w.get(wsem["country_num"]), "weather.country")
        year = g1.intval(w.get(wsem["year"]), "weather.year")
        if country != usa or year not in modeled_years:
            continue
        if g1.intval(w.get(wsem["run_type"]), "weather.RunType") != run_type:
            continue
        if g1.intval(w.get(wsem["quality_current_id"]), "weather.QualityCurrentID") != qid:
            continue
        key = (
            country,
            g1.intval(w.get(wsem["state_num"]), "weather.state"),
            g1.intval(w.get(wsem["route"]), "weather.route"),
        )
        if key not in usa_routes:
            raise RuntimeError(f"quality-valid weather route absent from Routes.csv: {(key, year)}")
        ky = (key, year)
        if ky in seen:
            raise RuntimeError(f"duplicate quality-valid route-year during Gate2 reconstruction: {ky}")
        seen.add(ky)
        eligible_by_route.setdefault(key, set()).add(year)

    cal = set(map(int, g1.CONTRACT["eligibility"]["calibration_years"]))
    hold = set(map(int, g1.CONTRACT["eligibility"]["heldout_years"]))
    min_cal = int(g1.CONTRACT["eligibility"]["minimum_quality_valid_calibration_years_per_route"])
    min_hold = int(g1.CONTRACT["eligibility"]["minimum_quality_valid_heldout_years_per_route"])
    analysis_keys = sorted(
        k for k, ys in eligible_by_route.items()
        if len(ys & cal) >= min_cal and len(ys & hold) >= min_hold
    )
    reg = [
        {
            "country_num": k[0],
            "state_num": k[1],
            "route": k[2],
            "latitude": usa_routes[k]["latitude"],
            "longitude": usa_routes[k]["longitude"],
            "years": sorted(eligible_by_route[k]),
        }
        for k in analysis_keys
    ]
    return reg


def haversine_matrix(reg):
    radius = float(CONTRACT["geometry"]["earth_radius_km"])
    lat = np.radians(np.asarray([r["latitude"] for r in reg], dtype=float))
    lon = np.radians(np.asarray([r["longitude"] for r in reg], dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    h = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    np.clip(h, 0.0, 1.0, out=h)
    matrix = 2.0 * radius * np.arcsin(np.sqrt(h))
    np.fill_diagonal(matrix, 0.0)
    return matrix


def main():
    result = {
        "schema": "eog.bbs_northern_bobwhite_replication_2.gate2_structural.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "registry": {},
        "ladder": {},
        "allowed_files": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        route_header, route_rows, route_meta = fetch_allowed("Routes.csv")
        weather_header, weather_rows, weather_meta = fetch_allowed("Weather.csv")
        result["allowed_files"] = {"Routes.csv": route_meta, "Weather.csv": weather_meta}
        reg = reconstruct_registry(route_rows, route_header, weather_rows, weather_header)
        observed_fp = fp(reg)
        expected = CONTRACT["gate1_required"]
        if len(reg) != int(expected["analysis_route_count"]):
            raise RuntimeError(f"analysis route count drift: {len(reg)} != {expected['analysis_route_count']}")
        if observed_fp != expected["analysis_registry_fingerprint"]:
            raise RuntimeError(f"analysis registry fingerprint drift: {observed_fp} != {expected['analysis_registry_fingerprint']}")

        node_ids = [f"{r['country_num']}:{r['state_num']}:{r['route']}" for r in reg]
        matrix = haversine_matrix(reg)
        declaration = StructuralScaleLadderDeclaration(
            axis_id=CONTRACT["geometry"]["axis_id"],
            target_largest_component_fractions=tuple(CONTRACT["structural_ladder"]["target_largest_component_fractions"]),
        )
        ladder = build_structural_scale_ladder(node_ids, matrix, declaration)
        levels = [
            {
                "level_id": x.level_id,
                "target_lcc_fraction": x.target_largest_component_fraction,
                "distance_threshold_km": x.distance_threshold,
                "achieved_lcc_fraction": x.achieved_largest_component_fraction,
                "weak_component_count": x.weak_component_count,
                "isolated_node_fraction": x.isolated_node_fraction,
                "directed_edge_count": x.directed_edge_count,
                "fingerprint": x.fingerprint,
            }
            for x in ladder.levels
        ]
        positive = [float(x.distance_threshold) for x in ladder.levels if float(x.distance_threshold) > 0.0]
        distinct_positive = []
        for value in positive:
            if not distinct_positive or abs(value - distinct_positive[-1]) > 1e-12:
                distinct_positive.append(value)
        result["registry"] = {
            "route_count": len(reg),
            "registry_fingerprint": observed_fp,
            "node_id_fingerprint": fp(node_ids),
        }
        result["ladder"] = {
            "axis_id": ladder.axis_id,
            "declaration_fingerprint": ladder.declaration_fingerprint,
            "distance_matrix_fingerprint": ladder.distance_matrix_fingerprint,
            "fingerprint": ladder.fingerprint,
            "levels": levels,
            "distinct_positive_threshold_count": len(distinct_positive),
            "distinct_positive_thresholds_km": distinct_positive,
        }
        if len(distinct_positive) < int(CONTRACT["structural_ladder"]["minimum_distinct_positive_thresholds"]):
            result["status"] = "stop_insufficient_response_blind_structural_scales"
            result["reason"] = f"only {len(distinct_positive)} distinct positive structural thresholds were realized"
        else:
            result["status"] = "gate2_pass_response_blind_structural_ladder"
            result["reason"] = "the exact Gate1 1,880-route registry realizes the prospectively frozen response-blind Haversine LCC ladder without bird-count access"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
