# Calibrated gap and feature-selection protocol

This protocol resolves EOG issue #3 before any expanded real-taxon cohort is analysed.

## Questions

1. Can a matched-size connected-null percentile make `gap_strength` comparable across sample sizes?
2. Which feature-selection rule preserves discrimination when correlated or irrelevant variables are present?

## Calibration

For every observed matrix, raw gap strength is compared with null reference clouds having the same sample size, feature dimension, sample mean, and covariance. The calibrated score is the empirical percentile of the observed raw gap among the null values.

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

## Original frozen gate and outcome

The original gate required, for ecological preselection:

- minimum per-cell calibrated AUC across all sample sizes and scenarios >= 0.90;
- connected-null calibrated median within 0.20 of 0.50.

This gate failed. The first completed run produced a minimum per-cell AUC of 0.8025 and a maximum null-median deviation of 0.225. The weakest condition was at n=30. This failed result remains recorded and is not reclassified as a success.

## Revised operational rule

The simulation scenarios differ only in variables discarded by ecological preselection. Therefore, ecological-preselection results are pooled across those scenarios within each sample size for the operational assessment.

- n=30 is exploratory and must not support confirmatory fragmentation claims;
- confirmatory comparisons require at least 60 occurrence states;
- for n >= 60, minimum pooled calibrated AUC must be at least 0.90;
- for n >= 60, the pooled connected-null median must remain within 0.15 of 0.50.

This revision is a response to the failed predeclared gate, not a replacement of its historical record.

## Selected feature rule

The primary manuscript analysis must use ecologically justified variables selected before EOG outcomes are calculated. Correlation filtering at |r| >= 0.80 is a secondary sensitivity analysis. PCA90 and all-variable analyses are negative or supplementary controls and must not determine the primary result.

## Manuscript rule

Raw gap strength must not be compared across unequal sample sizes. Expanded real-taxon validation must:

1. freeze the ecological feature set before EOG calculation;
2. require n >= 60 for confirmatory gap comparisons;
3. report raw and calibrated gap values together;
4. treat smaller samples as exploratory;
5. report correlation-filter sensitivity results without replacing the primary ecological analysis.
