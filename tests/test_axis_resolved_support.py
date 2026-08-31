import numpy as np
import pytest

from eog.v2.axis_resolved_support import (
    audit_axis_resolved_overlap,
    schoener_overlap,
)


def test_vertical_partition_is_hidden_by_xy_projection():
    a = np.zeros((2, 3, 2, 1), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, 0] = 1.0
    b[:, :, 1, 0] = 1.0

    result = audit_axis_resolved_overlap(a, b)

    assert result.horizontal_projection_overlap == pytest.approx(1.0)
    assert result.horizontal_vertical_overlap == pytest.approx(0.0)
    assert result.horizontal_temporal_overlap == pytest.approx(1.0)
    assert result.full_overlap == pytest.approx(0.0)
    assert result.vertical_hidden_partition_gap == pytest.approx(1.0)
    assert result.temporal_hidden_partition_gap == pytest.approx(0.0)
    assert result.total_projection_collapse_gap == pytest.approx(1.0)


def test_temporal_partition_is_hidden_by_xy_projection():
    a = np.zeros((2, 2, 1, 4), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, :2] = 1.0
    b[:, :, 0, 2:] = 1.0

    result = audit_axis_resolved_overlap(a, b)

    assert result.horizontal_projection_overlap == pytest.approx(1.0)
    assert result.horizontal_vertical_overlap == pytest.approx(1.0)
    assert result.horizontal_temporal_overlap == pytest.approx(0.0)
    assert result.full_overlap == pytest.approx(0.0)
    assert result.vertical_hidden_partition_gap == pytest.approx(0.0)
    assert result.temporal_hidden_partition_gap == pytest.approx(1.0)


def test_joint_z_time_partition_can_be_invisible_on_each_single_axis():
    a = np.zeros((1, 1, 2, 2), dtype=float)
    b = np.zeros_like(a)
    a[0, 0, 0, 0] = 1.0
    a[0, 0, 1, 1] = 1.0
    b[0, 0, 0, 1] = 1.0
    b[0, 0, 1, 0] = 1.0

    result = audit_axis_resolved_overlap(a, b)

    assert result.horizontal_projection_overlap == pytest.approx(1.0)
    assert result.horizontal_vertical_overlap == pytest.approx(1.0)
    assert result.horizontal_temporal_overlap == pytest.approx(1.0)
    assert result.full_overlap == pytest.approx(0.0)
    assert result.joint_only_hidden_partition_gap == pytest.approx(1.0)


def test_overlap_is_invariant_to_positive_rescaling_and_axis_positions():
    rng = np.random.default_rng(42)
    a = rng.random((3, 2, 4, 5))
    b = rng.random((3, 2, 4, 5))

    original = audit_axis_resolved_overlap(a, b)
    rescaled = audit_axis_resolved_overlap(a * 7.0, b * 0.25)
    permuted = audit_axis_resolved_overlap(
        np.transpose(a, (3, 2, 0, 1)),
        np.transpose(b, (3, 2, 0, 1)),
        horizontal_axes=(2, 3),
        vertical_axis=1,
        temporal_axis=0,
    )

    assert rescaled.full_overlap == pytest.approx(original.full_overlap)
    assert rescaled.horizontal_projection_overlap == pytest.approx(
        original.horizontal_projection_overlap
    )
    assert permuted.full_overlap == pytest.approx(original.full_overlap)
    assert permuted.horizontal_projection_overlap == pytest.approx(
        original.horizontal_projection_overlap
    )
    assert permuted.horizontal_vertical_overlap == pytest.approx(
        original.horizontal_vertical_overlap
    )
    assert permuted.horizontal_temporal_overlap == pytest.approx(
        original.horizontal_temporal_overlap
    )


def test_common_unavailable_mask_is_applied_before_normalisation():
    a = np.zeros((1, 2, 1, 2), dtype=float)
    b = np.zeros_like(a)
    a[0, 0, 0, 0] = 1.0
    b[0, 0, 0, 0] = 1.0
    a[0, 1, 0, 1] = 100.0
    b[0, 1, 0, 0] = 100.0
    unavailable = np.zeros_like(a, dtype=bool)
    unavailable[0, 1, :, :] = True

    assert schoener_overlap(a, b, unavailable_mask=unavailable) == pytest.approx(1.0)
    result = audit_axis_resolved_overlap(a, b, unavailable_mask=unavailable)
    assert result.available_cell_count == 2
    assert result.full_overlap == pytest.approx(1.0)


@pytest.mark.parametrize(
    "a,b,error",
    [
        (np.ones((2, 2, 2)), np.ones((2, 2, 2)), "at least 4D"),
        (np.ones((1, 1, 1, 1)), np.zeros((1, 1, 1, 1)), "positive mass"),
        (
            -np.ones((1, 1, 1, 1)),
            np.ones((1, 1, 1, 1)),
            "non-negative",
        ),
    ],
)
def test_invalid_support_fails_closed(a, b, error):
    with pytest.raises(ValueError, match=error):
        audit_axis_resolved_overlap(a, b)
