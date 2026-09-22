"""Response-independent known-truth examples for the generic effort/context ledger."""

from __future__ import annotations

import json

from eog.v2.effort_context import (
    EffortContextRow,
    EffortEligibilityPolicy,
    evidence_fingerprint,
    freeze_effort_context_ledger,
)


def _row(unit_id, node_id, context_id, fold, eligible, payload):
    return EffortContextRow(
        unit_id=unit_id,
        node_id=node_id,
        context_id=context_id,
        fold=fold,
        eligible=eligible,
        evidence_summary=json.dumps(payload, sort_keys=True),
        evidence_fingerprint=evidence_fingerprint(payload),
    )


def run_benchmark() -> dict[str, object]:
    telemetry = freeze_effort_context_ledger(
        node_ids=("R1", "R2"),
        context_ids=("w1", "w2"),
        rows=(
            _row("R1|w1", "R1", "w1", 1, True, {"active_days": 7}),
            _row("R2|w1", "R2", "w1", 2, False, {"active_days": 0}),
            _row("R1|w2", "R1", "w2", 1, True, {"active_days": 7}),
            _row("R2|w2", "R2", "w2", 2, True, {"active_days": 5}),
        ),
        policy=EffortEligibilityPolicy(
            unit_definition="receiver x scored week",
            eligibility_rule="receiver activity independently certifies the scored week",
            unsurveyed_rule="inactive receiver-week is outside the endpoint",
            evidence_source="response_independent_effort",
        ),
    )

    transect = freeze_effort_context_ledger(
        node_ids=("T1", "T2"),
        context_ids=("v1", "v2"),
        rows=(
            _row("T1|v1", "T1", "v1", 1, True, {"linked_child_points": 4}),
            _row("T2|v1", "T2", "v1", 2, False, {"linked_child_points": 2}),
            _row("T1|v2", "T1", "v2", 1, True, {"linked_child_points": 3}),
            _row("T2|v2", "T2", "v2", 2, True, {"linked_child_points": 5}),
        ),
        policy=EffortEligibilityPolicy(
            unit_definition="parent transect visit",
            eligibility_rule="at least three linked child points",
            unsurveyed_rule="fewer than three linked child points is outside endpoint",
            evidence_source="response_independent_registry",
        ),
    )

    if telemetry.candidate_count != 3 or telemetry.unsurveyed_count != 1:
        raise AssertionError("telemetry eligibility oracle failed")
    if transect.candidate_count != 3 or transect.unsurveyed_count != 1:
        raise AssertionError("transect eligibility oracle failed")

    return {
        "schema": "eog.effort_context_known_truth.v1",
        "uses_biological_response": False,
        "systems": {
            "telemetry": {
                "candidate_unit_ids": [
                    unit.unit_id for unit in telemetry.candidate_units
                ],
                "unsurveyed_unit_ids": list(telemetry.unsurveyed_unit_ids),
                "ledger_fingerprint": telemetry.fingerprint,
                "policy_fingerprint": telemetry.policy_fingerprint,
            },
            "transect": {
                "candidate_unit_ids": [
                    unit.unit_id for unit in transect.candidate_units
                ],
                "unsurveyed_unit_ids": list(transect.unsurveyed_unit_ids),
                "ledger_fingerprint": transect.fingerprint,
                "policy_fingerprint": transect.policy_fingerprint,
            },
        },
        "interpretation": (
            "Different upstream effort calculations project to the same audited "
            "candidate-unit interface without using focal biological outcomes."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))
