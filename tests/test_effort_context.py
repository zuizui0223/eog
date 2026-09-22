import pytest

from eog.v2.effort_context import (
    EffortContextRow,
    EffortEligibilityPolicy,
    evidence_fingerprint,
    freeze_effort_context_ledger,
)


def _policy():
    return EffortEligibilityPolicy(
        unit_definition="node x context",
        eligibility_rule="declared response-independent effort threshold",
        unsurveyed_rule="below threshold is outside the binary endpoint",
        evidence_source="response_independent_effort",
    )


def _row(unit, node, context, eligible, evidence, fold=1):
    return EffortContextRow(
        unit_id=unit,
        node_id=node,
        context_id=context,
        fold=fold,
        eligible=eligible,
        evidence_summary=str(evidence),
        evidence_fingerprint=evidence_fingerprint(evidence),
    )


def test_ledger_projects_only_eligible_rows_to_candidate_units():
    ledger = freeze_effort_context_ledger(
        node_ids=("A", "B"),
        context_ids=("t1", "t2"),
        rows=(
            _row("B|t2", "B", "t2", False, {"active_days": 0}, 2),
            _row("A|t1", "A", "t1", True, {"active_days": 7}, 1),
            _row("B|t1", "B", "t1", True, {"active_days": 7}, 2),
            _row("A|t2", "A", "t2", False, {"active_days": 2}, 1),
        ),
        policy=_policy(),
    )
    assert tuple(row.unit_id for row in ledger.rows) == (
        "A|t1",
        "A|t2",
        "B|t1",
        "B|t2",
    )
    assert tuple(unit.unit_id for unit in ledger.candidate_units) == ("A|t1", "B|t1")
    assert ledger.unsurveyed_unit_ids == ("A|t2", "B|t2")
    assert ledger.candidate_count == 2
    assert ledger.unsurveyed_count == 2


def test_ledger_rejects_duplicate_unit_ids():
    row = _row("A|t1", "A", "t1", True, {"effort": 1})
    with pytest.raises(ValueError, match="unit IDs must be unique"):
        freeze_effort_context_ledger(
            node_ids=("A",),
            context_ids=("t1",),
            rows=(row, row),
            policy=_policy(),
        )


def test_ledger_rejects_unknown_node_or_context():
    with pytest.raises(ValueError, match="unknown node"):
        freeze_effort_context_ledger(
            node_ids=("A",),
            context_ids=("t1",),
            rows=(_row("B|t1", "B", "t1", True, {"effort": 1}),),
            policy=_policy(),
        )

    with pytest.raises(ValueError, match="unknown context"):
        freeze_effort_context_ledger(
            node_ids=("A",),
            context_ids=("t1",),
            rows=(_row("A|t2", "A", "t2", True, {"effort": 1}),),
            policy=_policy(),
        )


def test_ledger_requires_at_least_one_eligible_unit():
    with pytest.raises(ValueError, match="no eligible candidate units"):
        freeze_effort_context_ledger(
            node_ids=("A",),
            context_ids=("t1",),
            rows=(_row("A|t1", "A", "t1", False, {"effort": 0}),),
            policy=_policy(),
        )


def test_effort_policy_rejects_response_derived_evidence():
    with pytest.raises(ValueError, match="response-independent source"):
        EffortEligibilityPolicy(
            unit_definition="node x context",
            eligibility_rule="focal detections > 0",
            unsurveyed_rule="otherwise absent",
            evidence_source="focal_response",  # type: ignore[arg-type]
        )


def test_effort_evidence_fingerprint_is_deterministic():
    left = evidence_fingerprint({"days": 7, "source": "deployment"})
    right = evidence_fingerprint({"source": "deployment", "days": 7})
    assert left == right


def test_ledger_fingerprint_changes_when_effort_evidence_changes():
    first = freeze_effort_context_ledger(
        node_ids=("A",),
        context_ids=("t1",),
        rows=(_row("A|t1", "A", "t1", True, {"days": 7}),),
        policy=_policy(),
    )
    second = freeze_effort_context_ledger(
        node_ids=("A",),
        context_ids=("t1",),
        rows=(_row("A|t1", "A", "t1", True, {"days": 8}),),
        policy=_policy(),
    )
    assert first.fingerprint != second.fingerprint


def test_ledger_is_order_invariant_for_same_unit_evidence():
    rows = (
        _row("A|t1", "A", "t1", True, {"days": 7}, 1),
        _row("B|t1", "B", "t1", True, {"days": 7}, 2),
    )
    left = freeze_effort_context_ledger(
        node_ids=("A", "B"),
        context_ids=("t1",),
        rows=rows,
        policy=_policy(),
    )
    right = freeze_effort_context_ledger(
        node_ids=("A", "B"),
        context_ids=("t1",),
        rows=rows[::-1],
        policy=_policy(),
    )
    assert left.fingerprint == right.fingerprint
