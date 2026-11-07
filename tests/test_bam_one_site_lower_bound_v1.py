"""Independent post-result exhaustive lower-bound check for ideal local assays."""
from benchmarks import audit_bam_one_site_lower_bound_v1 as audit


def test_one_node_is_enough_when_a_single_bit_separates_response_labels():
    states = [
        {"mask": (3, 3, 3), "sign": -1, "world_ids": ["a"]},
        {"mask": (7, 3, 3), "sign": 1, "world_ids": ["b"]},
    ]
    info = audit.one_site_sufficiency(states, 3)
    assert info["sufficient"] is True
    assert info["example_site"] == "A:2"


def test_xor_pattern_cannot_be_resolved_by_any_single_local_axis_bit():
    states = [
        {"mask": (a, b, 3), "sign": sign, "world_ids": [str(i)]}
        for i, (a, b, sign) in enumerate(
            [(3, 3, -1), (7, 3, 1), (3, 11, 1), (7, 11, -1)]
        )
    ]
    assert audit.one_site_sufficiency(states, 4)["sufficient"] is False
