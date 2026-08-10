"""Geometry-only survey-component ladder for the Tanzania benchmark.

The first Tanzania radius proposal used upper quantiles of all 42-node MST edge
lengths.  A pre-outcome geometry audit showed that every surveyed fragment in
each region already belonged to one component at the smallest proposed radius.
That would collapse connected frequency to a same-region-anchor indicator.

This module replaces those radii without consulting any species label or model
score.  It selects the smallest distinct node-MST thresholds at which the
verified survey nodes occupy 4, 3, 2, and 1 components, respectively.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from .tanzania_design import (
    GeometryPoint,
    MstEdge,
    build_tanzania_design_contract,
    canonical_sha256,
    stable_mst,
)

SURVEY_COMPONENT_TARGETS = (4, 3, 2, 1)


@dataclass(frozen=True)
class SurveyComponentScenario:
    scenario_id: str
    target_component_count: int
    radius_km: float
    survey_partition: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        if self.target_component_count < 1:
            raise ValueError("target_component_count must be positive")
        if not math.isfinite(self.radius_km) or self.radius_km <= 0.0:
            raise ValueError("radius_km must be finite and positive")
        if len(self.survey_partition) > self.target_component_count:
            raise ValueError("survey partition exceeds its declared component target")


def _all_edge_nodes(edges: Sequence[MstEdge]) -> set[str]:
    nodes: set[str] = set()
    for edge in edges:
        nodes.add(edge.source_id)
        nodes.add(edge.target_id)
    return nodes


def _survey_partition(
    edges: Sequence[MstEdge],
    radius_km: float,
    survey_display_names: Mapping[str, str],
) -> tuple[tuple[str, ...], ...]:
    nodes = _all_edge_nodes(edges)
    if not survey_display_names:
        raise ValueError("at least one survey node is required")
    if not set(survey_display_names).issubset(nodes):
        missing = sorted(set(survey_display_names) - nodes)
        raise ValueError(f"survey nodes absent from MST: {missing}")
    display = [str(value).strip() for value in survey_display_names.values()]
    if any(not value for value in display) or len(set(display)) != len(display):
        raise ValueError("survey display names must be unique and non-empty")

    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        if edge.distance_km <= radius_km:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)

    component: dict[str, int] = {}
    component_id = 0
    for start in sorted(adjacency):
        if start in component:
            continue
        stack = [start]
        component[start] = component_id
        while stack:
            node = stack.pop()
            for neighbour in sorted(adjacency[node], reverse=True):
                if neighbour not in component:
                    component[neighbour] = component_id
                    stack.append(neighbour)
        component_id += 1

    groups: dict[int, list[str]] = {}
    for node_id, display_name in survey_display_names.items():
        groups.setdefault(component[node_id], []).append(str(display_name))
    return tuple(
        sorted(tuple(sorted(names)) for names in groups.values())
    )


def survey_component_ladder(
    edges: Sequence[MstEdge],
    survey_display_names: Mapping[str, str],
    targets: Sequence[int] = SURVEY_COMPONENT_TARGETS,
) -> tuple[SurveyComponentScenario, ...]:
    """Choose distinct MST thresholds using survey geometry only.

    For each descending target, select the smallest threshold larger than the
    previous threshold that puts the survey nodes in no more than the target
    number of components and induces a partition not used by an earlier
    scenario.  If the verified geometry cannot support all declared scenarios,
    the pre-outcome design fails rather than emitting a degenerate ensemble.
    """
    declared = tuple(int(value) for value in targets)
    if not declared or any(value < 1 for value in declared):
        raise ValueError("component targets must be positive")
    if any(left <= right for left, right in zip(declared, declared[1:])):
        raise ValueError("component targets must be strictly decreasing")
    if declared[0] > len(survey_display_names):
        raise ValueError("largest component target exceeds the number of survey nodes")
    if not edges:
        raise ValueError("at least one MST edge is required")

    thresholds = sorted({float(edge.distance_km) for edge in edges})
    selected: list[SurveyComponentScenario] = []
    previous_radius = -math.inf
    previous_partitions: set[tuple[tuple[str, ...], ...]] = set()

    for target in declared:
        chosen: SurveyComponentScenario | None = None
        for radius in thresholds:
            if radius <= previous_radius:
                continue
            partition = _survey_partition(edges, radius, survey_display_names)
            if len(partition) > target or partition in previous_partitions:
                continue
            chosen = SurveyComponentScenario(
                scenario_id=f"survey_c{target:02d}",
                target_component_count=target,
                radius_km=float(radius),
                survey_partition=partition,
            )
            break
        if chosen is None:
            raise ValueError(
                "verified geometry cannot produce a distinct survey-component "
                f"scenario for target {target}"
            )
        selected.append(chosen)
        previous_radius = chosen.radius_km
        previous_partitions.add(chosen.survey_partition)

    if tuple(len(item.survey_partition) for item in selected) != declared:
        raise ValueError(
            "survey-component ladder skipped a declared component count; "
            "the benchmark requires exact 4,3,2,1 partitions"
        )
    return tuple(selected)


def _region_geometry(
    region: str,
    nodes: Sequence[Mapping[str, object]],
    sites: Sequence[Mapping[str, object]],
) -> tuple[tuple[MstEdge, ...], dict[str, str]]:
    points: list[GeometryPoint] = []
    node_id_by_name: dict[str, str] = {}
    for row in nodes:
        patch_number = int(row["patch_number"])
        name = str(row["name"]).strip()
        node_id = f"{region}:{patch_number:02d}:{name}"
        points.append(
            GeometryPoint(
                node_id=node_id,
                latitude=float(row["centroid_lat"]),
                longitude=float(row["centroid_long"]),
            )
        )
        node_id_by_name[name] = node_id
    if len(points) != 42 or len(node_id_by_name) != 42:
        raise ValueError(f"{region} must contain 42 unique verified nodes")

    survey: dict[str, str] = {}
    for row in sites:
        if str(row["region"]).strip() != region:
            continue
        site_name = str(row["name"]).strip()
        node_id = node_id_by_name.get(site_name)
        if node_id is None:
            raise ValueError(f"survey site absent from {region} nodes: {site_name}")
        survey[node_id] = site_name
    if len(survey) < len(SURVEY_COMPONENT_TARGETS):
        raise ValueError(f"{region} has too few survey nodes for the declared ladder")
    return stable_mst(points), survey


def build_tanzania_survey_ladder_contract(
    *,
    sites: Sequence[Mapping[str, object]],
    east_nodes: Sequence[Mapping[str, object]],
    west_nodes: Sequence[Mapping[str, object]],
    eligible_species: Sequence[str],
    source_formula_evidence: Mapping[str, bool],
) -> dict[str, object]:
    """Apply the non-degenerate geometry-only ladder to the base contract."""
    contract = build_tanzania_design_contract(
        sites=sites,
        east_nodes=east_nodes,
        west_nodes=west_nodes,
        eligible_species=eligible_species,
        source_formula_evidence=source_formula_evidence,
    )
    graph = dict(contract["eog_graph"])
    graph["radius_rule"] = (
        "within-region 42-node MST thresholds selected by a geometry-only "
        "survey-component ladder targeting 4, 3, 2, and 1 survey components"
    )
    graph["radius_selection_audit"] = {
        "scenario_count": 4,
        "target_survey_component_counts": [4, 3, 2, 1],
        "selection_rule": (
            "for each target, choose the smallest distinct node-MST edge threshold "
            "at which the verified survey nodes occupy no more than that number of components"
        ),
        "label_use": "none; verified node and survey-site geometry only",
        "degeneracy_guard": (
            "each successive scenario must induce a distinct survey-node partition; "
            "otherwise the design gate fails before species features or performance"
        ),
        "reason_for_replacing_mst_quantiles": (
            "the earlier q50/q75/q90/q100 rule placed every surveyed site in one "
            "component at the smallest radius in both regions, collapsing connected "
            "frequency to a same-region-anchor indicator before any outcome score was computed"
        ),
    }

    regions = dict(graph["regions"])
    for region, nodes in (("E", east_nodes), ("W", west_nodes)):
        edges, survey = _region_geometry(region, nodes, sites)
        ladder = survey_component_ladder(edges, survey)
        region_contract = dict(regions[region])
        region_contract["scenario_radii_km"] = {
            item.scenario_id: item.radius_km for item in ladder
        }
        region_contract["survey_component_partitions"] = {
            item.scenario_id: [list(group) for group in item.survey_partition]
            for item in ladder
        }
        region_contract["survey_component_counts"] = {
            item.scenario_id: len(item.survey_partition) for item in ladder
        }
        regions[region] = region_contract
    graph["regions"] = regions
    contract["eog_graph"] = graph

    contract.pop("design_fingerprint", None)
    contract["design_fingerprint"] = canonical_sha256(contract)
    return contract
