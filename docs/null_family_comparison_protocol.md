# Connected-null family comparison protocol

This protocol addresses issue #7 before expanding EOG to a manuscript-scale real-taxon cohort.

## Motivation

All six frozen pilot taxa exceeded every moment-matched Gaussian reference draw. This may be a biological signal, but it may also reflect a null that is too restrictive for skewed, heavy-tailed, or curved connected occupancy clouds.

## Candidate null families

1. `gaussian`: multivariate normal with observed mean and covariance.
2. `student_t`: multivariate t with 5 degrees of freedom, scaled to the observed covariance.
3. `gaussian_copula`: empirical univariate margins combined with a Gaussian rank-correlation structure.
4. `radial_bootstrap`: whiten the observed cloud, resample observed radii, randomize directions, then recolor to the observed covariance.

Every reference cloud has the observed sample size and feature dimension. The calibrated score remains an empirical percentile, not a fragmentation probability.

## Synthetic generators

Connected calibration cases:

- Gaussian;
- heavy-tailed t;
- skewed marginal distribution;
- curved banana distribution.

Fragmented power cases:

- two separated modes;
- a missing central bridge.

Sample sizes are 60, 120, and 240. All generators use two signal dimensions because ecological preselection is the frozen primary feature rule.

## Metrics

For connected cases:

- median calibrated percentile;
- absolute deviation of that median from 0.50;
- fraction of scores at or above 0.95;
- deviation of that fraction from the nominal 0.05.

For fragmented cases:

- fraction of scores at or above 0.95;
- AUC against connected scores at the same sample size and null family.

## Frozen selection rule

For each null family, compute:

- `calibration_loss`: mean absolute median deviation plus mean absolute upper-tail-rate deviation across connected cells;
- `minimum_fragmented_auc`: minimum AUC across fragmented structures and sample sizes;
- `minimum_fragmented_detection`: minimum fraction above 0.95 across fragmented cells.

A family is eligible as the primary null when:

- calibration loss <= 0.25;
- minimum fragmented AUC >= 0.80;
- minimum fragmented detection >= 0.50.

Among eligible families, select the lowest calibration loss. Break ties by higher minimum fragmented AUC, then higher minimum fragmented detection, then the fixed family order above. The next eligible family with a structurally different construction is the sensitivity null.

If no family is eligible, no primary null is frozen and the manuscript-scale cohort must not start.

## CI policy

CI gates execution integrity and retention of the predeclared selection rule. It does not require a preferred family to win. A scientifically negative result must remain mergeable and auditable.