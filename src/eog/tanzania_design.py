"""Pre-outcome geometry and formula contract for the Tanzania benchmark.

The module derives folds and EOG graph scales from verified coordinates only.
It also records the executable model roles recovered from the official Dryad
scripts.  It never fits a species model or scores an occurrence outcome.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

EARTH_RADIUS_KM = 6371.0088
MST_RADIUS_QUANTILES = (0.50, 0.75, 0.90, 1.00)
RESISTANCE_LEVELS = (1, 2, 4, 8, 16, 32, 64, 128)
EXPECTED_ELIGIBLE_SPECIES = 60
EXPECTED_ELIGIBLE_SPECIES_SHA256 = (
    "4859178d155db2594a635896d794d1af4c4d655da924489d41ff64e8fc57f135"
)
HELDOUT_L2_PENALTY = 1.0


@dataclass(frozen=True)
class GeometryPoint:
    node_id: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not np.isfinite((self.latitude, self.longitude)).all():
            raise ValueError("coordinates must be finite")
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude outside [-90, 90]")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude outside [-180, 180]")


@dataclass(frozen=True)
class MstEdge:
    source_id: str
    target_id: str
    distance_km: float

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id or self.source_id == self.target_id:
            raise ValueError("MST edge endpoints must be distinct non-empty IDs")
        if self.source_id > self.target_id:
            raise ValueError("MST edge IDs must be stored in lexical order")
        if not np.isfinite(self.distance_km) or self.distance_km <= 0.0:
            raise ValueError("MST distance must be finite and positive")


def haversine_km(a: GeometryPoint, b: GeometryPoint) -> float:
    lat1, lon1, lat2, lon2 = map(
        math.radians,
        (a.latitude, a.longitude, b.latitude, b.longitude),
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    return float(2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(value))))


def stable_mst(points: Sequence[GeometryPoint]) -> tuple[MstEdge, ...]:
    """Return a deterministic Prim MST with lexical tie breaking."""
    ordered = tuple(sorted(points, key=lambda point: point.node_id))
    if len(ordered) < 2 or len({point.node_id for point in ordered}) != len(ordered):
        raise ValueError("points must contain at least two unique node IDs")

    selected: set[int] = {0}
    result: list[MstEdge] = []
    while len(selected) < len(ordered):
        candidates: list[tuple[float, str, str, int, int]] = []
        for source in sorted(selected):
            for target in range(len(ordered)):
                if target in selected:
                    continue
                distance = haversine_km(ordered[source], ordered[target])
                first, second = sorted(
                    (ordered[source].node_id, ordered[target].node_id)
                )
                candidates.append((distance, first, second, source, target))
        if not candidates:
            raise RuntimeError("failed to extend deterministic MST")
        distance, first, second, _source, target = min(candidates)
        if distance <= 0.0:
            raise ValueError(
                f"duplicate geometry for distinct nodes {first!r} and {second!r}"
            )
        result.append(MstEdge(first, second, float(distance)))
        selected.add(target)
    return tuple(result)


def mst_quantile_radii(
    edges: Sequence[MstEdge],
    quantiles: Sequence[float] = MST_RADIUS_QUANTILES,
) -> dict[str, float]:
    if not edges:
        raise ValueError("at least one MST edge is required")
    values = np.asarray([edge.distance_km for edge in edges], dtype=float)
    output: dict[str, float] = {}
    previous = -math.inf
    for quantile in quantiles:
        value = float(quantile)
        if not 0.0 < value <= 1.0:
            raise ValueError("MST radius quantiles must lie in (0, 1]")
        radius = float(np.quantile(values, value, method="linear"))
        if radius < previous:
            raise RuntimeError("MST radius quantiles are not monotonic")
        output[f"mst_q{int(round(value * 100)):02d}"] = radius
        previous = radius
    return output


def mst_spatial_blocks(
    points: Sequence[GeometryPoint],
    n_blocks: int,
) -> tuple[tuple[str, ...], ...]:
    """Cut the largest MST edges to obtain deterministic contiguous blocks."""
    ordered = tuple(sorted(points, key=lambda point: point.node_id))
    if not 2 <= n_blocks <= len(ordered):
        raise ValueError("n_blocks must lie between 2 and the number of points")
    edges = stable_mst(ordered)
    removed = {
        (edge.source_id, edge.target_id)
        for edge in sorted(
            edges,
            key=lambda edge: (
                -edge.distance_km,
                edge.source_id,
                edge.target_id,
            ),
        )[: n_blocks - 1]
    }
    adjacency: dict[str, set[str]] = {point.node_id: set() for point in ordered}
    for edge in edges:
        key = (edge.source_id, edge.target_id)
        if key in removed:
            continue
        adjacency[edge.source_id].add(edge.target_id)
        adjacency[edge.target_id].add(edge.source_id)

    components: list[tuple[str, ...]] = []
    visited: set[str] = set()
    for start in sorted(adjacency):
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        component: list[str] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbour in sorted(adjacency[node], reverse=True):
                if neighbour not in visited:
                    visited.add(neighbour)
                    stack.append(neighbour)
        components.append(tuple(sorted(component)))
    result = tuple(sorted(components))
    if len(result) != n_blocks:
        raise RuntimeError(
            f"MST cut produced {len(result)} blocks, expected {n_blocks}"
        )
    return result


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def eligible_species_sha256(species: Iterable[str]) -> str:
    ordered = sorted(str(value).strip() for value in species)
    if any(not value for value in ordered) or len(set(ordered)) != len(ordered):
        raise ValueError("eligible species IDs must be unique and non-empty")
    payload = json.dumps(ordered, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _site_records(sites: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in sites:
        site_id = str(row["name"]).strip()
        region = str(row["region"]).strip()
        if not site_id or site_id in seen:
            raise ValueError("site names must be non-empty and unique")
        if region not in {"E", "W"}:
            raise ValueError(f"unexpected Tanzania region: {region!r}")
        area = float(row["area_ha"])
        latitude = float(row["centroid_lat"])
        longitude = float(row["centroid_long"])
        patch_number = int(row["patch_number"])
        if not np.isfinite((area, latitude, longitude)).all() or area <= 0.0:
            raise ValueError(f"invalid site attributes for {site_id}")
        output.append(
            {
                "site_id": site_id,
                "region": region,
                "patch_number": patch_number,
                "area_ha": area,
                "latitude": latitude,
                "longitude": longitude,
            }
        )
        seen.add(site_id)
    if len(output) != 14:
        raise ValueError(f"expected 14 Tanzania sites, got {len(output)}")
    return sorted(output, key=lambda row: (str(row["region"]), str(row["site_id"])))


def _node_records(
    rows: Sequence[Mapping[str, object]],
    region: str,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    seen_patch: set[int] = set()
    seen_name: set[str] = set()
    for row in rows:
        patch_number = int(row["patch_number"])
        name = str(row["name"]).strip()
        if patch_number in seen_patch or not name or name in seen_name:
            raise ValueError(f"duplicate or blank {region} node identity")
        output.append(
            {
                "node_id": f"{region}:{patch_number:02d}:{name}",
                "name": name,
                "patch_number": patch_number,
                "area_ha": float(row["Area_ha"]),
                "latitude": float(row["centroid_lat"]),
                "longitude": float(row["centroid_long"]),
            }
        )
        seen_patch.add(patch_number)
        seen_name.add(name)
    if len(output) != 42 or seen_patch != set(range(1, 43)):
        raise ValueError(
            f"{region} node table must contain patch numbers 1..42 exactly"
        )
    if any(
        not np.isfinite(
            (row["area_ha"], row["latitude"], row["longitude"])
        ).all()
        or float(row["area_ha"]) <= 0.0
        for row in output
    ):
        raise ValueError(f"invalid {region} node attributes")
    return sorted(output, key=lambda row: int(row["patch_number"]))


def _verify_sites_are_nodes(
    sites: Sequence[Mapping[str, object]],
    nodes_by_region: Mapping[str, Sequence[Mapping[str, object]]],
) -> None:
    for site in sites:
        region = str(site["region"])
        lookup = {str(row["name"]): row for row in nodes_by_region[region]}
        node = lookup.get(str(site["site_id"]))
        if node is None:
            raise ValueError(f"survey site absent from {region} node table: {site['site_id']}")
        checks = (
            int(node["patch_number"]) == int(site["patch_number"]),
            abs(float(node["latitude"]) - float(site["latitude"])) <= 1e-12,
            abs(float(node["longitude"]) - float(site["longitude"])) <= 1e-12,
        )
        if not all(checks):
            raise ValueError(
                f"survey site/node identity mismatch for {site['site_id']}"
            )


def build_tanzania_design_contract(
    *,
    sites: Sequence[Mapping[str, object]],
    east_nodes: Sequence[Mapping[str, object]],
    west_nodes: Sequence[Mapping[str, object]],
    eligible_species: Sequence[str],
    source_formula_evidence: Mapping[str, bool],
) -> dict[str, object]:
    site_rows = _site_records(sites)
    nodes_by_region = {
        "E": _node_records(east_nodes, "E"),
        "W": _node_records(west_nodes, "W"),
    }
    _verify_sites_are_nodes(site_rows, nodes_by_region)

    eligible = sorted(str(value).strip() for value in eligible_species)
    eligible_hash = eligible_species_sha256(eligible)
    if len(eligible) != EXPECTED_ELIGIBLE_SPECIES:
        raise ValueError(
            f"eligible species count {len(eligible)} != frozen {EXPECTED_ELIGIBLE_SPECIES}"
        )
    if eligible_hash != EXPECTED_ELIGIBLE_SPECIES_SHA256:
        raise ValueError("eligible species fingerprint drifted from the pre-outcome freeze")
    if not source_formula_evidence or not all(source_formula_evidence.values()):
        missing = sorted(
            key for key, value in source_formula_evidence.items() if not value
        )
        raise ValueError(f"official source formula evidence missing: {missing}")

    primary_folds = [
        {
            "fold_id": f"LOSO_{index:02d}",
            "held_out_sites": [str(row["site_id"])],
            "held_out_region": str(row["region"]),
        }
        for index, row in enumerate(site_rows, start=1)
    ]

    block_folds: list[dict[str, object]] = []
    spatial_blocks: dict[str, list[list[str]]] = {}
    for region in ("E", "W"):
        region_sites = [row for row in site_rows if row["region"] == region]
        points = [
            GeometryPoint(
                str(row["site_id"]),
                float(row["latitude"]),
                float(row["longitude"]),
            )
            for row in region_sites
        ]
        n_blocks = max(2, int(math.floor(math.sqrt(len(points)) + 0.5)))
        blocks = mst_spatial_blocks(points, n_blocks)
        spatial_blocks[region] = [list(block) for block in blocks]
        for index, block in enumerate(blocks, start=1):
            block_folds.append(
                {
                    "fold_id": f"MSTBLOCK_{region}_{index:02d}",
                    "held_out_sites": list(block),
                    "held_out_region": region,
                }
            )

    reachability: dict[str, object] = {}
    for region in ("E", "W"):
        points = [
            GeometryPoint(
                str(row["node_id"]),
                float(row["latitude"]),
                float(row["longitude"]),
            )
            for row in nodes_by_region[region]
        ]
        edges = stable_mst(points)
        reachability[region] = {
            "n_nodes": len(points),
            "mst_edges": [asdict(edge) for edge in edges],
            "scenario_radii_km": mst_quantile_radii(edges),
            "mst_edge_sha256": canonical_sha256(
                [asdict(edge) for edge in edges]
            ),
        }

    contract: dict[str, object] = {
        "status": "tanzania_geometry_and_formula_contract_frozen_before_outcomes",
        "source": {
            "doi": "10.5061/dryad.p042h0c",
            "version_id": 23134,
            "n_sites": 14,
            "n_species": 89,
            "n_eligible_species": len(eligible),
            "eligible_species_rule": "presence >= 2 and absence >= 2",
            "eligible_species_sha256": eligible_hash,
            "eligible_species": eligible,
            "source_formula_evidence": dict(sorted(source_formula_evidence.items())),
        },
        "cross_validation": {
            "primary": {
                "name": "leave_one_fragment_out",
                "n_folds": len(primary_folds),
                "folds": primary_folds,
                "rationale": (
                    "maximal training size for 14 fragments; folds depend only on "
                    "verified site identity and never on species outcomes"
                ),
            },
            "spatial_sensitivity": {
                "name": "within_region_site_mst_blocks",
                "block_count_rule": "round(sqrt(n_sites_in_region)), minimum 2",
                "construction": (
                    "stable within-region site MST; cut the largest k-1 edges; "
                    "ties resolved lexically"
                ),
                "n_folds": len(block_folds),
                "blocks": spatial_blocks,
                "folds": block_folds,
                "applicability": (
                    "training class failures are reported; the global 2/2 source rule "
                    "guarantees LOSO class support but not block-fold support"
                ),
            },
        },
        "eog_graph": {
            "role": (
                "occurrence-anchored geography-only stepping-stone topology; matrix "
                "heterogeneity is controlled separately by the current-flow competitor"
            ),
            "region_rule": (
                "East and West are separate structural graphs; cross-region edges are "
                "prohibited regardless of numeric radius"
            ),
            "nodes": "all 42 verified forest-patch nodes per region",
            "survey_nodes": "the 14 surveyed fragments are exact node-table subsets",
            "edge_rule": "undirected great-circle edge when distance <= scenario radius",
            "radius_rule": (
                "within-region 42-node MST edge-distance quantiles q50, q75, q90, q100"
            ),
            "regions": reachability,
            "primary_score": (
                "connected_frequency: fraction of four geometry-only scenarios in "
                "which a node is connected to at least one training-presence anchor"
            ),
            "secondary_score": (
                "median normalized geographic bottleneck across the same four scenarios"
            ),
            "nearest_anchor_control": "log10(1 + great-circle distance in km)",
            "training_feature_crossfit": (
                "within each outer fold, every training site's anchor-distance and EOG "
                "features are recomputed after excluding that site's own occurrence; "
                "the outer held-out site uses all outer-training presences"
            ),
            "no_anchor_rule": (
                "a graph component with no training-presence anchor has connected_frequency=0; "
                "if cross-fitting leaves no anchor anywhere for a training row, that method/fold "
                "is non-estimable rather than imputed"
            ),
        },
        "source_formula_contract": {
            "local_patch_predictor": "log10(area_ha)",
            "simple_isolation_candidates": [
                {
                    "field": "distance1",
                    "paired_name_field": "nearest_fragment",
                    "transform": "log10(raw verified value); no unit conversion",
                },
                {
                    "field": "distance2",
                    "paired_name_field": "nearest_lg_fragment",
                    "transform": "log10(raw verified value); no unit conversion",
                },
            ],
            "current_flow": {
                "relative_resistance_levels": list(RESISTANCE_LEVELS),
                "candidate_count": len(RESISTANCE_LEVELS) ** 3,
                "varying_landcovers": ["eucalyptus", "tea", "other_agriculture"],
                "intact_forest_resistance": 1,
                "east_raster_classes": {
                    "1": "other_agriculture",
                    "2": "forest",
                    "3": "tea",
                    "4": "eucalyptus",
                },
                "west_raster_classes": {
                    "1": "other_agriculture",
                    "2": "eucalyptus",
                    "3": "forest",
                    "4": "tea",
                },
                "east_filename_resolution": (
                    "official script names raster_east3_new.tif, but the sole verified "
                    "archive raster is raster_east3.tif with final classes 1..4; execute "
                    "by byte-identical aliasing only, with no raster value modification"
                ),
                "pairwise_engine": "Circuitscape pairwise effective resistance",
                "patch_isolation_formula": (
                    "for target i, sum_j resistance_distance(j,i) / log10(area_ha_j), "
                    "preserving the official script exactly even when source-patch "
                    "log10(area_ha) is negative"
                ),
                "source_glm_formula": (
                    "occur ~ log10(area_ha) * log10(isolation)"
                ),
                "source_full_data_reproduction": (
                    "unpenalized binomial GLM; candidate comparison by AIC; preserve the "
                    "official convergence and pseudo-R2 checks; kept separate from held-out scoring"
                ),
                "outer_fold_selection": (
                    "among candidates passing the source convergence checks on outer-training "
                    "data only, choose minimum training AIC; exact ties resolved by ascending "
                    "(eucalyptus, tea, other_agriculture) resistance tuple"
                ),
                "no_candidate_rule": "current-flow tier is non-estimable for that species/fold",
            },
        },
        "heldout_probability_models": {
            "engine": (
                "deterministic L2 logistic regression with training-only standardization, "
                "unpenalized intercept, and fixed lambda=1"
            ),
            "l2_penalty": HELDOUT_L2_PENALTY,
            "minimum_outer_training_class_count": 1,
            "current_flow_refit_rule": (
                "after training-only source-AIC resistance selection, refit every held-out "
                "comparison tier with the shared fixed-L2 engine"
            ),
            "tiers": {
                "local": ["log_area"],
                "simple_isolation": [
                    "log_area",
                    "selected_log_simple_isolation",
                    "log_area_x_selected_log_simple_isolation",
                ],
                "current_flow": [
                    "log_area",
                    "selected_log_current_flow_isolation",
                    "log_area_x_selected_log_current_flow_isolation",
                ],
                "current_flow_plus_anchor_distance": [
                    "log_area",
                    "selected_log_current_flow_isolation",
                    "log_area_x_selected_log_current_flow_isolation",
                    "log1p_nearest_training_presence_km",
                ],
                "current_flow_plus_anchor_distance_plus_eog": [
                    "log_area",
                    "selected_log_current_flow_isolation",
                    "log_area_x_selected_log_current_flow_isolation",
                    "log1p_nearest_training_presence_km",
                    "eog_connected_frequency",
                ],
            },
            "strict_incremental_reference": "current_flow_plus_anchor_distance",
            "strict_incremental_candidate": (
                "current_flow_plus_anchor_distance_plus_eog"
            ),
            "reason_for_anchor_control": (
                "the strict contrast must distinguish graph configuration from simple "
                "distance to a known training occurrence, matching the A-Islands logic"
            ),
            "eog_parameter_rule": (
                "the current-flow resistance selected for the reference is reused unchanged "
                "in the EOG candidate; EOG addition never triggers resistance reselection"
            ),
        },
        "scoring_contract": {
            "primary": "paired held-out Bernoulli log loss",
            "direction": "candidate minus reference; negative favors candidate",
            "replication_unit": "species",
            "species_bootstrap_replicates": 10_000,
            "species_bootstrap_seed": 20260810,
            "species_sign_flip_replicates": 100_000,
            "species_sign_flip_seed": 20260810,
        },
        "claim_boundary": (
            "This design tests whether occurrence-anchored patch-network configuration "
            "adds held-out information beyond patch area, source simple isolation, "
            "nearest training occurrence distance, and a leakage-safe matrix-aware "
            "current-flow competitor. It does not estimate mechanistic colonisation probability."
        ),
        "species_outcomes_inspected": False,
        "model_fitted": False,
        "eog_score_computed": False,
        "current_flow_computed": False,
    }
    contract["design_fingerprint"] = canonical_sha256(contract)
    return contract
