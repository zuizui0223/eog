import numpy as np
import pytest

from eog.support_topology import (
    SupportGridMetadata,
    SupportTopologyConfig,
    assign_occurrence_anchors,
    evaluate_component_recovery,
    evaluate_support_topology_sensitivity,
    infer_support_topology,
)


def classes(result):
    return [component.component_class for component in result.components]


def test_one_occurrence_anchored_component():
    support = np.array([[0.9, 0.8], [0.1, 0.0]])
    result = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8, 0.5), minimum_persistence_steps=2),
    )
    anchored = [c for c in result.components if c.component_class == "occurrence_anchored_component"]
    assert len(anchored) == 1
    assert anchored[0].anchor_ids == ("known",)


def test_persistent_detached_component_and_lower_threshold_merge():
    support = np.array([[0.9, 0.4, 0.85]])
    result = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8, 0.6, 0.4), minimum_persistence_steps=2),
    )
    detached = [c for c in result.components if c.component_class == "persistent_detached_component"]
    assert len(detached) == 1
    assert detached[0].merge_into_anchored_threshold == 0.4
    assert detached[0].threshold_count == 2


def test_transient_noise_component():
    support = np.array([[0.9, 0.0, 0.71]])
    result = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8, 0.7), minimum_persistence_steps=2),
    )
    transient = [c for c in result.components if c.component_class == "transient_detached_component"]
    assert len(transient) == 1
    assert transient[0].first_threshold == 0.7
    assert transient[0].threshold_count == 1


def test_two_occurrence_anchors_merge_across_thresholds():
    support = np.array([[0.9, 0.5, 0.9]])
    result = infer_support_topology(
        support,
        {"west": (0, 0), "east": (0, 2)},
        SupportTopologyConfig((0.8, 0.5)),
    )
    assert classes(result).count("occurrence_anchored_component") == 2
    assert any(c.last_identifiable_threshold == 0.5 for c in result.components)


def test_four_vs_eight_neighbour_difference():
    support = np.array([[0.9, 0.0], [0.0, 0.9]])
    four = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8,), neighbourhood=4),
    )
    eight = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8,), neighbourhood=8),
    )
    assert len(four.components) == 2
    assert len(eight.components) == 1


def test_masked_sea_separates_identical_support_islands():
    support = np.array([[0.9, 0.9, 0.9, 0.9, 0.9]])
    sea = np.array([[False, False, True, False, False]])
    result = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8, 0.7), minimum_persistence_steps=2),
        missing_mask=sea,
    )
    assert len(result.components) == 2
    assert set(classes(result)) == {
        "occurrence_anchored_component",
        "persistent_detached_component",
    }
    assert result.masked_cell_count == 1


def test_all_identical_support_is_valid_and_deterministic():
    support = np.ones((2, 2)) * 0.5
    config = SupportTopologyConfig((0.6, 0.5))
    first = infer_support_topology(support, {"known": (0, 0)}, config)
    second = infer_support_topology(support, {"known": (0, 0)}, config)
    assert first.fingerprint == second.fingerprint
    assert len(first.components) == 1


def test_invalid_and_empty_inputs():
    with pytest.raises(ValueError):
        infer_support_topology(np.array([]), {}, SupportTopologyConfig((0.5,)))
    with pytest.raises(ValueError):
        infer_support_topology(np.array([[np.nan]]), {}, SupportTopologyConfig((0.5,)))
    with pytest.raises(ValueError):
        infer_support_topology(
            np.array([[0.5]]),
            {"outside": (1, 0)},
            SupportTopologyConfig((0.5,)),
        )
    result = infer_support_topology(
        np.array([[0.2]]), {}, SupportTopologyConfig((0.9, 0.8))
    )
    assert result.components == ()


def test_anchor_order_does_not_change_fingerprint():
    support = np.array([[0.9, 0.8, 0.9]])
    config = SupportTopologyConfig((0.8,))
    a = infer_support_topology(support, {"a": (0, 0), "b": (0, 2)}, config)
    b = infer_support_topology(support, {"b": (0, 2), "a": (0, 0)}, config)
    assert a.fingerprint == b.fingerprint
    assert [c.component_id for c in a.components] == [c.component_id for c in b.components]


def test_held_out_detection_recovered_by_detached_not_anchored_component():
    support = np.array([[0.9, 0.0, 0.9]])
    result = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8,)),
    )
    recovery = evaluate_component_recovery(result, {"future": (0, 2)})
    assert recovery[0].recovered
    assert recovery[0].component_class == "transient_detached_component"


def test_anchor_validation_and_grid_area():
    support = np.array([[0.9]])
    with pytest.raises(ValueError, match="duplicate occurrence anchor cell"):
        assign_occurrence_anchors(
            support.shape, {"a": (0, 0), "b": (0, 0)}
        )
    result = infer_support_topology(
        support,
        {"known": (0, 0)},
        SupportTopologyConfig((0.8,)),
        grid=SupportGridMetadata(x_resolution=10, y_resolution=-20),
    )
    assert result.components[0].area == 200


def test_sensitivity_audit_records_neighbourhood_choice():
    support = np.array([[0.9, 0.0], [0.0, 0.9]])
    rows = evaluate_support_topology_sensitivity(
        support,
        {"known": (0, 0)},
        [
            SupportTopologyConfig((0.8,), neighbourhood=4),
            SupportTopologyConfig((0.8,), neighbourhood=8),
        ],
    )
    assert rows[0]["component_count"] == 2
    assert rows[1]["component_count"] == 1
    assert rows[0]["fingerprint"] != rows[1]["fingerprint"]
