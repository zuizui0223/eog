#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from eog.v2.bam_ecological_expansion_margin import (
    build_expanded_ecological_lattice,
    declared_world_coordinates,
)
from eog.v2.bam_counterfactual_identifiability import (
    exact_minimum_truth_target_measurements,
)
from eog.v2.bam_future_target_evidence import (
    current_state_measurements,
    exact_minimum_truth_target_measurement_size,
    full_parameter_world_target,
    parameter_measurements,
)
from eog.v2.bam_structured_counterfactuals import (
    expanded_variant_bam_state_key,
    expanded_variant_counterfactual,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_future_target_evidence_v1/protocol_v1.json"
PARENT = ROOT / "validation/bam_structured_counterfactuals_v1/result_summary_v1.json"
EXPECTED_PARENT = "f502fb647ba4666f5c40ddbd5639123f3e0296fe492dd97a1ec19ec246531cb1"
TRANSFORMATIONS = ("climate_shift", "biotic_stress", "barrier_restoration")


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _dist(values):
    return {str(k): int(v) for k, v in sorted(Counter(values).items())}


def _mean(values):
    return None if not values else float(statistics.mean(values))


def _median(values):
    return None if not values else float(statistics.median(values))


def _plan_row(plan):
    return {
        "sufficient": bool(plan.evidence_library_sufficient),
        "minimum_size": plan.minimum_size,
        "minimum_measurement_ids": (
            None
            if plan.minimum_measurement_ids is None
            else list(plan.minimum_measurement_ids)
        ),
        "target_already_identified": bool(plan.target_already_identified),
    }


def _size_row(size):
    return {
        "sufficient": size is not None,
        "minimum_size": size,
        "minimum_measurement_ids": None,
        "target_already_identified": size == 0,
    }


def _complete_state_sufficient(
    state_by_id,
    truth_variant_id,
    target_by_world,
):
    truth_target = target_by_world[truth_variant_id]
    if len(set(target_by_world.values())) == 1:
        return True, True
    truth_state = state_by_id[truth_variant_id]
    same_state_ids = [
        world_id
        for world_id, state in state_by_id.items()
        if state == truth_state
    ]
    sufficient = all(
        target_by_world[world_id] == truth_target
        for world_id in same_state_ids
    )
    return sufficient, False


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("Phase-VI protocol is not frozen")
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    if parent.get("result_fingerprint") != EXPECTED_PARENT:
        raise RuntimeError("Phase-V parent fingerprint mismatch")

    roster = []
    truth_rows = []
    s11_matches = []

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
        by_coords = {row.coordinates: row for row in lattice}
        source_id = f"r{system.landscape.height // 2}c0"
        eligible_truths = tuple(
            world
            for world in system.worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )

        for truth in eligible_truths:
            G = int(truth.occupied_mask)
            survivors = tuple(
                row for row in lattice if int(row.occupied_mask) == G
            )
            survivor_ids = tuple(row.variant_id for row in survivors)
            truth_variant = by_coords[declared_world_coordinates(system, truth)]
            if int(truth_variant.occupied_mask) != G:
                raise RuntimeError("embedded truth variant does not reproduce truth G")

            # Parameter evidence is cheap to construct and is required for every truth.
            # Present-state signatures/libraries are built lazily only when a target is
            # not already E1-identified and the complete-state sufficiency question is
            # actually relevant.
            parameter_library = parameter_measurements(
                survivors,
                survivor_ids,
                truth_variant.variant_id,
            )
            state_by_id = None
            state_library = None

            parameter_world_target = full_parameter_world_target(
                survivors,
                survivor_ids,
            )
            world_plan = exact_minimum_truth_target_measurements(
                survivor_ids,
                truth_variant.variant_id,
                parameter_world_target,
                parameter_library,
            )
            if world_plan.minimum_size is None:
                raise RuntimeError("complete parameter library failed to identify W1 truth world")

            transformation_rows = {}
            for transformation in TRANSFORMATIONS:
                outcomes = {
                    row.variant_id: expanded_variant_counterfactual(
                        system, row, transformation
                    )
                    for row in survivors
                }
                exact_target = {
                    world_id: outcome.counterfactual_G
                    for world_id, outcome in outcomes.items()
                }
                binary_target = {
                    world_id: outcome.binary_decision
                    for world_id, outcome in outcomes.items()
                }

                exact_parameter = exact_minimum_truth_target_measurements(
                    survivor_ids,
                    truth_variant.variant_id,
                    exact_target,
                    parameter_library,
                )
                binary_parameter = exact_minimum_truth_target_measurements(
                    survivor_ids,
                    truth_variant.variant_id,
                    binary_target,
                    parameter_library,
                )

                exact_already = len(set(exact_target.values())) == 1
                binary_already = len(set(binary_target.values())) == 1

                if exact_already:
                    exact_state_sufficient = True
                else:
                    if state_by_id is None:
                        state_by_id = {
                            row.variant_id: expanded_variant_bam_state_key(system, row)
                            for row in survivors
                        }
                    exact_state_sufficient, _ = _complete_state_sufficient(
                        state_by_id,
                        truth_variant.variant_id,
                        exact_target,
                    )

                if binary_already:
                    binary_state_sufficient = True
                else:
                    if state_by_id is None:
                        state_by_id = {
                            row.variant_id: expanded_variant_bam_state_key(system, row)
                            for row in survivors
                        }
                    binary_state_sufficient, _ = _complete_state_sufficient(
                        state_by_id,
                        truth_variant.variant_id,
                        binary_target,
                    )

                # Combined target cardinality is needed only for the binary target.
                # If E1 already identifies the target it is zero. If one parameter
                # assay suffices, no union with state evidence can improve below one.
                if binary_already:
                    binary_combined_size = 0
                elif binary_parameter.minimum_size == 1:
                    binary_combined_size = 1
                else:
                    if state_library is None:
                        state_library = current_state_measurements(
                            system,
                            survivors,
                            survivor_ids,
                            truth_variant.variant_id,
                        )
                    binary_combined_size = exact_minimum_truth_target_measurement_size(
                        survivor_ids,
                        truth_variant.variant_id,
                        binary_target,
                        (*state_library, *parameter_library),
                    )

                if not binary_parameter.evidence_library_sufficient:
                    raise RuntimeError(
                        f"parameter library failed binary target: {spec.system_id} "
                        f"{truth.world_id} {transformation}"
                    )
                if not exact_parameter.evidence_library_sufficient:
                    raise RuntimeError(
                        f"parameter library failed exact target: {spec.system_id} "
                        f"{truth.world_id} {transformation}"
                    )

                transformation_rows[transformation] = {
                    "exact_target_class_count": len(set(exact_target.values())),
                    "binary_target_class_count": len(set(binary_target.values())),
                    "truth_binary_value": bool(binary_target[truth_variant.variant_id]),
                    "exact_map": {
                        "state_only": {
                            "sufficient": exact_state_sufficient,
                            "minimum_size": 0 if exact_already else None,
                            "minimum_measurement_ids": None,
                            "target_already_identified": exact_already,
                        },
                        "parameter_only": _plan_row(exact_parameter),
                        "combined": None,
                    },
                    "binary_decision": {
                        "state_only": {
                            "sufficient": binary_state_sufficient,
                            "minimum_size": 0 if binary_already else None,
                            "minimum_measurement_ids": None,
                            "target_already_identified": binary_already,
                        },
                        "parameter_only": _plan_row(binary_parameter),
                        "combined": _size_row(binary_combined_size),
                    },
                }

                if (
                    spec.system_id == "S11_9x5_gap"
                    and G == 2138792820255
                    and transformation == "climate_shift"
                ):
                    s11_matches.append(
                        {
                            "truth_world_id": truth.world_id,
                            "truth_variant_id": truth_variant.variant_id,
                            "survivor_count": len(survivors),
                            "binary_target_class_count": len(set(binary_target.values())),
                            "state_only": {
                                "sufficient": binary_state_sufficient,
                                "minimum_size": 0 if binary_already else None,
                                "minimum_measurement_ids": None,
                                "target_already_identified": binary_already,
                            },
                            "parameter_only": _plan_row(binary_parameter),
                            "combined": _size_row(binary_combined_size),
                        }
                    )

            truth_rows.append(
                {
                    "system_id": spec.system_id,
                    "truth_world_id": truth.world_id,
                    "truth_variant_id": truth_variant.variant_id,
                    "G_mask": G,
                    "G_count": len(truth.occupied_ids),
                    "W1_same_G_survivors": len(survivors),
                    "parameter_world": _plan_row(world_plan),
                    "transformations": transformation_rows,
                }
            )

    if len(truth_rows) != 768:
        raise RuntimeError(f"expected 768 frozen truths, got {len(truth_rows)}")
    if not s11_matches:
        raise RuntimeError("preregistered S11 dormant climate fiber not found")

    state_insufficiency_exists = False
    parameter_rescue_all = True
    target_saving_by_transformation = {}
    by_transformation = {}
    canonical_param_frequency = {}

    for transformation in TRANSFORMATIONS:
        binary_rows = [
            row["transformations"][transformation]["binary_decision"]
            for row in truth_rows
        ]
        exact_rows = [
            row["transformations"][transformation]["exact_map"]
            for row in truth_rows
        ]

        unresolved_binary_indices = [
            i
            for i, row in enumerate(binary_rows)
            if not row["state_only"]["target_already_identified"]
        ]
        state_insufficient_binary = [
            i
            for i in unresolved_binary_indices
            if not binary_rows[i]["state_only"]["sufficient"]
        ]
        state_insufficiency_exists = state_insufficiency_exists or bool(
            state_insufficient_binary
        )

        param_failed = [
            i
            for i in unresolved_binary_indices
            if not binary_rows[i]["parameter_only"]["sufficient"]
        ]
        parameter_rescue_all = parameter_rescue_all and not param_failed

        binary_param_sizes = [
            int(row["parameter_only"]["minimum_size"])
            for row in binary_rows
            if row["parameter_only"]["minimum_size"] is not None
        ]
        exact_param_sizes = [
            int(row["parameter_only"]["minimum_size"])
            for row in exact_rows
            if row["parameter_only"]["minimum_size"] is not None
        ]
        binary_combined_sizes = [
            int(row["combined"]["minimum_size"])
            for row in binary_rows
            if row["combined"]["minimum_size"] is not None
        ]

        world_sizes = [
            int(row["parameter_world"]["minimum_size"])
            for row in truth_rows
            if row["parameter_world"]["minimum_size"] is not None
        ]
        strict_saving = sum(
            int(binary_rows[i]["parameter_only"]["minimum_size"])
            < int(truth_rows[i]["parameter_world"]["minimum_size"])
            for i in range(len(truth_rows))
        )
        target_saving_by_transformation[transformation] = strict_saving > 0

        freq = Counter()
        for row in binary_rows:
            ids = row["parameter_only"]["minimum_measurement_ids"]
            if ids is None:
                continue
            for evidence_id in ids:
                freq[evidence_id] += 1
        canonical_param_frequency[transformation] = dict(sorted(freq.items()))

        by_transformation[transformation] = {
            "binary": {
                "already_identified_at_E1": sum(
                    row["state_only"]["target_already_identified"]
                    for row in binary_rows
                ),
                "unresolved_at_E1": len(unresolved_binary_indices),
                "state_only_insufficient": len(state_insufficient_binary),
                "state_only_resolvable": (
                    len(unresolved_binary_indices) - len(state_insufficient_binary)
                ),
                "parameter_library_failures": len(param_failed),
                "minimum_parameter_assay_distribution": _dist(binary_param_sizes),
                "minimum_parameter_assay_mean": _mean(binary_param_sizes),
                "minimum_parameter_assay_median": _median(binary_param_sizes),
                "minimum_combined_channel_distribution": _dist(binary_combined_sizes),
                "strict_parameter_assay_saving_vs_world_identification": strict_saving,
            },
            "exact_map": {
                "state_only_insufficient": sum(
                    (not row["state_only"]["target_already_identified"])
                    and (not row["state_only"]["sufficient"])
                    for row in exact_rows
                ),
                "minimum_parameter_assay_distribution": _dist(exact_param_sizes),
                "minimum_parameter_assay_mean": _mean(exact_param_sizes),
                "minimum_parameter_assay_median": _median(exact_param_sizes),
            },
            "canonical_minimum_parameter_frequency": canonical_param_frequency[
                transformation
            ],
        }

    world_sizes = [
        int(row["parameter_world"]["minimum_size"])
        for row in truth_rows
        if row["parameter_world"]["minimum_size"] is not None
    ]

    H1 = state_insufficiency_exists
    H2 = parameter_rescue_all
    H3 = all(target_saving_by_transformation.values())
    H4 = all(
        (not row["state_only"]["sufficient"])
        and row["parameter_only"]["sufficient"]
        and row["combined"]["sufficient"]
        for row in s11_matches
    )

    result = {
        "schema": "eog.bam_future_target_evidence.result.v1",
        "parent_result_fingerprint": EXPECTED_PARENT,
        "truth_count": len(truth_rows),
        "S11_dormant_climate_truth_matches": len(s11_matches),
        "predeclared_verdicts": {
            "H1_state_only_insufficiency_exists": "SUPPORTED" if H1 else "REFUTED",
            "H2_parameter_rescue_all": "SUPPORTED" if H2 else "REFUTED",
            "H3_target_specific_saving_exists": {
                key: "SUPPORTED" if value else "REFUTED"
                for key, value in target_saving_by_transformation.items()
            },
            "H4_dormant_alias_requires_parameter_evidence": (
                "SUPPORTED" if H4 else "REFUTED"
            ),
        },
        "parameter_world_identification": {
            "minimum_parameter_assay_distribution": _dist(world_sizes),
            "mean": _mean(world_sizes),
            "median": _median(world_sizes),
            "maximum": max(world_sizes) if world_sizes else None,
        },
        "by_transformation": by_transformation,
        "S11_dormant_climate_evidence": s11_matches,
        "activation_roster": roster,
        "truth_rows": truth_rows,
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
        "truth_count": result["truth_count"],
        "S11_dormant_climate_truth_matches": result["S11_dormant_climate_truth_matches"],
        "predeclared_verdicts": result["predeclared_verdicts"],
        "parameter_world_identification": result["parameter_world_identification"],
        "by_transformation": result["by_transformation"],
        "S11_dormant_climate_evidence": result["S11_dormant_climate_evidence"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
