#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

RADII_KM = (0.5, 1.0, 2.0, 5.0, 10.0)
CLUSTER_SCALES_KM = (0.5, 1.0, 2.0)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(rows: list[dict[str, str]], columns: set[str], name: str) -> None:
    if not rows:
        raise ValueError(f"{name} is empty")
    missing = columns - set(rows[0])
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def validate_coordinates(rows: list[dict[str, str]], id_col: str, name: str) -> None:
    ids = [row[id_col] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{name} contains duplicate {id_col}")
    for row in rows:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"{name} invalid coordinates for {row[id_col]}")


def cluster_points(rows: list[dict[str, str]], threshold_km: float) -> list[dict[str, object]]:
    # Deterministic complete-link clustering prevents long chains.
    ordered = sorted(rows, key=lambda r: (r["island"], float(r["latitude"]), float(r["longitude"]), r["discovery_id"]))
    clusters: list[list[dict[str, str]]] = []
    for row in ordered:
        point = (float(row["latitude"]), float(row["longitude"]))
        placed = False
        for members in clusters:
            if members[0]["island"] != row["island"]:
                continue
            if all(haversine_km(point, (float(m["latitude"]), float(m["longitude"]))) <= threshold_km for m in members):
                members.append(row)
                placed = True
                break
        if not placed:
            clusters.append([row])
    output = []
    for idx, members in enumerate(clusters, start=1):
        output.append({
            "cluster_id": f"C{idx:03d}",
            "island": members[0]["island"],
            "latitude": float(np.mean([float(m["latitude"]) for m in members])),
            "longitude": float(np.mean([float(m["longitude"]) for m in members])),
            "member_count": len(members),
            "member_ids": ";".join(m["discovery_id"] for m in members),
        })
    return output


def min_distance(cluster: dict[str, object], zones: list[dict[str, str]]) -> float:
    same = [z for z in zones if z["island"] == cluster["island"]]
    if not same:
        return math.inf
    point = (float(cluster["latitude"]), float(cluster["longitude"]))
    distances = []
    for zone in same:
        radius = float(zone.get("zone_radius_km") or 0.0)
        d = haversine_km(point, (float(zone["latitude"]), float(zone["longitude"]))) - radius
        distances.append(max(0.0, d))
    return min(distances)


def recovery_summary(clusters: list[dict[str, object]], zones: list[dict[str, str]]) -> dict[str, float]:
    distances = np.asarray([min_distance(c, zones) for c in clusters], dtype=float)
    finite = distances[np.isfinite(distances)]
    out = {
        "cluster_count": len(clusters),
        "median_min_distance_km": float(np.median(finite)) if len(finite) else math.inf,
        "mean_min_distance_km": float(np.mean(finite)) if len(finite) else math.inf,
    }
    for radius in RADII_KM:
        out[f"recall_within_{radius:g}km"] = float(np.mean(distances <= radius))
    return out


def topk_curve(clusters: list[dict[str, object]], ranked: list[dict[str, str]]) -> list[dict[str, object]]:
    out = []
    for k in range(1, len(ranked) + 1):
        summary = recovery_summary(clusters, ranked[:k])
        out.append({"k": k, **summary})
    return out


def random_comparison(
    clusters: list[dict[str, object]],
    zones: list[dict[str, str]],
    selected: list[dict[str, str]],
    draws: int,
    seed: int,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    quota = defaultdict(int)
    pools = defaultdict(list)
    for row in selected:
        quota[row["island"]] += 1
    for row in zones:
        pools[row["island"]].append(row)
    observed = recovery_summary(clusters, selected)
    random_rows = []
    for _ in range(draws):
        draw = []
        for island, count in sorted(quota.items()):
            pool = pools[island]
            if len(pool) < count:
                raise ValueError(f"not enough zones on {island} for stratified random comparison")
            idx = rng.choice(len(pool), size=count, replace=False)
            draw.extend(pool[int(i)] for i in idx)
        random_rows.append(recovery_summary(clusters, draw))
    result: dict[str, object] = {"draws": draws, "seed": seed, "observed": observed, "random": {}}
    metrics = ["median_min_distance_km"] + [f"recall_within_{r:g}km" for r in RADII_KM]
    for metric in metrics:
        values = np.asarray([float(r[metric]) for r in random_rows])
        obs = float(observed[metric])
        if metric == "median_min_distance_km":
            p = float((1 + np.sum(values <= obs)) / (draws + 1))
        else:
            p = float((1 + np.sum(values >= obs)) / (draws + 1))
        result["random"][metric] = {
            "median": float(np.median(values)),
            "q05": float(np.quantile(values, 0.05)),
            "q95": float(np.quantile(values, 0.95)),
            "one_sided_p": p,
        }
    return result


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def run(args: argparse.Namespace) -> dict[str, object]:
    zones = read_rows(args.zones)
    discoveries = read_rows(args.discoveries)
    require(zones, {"zone_id", "island", "latitude", "longitude", "frozen_rank"}, "zones")
    require(discoveries, {"discovery_id", "island", "latitude", "longitude"}, "discoveries")
    validate_coordinates(zones, "zone_id", "zones")
    validate_coordinates(discoveries, "discovery_id", "discoveries")
    ranked = sorted(zones, key=lambda r: (int(r["frozen_rank"]), r["zone_id"]))
    args.output.mkdir(parents=True, exist_ok=True)
    all_results = {}
    for scale in CLUSTER_SCALES_KM:
        clusters = cluster_points(discoveries, scale)
        write_csv(args.output / f"discovery_clusters_{scale:g}km.csv", clusters)
        curve = topk_curve(clusters, ranked)
        write_csv(args.output / f"topk_recovery_{scale:g}km.csv", curve)
        comparison = random_comparison(clusters, zones, ranked, args.random_draws, args.seed + int(scale * 1000))
        all_results[f"cluster_{scale:g}km"] = comparison
    primary = all_results["cluster_0.5km"]
    random_median = float(primary["random"]["median_min_distance_km"]["median"])
    observed_median = float(primary["observed"]["median_min_distance_km"])
    decision = {
        "input_zone_count": len(zones),
        "input_discovery_count": len(discoveries),
        "primary_cluster_count": int(primary["observed"]["cluster_count"]),
        "observed_median_distance_km": observed_median,
        "random_median_distance_km": random_median,
        "closer_than_random_median": bool(observed_median < random_median),
        "supports_positive_only_recovery_claim": bool(observed_median < random_median),
        "does_not_support_detection_or_occupancy_claims": True,
    }
    (args.output / "random_comparison.json").write_text(json.dumps(all_results, indent=2) + "\n", encoding="utf-8")
    (args.output / "positive_only_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zones", type=Path, required=True)
    parser.add_argument("--discoveries", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/positive_only_recovery"))
    parser.add_argument("--random-draws", type=int, default=999)
    parser.add_argument("--seed", type=int, default=20260718)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2))


if __name__ == "__main__":
    main()
