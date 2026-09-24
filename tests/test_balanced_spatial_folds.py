import pytest

from eog.v2.balanced_spatial_folds import build_balanced_spatial_folds


def grid_nodes(n=38):
    node_ids = tuple(f"N{i:02d}" for i in range(n))
    coordinates = {
        node_id: (-112.0 + i * 0.01, 56.0 + (i % 11) * 0.013)
        for i, node_id in enumerate(node_ids)
    }
    return node_ids, coordinates


def test_four_folds_are_balanced_for_38_nodes():
    node_ids, coordinates = grid_nodes(38)
    result = build_balanced_spatial_folds(
        node_ids,
        coordinates,
        n_folds=4,
        metric="lonlat",
    )
    assert sorted(result.fold_counts) == [9, 9, 10, 10]
    assert set(result.mapping) == set(node_ids)
    assert set(result.mapping.values()) == {1, 2, 3, 4}
    assert len(result.split_history) == 3


def test_fold_assignment_is_invariant_to_input_node_order():
    node_ids, coordinates = grid_nodes(38)
    left = build_balanced_spatial_folds(
        node_ids,
        coordinates,
        n_folds=4,
        metric="lonlat",
    )
    right = build_balanced_spatial_folds(
        node_ids[::-1],
        coordinates,
        n_folds=4,
        metric="lonlat",
    )
    assert left.mapping == right.mapping
    assert left.fingerprint == right.fingerprint


def test_fold_sizes_never_differ_by_more_than_one():
    for n_nodes in range(8, 43):
        node_ids, coordinates = grid_nodes(n_nodes)
        result = build_balanced_spatial_folds(
            node_ids,
            coordinates,
            n_folds=4,
            metric="lonlat",
        )
        assert max(result.fold_counts) - min(result.fold_counts) <= 1


def test_euclidean_coordinates_are_supported():
    node_ids = ("a", "b", "c", "d", "e")
    coordinates = {
        "a": (0.0, 0.0),
        "b": (1.0, 0.0),
        "c": (2.0, 0.0),
        "d": (3.0, 0.0),
        "e": (4.0, 0.0),
    }
    result = build_balanced_spatial_folds(
        node_ids,
        coordinates,
        n_folds=2,
        metric="euclidean",
    )
    assert sorted(result.fold_counts) == [2, 3]
    assert result.split_history[0].axis == "x"


def test_coordinate_key_mismatch_fails_closed():
    with pytest.raises(ValueError, match="coordinate keys"):
        build_balanced_spatial_folds(
            ("a", "b"),
            {"a": (0.0, 0.0)},
            n_folds=2,
        )


@pytest.mark.parametrize("n_folds", [0, 1, 6])
def test_invalid_fold_count_fails_closed(n_folds):
    node_ids, coordinates = grid_nodes(5)
    with pytest.raises(ValueError):
        build_balanced_spatial_folds(
            node_ids,
            coordinates,
            n_folds=n_folds,
        )
