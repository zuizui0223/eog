"""Build hypothesis support surfaces from bridge sensitivity scenario families."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping, Sequence

from .bridge_sensitivity import BridgeSensitivityResult, BridgeScenarioResult
from .hypothesis_discrimination import BridgeHypothesis

PathMode = Literal["minimum_cost", "minimum_bottleneck", "union"]


@dataclass(frozen=True)
class HypothesisFamilyDeclaration:
    """Assign a predeclared set of sensitivity scenarios to one ecological hypothesis."""

    hypothesis_id: str
    scenario_ids: tuple[str, ...]
    path_mode: PathMode = "minimum_cost"

    def __post_init__(self) -> None:
        if not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must be non-empty")
        if not self.scenario_ids:
            raise ValueError("each hypothesis family requires at least one scenario")
        if any(not scenario_id.strip() for scenario_id in self.scenario_ids):
            raise ValueError("scenario IDs must be non-empty")
        if len(set(self.scenario_ids)) != len(self.scenario_ids):
            raise ValueError("scenario IDs must be unique within a hypothesis family")
        if self.path_mode not in {"minimum_cost", "minimum_bottleneck", "union"}:
            raise ValueError("path_mode must be minimum_cost, minimum_bottleneck, or union")


@dataclass(frozen=True)
class HypothesisFamilySummary:
    hypothesis_id: str
    scenario_count: int
    connected_count: int
    connected_frequency: float
    path_mode: PathMode
    node_support: Mapping[str, float]


@dataclass(frozen=True)
class HypothesisAdapterResult:
    hypotheses: tuple[BridgeHypothesis, ...]
    summaries: tuple[HypothesisFamilySummary, ...]
    unassigned_scenario_ids: tuple[str, ...]
    fingerprint: str


def _intermediate_nodes(result: BridgeScenarioResult, mode: PathMode) -> set[str]:
    if not result.connected:
        return set()
    if mode == "minimum_cost":
        paths = (result.minimum_cost_nodes,)
    elif mode == "minimum_bottleneck":
        paths = (result.minimum_bottleneck_nodes,)
    else:
        paths = (result.minimum_cost_nodes, result.minimum_bottleneck_nodes)
    nodes: set[str] = set()
    for path in paths:
        nodes.update(path[1:-1])
    return nodes


def build_bridge_hypotheses(
    sensitivity: BridgeSensitivityResult,
    families: Sequence[HypothesisFamilyDeclaration],
    *,
    require_complete_assignment: bool = False,
    allow_scenario_overlap: bool = False,
) -> HypothesisAdapterResult:
    """Aggregate scenario paths into hypothesis-specific node support surfaces.

    Node support is the fraction of all declared scenarios in a family whose selected
    path contains the node. Disconnected scenarios remain in the denominator. These
    frequencies are robustness summaries, not posterior or occurrence probabilities.
    """
    ordered_families = tuple(sorted(families, key=lambda item: item.hypothesis_id))
    if len(ordered_families) < 2:
        raise ValueError("at least two hypothesis families are required")
    if len({family.hypothesis_id for family in ordered_families}) != len(ordered_families):
        raise ValueError("hypothesis IDs must be unique")

    by_id = {scenario.scenario_id: scenario for scenario in sensitivity.scenarios}
    declared_ids = {scenario.scenario_id for scenario in sensitivity.scenarios}
    assigned: list[str] = []
    for family in ordered_families:
        unknown = sorted(set(family.scenario_ids) - declared_ids)
        if unknown:
            raise ValueError(f"unknown scenario IDs: {', '.join(unknown)}")
        assigned.extend(family.scenario_ids)
    if not allow_scenario_overlap and len(set(assigned)) != len(assigned):
        raise ValueError("scenario IDs may not appear in multiple hypothesis families")

    unassigned = tuple(sorted(declared_ids - set(assigned)))
    if require_complete_assignment and unassigned:
        raise ValueError("all sensitivity scenarios must be assigned to a hypothesis family")

    summaries: list[HypothesisFamilySummary] = []
    hypotheses: list[BridgeHypothesis] = []
    for family in ordered_families:
        selected = tuple(by_id[scenario_id] for scenario_id in family.scenario_ids)
        counts: dict[str, int] = {}
        connected_count = 0
        for scenario in selected:
            if scenario.connected:
                connected_count += 1
            for node_id in _intermediate_nodes(scenario, family.path_mode):
                counts[node_id] = counts.get(node_id, 0) + 1
        denominator = len(selected)
        support = {
            node_id: count / denominator
            for node_id, count in sorted(counts.items())
        }
        summary = HypothesisFamilySummary(
            hypothesis_id=family.hypothesis_id,
            scenario_count=denominator,
            connected_count=connected_count,
            connected_frequency=connected_count / denominator,
            path_mode=family.path_mode,
            node_support=support,
        )
        summaries.append(summary)
        hypotheses.append(BridgeHypothesis(family.hypothesis_id, support))

    payload = {
        "sensitivity_fingerprint": sensitivity.fingerprint,
        "families": [
            {
                "hypothesis_id": family.hypothesis_id,
                "scenario_ids": sorted(family.scenario_ids),
                "path_mode": family.path_mode,
            }
            for family in ordered_families
        ],
        "require_complete_assignment": require_complete_assignment,
        "allow_scenario_overlap": allow_scenario_overlap,
        "summaries": [
            {
                **summary.__dict__,
                "node_support": dict(sorted(summary.node_support.items())),
            }
            for summary in summaries
        ],
        "unassigned_scenario_ids": unassigned,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return HypothesisAdapterResult(
        hypotheses=tuple(hypotheses),
        summaries=tuple(summaries),
        unassigned_scenario_ids=unassigned,
        fingerprint=fingerprint,
    )
