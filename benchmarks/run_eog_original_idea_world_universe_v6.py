#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    _generate_base,
    _node_id,
)
from benchmarks.run_eog_original_idea_analyst_worlds_v3 import RULES
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


PROTOCOL = ROOT / "validation/eog_original_idea_world_universe_v6/protocol_v6.json"
Q70 = "relative_edge_q70"
EVIDENCE_FRACTION = 0.25
LEVELS = ("U0_source_only", "U1_plus_barrier", "U2_plus_analyst")


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


def _universe_members(worlds, truth_barrier_density):
    return {
        "U0_source_only": tuple(
            world
            for world in worlds
            if world["barrier_density"] == truth_barrier_density
            and world["rule"] == Q70
        ),
        "U1_plus_barrier": tuple(
            world for world in worlds if world["rule"] == Q70
        ),
        "U2_plus_analyst": tuple(worlds),
    }


def _survivors(universe, anchors, truth_world_id):
    anchor_set = frozenset(anchors)
    rows = tuple(
        world
        for world in universe
        if anchor_set.issubset(world["reachable"])
    )
    if not rows:
        raise RuntimeError("truth-generated evidence eliminated all candidate worlds")
    if truth_world_id not in {row["world_id"] for row in rows}:
        raise RuntimeError("truth world was eliminated")
    return rows


def _node_statuses(survivors, certificate_nodes):
    rows = {}
    n = len(survivors)
    for node in certificate_nodes:
        count = sum(node in world["reachable"] for world in survivors)
        if count == n:
            status = "robust_reachable"
        elif count == 0:
            status = "robust_impossible"
        else:
            status = "contingent"
        rows[node] = {
            "status": status,
            "reachable_world_count": count,
            "survivor_world_count": n,
        }
    return rows


def _status_counts(statuses):
    out = {
        "robust_reachable": 0,
        "contingent": 0,
        "robust_impossible": 0,
    }
    for row in statuses.values():
        out[row["status"]] += 1
    return out


def _lost_certificates(smaller, larger):
    lost = []
    violations = []
    for node, row in smaller.items():
        before = row["status"]
        after = larger[node]["status"]
        if before in {"robust_reachable", "robust_impossible"}:
            if after == before:
                continue
            if after == "contingent":
                lost.append((node, before))
            else:
                violations.append((node, before, after))
        elif before == "contingent" and after != "contingent":
            violations.append((node, before, after))
    return tuple(lost), tuple(violations)


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    source = _truth_source(base, outlet)
    _, truth_graph = _graphs(base, barrier_density, Q70, outlet)

    from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _bfs_distances
    truth_dist = _bfs_distances(truth_graph, source)
    truth_reachable = frozenset(truth_dist)
    pool = tuple(sorted(node for node in truth_reachable if node != source))

    base_row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "truth_source": _node_id(source),
        "truth_reachable_node_count": len(truth_reachable),
        "truth_positive_pool_size": len(pool),
        "eligible": len(pool) >= 4,
    }
    if len(pool) < 4:
        return {**base_row, "levels": {}}

    order = _dispersed_order(pool, source)
    anchor_count = _coverage_count(len(pool), EVIDENCE_FRACTION)
    anchors = tuple(order[:anchor_count])

    worlds = _candidate_worlds(base, outlet, "directed")
    truth_id = _truth_world_id(source, barrier_density)
    universes = _universe_members(worlds, barrier_density)

    if not (
        {w["world_id"] for w in universes["U0_source_only"]}
        <= {w["world_id"] for w in universes["U1_plus_barrier"]}
        <= {w["world_id"] for w in universes["U2_plus_analyst"]}
    ):
        raise RuntimeError("candidate universe nesting failed")

    certificate_nodes = tuple(
        sorted(
            set(base["permissive"])
            .difference(anchors)
            .difference({source})
        )
    )
    if not certificate_nodes:
        return {**base_row, "eligible": False, "levels": {}}

    levels = {}
    statuses = {}
    for level in LEVELS:
        survivors = _survivors(universes[level], anchors, truth_id)
        stat = _node_statuses(survivors, certificate_nodes)
        statuses[level] = stat
        counts = _status_counts(stat)
        false_impossible = sum(
            stat[node]["status"] == "robust_impossible"
            and node in truth_reachable
            for node in certificate_nodes
        )
        false_reachable = sum(
            stat[node]["status"] == "robust_reachable"
            and node not in truth_reachable
            for node in certificate_nodes
        )
        levels[level] = {
            "candidate_world_count": len(universes[level]),
            "survivor_world_count": len(survivors),
            "surviving_source_count": len({w["source"] for w in survivors}),
            "status_counts": counts,
            "contingent_fraction": (
                counts["contingent"] / len(certificate_nodes)
                if certificate_nodes
                else 0.0
            ),
            "false_robust_impossible_count": false_impossible,
            "false_robust_reachable_count": false_reachable,
        }

    lost01, violations01 = _lost_certificates(
        statuses["U0_source_only"],
        statuses["U1_plus_barrier"],
    )
    lost12, violations12 = _lost_certificates(
        statuses["U1_plus_barrier"],
        statuses["U2_plus_analyst"],
    )
    lost02, violations02 = _lost_certificates(
        statuses["U0_source_only"],
        statuses["U2_plus_analyst"],
    )

    u0_reachable = [
        node
        for node in certificate_nodes
        if statuses["U0_source_only"][node]["status"] == "robust_reachable"
    ]
    u0_impossible = [
        node
        for node in certificate_nodes
        if statuses["U0_source_only"][node]["status"] == "robust_impossible"
    ]
    u2_reachable_retained = sum(
        statuses["U2_plus_analyst"][node]["status"] == "robust_reachable"
        for node in u0_reachable
    )
    u2_impossible_retained = sum(
        statuses["U2_plus_analyst"][node]["status"] == "robust_impossible"
        for node in u0_impossible
    )

    return {
        **base_row,
        "anchor_count": len(anchors),
        "anchors": [_node_id(node) for node in anchors],
        "certificate_node_count": len(certificate_nodes),
        "levels": levels,
        "U0_to_U1_lost_certificate_count": len(lost01),
        "U1_to_U2_lost_certificate_count": len(lost12),
        "U0_to_U2_lost_certificate_count": len(lost02),
        "monotonicity_violation_count": (
            len(violations01) + len(violations12) + len(violations02)
        ),
        "U0_robust_reachable_total": len(u0_reachable),
        "U0_robust_reachable_retained_U2": u2_reachable_retained,
        "U0_robust_impossible_total": len(u0_impossible),
        "U0_robust_impossible_retained_U2": u2_impossible_retained,
    }


