# Baseline-protected prediction (experimental)

## Motivation and scope

Frozen Tampa results remain adverse and unchanged. The posthoc mechanism audit
does not establish a causal explanation. Contextual innovation and calibration-only
promotion already exist, but neither supplies an outcome-wise loss bound under an
unseen shift. This optional output policy directly limits that failure mode.
It does not change Layer A, Layer B, any frozen scorer, or an empirical endpoint.

## Contract

Given binary baseline probability p, candidate probability r, and a nonnegative
budget b fixed before heldout outcomes, return r clipped into

    [exp(-b) * p, 1 - exp(-b) * (1-p)].

Both q >= exp(-b)*p and 1-q >= exp(-b)*(1-p) hold. Taking negative
natural logarithms proves loss(q,y) - loss(p,y) <= b for either y. The same
bound holds for a paired average or macro average using identical nonnegative
normalized weights. No distribution, calibration, or independence assumption is
required. Floating-point bounds round inward; tests allow numerical tolerance.
This interval is the largest admissible interval satisfying both inequalities,
so clipping preserves a candidate already within the interval. Budget zero returns
the baseline exactly. A small positive budget limits benefits as well as damage.

Import `protect_binary_probabilities` from `eog.v2.protected_prediction` and pass
aligned 1-D P(Y=1) arrays plus explicit `max_excess_log_loss`. Inputs are not mutated.
The baseline must be finite and strictly inside (0,1); candidate endpoints are
allowed. Invalid inputs are rejected, never silently repaired. Observation IDs,
class convention, and fit provenance must be aligned upstream. The API takes no
labels and must not be used to select its budget from outer outcomes.

The guarantee is **absolute excess natural-log loss**, not percent error, accuracy,
AUC, calibration, or improvement. It is relative to the supplied baseline after
its declared scoring preprocessing, not a different or hindsight-selected model.
Do not postprocess the output in a way that violates its interval.

## Fixed development checks

`benchmarks/protected_prediction_stress.py` fixes b=0.01 as an illustrative risk
budget (not a recommended deployment setting or a Tampa-derived optimum).
Four hand-constructed cases check helpful, unchanged, confidently reversed and
exactly reversed forecasts. A separate fitted test uses seeds 601/607/613/617,
500 training and 500 heldout rows, baseline two Gaussian predictors, and an
augmented signal plus nine nuisance features. The response has stable helpful,
neutral, or heldout-only sign-reversal regimes. Identical random forests use
64 trees, minimum leaf size 10, sqrt feature selection, seed 91, one worker.
Both forecasts use a predeclared [1e-6,1-1e-6] scoring clip before protection.
No search, calibration selection, or empirical response access occurs.

The extra columns are **not EOG-derived features**. These checks assess a generic
safety wrapper and cannot establish real ecological predictive gain. Existing
fresh-data programme STOPs remain in force. Integration into a future empirical
protocol requires a newly frozen fit/split/budget contract; old adverse results
cannot be relabeled as fresh successes.

Run with local src on PYTHONPATH:

    python -m pytest tests/test_protected_prediction.py
    python benchmarks/protected_prediction_stress.py

## Initial fitted development result

Mean heldout excess log loss over the identical baseline (four seeds per regime):

| Fixed regime | Unprotected candidate | Protected candidate |
| --- | ---: | ---: |
| Helpful signal | -0.181986 | -0.005988 |
| Neutral extra features | +0.004212 | -0.001606 |
| Unseen sign reversal | +0.400705 | +0.003869 |

The protection materially reduces reversal damage in this toy test, but forfeits
most of the helpful signal's gain. These are descriptive development results,
not an independent confirmation or a basis to optimize the budget. The algorithm
is a generic binary probability projection, not a novel ecological mechanism or
evidence that Layer B is useful. A zero-risk budget yields no departure from the
baseline; positive budgets still permit harm. The 0.01 bound is an absolute loss
increment, never a 1% claim.
