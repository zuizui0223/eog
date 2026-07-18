# EOG sample-size and dimensionality robustness audit

## Question

Do `gap_strength` and `continuity` retain their intended discrimination across realistic sample sizes, and how strongly are they degraded by irrelevant feature dimensions?

This audit is predeclared before inspecting its GitHub Actions artifact.

## Factorial design

- sample sizes: 30, 60, 120, 240;
- informative features: two;
- additional independent Gaussian noise features: 0, 2, 6;
- repeated simulations per cell;
- fixed seed recorded in the output.

## Scenarios

- connected occupied path;
- two separated modes;
- straight path;
- curved path.

The fragmentation comparison uses `gap_strength`. The path comparison uses lower `continuity` as the curved-path signal.

## Reported quantities

For each sample-size × noise-dimension cell:

- connected-null median and 95th percentile of `gap_strength`;
- two-mode median `gap_strength`;
- AUC for separating two modes from the connected null;
- straight and curved median `continuity`;
- AUC for separating curved from straight paths.

The audit explicitly reports drift of the connected-null gap distribution with sample size. A fixed universal cutoff for `gap_strength` must not be proposed unless this drift is acceptably small or a calibration procedure is introduced.

## CI gate

The CI gate applies only to the already-supported clean two-dimensional setting:

- minimum gap-strength AUC across sample sizes ≥ 0.80;
- minimum continuity AUC across sample sizes ≥ 0.80;
- all reported numerical values finite.

Performance with added noise dimensions is not gated. It is the scientific target of the audit and must be reported even if poor.

## Interpretation boundary

Success would support robustness across sample sizes in the clean setting. It would not establish robustness to arbitrary feature selection, correlated predictors, spatial sampling bias, or taxonomic generality. Those require separate analyses.
