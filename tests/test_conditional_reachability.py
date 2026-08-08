import numpy as np

from eog.conditional_reachability import conditional_reachability_concordance


def test_concordance_conditions_with_bins_fixed_before_labels_are_compared():
    support = np.repeat([0.1, 0.3, 0.5, 0.7, 0.9], 4)
    distance = np.tile([10.0, 20.0, 30.0, 40.0], 5)
    labels = np.tile([1, 0, 1, 0], 5)
    # Within each support-distance configuration, presence receives higher reachability.
    reachability = np.tile([0.9, 0.1, 0.8, 0.2], 5)
    result = conditional_reachability_concordance(
        labels, support, distance, reachability, support_bins=2, distance_bins=2
    )
    assert result.concordance is not None
    assert result.concordance > 0.5
    assert result.comparable_pairs > 0


def test_ties_contribute_half():
    labels = [1, 0, 1, 0]
    support = [0.2, 0.2, 0.8, 0.8]
    distance = [10.0, 10.0, 50.0, 50.0]
    reachability = [0.5, 0.5, 0.5, 0.5]
    result = conditional_reachability_concordance(
        labels, support, distance, reachability, support_bins=2, distance_bins=2
    )
    assert result.concordance == 0.5


def test_no_comparable_pairs_is_explicitly_unestimable():
    labels = [1, 1, 0, 0]
    support = [0.1, 0.2, 0.8, 0.9]
    distance = [10.0, 20.0, 80.0, 90.0]
    reachability = [1.0, 0.8, 0.2, 0.0]
    result = conditional_reachability_concordance(
        labels, support, distance, reachability, support_bins=2, distance_bins=2
    )
    assert result.concordance is None
    assert result.comparable_pairs == 0


def test_exact_covariate_ties_remain_in_same_bin():
    labels = [1, 0, 1, 0, 1, 0]
    support = np.ones(6) * 0.5
    distance = np.ones(6) * 20.0
    reachability = [0.9, 0.1, 0.8, 0.2, 0.7, 0.3]
    result = conditional_reachability_concordance(labels, support, distance, reachability)
    assert result.concordance == 1.0
    assert result.comparable_pairs == 9
