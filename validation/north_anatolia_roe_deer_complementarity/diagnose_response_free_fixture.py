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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stations", type=Path, required=True)
    parser.add_argument("--variables", type=Path, required=True)
    parser.add_argument("--effort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    runner = load_module("diag_paired_runner", ROOT / "paired_runner.py")
    harness = load_module("diag_smoke_harness", ROOT / "response_free_smoke_harness.py")
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
    chain = harness._deterministic_effort_aware_source_chain(
        effort,
        distance,
        threshold,
    )

    n_nodes, n_primary = effort.shape
    detected = np.zeros((n_nodes, n_primary), dtype=bool)
    for t, node in enumerate(chain):
        detected[node, t] = True

    selection_audit = []
    for t in range(n_primary - 1):
        source = detected[:, t] & (effort[:, t] > 0.0)
        source_nodes = np.flatnonzero(source)
        broad_reach = np.any(distance[:, source_nodes] <= threshold, axis=1)
        candidates = (
            (~detected[:, t])
            & (effort[:, t] > 0.0)
            & (effort[:, t + 1] > 0.0)
            & broad_reach
        )
        candidate_ids = np.flatnonzero(candidates)
        next_chain = chain[t + 1]
        required = [next_chain] if candidates[next_chain] else []
        preferred = candidate_ids[((candidate_ids + 5 * t) % 5) == 0].tolist()
        ordered = required + [node for node in preferred if node not in required]
        ordered.extend(node for node in candidate_ids.tolist() if node not in set(ordered))
        selected = np.asarray(ordered[: min(4, len(ordered))], dtype=int)
        min_distance_selected = {
            str(int(node)): float(np.min(distance[node, source_nodes]))
            for node in selected.tolist()
        }
        detected[selected, t + 1] = True
        selection_audit.append(
            {
                "transition_index": t,
                "source_nodes": source_nodes.tolist(),
                "candidate_count": int(len(candidate_ids)),
                "selected_nodes": selected.tolist(),
                "selected_min_source_distance_km": min_distance_selected,
                "next_chain_node": int(next_chain),
            }
        )

    post_audit = []
    first_mismatch = None
    for t in range(n_primary - 1):
        source = detected[:, t] & (effort[:, t] > 0.0)
        source_nodes = np.flatnonzero(source)
        broad_reach = np.any(distance[:, source_nodes] <= threshold, axis=1)
        candidates = (
            (~detected[:, t])
            & (effort[:, t] > 0.0)
            & (effort[:, t + 1] > 0.0)
        )
        positives = np.flatnonzero(candidates & detected[:, t + 1])
        bad = positives[~broad_reach[positives]]
        entry = {
            "transition_index": t,
            "source_nodes": source_nodes.tolist(),
            "positive_nodes": positives.tolist(),
            "bad_nodes": bad.tolist(),
            "bad_min_source_distance_km": {
                str(int(node)): float(np.min(distance[node, source_nodes]))
                for node in bad.tolist()
            },
            "source_set_equals_selection_time": (
                source_nodes.tolist() == selection_audit[t]["source_nodes"]
            ),
            "selected_nodes_at_construction": selection_audit[t]["selected_nodes"],
        }
        post_audit.append(entry)
        if len(bad) and first_mismatch is None:
            first_mismatch = entry

    result = {
        "status": "diagnostic_mismatch_found" if first_mismatch else "diagnostic_no_mismatch",
        "threshold_km": threshold,
        "source_chain": chain,
        "possible_source_counts": getattr(
            harness._deterministic_effort_aware_source_chain,
            "possible_counts",
            [],
        ),
        "selection_audit": selection_audit,
        "post_audit": post_audit,
        "first_mismatch": first_mismatch,
        "response_content_opened": False,
        "scientific_contract_changed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
