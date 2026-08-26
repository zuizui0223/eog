from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gate1_response_independent_profile as gate1
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)

CONTRACT = json.loads((HERE / "gate2_effort_geometry_contract.json").read_text())
OUT = ROOT / "build" / "vermont_american_marten_replication_2" / "gate2_effort_geometry_profile.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def percentile(values, q):
    xs = sorted(float(x) for x in values)
    if not xs:
        return None
    pos = (len(xs) - 1) * float(q)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def parse_float(value, label):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"blank {label}")
    x = float(text)
    if not math.isfinite(x):
        raise ValueError(f"non-finite {label}: {text!r}")
    return x


def parse_media_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(text[:10])
    except Exception:
        return None


def haversine_km(a, b):
    radius = float(CONTRACT["structural_geometry"]["earth_radius_km"])
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(h)))


def ladder_to_dict(ladder):
    return {
        "axis_id": ladder.axis_id,
        "declaration_fingerprint": ladder.declaration_fingerprint,
        "distance_matrix_fingerprint": ladder.distance_matrix_fingerprint,
        "fingerprint": ladder.fingerprint,
        "levels": [
            {
                "level_id": x.level_id,
                "target_largest_component_fraction": x.target_largest_component_fraction,
                "distance_threshold_km": x.distance_threshold,
                "achieved_largest_component_fraction": x.achieved_largest_component_fraction,
                "weak_component_count": x.weak_component_count,
                "isolated_node_fraction": x.isolated_node_fraction,
                "directed_edge_count": x.directed_edge_count,
                "fingerprint": x.fingerprint,
            }
            for x in ladder.levels
        ],
    }


