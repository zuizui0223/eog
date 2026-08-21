from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent


def load_runner():
    path = ROOT / "paired_runner.py"
    spec = importlib.util.spec_from_file_location("north_anatolia_paired_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load frozen paired runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def broad_compatible_synthetic_response(
    effort: np.ndarray,
    distance: np.ndarray,
    broad_threshold_km: float,
) -> np.ndarray:
    """Response-free fixture with guaranteed broad-world support for every appearance.

    This fixture is validation plumbing only. It does not change the scientific Layer-A
    contract. Persistent synthetic anchors are chosen only among stations with positive
    effort in every primary season, then every synthetic appearance is selected from the
    same candidate definition used by the real runner and is explicitly required to lie
    within the frozen broadest structural threshold of a current synthetic source.
    """

    n_nodes, n_primary = effort.shape
    detected = np.zeros((n_nodes, n_primary), dtype=bool)

    persistent_pool = np.flatnonzero(np.all(effort > 0.0, axis=1))
    if len(persistent_pool) == 0:
        raise RuntimeError(
            "response-free smoke fixture requires at least one station with positive "
            "effort in all 22 seasons; scientific contracts are not relaxed to rescue smoke"
        )

    # A small deterministic persistent source set prevents the fixture from losing all
    # current sources while leaving most nodes available as appearance candidates.
    anchor_count = min(8, len(persistent_pool))
    anchors = persistent_pool[np.linspace(0, len(persistent_pool) - 1, anchor_count, dtype=int)]
    detected[anchors, :] = True

    audit = []
    for t in range(n_primary - 1):
        source = detected[:, t] & (effort[:, t] > 0.0)
        if not source.any():
            raise RuntimeError(f"synthetic source set unexpectedly empty at transition {t}")

        broad_reach = np.any(distance[:, source] <= broad_threshold_km, axis=1)
        candidates = (
            (~detected[:, t])
            & (effort[:, t] > 0.0)
            & (effort[:, t + 1] > 0.0)
            & broad_reach
        )
        candidate_ids = np.flatnonzero(candidates)
        if len(candidate_ids) == 0:
            raise RuntimeError(
                f"no broad-compatible response-free appearance candidates at transition {t}"
            )

        # Four events per transition exceeds the inherited heldout minimum when all five
        # heldout transitions remain estimable, while avoiding saturation of 171 nodes.
        preferred = candidate_ids[((candidate_ids + 5 * t) % 5) == 0]
        selected = preferred[: min(4, len(preferred))]
        if len(selected) < min(4, len(candidate_ids)):
            missing = min(4, len(candidate_ids)) - len(selected)
            remainder = np.asarray(
                [node for node in candidate_ids if node not in set(selected.tolist())],
                dtype=int,
            )
            selected = np.concatenate([selected, remainder[:missing]])

        if len(selected) == 0:
            raise RuntimeError(f"synthetic transition {t} produced zero events")
        if not np.all(broad_reach[selected]):
            raise RuntimeError(
                f"synthetic generator attempted an appearance outside broad-world support at {t}"
            )
        detected[selected, t + 1] = True
        audit.append(
            {
                "transition_index": t,
                "source_count": int(np.sum(source)),
                "candidate_count": int(len(candidate_ids)),
                "selected_event_count": int(len(selected)),
                "selected_nodes": selected.tolist(),
            }
        )

    # Re-evaluate the exact runner candidate/source semantics after the full fixture has
    # been constructed. This catches any accidental future-source mutation before the
    # paired runner is allowed to use the fixture.
    for t in range(n_primary - 1):
        source = detected[:, t] & (effort[:, t] > 0.0)
        broad_reach = np.any(distance[:, source] <= broad_threshold_km, axis=1)
        candidates = (
            (~detected[:, t])
            & (effort[:, t] > 0.0)
            & (effort[:, t + 1] > 0.0)
        )
        positives = np.flatnonzero(candidates & detected[:, t + 1])
        if len(positives) and not np.all(broad_reach[positives]):
            bad = positives[~broad_reach[positives]].tolist()
            raise RuntimeError(
                f"post-construction smoke audit found broad-incompatible positives at "
                f"transition {t}: {bad}"
            )

    broad_compatible_synthetic_response.last_audit = audit
    broad_compatible_synthetic_response.anchor_nodes = anchors.tolist()
    return detected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stations", type=Path, required=True)
    parser.add_argument("--variables", type=Path, required=True)
    parser.add_argument("--effort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    runner = load_runner()
    runner.make_synthetic_response = broad_compatible_synthetic_response
    result = runner.run(
        mode="smoke",
        stations_path=args.stations,
        variables_path=args.variables,
        effort_path=args.effort,
        response_path=None,
    )
    result["smoke_fixture"] = {
        "kind": "persistent-response-free-broad-compatible",
        "anchor_nodes": getattr(broad_compatible_synthetic_response, "anchor_nodes", []),
        "transition_audit": getattr(broad_compatible_synthetic_response, "last_audit", []),
        "scientific_contract_changed": False,
    }
    result["fingerprint"] = runner.canonical_sha256(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
