"""Known-mask geographic topology is not environmental MST geometry."""
import numpy as np
import pytest

from eog.bam_support_topology import profile_bam_support_topology
from eog.support_topology import SupportGridMetadata, SupportTopologyConfig


def _mask():
    return np.array([
        [True, True, False, True, True],
        [True, True, False, True, True],
    ], dtype=bool)


def _run(a, b, m, *, support=None, missing=None, thresholds=(0.9, 0.5)):
    return profile_bam_support_topology(
        np.ones((2, 5)) if support is None else support,
        A=a, B=b, M=m,
        occurrence_cells={"frozen_occurrence": (0, 0)},
        config=SupportTopologyConfig(
            thresholds=thresholds, neighbourhood=4,
            minimum_persistence_steps=2,
        ),
        grid=SupportGridMetadata(
            x_origin=0.0, y_origin=0.0,
            x_resolution=100.0, y_resolution=100.0,
            crs="EPSG:6933",
        ),
        missing_mask=missing,
    )


def test_known_masks_give_anchored_and_persistent_detached_geographic_components():
    allowed = _mask()
    all_cells = np.ones((2, 5), dtype=bool)
    result = _run(allowed, all_cells, all_cells)
    g = result["groups"]["ABM"]
    assert g["admitted_cell_count"] == 8
    assert g["tracked_component_lineages"] == 2
    assert g["lineage_class_counts"]["occurrence_anchored_component"] == 1
    assert g["lineage_class_counts"]["persistent_detached_component"] == 1
    assert g["topology_fingerprint"] != result["groups"]["U"]["topology_fingerprint"]
    assert result == _run(allowed, all_cells, all_cells)


def test_identical_G_has_identical_G_topology_despite_distinct_BAM_worlds():
    allowed = _mask()
    full = np.ones((2, 5), dtype=bool)
    left = _run(allowed, full, full)
    right = _run(full, allowed, full)
    assert left["masks_sha256"]["ABM"] == right["masks_sha256"]["ABM"]
    assert left["groups"]["ABM"] == right["groups"]["ABM"]
    assert left["groups"]["A"] != right["groups"]["A"]


def test_reject_zero_threshold_and_contradicting_anchor():
    full = np.ones((2, 5), dtype=bool)
    allowed = _mask()
    with pytest.raises(ValueError, match="strictly positive"):
        _run(allowed, full, full, thresholds=(0.5, 0.0))
    bad = allowed.copy()
    bad[0, 0] = False
    with pytest.raises(ValueError, match="contradicts BAM"):
        _run(bad, full, full)


def test_missing_is_not_confused_with_constraint_zero():
    full = np.ones((2, 5), dtype=bool)
    missing = np.zeros((2, 5), dtype=bool)
    missing[1, 4] = True
    result = _run(_mask(), full, full, missing=missing)
    assert result["available_cell_count"] == 9
    assert result["groups"]["ABM"]["admitted_cell_count"] == 7

    missing[0, 0] = True
    with pytest.raises(ValueError, match="missing cell"):
        _run(_mask(), full, full, missing=missing)


def test_reject_negative_or_incomplete_support_and_mask_shape():
    full = np.ones((2, 5), dtype=bool)
    bad_support = np.ones((2, 5), dtype=float)
    bad_support[0, 1] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        _run(full, full, full, support=bad_support)
    with pytest.raises(ValueError, match="Boolean raster"):
        _run(np.ones((2, 5), dtype=int), full, full)
    with pytest.raises(ValueError, match="Boolean raster"):
        _run(full[:, :4], full, full)
