import pytest

from eog.v2.observation_process import (
    BinaryObservationContract,
    materialize_binary_observation,
)
from eog.v2.problem_contract import (
    CandidateUnit,
    ObservationSemantics,
    freeze_pre_response_problem,
)


def _problem():
    return freeze_pre_response_problem(
        node_ids=("A", "B"),
        component_ids=("c", "c"),
        context_ids=("t1", "t2"),
        candidate_units=(
            CandidateUnit("A|t1", "A", "t1", 1),
            CandidateUnit("B|t1", "B", "t1", 2),
            CandidateUnit("A|t2", "A", "t2", 1),
            CandidateUnit("B|t2", "B", "t2", 2),
        ),
        observation_semantics=ObservationSemantics(
            effort_eligible_rule="candidate units are already effort eligible",
            positive_rule="declared downstream",
            negative_rule="declared downstream",
            unsurveyed_rule="not in candidate universe",
            zero_interpretation="recorded non-detection only",
        ),
        baseline_fields=(),
        split_fingerprint="split",
        world_family_fingerprint="worlds",
        source_fingerprint="source",
    )


def _explicit():
    return BinaryObservationContract(
        mode="explicit_binary_tokens",
        endpoint_name="site-occasion detection",
        positive_semantics="token 1",
        negative_semantics="token 0",
        unavailable_semantics="NA token",
        zero_interpretation="observed non-detection, not biological absence",
    )


def _complete_source():
    return BinaryObservationContract(
        mode="complete_source_zero",
        endpoint_name="receiver-week detection",
        positive_semantics="at least one focal event",
        negative_semantics="eligible unit with no focal event after complete response source",
        unavailable_semantics="unit excluded by frozen response mapping",
        zero_interpretation="observed non-detection under eligible effort",
    )


def test_explicit_binary_tokens_require_complete_classification():
    endpoint = materialize_binary_observation(
        _problem(),
        _explicit(),
        positive_unit_ids=("A|t1",),
        explicit_negative_unit_ids=("B|t1", "B|t2"),
        unavailable_unit_ids=("A|t2",),
    )
    assert endpoint.scored_unit_ids == ("A|t1", "B|t1", "B|t2")
    assert endpoint.labels == (1, 0, 0)
    assert endpoint.positive_count == 1
    assert endpoint.negative_count == 2
    assert endpoint.unavailable_unit_ids == ("A|t2",)


def test_explicit_mode_never_turns_missing_unit_into_zero():
    with pytest.raises(ValueError, match="requires every frozen candidate unit"):
        materialize_binary_observation(
            _problem(),
            _explicit(),
            positive_unit_ids=("A|t1",),
            explicit_negative_unit_ids=("B|t1",),
        )


def test_complete_source_zero_derives_only_after_completeness_confirmation():
    with pytest.raises(ValueError, match="response_source_complete=True"):
        materialize_binary_observation(
            _problem(),
            _complete_source(),
            positive_unit_ids=("A|t1",),
        )

    endpoint = materialize_binary_observation(
        _problem(),
        _complete_source(),
        positive_unit_ids=("A|t1",),
        unavailable_unit_ids=("A|t2",),
        response_source_complete=True,
    )
    assert endpoint.scored_unit_ids == ("A|t1", "B|t1", "B|t2")
    assert endpoint.labels == (1, 0, 0)


def test_complete_source_mode_rejects_explicit_negative_ids():
    with pytest.raises(ValueError, match="explicit_negative_unit_ids must be empty"):
        materialize_binary_observation(
            _problem(),
            _complete_source(),
            positive_unit_ids=("A|t1",),
            explicit_negative_unit_ids=("B|t1",),
            response_source_complete=True,
        )


def test_response_ids_outside_candidate_universe_fail_closed():
    with pytest.raises(ValueError, match="outside the frozen candidate universe"):
        materialize_binary_observation(
            _problem(),
            _complete_source(),
            positive_unit_ids=("C|t1",),
            response_source_complete=True,
        )


def test_overlapping_response_classes_fail_closed():
    with pytest.raises(ValueError, match="overlap"):
        materialize_binary_observation(
            _problem(),
            _explicit(),
            positive_unit_ids=("A|t1",),
            explicit_negative_unit_ids=("A|t1", "B|t1", "A|t2", "B|t2"),
        )


def test_duplicate_response_ids_fail_closed():
    with pytest.raises(ValueError, match="must not contain duplicates"):
        materialize_binary_observation(
            _problem(),
            _complete_source(),
            positive_unit_ids=("A|t1", "A|t1"),
            response_source_complete=True,
        )


def test_complete_source_flag_is_forbidden_in_explicit_mode():
    with pytest.raises(ValueError, match="reserved for complete_source_zero"):
        materialize_binary_observation(
            _problem(),
            _explicit(),
            positive_unit_ids=("A|t1",),
            explicit_negative_unit_ids=("B|t1", "A|t2", "B|t2"),
            response_source_complete=True,
        )


def test_materialization_is_deterministic_and_candidate_ordered():
    kwargs = dict(
        positive_unit_ids=("B|t2", "A|t1"),
        explicit_negative_unit_ids=("B|t1", "A|t2"),
    )
    left = materialize_binary_observation(_problem(), _explicit(), **kwargs)
    right = materialize_binary_observation(_problem(), _explicit(), **kwargs)
    assert left.fingerprint == right.fingerprint
    assert left.scored_unit_ids == ("A|t1", "B|t1", "A|t2", "B|t2")
    assert left.labels == (1, 0, 0, 1)
