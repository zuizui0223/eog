"""Post-exposure EOG × BAM paired readout: numerical and design integrity tests."""
import json
import numpy as np
import pytest

from benchmarks.run_bam_one_axis_paired_v1 import (
    AXES, bit_indices, span, centroid,
)


def test_shared_coordinate_span_not_restandardized():
    z = np.array([[0.0, 0.0], [0.0, 3.0], [4.0, 0.0]])
    assert span(z) == pytest.approx(4.8)
    assert centroid(z) > 0


def test_zero_one_point_not_estimated():
    assert span(np.zeros((0, 2))) is None
    assert span(np.zeros((1, 2))) is None
    assert centroid(np.zeros((1, 2))) is None
    assert span(np.array([[1.0, 1.0], [1.0, 1.0]])) == 0.0


def test_row_order_mask_and_axis_roster_frozen():
    assert bit_indices(0b01010, 5).tolist() == [1, 3]
    assert len(AXES) == 5
    assert set(AXES) == {
        "A_narrow_vs_broad",
        "B_obligate_partner_vs_none",
        "B_antagonist_exclusion_vs_none",
        "B_partner_and_antagonist_vs_none",
        "M_barrier_closed_vs_open",
    }


def test_expected_counts_are_labeled_post_result():
    from pathlib import Path
    p = Path("validation/bam_one_axis_paired_v1/post_exposure_expected_v1.json")
    result = json.loads(p.read_text())
    assert result["status"].startswith("post_result")
    assert result["n_worlds"] == 768
    assert result["n_pairs"] == sum(v["total"] for v in result["by_axis"].values())
    assert result["n_changed_G_pairs"] == sum(v["changed"] for v in result["by_axis"].values())
    for v in result["by_axis"].values():
        assert v["changed"] == v["smaller"] + v["larger"] + v["tie"]
        assert v["changed"] <= v["total"]
