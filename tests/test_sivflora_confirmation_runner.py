import runpy

import pytest

pytest.importorskip("openpyxl")
pytest.importorskip("sklearn")

_NS = runpy.run_path("benchmarks/run_sivflora_worldset_confirmation.py")
pair_state = _NS["pair_state"]
_identity_not_determined = _NS["_identity_not_determined"]


def test_pair_state_keeps_catalogue_nonrecord_distinct_from_alien_or_ambiguous_record():
    assert pair_state(True, False, True) == 1
    assert pair_state(False, False, False) == 0
    assert pair_state(False, True, True) is None
    assert pair_state(True, True, True) is None


def _row(signature, bits):
    names = (
        "geography_only_support_count",
        "chelsa_q50_support_count",
        "chelsa_q75_support_count",
        "worldclim_q50_support_count",
        "worldclim_q75_support_count",
    )
    row = {name: value for name, value in zip(names, signature)}
    row["world_bits"] = bits
    return row


def test_identity_condition_requires_same_R2_decomposition_with_distinct_world_bits():
    rows = [
        _row((2, 1, 0, 1, 0), "11001000000000000000"),
        _row((2, 1, 0, 1, 0), "10101000000000000000"),
        _row((4, 4, 4, 4, 4), "11111111111111111111"),
    ]
    extra, groups, collision_rows = _identity_not_determined(rows)
    assert extra is True
    assert groups == 1
    assert collision_rows == 2


def test_identity_condition_fails_when_R2_signature_determines_bits():
    rows = [
        _row((2, 1, 0, 1, 0), "11001000000000000000"),
        _row((4, 4, 4, 4, 4), "11111111111111111111"),
    ]
    extra, groups, collision_rows = _identity_not_determined(rows)
    assert extra is False
    assert groups == 0
    assert collision_rows == 0
