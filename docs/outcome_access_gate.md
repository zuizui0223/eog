# Once-only outcome-access gate

## Purpose

Fresh EOG-WF validation separates two questions:

1. may response-blind scientific/modeling work continue?;
2. has the attempt frozen enough information to open row-level outcome data exactly once?

PR #212 clarified the first question for `uncertain_pre_response`.  This gate makes the
second question executable.

Authorization does **not** mean the empirical endpoint is estimable and does not permit
immediate model fitting.  It means only that the fully frozen once-only outcome runner
may begin, with the exact count gate as its first outcome-dependent operation.

## Required response-blind freezes

`FrozenOutcomeAccessContract` requires candidate-specific fingerprints for:

1. source identity;
2. response identity;
3. node universe / response-independent geometry;
4. response semantics;
5. temporal calibration/heldout split;
6. exact count-gate declaration;
7. process/source closure semantics;
8. world-scale construction;
9. structural-adequacy rule/result;
10. Layer-A rule identities and update policy;
11. Layer-B predictive representation;
12. external comparators;
13. preprocessing and model-fitting policy;
14. metrics plus favourable/null/adverse decision rules;
15. exact runtime / empirical runner identity;
16. non-estimable stop behaviour.

A blank or absent required fingerprint blocks outcome access.

## Safety invariants

Three invariants are mandatory:

- `exact_count_gate_first = true`;
- `zero_fit_on_count_failure = true`;
- `no_post_open_redesign = true`.

If any is false, outcome access remains blocked.

## Interaction with prospective estimability

Known pre-response ineligibility always blocks, even if the freeze ledger is complete.

`uncertain_pre_response` and `plausibly_eligible_pre_response` can both reach:

`authorized_once_only_exact_count_gate_required`

but only after all response-blind freezes are present.

This preserves the distinction introduced in PR #212:

- missing published aggregate counts do not prove sparsity;
- they also do not waive the exact empirical count gate.

## Once-only runner contract

After authorization, the empirical runner must:

1. verify the response identity and its own frozen runtime/runner fingerprint;
2. open the response once;
3. compute exact calibration/heldout event, non-event and both-class counts;
4. stop with zero model fits and zero heldout scores if any frozen minimum fails;
5. only then fit the already-frozen models and score the already-frozen heldout endpoint.

No outcome-derived change to worlds, split, response semantics, Layer B, comparator,
preprocessing, metrics or decision thresholds is permitted between steps 3 and 5.

## What this gate is not

It is not:

- a new ecological operator;
- a replacement for the response firewall;
- proof that a candidate will be estimable;
- permission to inspect response rows during candidate selection;
- a mechanism for reopening previously stopped systems.

Its sole purpose is to turn the repository's anti-tuning / response-firewall discipline
into a reusable, fingerprinted authorization object before the next fresh independent
Layer-B validation attempt.
