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


def _deterministic_effort_aware_source_chain(
    effort: np.ndarray,
    distance: np.ndarray,
    broad_threshold_km: float,
) -> list[int]:
    """Find one 22-season response-free chain under the frozen source/candidate rules."""

    n_nodes, n_primary = effort.shape
    viable: list[set[int]] = [set() for _ in range(n_primary)]
    pointer: list[dict[int, int]] = [dict() for _ in range(n_primary - 1)]
    viable[-1] = set(np.flatnonzero(effort[:, -1] > 0.0).tolist())
    if not viable[-1]:
        raise RuntimeError("no positive-effort station in final synthetic primary season")

    for t in range(n_primary - 2, -1, -1):
        current_nodes = np.flatnonzero(effort[:, t] > 0.0)
        next_nodes = sorted(viable[t + 1])
        for i in current_nodes.tolist():
            chosen = None
            for j in next_nodes:
                # Same-station persistence is not a candidate appearance; it only needs
                # target-season effort. A station change must obey the exact real-runner
                # candidate effort rule and broadest structural reachability.
                if i == j:
                    if effort[j, t + 1] > 0.0:
                        chosen = j
                        break
                elif (
                    effort[j, t] > 0.0
                    and effort[j, t + 1] > 0.0
                    and distance[j, i] <= broad_threshold_km
                ):
                    chosen = j
                    break
            if chosen is not None:
                viable[t].add(i)
                pointer[t][i] = chosen
        if not viable[t]:
            raise RuntimeError(
                f"no response-free source chain can traverse frozen transition {t}->{t + 1} "
                f"under effort and broad-world rules"
            )

    start = min(viable[0])
    chain = [start]
    current = start
    for t in range(n_primary - 1):
        current = pointer[t][current]
        chain.append(current)
    if len(chain) != n_primary:
        raise RuntimeError("synthetic source-chain length drift")
    return chain


def broad_compatible_synthetic_response(
    effort: np.ndarray,
    distance: np.ndarray,
    broad_threshold_km: float,
) -> np.ndarray:
    """Response-free fixture with guaranteed broad-world support for every appearance.

    This is validation plumbing only. It searches the response-independent effort/geometry
    for a deterministic 22-season source chain, then adds a few synthetic appearances per
    transition only when they satisfy the exact real-runner candidate definition and the
    frozen broadest structural world. No scientific threshold or count gate is relaxed.
    """

    n_nodes, n_primary = effort.shape
    detected = np.zeros((n_nodes, n_primary), dtype=bool)
    source_chain = _deterministic_effort_aware_source_chain(
        effort,
        distance,
        broad_threshold_km,
    )
    for t, node in enumerate(source_chain):
        detected[node, t] = True

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

        next_chain_node = source_chain[t + 1]
        required = []
        if candidates[next_chain_node]:
            required.append(next_chain_node)
        elif next_chain_node != source_chain[t] and not detected[next_chain_node, t]:
            raise RuntimeError(
                f"source-chain transition {t} changes station without satisfying the "
                f"real appearance-candidate rule"
            )

        preferred = candidate_ids[((candidate_ids + 5 * t) % 5) == 0].tolist()
        ordered = required + [node for node in preferred if node not in required]
        ordered.extend(
            node
            for node in candidate_ids.tolist()
            if node not in set(ordered)
        )
        selected = np.asarray(ordered[: min(4, len(ordered))], dtype=int)
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
                "chain_source_node": int(source_chain[t]),
                "chain_target_node": int(source_chain[t + 1]),
            }
        )

    # Re-evaluate the exact real-runner source/candidate semantics after all synthetic
    # seasons have been built. This prevents later target assignments from silently
    # creating a broad-incompatible appearance in an earlier transition.
    for t in range(n_primary - 1):
        source = detected[:, t] & (effort[:, t] > 0.0)
        if not source.any():
            raise RuntimeError(f"post-construction source set empty at transition {t}")
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
    broad_compatible_synthetic_response.source_chain = source_chain
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
        "kind": "effort-aware-source-chain-broad-compatible",
        "source_chain": getattr(broad_compatible_synthetic_response, "source_chain", []),
        "transition_audit": getattr(broad_compatible_synthetic_response, "last_audit", []),
        "scientific_contract_changed": False,
    }
    result["fingerprint"] = runner.canonical_sha256(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
