#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_virtual_worlds_v2 import (
    AUTOCORR_LEVELS,
    BARRIER_LEVELS,
    NEIGHBOURHOODS,
    REPLICATES,
    _bfs_distances,
    _generate_base,
    _node_id,
)
from benchmarks.run_eog_original_idea_occurrence_information_v4 import (
    _coverage_count,
    _dispersed_order,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _candidate_worlds,
    _graphs,
    _outlet_corner,
    _truth_source,
)
from benchmarks.run_eog_original_idea_world_universe_v6 import (
    EVIDENCE_FRACTION,
    Q70,
)


PROTOCOL = ROOT / "validation/eog_original_idea_expansion_direction_v7/protocol_v7.json"
UNIVERSES = (
    "B0_reference",
    "B_restrictive",
    "B_permissive",
    "B_directional_mixed",
    "B_same_source_full",
    "B_all_source_full",
)


def _sha256(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _truth_world_id(source, barrier_density):
    return f"{_node_id(source)}|b{barrier_density:.2f}|{Q70}"


def _compatible(world, anchors):
    return frozenset(anchors).issubset(world["reachable"])


def _classify(candidate, reference):
    c = candidate["reachable"]
    r = reference["reachable"]
    if c == r:
        return "equivalent"
    if c < r:
        return "restrictive"
    if r < c:
        return "permissive"
    return "incomparable"


def _statuses(worlds, nodes):
    n = len(worlds)
    if n == 0:
        raise RuntimeError("empty survivor universe")
    out = {}
    for node in nodes:
        count = sum(node in world["reachable"] for world in worlds)
        if count == n:
            status = "robust_reachable"
        elif count == 0:
            status = "robust_impossible"
        else:
            status = "contingent"
        out[node] = status
    return out


def _counts(statuses):
    return {
        label: sum(value == label for value in statuses.values())
        for label in ("robust_reachable", "contingent", "robust_impossible")
    }


def _losses(b0, other):
    reachable = 0
    impossible = 0
    violations = 0
    for node, before in b0.items():
        after = other[node]
        if before == "robust_reachable":
            if after == "contingent":
                reachable += 1
            elif after != "robust_reachable":
                violations += 1
        elif before == "robust_impossible":
            if after == "contingent":
                impossible += 1
            elif after != "robust_impossible":
                violations += 1
        elif before == "contingent" and after != "contingent":
            violations += 1
    return {
        "reachable_loss": reachable,
        "impossible_loss": impossible,
        "monotonicity_violation": violations,
    }


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    truth_source = _truth_source(base, outlet)
    _, truth_graph = _graphs(base, barrier_density, Q70, outlet)
    truth_dist = _bfs_distances(truth_graph, truth_source)
    truth_reachable = frozenset(truth_dist)
    pool = tuple(
        sorted(node for node in truth_reachable if node != truth_source)
    )

    base_row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "truth_source": _node_id(truth_source),
        "truth_positive_pool_size": len(pool),
        "truth_reachable_node_count": len(truth_reachable),
        "eligible": len(pool) >= 4,
    }
    if len(pool) < 4:
        return {**base_row, "universes": {}}

    order = _dispersed_order(pool, truth_source)
    anchor_count = _coverage_count(len(pool), EVIDENCE_FRACTION)
    anchors = tuple(order[:anchor_count])
    cert_nodes = tuple(
        sorted(
            set(base["permissive"])
            .difference(anchors)
            .difference({truth_source})
        )
    )
    if not cert_nodes:
        return {**base_row, "eligible": False, "universes": {}}

    full_worlds = _candidate_worlds(base, outlet, "directed")
    truth_id = _truth_world_id(truth_source, barrier_density)

    references = {
        world["source"]: world
        for world in full_worlds
        if world["barrier_density"] == barrier_density
        and world["rule"] == Q70
    }
    if len(references) != len(base["permissive"]):
        raise RuntimeError("missing source reference world")

    b0 = tuple(
        world
        for world in references.values()
        if _compatible(world, anchors)
    )
    if not b0:
        raise RuntimeError("no baseline survivors")
    if truth_id not in {world["world_id"] for world in b0}:
        raise RuntimeError("truth world missing from B0")

    baseline_sources = {world["source"] for world in b0}
    same_source_compatible = tuple(
        world
        for world in full_worlds
        if world["source"] in baseline_sources
        and _compatible(world, anchors)
    )
    all_source_compatible = tuple(
        world for world in full_worlds if _compatible(world, anchors)
    )

    classified = {
        "restrictive": [],
        "permissive": [],
        "equivalent": [],
        "incomparable": [],
    }
    for world in same_source_compatible:
        reference = references[world["source"]]
        classified[_classify(world, reference)].append(world)

    def unique(rows):
        by_id = {row["world_id"]: row for row in rows}
        return tuple(by_id[key] for key in sorted(by_id))

    universes = {
        "B0_reference": unique(b0),
        "B_restrictive": unique((*b0, *classified["restrictive"])),
        "B_permissive": unique((*b0, *classified["permissive"])),
        "B_directional_mixed": unique(
            (*b0, *classified["restrictive"], *classified["permissive"])
        ),
        "B_same_source_full": unique(same_source_compatible),
        "B_all_source_full": unique(all_source_compatible),
    }

    if not (
        {w["world_id"] for w in universes["B0_reference"]}
        <= {w["world_id"] for w in universes["B_same_source_full"]}
        <= {w["world_id"] for w in universes["B_all_source_full"]}
    ):
        raise RuntimeError("full universe nesting failed")

    status = {
        name: _statuses(worlds, cert_nodes)
        for name, worlds in universes.items()
    }
    b0_status = status["B0_reference"]

    universe_rows = {}
    for name, worlds in universes.items():
        counts = _counts(status[name])
        false_impossible = sum(
            status[name][node] == "robust_impossible"
            and node in truth_reachable
            for node in cert_nodes
        )
        false_reachable = sum(
            status[name][node] == "robust_reachable"
            and node not in truth_reachable
            for node in cert_nodes
        )
        universe_rows[name] = {
            "world_count": len(worlds),
            "source_count": len({w["source"] for w in worlds}),
            "status_counts": counts,
            "false_robust_impossible_count": false_impossible,
            "false_robust_reachable_count": false_reachable,
            "losses_vs_B0": _losses(b0_status, status[name]),
        }

    # Exact theorem checks.
    restrictive_impossible_violation = sum(
        b0_status[node] == "robust_impossible"
        and status["B_restrictive"][node] != "robust_impossible"
        for node in cert_nodes
    )
    permissive_reachable_violation = sum(
        b0_status[node] == "robust_reachable"
        and status["B_permissive"][node] != "robust_reachable"
        for node in cert_nodes
    )

    mixed_losses = universe_rows["B_directional_mixed"]["losses_vs_B0"]
    same_losses = universe_rows["B_same_source_full"]["losses_vs_B0"]
    all_losses = universe_rows["B_all_source_full"]["losses_vs_B0"]

    mixed_total_loss = (
        mixed_losses["reachable_loss"] + mixed_losses["impossible_loss"]
    )
    same_total_loss = (
        same_losses["reachable_loss"] + same_losses["impossible_loss"]
    )
    all_total_loss = (
        all_losses["reachable_loss"] + all_losses["impossible_loss"]
    )

    return {
        **base_row,
        "anchor_count": len(anchors),
        "certificate_node_count": len(cert_nodes),
        "baseline_source_count": len(baseline_sources),
        "compatible_added_world_class_counts": {
            key: len(value) for key, value in classified.items()
        },
        "universes": universe_rows,
        "restrictive_impossible_protection_violation_count": (
            restrictive_impossible_violation
        ),
        "permissive_reachable_protection_violation_count": (
            permissive_reachable_violation
        ),
        "additional_loss_from_incomparable_or_equivalent_worlds": (
            same_total_loss - mixed_total_loss
        ),
        "additional_loss_from_new_sources": (
            all_total_loss - same_total_loss
        ),
    }


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_directional_expansion_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v7 protocol is not frozen")

    rows = []
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                for barrier_density in BARRIER_LEVELS:
                    rows.append(
                        _evaluate_row(
                            replicate,
                            autocorr,
                            neighbourhood,
                            barrier_density,
                        )
                    )
    if len(rows) != 384:
        raise RuntimeError(f"expected 384 rows, got {len(rows)}")

    eligible = [row for row in rows if row["eligible"] and row["universes"]]
    if not eligible:
        raise RuntimeError("no eligible v7 rows")

    e1_violations = sum(
        row["restrictive_impossible_protection_violation_count"]
        for row in eligible
    )
    e2_violations = sum(
        row["permissive_reachable_protection_violation_count"]
        for row in eligible
    )
    false_certificates = sum(
        item["false_robust_impossible_count"]
        + item["false_robust_reachable_count"]
        for row in eligible
        for item in row["universes"].values()
    )
    monotonicity_violations = sum(
        item["losses_vs_B0"]["monotonicity_violation"]
        for row in eligible
        for item in row["universes"].values()
    )

    restrictive_reachable_loss_rows = sum(
        row["universes"]["B_restrictive"]["losses_vs_B0"]["reachable_loss"] > 0
        for row in eligible
    )
    permissive_impossible_loss_rows = sum(
        row["universes"]["B_permissive"]["losses_vs_B0"]["impossible_loss"] > 0
        for row in eligible
    )
    mixed_reachable_loss = sum(
        row["universes"]["B_directional_mixed"]["losses_vs_B0"]["reachable_loss"]
        for row in eligible
    )
    mixed_impossible_loss = sum(
        row["universes"]["B_directional_mixed"]["losses_vs_B0"]["impossible_loss"]
        for row in eligible
    )
    incomparable_extra_rows = sum(
        row["additional_loss_from_incomparable_or_equivalent_worlds"] > 0
        for row in eligible
    )
    new_source_extra_rows = sum(
        row["additional_loss_from_new_sources"] > 0
        for row in eligible
    )

    class_totals = {
        key: sum(
            row["compatible_added_world_class_counts"][key]
            for row in eligible
        )
        for key in ("restrictive", "permissive", "equivalent", "incomparable")
    }

    verdicts = {
        "E1_restrictive_expansion_protects_impossibility": (
            "SUPPORTED" if e1_violations == 0 else "REFUTED"
        ),
        "E2_permissive_expansion_protects_reachability": (
            "SUPPORTED" if e2_violations == 0 else "REFUTED"
        ),
        "E3_restrictive_worlds_can_erode_reachability": (
            "SUPPORTED" if restrictive_reachable_loss_rows > 0 else "REFUTED"
        ),
        "E4_permissive_worlds_can_erode_impossibility": (
            "SUPPORTED" if permissive_impossible_loss_rows > 0 else "REFUTED"
        ),
        "E5_directional_mixed_expansion_can_erode_both_certificate_types": (
            "SUPPORTED"
            if mixed_reachable_loss > 0 and mixed_impossible_loss > 0
            else "REFUTED"
        ),
        "E6_incomparable_worlds_add_certificate_fragility": (
            "SUPPORTED" if incomparable_extra_rows > 0 else "REFUTED"
        ),
        "E7_new_source_hypotheses_add_certificate_fragility": (
            "SUPPORTED" if new_source_extra_rows > 0 else "REFUTED"
        ),
        "E8_truth_soundness": (
            "SUPPORTED"
            if (
                false_certificates == 0
                and monotonicity_violations == 0
                and e1_violations == 0
                and e2_violations == 0
            )
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_expansion_direction.result.v7",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "compatible_added_world_class_totals": class_totals,
        "restrictive_impossible_protection_violation_count": e1_violations,
        "permissive_reachable_protection_violation_count": e2_violations,
        "restrictive_reachable_loss_row_count": restrictive_reachable_loss_rows,
        "permissive_impossible_loss_row_count": permissive_impossible_loss_rows,
        "directional_mixed_reachable_certificate_loss_count": mixed_reachable_loss,
        "directional_mixed_impossible_certificate_loss_count": mixed_impossible_loss,
        "incomparable_or_equivalent_extra_loss_row_count": incomparable_extra_rows,
        "new_source_extra_loss_row_count": new_source_extra_rows,
        "false_universal_certificate_count": false_certificates,
        "monotonicity_violation_count": monotonicity_violations,
        "rows": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "row_count": result["row_count"],
                "eligible_row_count": result["eligible_row_count"],
                "predeclared_verdicts": result["predeclared_verdicts"],
                "compatible_added_world_class_totals": result[
                    "compatible_added_world_class_totals"
                ],
                "restrictive_reachable_loss_row_count": result[
                    "restrictive_reachable_loss_row_count"
                ],
                "permissive_impossible_loss_row_count": result[
                    "permissive_impossible_loss_row_count"
                ],
                "incomparable_or_equivalent_extra_loss_row_count": result[
                    "incomparable_or_equivalent_extra_loss_row_count"
                ],
                "new_source_extra_loss_row_count": result[
                    "new_source_extra_loss_row_count"
                ],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
