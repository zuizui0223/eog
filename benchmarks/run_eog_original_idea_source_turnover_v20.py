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
    _generate_base,
    _node_id,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs,
    _outlet_corner,
    _truth_source,
)
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    DESIGNS,
    RULE,
    _candidate_sources,
    _euclidean,
    _metrics,
    _source_sets,
)


PROTOCOL = ROOT / "validation/eog_original_idea_source_turnover_v20/protocol_v20.json"
STRATEGIES = (
    "local_near_lost",
    "clustered_near_survivors",
    "dispersed_far_from_survivors",
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


def _choose_worst_source(graph, permissive, sources):
    rows = []
    for removed in sources:
        remaining = tuple(source for source in sources if source != removed)
        metrics = _metrics(graph, permissive, remaining)
        rows.append(
            (
                metrics["union_reachable_node_count"],
                _node_id(removed),
                removed,
                remaining,
                metrics,
            )
        )
    rows.sort(key=lambda row: (row[0], row[1]))
    _, _, removed, remaining, metrics = rows[0]
    return removed, tuple(remaining), metrics


def _replacement_pool(candidates, survivors, lost):
    forbidden = set(survivors) | {lost}
    return tuple(sorted(node for node in candidates if node not in forbidden))


def _choose_replacement(pool, survivors, lost, strategy):
    if not pool:
        raise ValueError("replacement pool is empty")
    if strategy == "local_near_lost":
        return sorted(
            pool,
            key=lambda node: (_euclidean(node, lost), _node_id(node)),
        )[0]
    if strategy == "clustered_near_survivors":
        return sorted(
            pool,
            key=lambda node: (
                min(_euclidean(node, survivor) for survivor in survivors),
                _node_id(node),
            ),
        )[0]
    if strategy == "dispersed_far_from_survivors":
        return sorted(
            pool,
            key=lambda node: (
                -min(_euclidean(node, survivor) for survivor in survivors),
                _node_id(node),
            ),
        )[0]
    raise ValueError(f"unknown replacement strategy: {strategy}")


def _recovery_fraction(original, post_loss, replacement):
    denom = float(original) - float(post_loss)
    if denom <= 1e-15:
        return None
    return (float(replacement) - float(post_loss)) / denom


def _insurance_recovery(original, replacement):
    if original <= 1e-15:
        return None
    return float(replacement) / float(original)


def _evaluate_design(graph, permissive, candidates, original_sources, design):
    original = _metrics(graph, permissive, original_sources)
    lost, survivors, post_loss = _choose_worst_source(
        graph,
        permissive,
        original_sources,
    )
    pool = _replacement_pool(candidates, survivors, lost)

    row = {
        "starting_design": design,
        "original_source_ids": [_node_id(node) for node in original_sources],
        "lost_source_id": _node_id(lost),
        "surviving_source_ids": [_node_id(node) for node in survivors],
        "replacement_candidate_count": len(pool),
        "estimable": bool(pool),
        "original": original,
        "post_loss": post_loss,
        "replacements": {},
    }
    if not pool:
        return row

    for strategy in STRATEGIES:
        replacement = _choose_replacement(
            pool,
            survivors,
            lost,
            strategy,
        )
        sources = tuple((*survivors, replacement))
        if len(set(sources)) != 3:
            raise RuntimeError("replacement network does not contain three unique sources")
        if replacement == lost:
            raise RuntimeError("lost source was reused as replacement")

        metrics = _metrics(graph, permissive, sources)
        coverage_recovery = _recovery_fraction(
            original["union_reachable_fraction"],
            post_loss["union_reachable_fraction"],
            metrics["union_reachable_fraction"],
        )
        insurance_recovery = _insurance_recovery(
            original["worst_source_loss_retention"],
            metrics["worst_source_loss_retention"],
        )
        row["replacements"][strategy] = {
            "replacement_source_id": _node_id(replacement),
            "source_ids": [_node_id(node) for node in sources],
            "metrics": metrics,
            "coverage_recovery_fraction": coverage_recovery,
            "insurance_recovery_fraction": insurance_recovery,
            "coverage_overshoot": (
                metrics["union_reachable_fraction"]
                > original["union_reachable_fraction"] + 1e-15
            ),
            "full_coverage_recovery": (
                metrics["union_reachable_fraction"] + 1e-15
                >= original["union_reachable_fraction"]
            ),
        }
    return row


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    anchor = _truth_source(base, outlet)
    _, graph = _graphs(base, barrier_density, RULE, outlet)

    candidates, median_potential = _candidate_sources(base, outlet, anchor)
    source_sets = _source_sets(candidates, anchor)
    row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "anchor_source": _node_id(anchor),
        "candidate_potential_median": median_potential,
        "eligible": bool(source_sets),
        "designs": {},
    }
    if not source_sets:
        return row

    for design in DESIGNS:
        original_sources = source_sets[design][3]
        row["designs"][design] = _evaluate_design(
            graph,
            base["permissive"],
            candidates,
            original_sources,
            design,
        )
    return row


