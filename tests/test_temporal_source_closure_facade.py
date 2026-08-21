from __future__ import annotations


def test_validation_facade_exposes_temporal_source_closure_lazily():
    from eog.v2 import validation
    from eog.v2.temporal_source_closure import (
        TemporalSourceClosureDeclaration,
        TemporalSourceClosureResult,
        TemporalSourceClosureTransition,
        evaluate_temporal_source_closure,
    )

    assert validation.TemporalSourceClosureDeclaration is TemporalSourceClosureDeclaration
    assert validation.TemporalSourceClosureTransition is TemporalSourceClosureTransition
    assert validation.TemporalSourceClosureResult is TemporalSourceClosureResult
    assert validation.evaluate_temporal_source_closure is evaluate_temporal_source_closure

    import eog.v2 as v2

    assert "TemporalSourceClosureDeclaration" not in v2.__all__
