import pandas as pd

from eog.v2.bam_sweden_riverbarrier_external_bridge import (
    RAW_COLUMNS,
    all_worlds,
    execute_bridge,
    fit_distance_thresholds,
    validate_raw_frame,
)


def _frame():
    rows = [
        [0, 0, "A", "R1", 1990, 1, 0, 0],
        [10, 0, "A", "R1", 1990, 0, 1, 0],
        [20, 0, "B", "R1", 1990, 0, 0, 1],
        [30, 0, "B", "R1", 1990, 0, 0, 0],
        [0, 0, "A", "R1", 2010, 1, 0, 0],
        [10, 0, "A", "R1", 2010, 0, 1, 0],
        [20, 0, "B", "R1", 2010, 1, 0, 1],
        [30, 0, "B", "R1", 2010, 0, 1, 0],
    ]
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def test_frozen_world_count_is_nine():
    assert len(all_worlds()) == 9


def test_geometry_thresholds_are_response_independent_and_positive():
    thresholds = fit_distance_thresholds(_frame())
    assert [name for name, _ in thresholds] == ["q25", "q50", "q75", "q90"]
    assert all(value > 0 for _, value in thresholds)


def test_exact_schema_required():
    frame = _frame()[list(RAW_COLUMNS)[::-1]]
    try:
        validate_raw_frame(frame)
    except Exception as exc:
        assert "physical schema mismatch" in str(exc)
    else:
        raise AssertionError("schema order drift should stop")


def test_bridge_retains_all_three_species_rows():
    result = execute_bridge(_frame())
    assert len(result["species_results"]) == 3
    assert {row["species"] for row in result["species_results"]} == {
        "Salmo trutta",
        "Phoxinus phoxinus",
        "Esox lucius",
    }
