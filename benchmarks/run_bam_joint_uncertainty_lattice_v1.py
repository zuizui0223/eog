#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from eog.v2.bam_ecological_expansion_margin import (
    build_expanded_ecological_lattice,
)
from eog.v2.bam_future_assay_observation import PARAMETER_FIELDS
from eog.v2.bam_joint_uncertainty_lattice import (
    O0,
    O1,
    ecological_expansion_creates_calibration_need,
    embedded_w0_same_g_variants,
    exact_joint_target_burden,
    joint_burden_monotonicity_violations,
    same_g_w1_variants,
    strict_joint_interaction,
)
from eog.v2.bam_structured_counterfactuals import (
    expanded_variant_counterfactual,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_joint_uncertainty_lattice_v1/protocol_v1.json"

PARENTS = {
    "structured_future_targets": (
        ROOT / "validation/bam_structured_counterfactuals_v1/result_summary_v1.json",
        "f502fb647ba4666f5c40ddbd5639123f3e0296fe492dd97a1ec19ec246531cb1",
    ),
    "future_target_evidence": (
        ROOT / "validation/bam_future_target_evidence_v1/result_summary_v1.json",
        "b87bfa721e21acfdc0a03239b0ed556f77bd77e3ee49f25c11d56ece02b8db58",
    ),
    "assay_observation": (
        ROOT / "validation/bam_future_assay_observation_v1/result_summary_v1.json",
        "3bed33f39d2c8845cb52989855f2ab024327464870224a11568ebb7436bbe332",
    ),
    "stochastic_assay_risk": (
        ROOT / "validation/bam_stochastic_assay_risk_v1/result_summary_v1.json",
        "545fad056cdfe3f93eca3e1a973560aeb67c605cb0ae8508ff6fc75c01b09121",
    ),
}
TRANSFORMATIONS = ("climate_shift", "biotic_stress", "barrier_restoration")
ACTION_IDS = tuple(
    sorted(
        (
            *(f"assay:{field}" for field in PARAMETER_FIELDS),
            "assay_process_calibration",
        )
    )
)
LEVELS = ("W0O0", "W0O1", "W1O0", "W1O1")


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _burden_value(value):
    return math.inf if value is None else int(value)


def _json_burden(value):
    return None if value is None else int(value)


def _dist(values):
    finite = [int(value) for value in values if value is not None]
    out = {str(k): int(v) for k, v in sorted(Counter(finite).items())}
    missing = sum(value is None for value in values)
    if missing:
        out["INF"] = missing
    return out


def _mean(values):
    finite = [int(value) for value in values if value is not None]
    return None if not finite else float(statistics.mean(finite))


def _median(values):
    finite = [int(value) for value in values if value is not None]
    return None if not finite else float(statistics.median(finite))


def _burden_row(row):
    return {
        "minimum_size": _json_burden(row.minimum_size),
        "minimum_action_ids": (
            None if row.minimum_action_ids is None else list(row.minimum_action_ids)
        ),
        "sufficient": bool(row.sufficient),
        "target_class_count": int(row.target_class_count),
        "ecological_world_count": int(row.ecological_world_count),
        "joint_hypothesis_count": int(row.joint_hypothesis_count),
        "no_calibration_minimum_size": _json_burden(
            row.no_calibration_minimum_size
        ),
        "calibration_required_for_minimum": bool(
            row.calibration_required_for_minimum
        ),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("Phase-IX protocol is not frozen")

    for label, (path, expected) in PARENTS.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("result_fingerprint") != expected:
            raise RuntimeError(f"{label} parent fingerprint mismatch")

    roster = []
    rows = []
    monotonicity_violations = []
    interaction_examples = []
    calibration_creation_examples = []

    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        activation = audit_system_activation(system)
        roster.append(
            {
                "system_id": spec.system_id,
                "activation_status": activation.status,
                "system_fingerprint": system.fingerprint,
                "activation_fingerprint": activation.fingerprint,
            }
        )
        if activation.status != "PASS":
            continue

        lattice = build_expanded_ecological_lattice(system)
        source_id = f"r{system.landscape.height // 2}c0"
        eligible_truths = tuple(
            world
            for world in system.worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )
        by_G = {}
        for truth in eligible_truths:
            by_G.setdefault(int(truth.occupied_mask), []).append(truth)

        for G, truths in sorted(by_G.items()):
            w0 = embedded_w0_same_g_variants(system, lattice, G)
            w1 = same_g_w1_variants(lattice, G)
            w0_ids = {row.variant_id for row in w0}
            w1_ids = {row.variant_id for row in w1}
            if not w0_ids.issubset(w1_ids):
                raise RuntimeError("W0 same-G variants are not a subset of W1")

            for transformation in TRANSFORMATIONS:
                target_w1 = {
                    row.variant_id: expanded_variant_counterfactual(
                        system, row, transformation
                    ).binary_decision
                    for row in w1
                }
                target_w0 = {
                    row.variant_id: target_w1[row.variant_id]
                    for row in w0
                }

                burdens = {
                    "W0O0": exact_joint_target_burden(
                        w0,
                        target_w0,
                        O0,
                        ecological_universe="W0",
                        observation_universe="O0",
                        available_action_ids=ACTION_IDS,
                    ),
                    "W0O1": exact_joint_target_burden(
                        w0,
                        target_w0,
                        O1,
                        ecological_universe="W0",
                        observation_universe="O1",
                        available_action_ids=ACTION_IDS,
                    ),
                    "W1O0": exact_joint_target_burden(
                        w1,
                        target_w1,
                        O0,
                        ecological_universe="W1",
                        observation_universe="O0",
                        available_action_ids=ACTION_IDS,
                    ),
                    "W1O1": exact_joint_target_burden(
                        w1,
                        target_w1,
                        O1,
                        ecological_universe="W1",
                        observation_universe="O1",
                        available_action_ids=ACTION_IDS,
                    ),
                }

                violations = joint_burden_monotonicity_violations(burdens)
                if violations:
                    monotonicity_violations.append(
                        {
                            "system_id": spec.system_id,
                            "G_mask": G,
                            "transformation": transformation,
                            "violations": list(violations),
                        }
                    )

                interaction = strict_joint_interaction(burdens)
                calibration_created = ecological_expansion_creates_calibration_need(
                    burdens
                )

                record = {
                    "system_id": spec.system_id,
                    "G_mask": G,
                    "G_count": G.bit_count(),
                    "truth_multiplicity": len(truths),
                    "transformation": transformation,
                    "burdens": {
                        level: _burden_row(burdens[level])
                        for level in LEVELS
                    },
                    "strict_joint_interaction": interaction,
                    "ecological_expansion_creates_calibration_need": (
                        calibration_created
                    ),
                }
                rows.append(record)

                if interaction and len(interaction_examples) < 12:
                    interaction_examples.append(record)
                if calibration_created and len(calibration_creation_examples) < 12:
                    calibration_creation_examples.append(record)

    if monotonicity_violations:
        raise RuntimeError(
            f"joint burden monotonicity violations: {len(monotonicity_violations)}"
        )

    by_transformation = {}
    interaction_count = 0
    calibration_creation_count = 0
    w1o1_failures = 0

    for transformation in TRANSFORMATIONS:
        subset = [row for row in rows if row["transformation"] == transformation]
        level_summary = {}
        for level in LEVELS:
            values = [
                row["burdens"][level]["minimum_size"]
                for row in subset
            ]
            level_summary[level] = {
                "burden_distribution": _dist(values),
                "finite_mean": _mean(values),
                "finite_median": _median(values),
                "target_identified_zero_burden_fibers": sum(
                    value == 0 for value in values
                ),
                "insufficient_fibers": sum(value is None for value in values),
                "calibration_required_for_minimum_fibers": sum(
                    row["burdens"][level][
                        "calibration_required_for_minimum"
                    ]
                    for row in subset
                ),
                "truth_weighted_burden_distribution": _dist(
                    [
                        row["burdens"][level]["minimum_size"]
                        for row in subset
                        for _ in range(int(row["truth_multiplicity"]))
                    ]
                ),
            }

        ecological_only_increase = sum(
            _burden_value(row["burdens"]["W1O0"]["minimum_size"])
            > _burden_value(row["burdens"]["W0O0"]["minimum_size"])
            for row in subset
        )
        observation_only_increase = sum(
            _burden_value(row["burdens"]["W0O1"]["minimum_size"])
            > _burden_value(row["burdens"]["W0O0"]["minimum_size"])
            for row in subset
        )
        joint_increment = sum(row["strict_joint_interaction"] for row in subset)
        calibration_created = sum(
            row["ecological_expansion_creates_calibration_need"]
            for row in subset
        )
        w1_fail = sum(
            not row["burdens"]["W1O1"]["sufficient"]
            for row in subset
        )

        interaction_count += joint_increment
        calibration_creation_count += calibration_created
        w1o1_failures += w1_fail

        by_transformation[transformation] = {
            "unique_fibers": len(subset),
            "levels": level_summary,
            "ecological_only_burden_increase_fibers": ecological_only_increase,
            "observation_only_burden_increase_fibers": observation_only_increase,
            "strict_joint_interaction_fibers": joint_increment,
            "ecological_expansion_created_calibration_need_fibers": (
                calibration_created
            ),
            "W1O1_complete_library_failures": w1_fail,
        }

    verdicts = {
        "H1_nested_joint_burden_monotonicity": (
            "SUPPORTED" if not monotonicity_violations else "REFUTED"
        ),
        "H2_joint_uncertainty_interaction_exists": (
            "SUPPORTED" if interaction_count > 0 else "REFUTED"
        ),
        "H3_ecological_expansion_can_create_calibration_need": (
            "SUPPORTED" if calibration_creation_count > 0 else "REFUTED"
        ),
        "H4_complete_joint_library_resolves_all": (
            "SUPPORTED" if w1o1_failures == 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.bam_joint_uncertainty_lattice.result.v1",
        "fiber_transformation_row_count": len(rows),
        "monotonicity_violation_count": len(monotonicity_violations),
        "strict_joint_interaction_count": interaction_count,
        "ecological_expansion_created_calibration_need_count": (
            calibration_creation_count
        ),
        "W1O1_complete_library_failure_count": w1o1_failures,
        "predeclared_verdicts": verdicts,
        "by_transformation": by_transformation,
        "interaction_examples": interaction_examples,
        "calibration_creation_examples": calibration_creation_examples,
        "activation_roster": roster,
        "rows": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "fiber_transformation_row_count": result[
            "fiber_transformation_row_count"
        ],
        "strict_joint_interaction_count": result[
            "strict_joint_interaction_count"
        ],
        "ecological_expansion_created_calibration_need_count": result[
            "ecological_expansion_created_calibration_need_count"
        ],
        "W1O1_complete_library_failure_count": result[
            "W1O1_complete_library_failure_count"
        ],
        "predeclared_verdicts": result["predeclared_verdicts"],
        "by_transformation": result["by_transformation"],
        "interaction_examples": result["interaction_examples"],
        "calibration_creation_examples": result[
            "calibration_creation_examples"
        ],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
