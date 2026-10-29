"""Regression gates for descriptive 12x64 BAM × EOG geometry audit."""
from dataclasses import replace

import numpy as np
import pytest

from eog.comparative import fit_robust_reference, infer_comparative_geometry, transform_with_reference
from eog.v2.known_truth_bam_generality import SYSTEM_SPECS, build_generality_system
from benchmarks.run_bam_geometry_768_v1 import (
    _assert_grid,
    _boolmask,
    _masks,
    _positive_span,
    run,
)


def test_full_and_fast_positive_span_use_identical_shared_reference():
    x = np.array([[0.1, 0.2], [0.3, 0.9], [0.7, 0.4], [1.3, 1.2]])
    ref = fit_robust_reference(x, provenance="predefined full candidate grid")
    scaled = transform_with_reference(x, ref)
    for i in (2, 3, 4):
        observed = _positive_span(scaled[:i])
        expected = infer_comparative_geometry(x[:i], ref).span
        assert observed == pytest.approx(expected, rel=1e-12, abs=1e-12)


def test_legacy_bam_mask_decoding_and_strict_grid_row_order():
    system = build_generality_system(SYSTEM_SPECS[0])
    _assert_grid(system)
    n = len(system.landscape.node_ids)
    world = system.worlds[0]
    masks = _masks(world, n)
    assert masks["ABM"] == (
        masks["A"] & masks["B"] & masks["M"]
    )
    assert int(np.count_nonzero(_boolmask(masks["ABM"], n))) == (
        world.occupied_mask.bit_count()
    )
    scrambled = replace(
        system, landscape=replace(
            system.landscape,
            node_ids=tuple(reversed(system.landscape.node_ids)),
        )
    )
    with pytest.raises(ValueError, match="row-major"):
        _assert_grid(scrambled)


def test_smoke_uses_original_world_generator_and_is_reproducible():
    first, rows = run(smoke=True)
    second, rows_again = run(smoke=True)
    assert first == second
    assert rows == rows_again
    assert first["n_systems"] == 1
    assert first["n_worlds"] == 4
    assert first["n_G_estimable"] + first["n_G_unestimable"] == 4
    assert first["n_spatial_MST_comparable"] == first["n_G_estimable"]
    assert first["status"] == "POST_EXPOSURE_EXPLORATORY_KNOWN_TRUTH"
    assert len(first["fingerprint"]) == 64
    assert len(rows) == 4
    for row in rows:
        assert row["G_bits"] == (row["A_bits"] & row["B_bits"] & row["M_bits"])
        assert row["G_nodes"] <= row["node_count"]
        assert "G_geographic_component_count" in row
        assert "G_environmental_geometry" in row
