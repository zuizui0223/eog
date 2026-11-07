"""One erroneous A/B/M read: exact finite multicover and independent decoder."""
import hashlib
import json
from pathlib import Path
import pytest

from benchmarks.bam_one_bit_error_v1 import (
    exact_fixed_panel, check_error_correction, observations, BUDGETS
)


def mk(rows):
    return [{"masks": masks, "sign": sign} for masks, sign in rows]


def test_one_discriminating_bit_requires_three_individual_readings():
    s = mk([((3, 3, 3), -1), ((7, 3, 3), 1)])
    old = exact_fixed_panel(s, 3, errors=0)
    robust = exact_fixed_panel(s, 3, errors=1)
    assert old["minimum_reads"] == 1
    assert robust["minimum_reads"] == 3
    assert robust["unique_tests"] == 1
    assert robust["readings"] == ["A:2"] * 3
    assert check_error_correction(s, robust["readings"], errors=1)


def test_cross_axis_xor_requires_six_readings_for_one_error():
    s = mk([
        ((3, 3, 3), -1),
        ((7, 3, 3), 1),
        ((3, 11, 3), 1),
        ((7, 11, 3), -1),
    ])
    assert exact_fixed_panel(s, 4, errors=0)["minimum_reads"] == 2
    r = exact_fixed_panel(s, 4, errors=1)
    assert r["minimum_reads"] == 6
    assert r["unique_tests"] == 2
    assert check_error_correction(s, r["readings"], errors=1)


def test_if_target_already_identified_assay_not_needed():
    s = mk([((3, 3, 3), 0), ((7, 3, 3), 0)])
    assert exact_fixed_panel(s, 3, errors=0)["minimum_reads"] == 0
    assert exact_fixed_panel(s, 3, errors=1)["minimum_reads"] == 0


def test_two_reads_cannot_certify_opposite_targets_with_one_wrong_bit():
    s = mk([((3, 3, 3), -1), ((7, 3, 3), 1)])
    assert not check_error_correction(s, ["A:2", "A:2"], errors=1)
    assert check_error_correction(s, ["A:2"] * 3, errors=1)


def test_invalid_masks_and_channel_refused():
    s = mk([((3, 3, 3), -1), ((7, 3, 3), 1)])
    with pytest.raises(ValueError):
        exact_fixed_panel(s, 3, errors=2)
    with pytest.raises(ValueError):
        exact_fixed_panel(s, 0, errors=1)
    with pytest.raises(ValueError):
        exact_fixed_panel([], 3, errors=1)
    with pytest.raises(ValueError):
        exact_fixed_panel(mk([((3, 3, 3), -1), ((8, 3, 3), 1)]), 3)


def test_protocol_is_still_original_one_miss_source():
    p = json.loads(Path("validation/bam_assay_bit_error_v1/protocol_v1.json").read_text())
    assert p["source"]["parameter_worlds"] == 768
    assert p["source"]["observed_D_fibres"] == 2627
    assert p["error_model"]["e"] == 1
    assert p["measurement_policy"]["primary"].startswith("Find exact minimum")
    assert BUDGETS == (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12)


def test_one_miss_observation_enumeration_unchanged():
    assert observations(0b1101) == (13, 12, 9, 5)
