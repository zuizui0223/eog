# First innovation-offset development comparison

Design was committed at `ff8c1c4` before comparison execution. All four seeds
and four regimes are retained in
`validation/layer_b_mechanism_v2/innovation_offset_development_result_v1.json`.
No ridge, model, generator or selector was retuned after these scores were opened.
The initial runtime was Python 3.10.11, NumPy 2.2.6, scikit-learn 1.7.2,
and SciPy 1.15.3; this is recorded alongside the results. The repository's
development dependency pins scikit-learn 1.5.2, so that environment is separately
checked for portability without replacing the initial record.

Both environments pass 37 focused tests, including the first seed's four-regime
pipeline replay. A full 16-case rerun on scikit-learn 1.5.2 retained every adoption
decision, but the strict 1e-10 cross-version equality check failed: maximum
absolute always-on log-loss difference was 0.0000069727362324023545. This is a
recorded reproducibility limit, not a change to the design or a replacement of
the initial scores. Do not claim bitwise or 1e-10 equality across library versions.

## Paired mean excess log loss over the fixed baseline

These values use calibration-only adoption (negative is better). Always-on and
per-seed scores remain in the JSON, including all unhelpful outcomes.

| Regime | RF + absolute summary | RF + innovation | Offset, all 10 | Offset, mean only |
| --- | ---: | ---: | ---: | ---: |
| Mean-change signal | -0.088547 | -0.098681 | -0.111175 | -0.100754 |
| Spread-change signal | -0.112143 | -0.110182 | -0.110247 | +0.000319 |
| No structural signal | +0.002562 | +0.012824 | +0.000863 | +0.000045 |
| Unseen sign reversal | +0.263325 | +0.379043 | +0.353787 | +0.225158 |

## What this supports and does not support

At zero correction, the fit gradient is `Z.T @ (p_baseline - y) / n`.
Thus correction fitting responds to covariance between innovation and the
baseline's probability residuals. This motivates the term residual correction;
it is not proof that features are orthogonal to conventional covariates, and
the fitted coefficients are not ecological effects.

The offset module and existing innovation projection now form a functioning
prediction path, rather than only an identifiability diagnostic. On this small
development design it improves the mean-signal comparison, and reduces neutral
feature harm relative to concatenation. It does not win the spread-signal case
against absolute-feature RF, and it fails badly under unseen reversal. Inner
selection promotes all informative candidates before that reversal, as expected.

Mean-only correction cannot exploit the stipulated spread signal. This shows
why a non-mean feature can be needed in this generator, not why all ten features
are needed in practice. Several summary columns are correlated; using the same
ridge across representations does not equate their effective regularization.
No advantage can be attributed uniquely to EOG semantics from this comparison.
Permuted-feature controls do not supply a positive gain in any regime average.

These are four-replicate engineering results with hand-stipulated support tensors,
not geometry-generated forecasts, an independent confirmation, an empirical
endpoint, or a new GLM principle. The OOF baseline uses 400 rows per fold while
the final baseline uses 600; the resulting prediction-distribution change remains
a limitation. This setup is independent synthetic nodes, not a time-series claim.

## Next methodological gate

Do not promote a methods-paper superiority claim yet. A separately frozen
confirmation must compare raw conventional predictors, mean/spread-only simple
corrections, EOG innovation correction, and matched null features under independently
specified truth mechanisms and geometry-generated supports. It must retain neutral
and reversal cases, use the same outcome budget and grouping, and distinguish
always-on gain from selection and safety. PR #433's outcome-wise protection is
an optional separate policy; it was not used to obtain the scores above and must
not be reported as a demonstrated combined-method result.

The implementation is small and optional. Existing frozen empirical programmes,
Tampa's adverse result, and default pipelines are unchanged. This result identifies
a candidate learning change and its failure mode; it does not establish a reason
to use EOG instead of a simpler predictor on a real task.
