# Calibrated gap and feature-selection protocol

This protocol resolves EOG issue #3 before any expanded real-taxon cohort is analysed.

## Questions

1. Can a matched-size connected-null percentile make `gap_strength` comparable across sample sizes?
2. Which feature-selection rule preserves discrimination when correlated or irrelevant variables are present?

## Calibration

For every observed matrix, the raw gap strength is compared with null reference clouds having the same sample size, feature dimension, sample mean, and covariance. The calibrated score is the empirical percentile of the observed raw gap among the null values.

This is a comparative score, not a probability that the cloud is fragmented.

## Predeclared feature strategies

- `ecological`: retain the two variables known by simulation design to contain the ecological signal. In real analyses this corresponds to variables selected from ecological rationale before EOG is calculated.
- `correlation_filter`: scan variables in declared input order and retain a variable only when its absolute correlation with every retained variable is below 0.80.
- `pca90`: retain the smallest number of principal components explaining at least 90% of variance.
- `all`: retain every variable. This is a negative-control strategy, not the preferred analysis.

Variable order must be declared before analysis because the correlation filter is order dependent.

## Simulations

- sample sizes: 30, 60, 120, 240;
- structures: connected and two-mode;
- data scenarios: clean, correlated redundant variables, and six independent irrelevant variables;
- repeated simulations with fixed seed;
- raw and calibrated AUC reported for every cell.

## Frozen gate

The gate applies only to the ecological preselection strategy:

- minimum calibrated AUC across all sample sizes and scenarios >= 0.90;
- connected-null calibrated median within 0.20 of 0.50.

Other strategies are reported without winner gates. The purpose is to choose a defensible rule, not force every generic strategy to succeed.

## Manuscript rule

Until this protocol is completed, raw gap strength must not be compared across unequal sample sizes. Expanded real-taxon validation must use a feature set frozen before EOG outcomes are inspected and report both raw and calibrated gap values.
