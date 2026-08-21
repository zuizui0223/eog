from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vectorized_next(
    current: np.ndarray,
    effort: np.ndarray,
    distance: np.ndarray,
    threshold: float,
    transition_index: int,
) -> np.ndarray:
    source_indices = np.flatnonzero(current)
    next_possible = np.zeros(current.shape[0], dtype=bool)
    if len(source_indices):
        next_possible[source_indices] |= effort[source_indices, transition_index + 1] > 0.0
        target_eligible = (
            (effort[:, transition_index] > 0.0)
            & (effort[:, transition_index + 1] > 0.0)
        )
        reachable_from_current = np.any(
            distance[:, source_indices] <= threshold,
            axis=1,
        )
        next_possible |= target_eligible & reachable_from_current
    return next_possible


def parent_map_next(
    current_nodes: set[int],
    effort: np.ndarray,
    distance: np.ndarray,
    threshold: float,
    transition_index: int,
) -> tuple[set[int], dict[int, int]]:
    parent_for_next: dict[int, int] = {}
    for i in sorted(current_nodes):
        if effort[i, transition_index + 1] > 0.0:
            parent_for_next.setdefault(i, i)
        target_eligible = np.flatnonzero(
            (effort[:, transition_index] > 0.0)
            & (effort[:, transition_index + 1] > 0.0)
            & (distance[:, i] <= threshold)
        )
        for j in target_eligible.tolist():
            parent_for_next.setdefault(int(j), int(i))
    return set(parent_for_next), parent_for_next


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stations", type=Path, required=True)
    parser.add_argument("--variables", type=Path, required=True)
    parser.add_argument("--effort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    runner = load_module("diag_paired_runner", ROOT / "paired_runner.py")
    source = runner.load_json(ROOT / "source_freeze.json")
    geometry_contract = runner.load_json(ROOT / "geometry_gate_contract.json")
    prediction_contract = runner.load_json(ROOT / "gate2_prediction_contract.json")

    _, _, distance, _ = runner.load_registry(
        args.stations,
        args.variables,
        source,
        geometry_contract,
    )
    effort = runner.load_effort(args.effort, source, prediction_contract)
    threshold = max(
        float(world["threshold_km"])
        for world in prediction_contract["layer_a"]["declared_worlds"]
    )

    vector_current = effort[:, 0] > 0.0
    parent_current = set(np.flatnonzero(effort[:, 0] > 0.0).tolist())
    comparison = []
    first_divergence = None
    parent_maps: list[dict[int, int]] = []

    for t in range(21):
        vector_next_state = vectorized_next(
            vector_current,
            effort,
            distance,
            threshold,
            t,
        )
        parent_next_nodes, parent_map = parent_map_next(
            parent_current,
            effort,
            distance,
            threshold,
            t,
        )
        parent_maps.append(parent_map)
        vector_nodes = set(np.flatnonzero(vector_next_state).tolist())
        only_vector = sorted(vector_nodes - parent_next_nodes)
        only_parent = sorted(parent_next_nodes - vector_nodes)
        entry = {
            "transition_index": t,
            "vector_before_count": int(np.sum(vector_current)),
            "parent_before_count": len(parent_current),
            "vector_after_count": len(vector_nodes),
            "parent_after_count": len(parent_next_nodes),
            "only_vector": only_vector,
            "only_parent": only_parent,
            "equal": vector_nodes == parent_next_nodes,
            "positive_effort_source_count_vector": int(
                np.sum(vector_current & (effort[:, t] > 0.0))
            ),
            "positive_effort_source_count_parent": sum(
                effort[node, t] > 0.0 for node in parent_current
            ),
        }
        comparison.append(entry)
        if not entry["equal"] and first_divergence is None:
            first_divergence = entry
        vector_current = vector_next_state
        parent_current = parent_next_nodes

    chain = None
    chain_error = None
    if parent_current:
        final_node = min(parent_current)
        recovered = [final_node]
        node = final_node
        try:
            for t in range(20, -1, -1):
                node = parent_maps[t][node]
                recovered.append(node)
            recovered.reverse()
            chain = recovered
        except KeyError as exc:
            chain_error = f"parent-map backtrack missing node {exc.args[0]}"
    else:
        chain_error = "parent-map possible set empty after final transition"

    result = {
        "status": (
            "diagnostic_closure_implementations_diverge"
            if first_divergence is not None
            else "diagnostic_closure_implementations_match"
        ),
        "threshold_km": threshold,
        "initial_possible_count": int(np.sum(effort[:, 0] > 0.0)),
        "effort_positive_counts_by_season": [
            int(np.sum(effort[:, t] > 0.0)) for t in range(22)
        ],
        "comparison": comparison,
        "first_divergence": first_divergence,
        "vector_final_count": int(np.sum(vector_current)),
        "parent_final_count": len(parent_current),
        "recovered_chain": chain,
        "chain_error": chain_error,
        "response_content_opened": False,
        "scientific_contract_changed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