def _mean(values):
    vals = [float(value) for value in values if value is not None]
    return None if not vals else float(np.mean(vals))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_source_turnover_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v20 protocol is not frozen")

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

    eligible = [row for row in rows if row["eligible"]]
    design_rows = {
        design: [
            row["designs"][design]
            for row in eligible
            if row["designs"][design]["estimable"]
        ]
        for design in DESIGNS
    }
    if not all(design_rows.values()):
        raise RuntimeError("no estimable turnover rows for a starting design")

    arrangement_difference_count = 0
    overshoot_count = 0
    all_strategies_below_original_count = 0
    tradeoff_count = 0
    t8_violations = 0

    for row in eligible:
        for design in DESIGNS:
            drow = row["designs"][design]
            if not drow["estimable"]:
                continue
            coverages = {
                strategy: drow["replacements"][strategy]["metrics"][
                    "union_reachable_fraction"
                ]
                for strategy in STRATEGIES
            }
            if len(set(round(value, 15) for value in coverages.values())) > 1:
                arrangement_difference_count += 1

            overshoot_count += sum(
                drow["replacements"][strategy]["coverage_overshoot"]
                for strategy in STRATEGIES
            )
            if all(
                not drow["replacements"][strategy]["full_coverage_recovery"]
                for strategy in STRATEGIES
            ):
                all_strategies_below_original_count += 1

            clustered = drow["replacements"]["clustered_near_survivors"]["metrics"]
            dispersed = drow["replacements"]["dispersed_far_from_survivors"]["metrics"]
            if (
                dispersed["union_reachable_fraction"]
                > clustered["union_reachable_fraction"] + 1e-15
                and clustered["worst_source_loss_retention"]
                > dispersed["worst_source_loss_retention"] + 1e-15
            ):
                tradeoff_count += 1

            for strategy in STRATEGIES:
                srow = drow["replacements"][strategy]
                ids = srow["source_ids"]
                if (
                    len(ids) != 3
                    or len(set(ids)) != 3
                    or srow["replacement_source_id"] == drow["lost_source_id"]
                ):
                    t8_violations += 1

    mean_profiles = {}
    contrasts = {}
    for design in DESIGNS:
        mean_profiles[design] = {}
        for strategy in STRATEGIES:
            mean_profiles[design][strategy] = {
                "coverage": _mean(
                    row["replacements"][strategy]["metrics"][
                        "union_reachable_fraction"
                    ]
                    for row in design_rows[design]
                ),
                "multi_source_overlap": _mean(
                    row["replacements"][strategy]["metrics"][
                        "multi_source_overlap_fraction"
                    ]
                    for row in design_rows[design]
                ),
                "worst_source_loss_retention": _mean(
                    row["replacements"][strategy]["metrics"][
                        "worst_source_loss_retention"
                    ]
                    for row in design_rows[design]
                ),
                "exclusive_source_fraction": _mean(
                    row["replacements"][strategy]["metrics"][
                        "exclusive_source_fraction"
                    ]
                    for row in design_rows[design]
                ),
                "coverage_recovery_fraction": _mean(
                    row["replacements"][strategy][
                        "coverage_recovery_fraction"
                    ]
                    for row in design_rows[design]
                ),
                "insurance_recovery_fraction": _mean(
                    row["replacements"][strategy][
                        "insurance_recovery_fraction"
                    ]
                    for row in design_rows[design]
                ),
            }

        dispersed = mean_profiles[design]["dispersed_far_from_survivors"]
        clustered = mean_profiles[design]["clustered_near_survivors"]
        contrasts[design] = {
            "dispersed_minus_clustered_coverage": (
                dispersed["coverage"] - clustered["coverage"]
            ),
            "clustered_minus_dispersed_overlap": (
                clustered["multi_source_overlap"]
                - dispersed["multi_source_overlap"]
            ),
            "clustered_minus_dispersed_insurance": (
                clustered["worst_source_loss_retention"]
                - dispersed["worst_source_loss_retention"]
            ),
        }

    verdicts = {
        "T1_restoring_source_count_does_not_restore_one_unique_function": (
            "SUPPORTED" if arrangement_difference_count > 0 else "REFUTED"
        ),
        "T2_dispersed_replacement_maximizes_coverage_on_average": (
            "SUPPORTED"
            if all(
                contrasts[design]["dispersed_minus_clustered_coverage"] > 0
                for design in DESIGNS
            )
            else "REFUTED"
        ),
        "T3_clustered_replacement_maximizes_overlap_on_average": (
            "SUPPORTED"
            if all(
                contrasts[design]["clustered_minus_dispersed_overlap"] > 0
                for design in DESIGNS
            )
            else "REFUTED"
        ),
        "T4_clustered_replacement_maximizes_source_loss_insurance_on_average": (
            "SUPPORTED"
            if all(
                contrasts[design]["clustered_minus_dispersed_insurance"] > 0
                for design in DESIGNS
            )
            else "REFUTED"
        ),
        "T5_replacement_can_overshoot_original_coverage": (
            "SUPPORTED" if overshoot_count > 0 else "REFUTED"
        ),
        "T6_source_count_recovery_does_not_guarantee_full_coverage_recovery": (
            "SUPPORTED"
            if all_strategies_below_original_count > 0
            else "REFUTED"
        ),
        "T7_coverage_insurance_tradeoff_reappears_after_turnover": (
            "SUPPORTED" if tradeoff_count > 0 else "REFUTED"
        ),
        "T8_replacement_source_count_is_exactly_three": (
            "SUPPORTED" if t8_violations == 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_source_turnover.result.v20",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "estimable_design_row_count": {
            design: len(design_rows[design]) for design in DESIGNS
        },
        "predeclared_verdicts": verdicts,
        "mean_profiles": mean_profiles,
        "strategy_contrasts": contrasts,
        "arrangement_difference_design_row_count": arrangement_difference_count,
        "coverage_overshoot_strategy_count": overshoot_count,
        "all_strategies_below_original_design_row_count": (
            all_strategies_below_original_count
        ),
        "post_turnover_coverage_insurance_tradeoff_design_row_count": tradeoff_count,
        "replacement_invariant_violation_count": t8_violations,
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
                "strategy_contrasts": result["strategy_contrasts"],
                "arrangement_difference_design_row_count": result[
                    "arrangement_difference_design_row_count"
                ],
                "coverage_overshoot_strategy_count": result[
                    "coverage_overshoot_strategy_count"
                ],
                "all_strategies_below_original_design_row_count": result[
                    "all_strategies_below_original_design_row_count"
                ],
                "post_turnover_coverage_insurance_tradeoff_design_row_count": result[
                    "post_turnover_coverage_insurance_tradeoff_design_row_count"
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