def write(result):
    result["fingerprint"] = gate1.fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = {
        "schema": "eog.vermont_american_marten_replication_2.gate2_effort_geometry_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "site_registry": {},
        "media_effort": {},
        "temporal_profile": {},
        "structural_ladder": {},
        "biological_response_firewall": dict(CONTRACT["biological_response_firewall"]),
    }
    try:
        item_id = gate1.CONTRACT["sciencebase"]["item_id"]
        item, _, _ = gate1.get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        if item.get("id") != item_id:
            raise RuntimeError("ScienceBase item mismatch")

        parsed = {}
        payload_meta = {}
        for name in ("locations.csv", "visits.csv", "media.csv"):
            spec = gate1.ALLOWED[name]
            raw, meta = gate1.fetch_allowed(item, name, spec)
            header, rows, enc, delim = gate1.decode(raw, name)
            parsed[name] = (header, rows)
            payload_meta[name] = {**meta, "encoding": enc, "delimiter": delim, "row_count": len(rows)}

        # --- Frozen site registry: source-defined monitoring stations with complete public bbox. ---
        loc_header, loc_rows = parsed["locations.csv"]
        required_loc = {"pk_locationid", "location_type", "lat_min", "lat_max", "long_min", "long_max"}
        if not required_loc.issubset(loc_header):
            raise RuntimeError(f"locations schema missing {sorted(required_loc - set(loc_header))}")
        all_location_ids = [str(r.get("pk_locationid") or "").strip() for r in loc_rows]
        if any(not x for x in all_location_ids) or len(set(all_location_ids)) != len(all_location_ids):
            raise RuntimeError("locations pk_locationid is blank or non-unique")

        registry = {}
        bbox_lat_spans = []
        bbox_lon_spans = []
        monitoring_incomplete = []
        for row in loc_rows:
            lid = str(row["pk_locationid"]).strip()
            if str(row.get("location_type") or "").strip() != CONTRACT["site_registry"]["eligible_location_type_exact"]:
                continue
            try:
                lat_min = parse_float(row.get("lat_min"), f"{lid}.lat_min")
                lat_max = parse_float(row.get("lat_max"), f"{lid}.lat_max")
                lon_min = parse_float(row.get("long_min"), f"{lid}.long_min")
                lon_max = parse_float(row.get("long_max"), f"{lid}.long_max")
            except Exception as exc:
                monitoring_incomplete.append({"location_id": lid, "reason": str(exc)})
                continue
            if not (-90 <= lat_min <= lat_max <= 90 and -180 <= lon_min <= lon_max <= 180):
                raise RuntimeError(f"invalid public bbox ordering/range for {lid}")
            lat_proxy = (lat_min + lat_max) / 2.0
            lon_proxy = (lon_min + lon_max) / 2.0
            registry[lid] = {
                "location_id": lid,
                "lat_proxy": lat_proxy,
                "lon_proxy": lon_proxy,
                "lat_span_deg": lat_max - lat_min,
                "lon_span_deg": lon_max - lon_min,
            }
            bbox_lat_spans.append(lat_max - lat_min)
            bbox_lon_spans.append(lon_max - lon_min)

        expected_sites = int(CONTRACT["site_registry"]["expected_eligible_site_count_from_gate1"])
        if len(registry) != expected_sites:
            result["status"] = "stop_site_registry_not_reproduced"
            result["reason"] = f"eligible monitoring-station proxy registry has {len(registry)} sites, expected {expected_sites}"
            result["site_registry"] = {"eligible_site_count": len(registry), "monitoring_incomplete": monitoring_incomplete}
            write(result)
            return 0

        site_records = [registry[k] for k in sorted(registry)]
        result["site_registry"] = {
            "source_payloads": {k: payload_meta[k] for k in ("locations.csv",)},
            "all_location_rows": len(loc_rows),
            "eligible_site_count": len(registry),
            "monitoring_incomplete": monitoring_incomplete,
            "proxy_coordinate_interpretation": CONTRACT["site_registry"]["proxy_coordinate_rule"]["interpretation"],
            "registry_fingerprint": gate1.fp(site_records),
            "bbox_lat_span_deg": {
                "min": min(bbox_lat_spans), "median": statistics.median(bbox_lat_spans), "max": max(bbox_lat_spans)
            },
            "bbox_lon_span_deg": {
                "min": min(bbox_lon_spans), "median": statistics.median(bbox_lon_spans), "max": max(bbox_lon_spans)
            },
        }

        # --- Response-blind structural ladder on public proxy centers. ---
        site_ids = sorted(registry)
        n = len(site_ids)
        dist = np.zeros((n, n), dtype=float)
        for i in range(n):
            a = (registry[site_ids[i]]["lat_proxy"], registry[site_ids[i]]["lon_proxy"])
            for j in range(i + 1, n):
                b = (registry[site_ids[j]]["lat_proxy"], registry[site_ids[j]]["lon_proxy"])
                d = haversine_km(a, b)
                dist[i, j] = d
                dist[j, i] = d
        declaration = StructuralScaleLadderDeclaration(
            axis_id=CONTRACT["structural_geometry"]["axis_id"],
            target_largest_component_fractions=tuple(CONTRACT["structural_geometry"]["target_largest_component_fractions"]),
        )
        ladder = build_structural_scale_ladder(site_ids, dist, declaration)
        ladder_dict = ladder_to_dict(ladder)
        positive = [float(x.distance_threshold) for x in ladder.levels if float(x.distance_threshold) > 0]
        distinct_positive = sorted(set(positive))
        ladder_dict["distinct_positive_thresholds_km"] = distinct_positive
        ladder_dict["distinct_positive_threshold_count"] = len(distinct_positive)
        result["structural_ladder"] = ladder_dict
        if len(distinct_positive) < int(CONTRACT["structural_geometry"]["require_distinct_positive_thresholds_at_least"]):
            result["status"] = "stop_structural_scale_diversity_insufficient"
            result["reason"] = f"only {len(distinct_positive)} distinct positive structural thresholds"
            write(result)
            return 0

        # --- Label-free media site-week eligibility. ---
        visit_header, visit_rows = parsed["visits.csv"]
        media_header, media_rows = parsed["media.csv"]
        required_visit = {"pk_visitid", "fk_locationid"}
        required_media = {"pk_mediaid", "fk_visitid", "start_date", "sb_exclude"}
        if not required_visit.issubset(visit_header):
            raise RuntimeError(f"visits schema missing {sorted(required_visit - set(visit_header))}")
        if not required_media.issubset(media_header):
            raise RuntimeError(f"media schema missing {sorted(required_media - set(media_header))}")
        visit_lookup = {}
        for row in visit_rows:
            vid = str(row.get("pk_visitid") or "").strip()
            if not vid or vid in visit_lookup:
                raise RuntimeError("visits pk_visitid blank or non-unique")
            visit_lookup[vid] = str(row.get("fk_locationid") or "").strip()

        false_tokens = set(CONTRACT["effort_endpoint_universe"]["sb_exclude_false_tokens_casefolded"])
        true_tokens = set(CONTRACT["effort_endpoint_universe"]["sb_exclude_true_tokens_casefolded"])
        exclusion_counts = Counter()
        site_week_media = Counter()
        media_rows_by_year = Counter()
        media_ids_seen = set()
        for row in media_rows:
            mid = str(row.get("pk_mediaid") or "").strip()
            if not mid or mid in media_ids_seen:
                raise RuntimeError("media pk_mediaid blank or non-unique")
            media_ids_seen.add(mid)
            token = str(row.get("sb_exclude") or "").strip().casefold()
            if token in true_tokens:
                exclusion_counts["source_sb_exclude_true"] += 1
                continue
            if token not in false_tokens:
                result["status"] = "stop_unexpected_sb_exclude_token"
                result["reason"] = f"unexpected sb_exclude token {token!r}"
                write(result)
                return 0
            vid = str(row.get("fk_visitid") or "").strip()
            if vid not in visit_lookup:
                exclusion_counts["visit_not_found"] += 1
                continue
            lid = visit_lookup[vid]
            if lid not in registry:
                exclusion_counts["location_outside_eligible_registry"] += 1
                continue
            d = parse_media_date(row.get("start_date"))
            if d is None:
                exclusion_counts["unparseable_start_date"] += 1
                continue
            week_start = d - timedelta(days=d.weekday())
            site_week_media[(lid, week_start.isoformat())] += 1
            media_rows_by_year[week_start.year] += 1

        if not site_week_media:
            result["status"] = "stop_no_eligible_label_free_site_weeks"
            result["reason"] = "no eligible media-linked site-weeks were reconstructed"
            write(result)
            return 0

        site_weeks_by_year = Counter()
        sites_by_year = defaultdict(set)
        for (lid, week), count in site_week_media.items():
            year = date.fromisoformat(week).year
            site_weeks_by_year[year] += 1
            sites_by_year[year].add(lid)
        weeks = sorted(week for _, week in site_week_media)
        counts = list(site_week_media.values())
        result["media_effort"] = {
            "source_payloads": {k: payload_meta[k] for k in ("visits.csv", "media.csv")},
            "published_media_rows_reproduced": len(media_rows),
            "eligible_media_rows": int(sum(counts)),
            "excluded_media_rows_by_reason": dict(sorted(exclusion_counts.items())),
            "eligible_site_week_count": len(site_week_media),
            "eligible_site_count_with_at_least_one_media_week": len({lid for lid, _ in site_week_media}),
            "site_week_media_count_distribution": {
                "min": min(counts),
                "q25": percentile(counts, 0.25),
                "median": statistics.median(counts),
                "q75": percentile(counts, 0.75),
                "max": max(counts),
            },
            "eligible_site_week_registry_fingerprint": gate1.fp([
                {"location_id": lid, "week_start": week, "media_count": site_week_media[(lid, week)]}
                for lid, week in sorted(site_week_media)
            ]),
            "endpoint_interpretation": CONTRACT["effort_endpoint_universe"]["endpoint_interpretation"],
            "track_sign_used": false if False else False
        }
        result["temporal_profile"] = {
            "earliest_eligible_week_start": min(weeks),
            "latest_eligible_week_start": max(weeks),
            "eligible_site_weeks_by_calendar_year": {str(y): site_weeks_by_year[y] for y in sorted(site_weeks_by_year)},
            "eligible_sites_by_calendar_year": {str(y): len(sites_by_year[y]) for y in sorted(sites_by_year)},
            "eligible_media_rows_by_calendar_year": {str(y): media_rows_by_year[y] for y in sorted(media_rows_by_year)},
            "split_frozen": False,
        }

        result["status"] = "gate2_response_independent_effort_geometry_pass"
        result["reason"] = "70 monitoring-station public proxy centers, a response-blind structural ladder, and label-free recorded-imaging site-weeks were reconstructed without biological-response access"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
