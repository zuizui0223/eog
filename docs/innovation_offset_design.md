# Innovation-only offset learning: development design v1

This design is fixed before running its comparison. It is a development
experiment, not a fresh ecological endpoint or a rescue of Tampa.

## Method

Keep the baseline learner and fit a penalized binary-logistic correction:

    logit(p_corrected) = logit(p_baseline) + (innovation / fit_RMS) @ beta

Innovation is the existing source-symmetric summary minus a fixed pre-outcome
reference summary. The correction has no intercept and does not center features;
zero innovation therefore returns the baseline exactly. The baseline offset has
coefficient one. This is a standard GLM construction, not a novelty claim; see
[statsmodels GLM](https://www.statsmodels.org/v0.14.4/generated/statsmodels.genmod.generalized_linear_model.GLM.html).
The intended methodological contribution, if supported, is the EOG-specific
representation and evaluation protocol, not logistic offsets themselves.

Use out-of-fold baseline predictions for correction fitting, not training-set
predictions. Freeze feature identity, baseline fit policy, and ridge before outer
scoring. No causal orthogonality or guaranteed non-degradation is claimed. The
baseline is a fixed offset but the correction can still exploit redundant
information, overfit, or fail under shift. PR #433's output protection is separate
and deliberately excluded to isolate this method comparison.

## Fixed comparison

- Seeds 701, 709, 719, 727; 1500 distinct synthetic nodes per seed.
- Rows 0:600 fit; 600:900 select; 900:1500 outer. Three out-of-fold baseline
  fits on the first 600 rows, assigned by row index modulo three.
- Same RF for baseline and concatenation: 64 trees, leaf size 10, sqrt features,
  seed 91, one worker. Both full fits see the same 600 training responses.
- Offset uses the same 600 responses and baseline OOF predictions. It has
  additional computation, not additional outcomes. Fixed ridge 0.1, no search.
- Candidate feature tensors are generated response-free, with two sources and
  two worlds. Existing EOG source-symmetric and contextual-innovation functions
  produce ten features. Supports are stipulated synthetic inputs, not outputs of
  the geometry/bridge operator and not real ecological data.
- Compare baseline; RF plus current absolute summary; RF plus innovation;
  offset plus ten innovations; offset plus mean-support innovation only; and
  offset with independently permuted innovation rows within each split.
- Every candidate has an always-on and a calibration-selected result. Selection
  uses only rows 600:900; exact ties choose baseline. No refit after selection.
- Regimes: response depends on mean-support change; response depends on
  spread change; no extra structural signal; mean-effect sign reverses only
  in outer rows. All regimes and seeds are retained regardless of outcome.
- Four seeds are a small engineering comparison, not independent confirmation.
  Data generation deliberately favours specified signals, so a favourable result
  does not establish biological relevance or universal superiority.

Baseline probabilities are clipped to [1e-6,1-1e-6] before logit construction;
all reported scores use the same clip. Mean log loss and paired differences are
reported. The offset gradient convergence threshold is 1e-9; failure raises an
error rather than silently substituting a model.

## Decision boundary

Keep this as an experimental direct-import module until tested. No existing
empirical pipeline defaults change. Improvement against concatenation must be
separated from improvement against baseline and the one-feature correction.
If the one-feature correction suffices, prefer it; ten summaries are not a
contribution by themselves. If unseen shift remains adverse, retain that result
and do not tune the selector to the outer labels. A frozen independent larger
comparison and real application would still be required for a methods claim.
