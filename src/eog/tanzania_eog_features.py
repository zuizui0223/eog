"""Training-only EOG structural features for the Tanzania benchmark.

The module consumes an already-frozen Tanzania design contract. It never fits
an occurrence model or computes a performance metric. Within every outer fold,
only training presences can act as anchors. Training rows are additionally
cross-fitted by removing the target row itself from the anchor set.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import heapq
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

EARTH_RADIUS_KM = 6371.0088
FEATURE_SCHEMA_VERSION = "tanzania_eog_features_v1"
FROZEN_DESIGN_FINGERPRINT = (
    "f8b37bb30d230f92ad323870020d34e2225f898b85394124b965a2d0ecdeb324"
)
FROZEN_ELIGIBLE_SPECIES_SHA256 = (
    "4859178d155db2594a635896d794d1af4c4d655da924489d41ff64e8fc57f135"
)
FROZEN_SCENARIO_IDS = (
    "survey_c04",
    "survey_c03",
    "survey_c02",
    "survey_c01",
)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_jsonl_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(canonical_json(row).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_canonical_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(row))
            handle.write("\n")
    return canonical_jsonl_sha256(rows)


def _finite_float(value: object, label: str) -> float:
    try:
        result = float(value)
    except Exception as exc:
        raise ValueError(f"{label} must be numeric: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite: {value!r}")
    return result


def _binary(value: object, label: str) -> int:
    text = str(value).strip()
    if text in {"0", "0.0"}:
        return 0
    if text in {"1", "1.0"}:
        return 1
    raise ValueError(f"{label} must be binary 0/1: {value!r}")


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    lat1, lon1, lat2, lon2 = map(
        math.radians,
        (latitude_a, longitude_a, latitude_b, longitude_b),
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    return float(2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(value))))


@dataclass(frozen=True)
class SiteRecord:
    site_id: str
    region: str
    patch_number: int
    latitude: float
    longitude: float
    node_id: str

    def __post_init__(self) -> None:
        if not self.site_id.strip() or not self.node_id.strip():
            raise ValueError("site_id and node_id must be non-empty")
        if self.region not in {"E", "W"}:
            raise ValueError(f"unexpected Tanzania region: {self.region!r}")
        if self.patch_number <= 0:
            raise ValueError("patch_number must be positive")
        if not math.isfinite(self.latitude) or not math.isfinite(self.longitude):
            raise ValueError("site coordinates must be finite")
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("site latitude outside [-90, 90]")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("site longitude outside [-180, 180]")


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    site_name: str
    region: str
    patch_number: int
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.site_name.strip():
            raise ValueError("node_id and site_name must be non-empty")
        if self.region not in {"E", "W"}:
            raise ValueError(f"unexpected Tanzania region: {self.region!r}")
        if self.patch_number <= 0:
            raise ValueError("patch_number must be positive")
        if not math.isfinite(self.latitude) or not math.isfinite(self.longitude):
            raise ValueError("node coordinates must be finite")


@dataclass(frozen=True)
class ScenarioTargetFeature:
    scenario_id: str
    radius_km: float
    reachable: bool
    normalized_geographic_bottleneck: float | None


@dataclass(frozen=True)
class TargetStructuralFeature:
    feature_valid: bool
    failure_reason: str | None
    global_anchor_count: int
    same_region_anchor_count: int
    anchor_set_sha256: str | None
    nearest_anchor_distance_km: float | None
    log10_1p_nearest_anchor_km: float | None
    eog_connected_frequency: float | None
    eog_median_normalized_bottleneck: float | None
    scenarios: tuple[ScenarioTargetFeature, ...]


class TanzaniaRegionGraph:
    """One verified regional patch graph across frozen geometry-only scenarios."""

    def __init__(
        self,
        region: str,
        nodes: Sequence[NodeRecord],
        scenario_radii_km: Mapping[str, float],
    ) -> None:
        if region not in {"E", "W"}:
            raise ValueError(f"unexpected Tanzania graph region: {region!r}")
        ordered = tuple(sorted(nodes, key=lambda row: row.node_id))
        if len(ordered) < 2 or any(row.region != region for row in ordered):
            raise ValueError("regional graph requires at least two nodes in one region")
        if len({row.node_id for row in ordered}) != len(ordered):
            raise ValueError("regional graph node IDs must be unique")
        if len({row.site_name for row in ordered}) != len(ordered):
            raise ValueError("regional graph node site names must be unique")
        scenario_items = tuple(
            (str(scenario_id), _finite_float(radius, f"radius {scenario_id}"))
            for scenario_id, radius in scenario_radii_km.items()
        )
        if not scenario_items or len({item[0] for item in scenario_items}) != len(
            scenario_items
        ):
            raise ValueError("scenario IDs must be non-empty and unique")
        if any(not scenario_id or radius <= 0.0 for scenario_id, radius in scenario_items):
            raise ValueError("scenario IDs/radii must be non-empty and positive")
        radius_values = [radius for _, radius in scenario_items]
        if radius_values != sorted(radius_values):
            raise ValueError("scenario radii must be declared in ascending order")

        self.region = region
        self.nodes = ordered
        self.scenario_items = scenario_items
        self.node_index = {row.node_id: index for index, row in enumerate(ordered)}
        self.site_node_id = {row.site_name: row.node_id for row in ordered}
        n_nodes = len(ordered)
        distance = np.zeros((n_nodes, n_nodes), dtype=float)
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                value = haversine_km(
                    ordered[i].latitude,
                    ordered[i].longitude,
                    ordered[j].latitude,
                    ordered[j].longitude,
                )
                if value <= 0.0:
                    raise ValueError(
                        "distinct Tanzania nodes cannot share identical coordinates: "
                        f"{ordered[i].node_id!r}, {ordered[j].node_id!r}"
                    )
                distance[i, j] = value
                distance[j, i] = value
        self.distance_km = distance
        self.adjacency: dict[str, tuple[tuple[tuple[int, float], ...], ...]] = {}
        for scenario_id, radius in scenario_items:
            rows: list[list[tuple[int, float]]] = [[] for _ in range(n_nodes)]
            for i in range(n_nodes):
                for j in range(i + 1, n_nodes):
                    value = float(distance[i, j])
                    if value <= radius + 1e-12:
                        rows[i].append((j, value))
                        rows[j].append((i, value))
            self.adjacency[scenario_id] = tuple(tuple(row) for row in rows)

    def evaluate_target(
        self,
        *,
        target_node_id: str,
        anchor_node_ids: Sequence[str],
    ) -> tuple[ScenarioTargetFeature, ...]:
        if target_node_id not in self.node_index:
            raise ValueError(f"target node absent from {self.region} graph: {target_node_id}")
        anchors = tuple(sorted(set(str(value) for value in anchor_node_ids)))
        missing = sorted(set(anchors) - set(self.node_index))
        if missing:
            raise ValueError(f"anchor nodes absent from {self.region} graph: {missing}")
        if target_node_id in anchors:
            raise ValueError("target node must be excluded from its own anchor set")
        target = self.node_index[target_node_id]

        output: list[ScenarioTargetFeature] = []
        for scenario_id, radius in self.scenario_items:
            if not anchors:
                output.append(
                    ScenarioTargetFeature(
                        scenario_id=scenario_id,
                        radius_km=radius,
                        reachable=False,
                        normalized_geographic_bottleneck=None,
                    )
                )
                continue
            bottleneck = np.full(len(self.nodes), np.inf, dtype=float)
            queue: list[tuple[float, int]] = []
            for node_id in anchors:
                index = self.node_index[node_id]
                bottleneck[index] = 0.0
                heapq.heappush(queue, (0.0, index))
            while queue:
                current, node = heapq.heappop(queue)
                if current != bottleneck[node]:
                    continue
                for neighbour, edge_distance in self.adjacency[scenario_id][node]:
                    candidate = max(current, edge_distance)
                    if candidate < bottleneck[neighbour]:
                        bottleneck[neighbour] = candidate
                        heapq.heappush(queue, (candidate, neighbour))
            value = float(bottleneck[target])
            reachable = math.isfinite(value)
            output.append(
                ScenarioTargetFeature(
                    scenario_id=scenario_id,
                    radius_km=radius,
                    reachable=reachable,
                    normalized_geographic_bottleneck=(
                        value / radius if reachable else None
                    ),
                )
            )
        return tuple(output)


def evaluate_structural_target(
    *,
    target_site_id: str,
    anchor_site_ids: Sequence[str],
    sites: Mapping[str, SiteRecord],
    graphs: Mapping[str, TanzaniaRegionGraph],
) -> TargetStructuralFeature:
    if target_site_id not in sites:
        raise ValueError(f"unknown target site: {target_site_id}")
    anchors = tuple(sorted(set(str(value) for value in anchor_site_ids)))
    if target_site_id in anchors:
        raise ValueError("target site must be excluded from its own anchor set")
    missing = sorted(set(anchors) - set(sites))
    if missing:
        raise ValueError(f"unknown anchor sites: {missing}")
    if not anchors:
        return TargetStructuralFeature(
            feature_valid=False,
            failure_reason="no_training_presence_anchor_after_row_exclusion",
            global_anchor_count=0,
            same_region_anchor_count=0,
            anchor_set_sha256=None,
            nearest_anchor_distance_km=None,
            log10_1p_nearest_anchor_km=None,
            eog_connected_frequency=None,
            eog_median_normalized_bottleneck=None,
            scenarios=(),
        )

    target = sites[target_site_id]
    nearest = min(
        haversine_km(
            target.latitude,
            target.longitude,
            sites[anchor].latitude,
            sites[anchor].longitude,
        )
        for anchor in anchors
    )
    graph = graphs.get(target.region)
    if graph is None:
        raise ValueError(f"missing regional graph for {target.region}")
    same_region_sites = tuple(
        anchor for anchor in anchors if sites[anchor].region == target.region
    )
    same_region_nodes = tuple(sites[anchor].node_id for anchor in same_region_sites)
    scenario_features = graph.evaluate_target(
        target_node_id=target.node_id,
        anchor_node_ids=same_region_nodes,
    )
    connected = [feature.reachable for feature in scenario_features]
    finite_bottlenecks = [
        feature.normalized_geographic_bottleneck
        for feature in scenario_features
        if feature.normalized_geographic_bottleneck is not None
    ]
    median_bottleneck = (
        float(np.median(np.asarray(finite_bottlenecks, dtype=float)))
        if finite_bottlenecks
        else None
    )
    return TargetStructuralFeature(
        feature_valid=True,
        failure_reason=None,
        global_anchor_count=len(anchors),
        same_region_anchor_count=len(same_region_sites),
        anchor_set_sha256=canonical_sha256(list(anchors)),
        nearest_anchor_distance_km=float(nearest),
        log10_1p_nearest_anchor_km=float(math.log10(1.0 + nearest)),
        eog_connected_frequency=float(sum(connected) / len(connected)),
        eog_median_normalized_bottleneck=median_bottleneck,
        scenarios=scenario_features,
    )


def _normalize_nodes(
    rows: Sequence[Mapping[str, object]],
    region: str,
    *,
    strict_source_shape: bool,
) -> tuple[NodeRecord, ...]:
    output: list[NodeRecord] = []
    for row in rows:
        patch_number = int(row["patch_number"])
        name = str(row["name"]).strip()
        output.append(
            NodeRecord(
                node_id=f"{region}:{patch_number:02d}:{name}",
                site_name=name,
                region=region,
                patch_number=patch_number,
                latitude=_finite_float(row["centroid_lat"], f"{region} node latitude"),
                longitude=_finite_float(
                    row["centroid_long"], f"{region} node longitude"
                ),
            )
        )
    if strict_source_shape:
        if len(output) != 42 or {row.patch_number for row in output} != set(
            range(1, 43)
        ):
            raise ValueError(f"{region} must contain patch numbers 1..42 exactly")
    return tuple(sorted(output, key=lambda row: row.node_id))


def _normalize_sites(
    rows: Sequence[Mapping[str, object]],
    nodes_by_region: Mapping[str, Sequence[NodeRecord]],
    *,
    strict_source_shape: bool,
) -> dict[str, SiteRecord]:
    node_lookup = {
        region: {node.site_name: node for node in nodes}
        for region, nodes in nodes_by_region.items()
    }
    output: dict[str, SiteRecord] = {}
    for row in rows:
        site_id = str(row["name"]).strip()
        region = str(row["region"]).strip()
        if site_id in output:
            raise ValueError(f"duplicate site ID: {site_id}")
        if region not in node_lookup or site_id not in node_lookup[region]:
            raise ValueError(f"survey site absent from {region} node table: {site_id}")
        node = node_lookup[region][site_id]
        patch_number = int(row["patch_number"])
        latitude = _finite_float(row["centroid_lat"], f"site {site_id} latitude")
        longitude = _finite_float(row["centroid_long"], f"site {site_id} longitude")
        if patch_number != node.patch_number:
            raise ValueError(f"site/node patch-number mismatch for {site_id}")
        if abs(latitude - node.latitude) > 1e-12 or abs(longitude - node.longitude) > 1e-12:
            raise ValueError(f"site/node coordinate mismatch for {site_id}")
        output[site_id] = SiteRecord(
            site_id=site_id,
            region=region,
            patch_number=patch_number,
            latitude=latitude,
            longitude=longitude,
            node_id=node.node_id,
        )
    if strict_source_shape:
        if len(output) != 14:
            raise ValueError(f"expected 14 Tanzania survey sites, got {len(output)}")
        counts = Counter(row.region for row in output.values())
        if counts != Counter({"E": 9, "W": 5}):
            raise ValueError(f"unexpected Tanzania survey-region counts: {counts}")
    return dict(sorted(output.items()))


def _occurrence_matrix(
    rows: Sequence[Mapping[str, object]],
    *,
    site_ids: Sequence[str],
    species_ids: Sequence[str],
) -> dict[str, dict[str, int]]:
    sites = set(site_ids)
    species = set(species_ids)
    output: dict[str, dict[str, int]] = {name: {} for name in species_ids}
    for row in rows:
        species_id = str(row["species"]).strip()
        if species_id not in species:
            continue
        site_id = str(row["name"]).strip()
        if site_id not in sites:
            raise ValueError(f"unknown occurrence site: {site_id}")
        if site_id in output[species_id]:
            raise ValueError(f"duplicate occurrence row: {species_id}@{site_id}")
        output[species_id][site_id] = _binary(
            row["occur"], f"occurrence {species_id}@{site_id}"
        )
    expected_sites = set(site_ids)
    for species_id in species_ids:
        observed = set(output[species_id])
        if observed != expected_sites:
            raise ValueError(
                f"incomplete occurrence matrix for {species_id}: "
                f"missing={sorted(expected_sites-observed)}, extra={sorted(observed-expected_sites)}"
            )
    return output


def _validate_design(
    design: Mapping[str, Any],
    *,
    enforce_frozen_contract: bool,
) -> tuple[tuple[str, ...], dict[str, tuple[dict[str, Any], ...]]]:
    if design.get("status") != "tanzania_geometry_and_formula_contract_frozen_before_outcomes":
        raise ValueError("verified Tanzania geometry/formula contract is required")
    for flag in (
        "species_outcomes_inspected",
        "model_fitted",
        "current_flow_computed",
        "eog_score_computed",
    ):
        if design.get(flag) is not False:
            raise ValueError(f"Tanzania design scientific-boundary flag is not false: {flag}")
    if enforce_frozen_contract and design.get("design_fingerprint") != FROZEN_DESIGN_FINGERPRINT:
        raise ValueError("Tanzania design fingerprint drifted before feature construction")
    source = dict(design.get("source") or {})
    eligible = tuple(str(value) for value in source.get("eligible_species", []))
    if not eligible or len(set(eligible)) != len(eligible):
        raise ValueError("Tanzania design has no unique eligible species list")
    if enforce_frozen_contract:
        if source.get("eligible_species_sha256") != FROZEN_ELIGIBLE_SPECIES_SHA256:
            raise ValueError("Tanzania eligible species fingerprint drifted")
        if len(eligible) != 60:
            raise ValueError("Tanzania frozen source cohort must contain 60 species")

    cv = dict(design.get("cross_validation") or {})
    partitions: dict[str, tuple[dict[str, Any], ...]] = {}
    for output_name, contract_name in (
        ("primary_loso", "primary"),
        ("spatial_mst_block", "spatial_sensitivity"),
    ):
        payload = dict(cv.get(contract_name) or {})
        folds = payload.get("folds")
        if not isinstance(folds, list) or not folds:
            raise ValueError(f"Tanzania design has no {contract_name} folds")
        partitions[output_name] = tuple(dict(fold) for fold in folds)
    return eligible, partitions


def _scenario_mapping(
    design: Mapping[str, Any],
    region: str,
    *,
    enforce_frozen_contract: bool,
) -> dict[str, float]:
    graph = dict(design.get("eog_graph") or {})
    regions = dict(graph.get("regions") or {})
    payload = dict(regions.get(region) or {})
    radii = payload.get("scenario_radii_km")
    if not isinstance(radii, dict) or not radii:
        raise ValueError(f"Tanzania design has no {region} scenario radii")
    output = {
        str(key): _finite_float(value, f"{region} radius {key}")
        for key, value in radii.items()
    }
    if enforce_frozen_contract and tuple(output) != FROZEN_SCENARIO_IDS:
        raise ValueError(f"Tanzania {region} scenario IDs drifted: {tuple(output)}")
    return output


def _scenario_dict(feature: ScenarioTargetFeature) -> dict[str, Any]:
    return {
        "scenario_id": feature.scenario_id,
        "radius_km": feature.radius_km,
        "reachable": feature.reachable,
        "normalized_geographic_bottleneck": (
            feature.normalized_geographic_bottleneck
        ),
    }


def _record_from_feature(
    *,
    analysis_partition: str,
    fold_id: str,
    species_id: str,
    target: SiteRecord,
    role: str,
    outer_training_site_count: int,
    outer_training_presence_count: int,
    row_exclusion_applied: bool,
    feature: TargetStructuralFeature,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "analysis_partition": analysis_partition,
        "fold_id": fold_id,
        "species_id": species_id,
        "site_id": target.site_id,
        "region": target.region,
        "target_node_id": target.node_id,
        "role": role,
        "outer_training_site_count": outer_training_site_count,
        "outer_training_presence_count": outer_training_presence_count,
        "row_exclusion_applied": row_exclusion_applied,
        "heldout_label_used_in_construction": False,
        "feature_valid": feature.feature_valid,
        "failure_reason": feature.failure_reason,
        "global_anchor_count": feature.global_anchor_count,
        "same_region_anchor_count": feature.same_region_anchor_count,
        "anchor_set_sha256": feature.anchor_set_sha256,
        "nearest_anchor_distance_km": feature.nearest_anchor_distance_km,
        "log10_1p_nearest_anchor_km": feature.log10_1p_nearest_anchor_km,
        "eog_connected_frequency": feature.eog_connected_frequency,
        "eog_median_normalized_bottleneck": (
            feature.eog_median_normalized_bottleneck
        ),
        "scenario_features": [_scenario_dict(item) for item in feature.scenarios],
    }
    record["row_fingerprint_sha256"] = canonical_sha256(record)
    return record


def generate_tanzania_eog_features(
    *,
    sites_rows: Sequence[Mapping[str, object]],
    east_node_rows: Sequence[Mapping[str, object]],
    west_node_rows: Sequence[Mapping[str, object]],
    occurrence_rows: Sequence[Mapping[str, object]],
    design: Mapping[str, Any],
    enforce_frozen_contract: bool = True,
    strict_source_shape: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible, partitions = _validate_design(
        design, enforce_frozen_contract=enforce_frozen_contract
    )
    nodes_by_region = {
        "E": _normalize_nodes(
            east_node_rows, "E", strict_source_shape=strict_source_shape
        ),
        "W": _normalize_nodes(
            west_node_rows, "W", strict_source_shape=strict_source_shape
        ),
    }
    sites = _normalize_sites(
        sites_rows,
        nodes_by_region,
        strict_source_shape=strict_source_shape,
    )
    site_ids = tuple(sorted(sites))
    occurrence = _occurrence_matrix(
        occurrence_rows,
        site_ids=site_ids,
        species_ids=eligible,
    )
    graphs = {
        region: TanzaniaRegionGraph(
            region,
            nodes_by_region[region],
            _scenario_mapping(
                design,
                region,
                enforce_frozen_contract=enforce_frozen_contract,
            ),
        )
        for region in ("E", "W")
    }

    records: list[dict[str, Any]] = []
    applicability: list[dict[str, Any]] = []
    all_sites = set(site_ids)
    for analysis_partition, folds in partitions.items():
        for fold in folds:
            fold_id = str(fold.get("fold_id") or "").strip()
            heldout = {str(value) for value in fold.get("held_out_sites", [])}
            if not fold_id or not heldout or not heldout.issubset(all_sites):
                raise ValueError(f"invalid Tanzania fold declaration: {fold}")
            training = all_sites - heldout
            if not training:
                raise ValueError(f"Tanzania fold has no training sites: {fold_id}")
            for species_id in eligible:
                response = occurrence[species_id]
                outer_training_presences = tuple(
                    sorted(site_id for site_id in training if response[site_id] == 1)
                )
                group_records: list[dict[str, Any]] = []
                for site_id in site_ids:
                    role = "heldout" if site_id in heldout else "training"
                    row_anchors = (
                        outer_training_presences
                        if role == "heldout"
                        else tuple(
                            anchor
                            for anchor in outer_training_presences
                            if anchor != site_id
                        )
                    )
                    feature = evaluate_structural_target(
                        target_site_id=site_id,
                        anchor_site_ids=row_anchors,
                        sites=sites,
                        graphs=graphs,
                    )
                    record = _record_from_feature(
                        analysis_partition=analysis_partition,
                        fold_id=fold_id,
                        species_id=species_id,
                        target=sites[site_id],
                        role=role,
                        outer_training_site_count=len(training),
                        outer_training_presence_count=len(outer_training_presences),
                        row_exclusion_applied=role == "training",
                        feature=feature,
                    )
                    records.append(record)
                    group_records.append(record)

                training_records = [
                    row for row in group_records if row["role"] == "training"
                ]
                heldout_records = [
                    row for row in group_records if row["role"] == "heldout"
                ]
                valid_training_presence = sum(
                    bool(row["feature_valid"])
                    and response[str(row["site_id"])] == 1
                    for row in training_records
                )
                valid_training_absence = sum(
                    bool(row["feature_valid"])
                    and response[str(row["site_id"])] == 0
                    for row in training_records
                )
                heldout_valid = sum(bool(row["feature_valid"]) for row in heldout_records)
                estimable = (
                    valid_training_presence > 0
                    and valid_training_absence > 0
                    and heldout_valid > 0
                )
                if heldout_valid == 0:
                    failure_reason = "no_valid_heldout_structural_features"
                elif valid_training_presence == 0 or valid_training_absence == 0:
                    failure_reason = "valid_training_structural_rows_single_class"
                else:
                    failure_reason = None
                applicability.append(
                    {
                        "analysis_partition": analysis_partition,
                        "fold_id": fold_id,
                        "species_id": species_id,
                        "training_site_count": len(training_records),
                        "heldout_site_count": len(heldout_records),
                        "training_valid_count": sum(
                            bool(row["feature_valid"]) for row in training_records
                        ),
                        "training_invalid_count": sum(
                            not bool(row["feature_valid"])
                            for row in training_records
                        ),
                        "training_valid_presence_count": valid_training_presence,
                        "training_valid_absence_count": valid_training_absence,
                        "heldout_valid_count": heldout_valid,
                        "heldout_invalid_count": len(heldout_records) - heldout_valid,
                        "anchor_feature_model_estimable": estimable,
                        "failure_reason": failure_reason,
                        "heldout_labels_used": False,
                        "performance_metric_computed": False,
                    }
                )

    records.sort(
        key=lambda row: (
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
            str(row["site_id"]),
        )
    )
    applicability.sort(
        key=lambda row: (
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
        )
    )
    return records, applicability


def _frequency_distribution(
    rows: Sequence[Mapping[str, Any]],
    *,
    field: str,
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(field)
        key = "null" if value is None else format(float(value), ".12g")
        counts[key] += 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def build_feature_manifest(
    *,
    records: Sequence[Mapping[str, Any]],
    applicability: Sequence[Mapping[str, Any]],
    design: Mapping[str, Any],
) -> dict[str, Any]:
    partition_summary: dict[str, Any] = {}
    for partition in sorted({str(row["analysis_partition"]) for row in records}):
        selected = [row for row in records if row["analysis_partition"] == partition]
        selected_app = [
            row for row in applicability if row["analysis_partition"] == partition
        ]
        heldout = [row for row in selected if row["role"] == "heldout"]
        partition_summary[partition] = {
            "n_rows": len(selected),
            "n_valid_rows": sum(bool(row["feature_valid"]) for row in selected),
            "n_invalid_rows": sum(not bool(row["feature_valid"]) for row in selected),
            "invalid_by_role": dict(
                sorted(
                    Counter(
                        str(row["role"])
                        for row in selected
                        if not bool(row["feature_valid"])
                    ).items()
                )
            ),
            "invalid_by_reason": dict(
                sorted(
                    Counter(
                        str(row["failure_reason"])
                        for row in selected
                        if not bool(row["feature_valid"])
                    ).items()
                )
            ),
            "n_heldout_rows": len(heldout),
            "n_valid_heldout_rows": sum(
                bool(row["feature_valid"]) for row in heldout
            ),
            "heldout_connected_frequency_distribution": _frequency_distribution(
                [row for row in heldout if bool(row["feature_valid"])],
                field="eog_connected_frequency",
            ),
            "heldout_without_same_region_anchor": sum(
                bool(row["feature_valid"])
                and int(row["same_region_anchor_count"]) == 0
                for row in heldout
            ),
            "n_species_fold_groups": len(selected_app),
            "n_anchor_feature_model_estimable": sum(
                bool(row["anchor_feature_model_estimable"])
                for row in selected_app
            ),
            "n_anchor_feature_model_nonestimable": sum(
                not bool(row["anchor_feature_model_estimable"])
                for row in selected_app
            ),
            "nonestimable_by_reason": dict(
                sorted(
                    Counter(
                        str(row["failure_reason"])
                        for row in selected_app
                        if not bool(row["anchor_feature_model_estimable"])
                    ).items()
                )
            ),
        }
    return {
        "status": "tanzania_training_only_eog_features_built",
        "schema_version": FEATURE_SCHEMA_VERSION,
        "source_doi": "10.5061/dryad.p042h0c",
        "source_version_id": 23134,
        "design_fingerprint": design.get("design_fingerprint"),
        "eligible_species_sha256": dict(design.get("source") or {}).get(
            "eligible_species_sha256"
        ),
        "scenario_ids": list(FROZEN_SCENARIO_IDS),
        "n_feature_rows": len(records),
        "n_applicability_rows": len(applicability),
        "feature_rows_sha256": canonical_jsonl_sha256(records),
        "applicability_rows_sha256": canonical_jsonl_sha256(applicability),
        "partitions": partition_summary,
        "construction_contract": {
            "anchors": "outer-training presences only",
            "training_row_crossfit": (
                "remove the target training site from its own anchor set before "
                "nearest-distance and EOG construction"
            ),
            "heldout_anchor_rule": "all outer-training presences; heldout label unused",
            "nearest_anchor_scope": (
                "all training-presence survey sites across both regions"
            ),
            "eog_scope": (
                "same-region 42-node graph only; cross-region EOG edges prohibited"
            ),
            "no_same_region_anchor": (
                "nearest distance remains finite when global anchors exist; EOG "
                "connected frequency is zero and bottleneck is null"
            ),
            "no_global_anchor": "row marked invalid; no imputation",
        },
        "heldout_labels_used_in_construction": False,
        "heldout_labels_exported": False,
        "occurrence_model_fitted": False,
        "current_flow_computed": False,
        "performance_metric_computed": False,
        "eog_performance_inspected": False,
        "next_gate": (
            "freeze/execute source-faithful current-flow candidates, then fit the "
            "already-declared held-out probability tiers and score untouched labels"
        ),
    }


def write_feature_artifacts(
    *,
    output_dir: Path,
    records: Sequence[Mapping[str, Any]],
    applicability: Sequence[Mapping[str, Any]],
    design: Mapping[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    primary = [
        row for row in records if row["analysis_partition"] == "primary_loso"
    ]
    sensitivity = [
        row for row in records if row["analysis_partition"] == "spatial_mst_block"
    ]
    write_canonical_jsonl(output_dir / "primary_features.jsonl", primary)
    write_canonical_jsonl(
        output_dir / "spatial_sensitivity_features.jsonl", sensitivity
    )
    write_canonical_jsonl(output_dir / "applicability.jsonl", applicability)
    manifest = build_feature_manifest(
        records=records,
        applicability=applicability,
        design=design,
    )
    (output_dir / "feature_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