def _mean(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_universe_expansion_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v6 protocol is not frozen")

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

    eligible = [row for row in rows if row["eligible"] and row["levels"]]
    if not eligible:
        raise RuntimeError("no eligible v6 rows")

    monotonicity_violations = sum(
        row["monotonicity_violation_count"] for row in eligible
    )
    barrier_loss_rows = sum(
        row["U0_to_U1_lost_certificate_count"] > 0 for row in eligible
    )
    analyst_loss_rows = sum(
        row["U1_to_U2_lost_certificate_count"] > 0 for row in eligible
    )

    rr_total = sum(row["U0_robust_reachable_total"] for row in eligible)
    rr_retained = sum(
        row["U0_robust_reachable_retained_U2"] for row in eligible
    )
    ri_total = sum(row["U0_robust_impossible_total"] for row in eligible)
    ri_retained = sum(
        row["U0_robust_impossible_retained_U2"] for row in eligible
    )
    rr_retention = None if rr_total == 0 else rr_retained / rr_total
    ri_retention = None if ri_total == 0 else ri_retained / ri_total
    c4_contrast = (
        None
        if rr_retention is None or ri_retention is None
        else ri_retention - rr_retention
    )

    total_u2_reachable = sum(
        row["levels"]["U2_plus_analyst"]["status_counts"]["robust_reachable"]
        for row in eligible
    )
    total_u2_impossible = sum(
        row["levels"]["U2_plus_analyst"]["status_counts"]["robust_impossible"]
        for row in eligible
    )

    false_certificates = sum(
        row["levels"][level]["false_robust_impossible_count"]
        + row["levels"][level]["false_robust_reachable_count"]
        for row in eligible
        for level in LEVELS
    )

    contingent_means = {
        level: _mean(
            row["levels"][level]["contingent_fraction"]
            for row in eligible
        )
        for level in LEVELS
    }
    c7_contrast = (
        contingent_means["U2_plus_analyst"]
        - contingent_means["U0_source_only"]
    )

    verdicts = {
        "C1_universe_expansion_only_erodes_universal_certificates": (
            "SUPPORTED" if monotonicity_violations == 0 else "REFUTED"
        ),
        "C2_barrier_expansion_erodes_some_certificates": (
            "SUPPORTED" if barrier_loss_rows > 0 else "REFUTED"
        ),
        "C3_analyst_expansion_erodes_additional_certificates": (
            "SUPPORTED" if analyst_loss_rows > 0 else "REFUTED"
        ),
        "C4_impossibility_certificates_are_more_persistent_than_reachability_certificates": (
            "SUPPORTED"
            if c4_contrast is not None and c4_contrast > 0
            else "REFUTED"
        ),
        "C5_some_certificates_survive_full_world_expansion": (
            "SUPPORTED"
            if total_u2_reachable > 0 and total_u2_impossible > 0
            else "REFUTED"
        ),
        "C6_full_world_expansion_preserves_truth_soundness": (
            "SUPPORTED" if false_certificates == 0 else "REFUTED"
        ),
        "C7_world_expansion_creates_contingency": (
            "SUPPORTED" if c7_contrast > 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_world_universe_certificate_persistence.result.v6",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "evidence_fraction": EVIDENCE_FRACTION,
        "predeclared_verdicts": verdicts,
        "monotonicity_violation_count": monotonicity_violations,
        "barrier_expansion_certificate_loss_row_count": barrier_loss_rows,
        "analyst_expansion_certificate_loss_row_count": analyst_loss_rows,
        "certificate_persistence": {
            "U0_robust_reachable_total": rr_total,
            "U0_robust_reachable_retained_U2": rr_retained,
            "robust_reachable_retention_fraction": rr_retention,
            "U0_robust_impossible_total": ri_total,
            "U0_robust_impossible_retained_U2": ri_retained,
            "robust_impossible_retention_fraction": ri_retention,
            "impossible_minus_reachable_retention": c4_contrast,
        },
        "U2_certificate_totals": {
            "robust_reachable": total_u2_reachable,
            "robust_impossible": total_u2_impossible,
        },
        "false_universal_certificate_count": false_certificates,
        "mean_contingent_fraction": contingent_means,
        "U2_minus_U0_mean_contingent_fraction": c7_contrast,
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
                "certificate_persistence": result["certificate_persistence"],
                "mean_contingent_fraction": result["mean_contingent_fraction"],
                "U2_minus_U0_mean_contingent_fraction": result[
                    "U2_minus_U0_mean_contingent_fraction"
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
