# Prospective estimability execution protocol

## Purpose

This protocol defines how the response-blind aggregate estimability screen controls a
fresh EOG-WF validation attempt.  It is validation infrastructure only.  It does not
change an ecological operator, a world definition, a prediction feature, a count
minimum, a comparator, or a favourable/adverse decision rule.

The governing principle is:

> **Use published/documented aggregate counts to reject known-sparse systems early, but do not confuse unavailable aggregate reporting with evidence that the frozen endpoint is sparse.**

The exact empirical count gate remains mandatory inside the once-only outcome runner.

## Three pre-response states

`evaluate_prospective_estimability()` returns exactly one of three states.

### `plausibly_eligible_pre_response`

Every required quantity has a published/documented lower bound at or above the frozen
minimum.

Allowed action:

- continue response-blind validation work;
- still enforce the exact row-level count gate at the start of the once-only empirical
  runner.

This is a prospective screen, not exact estimability proof.

### `ineligible_pre_response`

At least one published/documented upper bound is already below the frozen minimum.

Required action:

- stop the candidate before response access;
- do not change the endpoint, split, count minimum, world universe, or comparator to
  rescue it.

### `uncertain_pre_response`

Published/documented aggregate evidence is incomplete, or its endpoint definition does
not establish the planned count quantities.

Allowed action:

- **continue through response-blind gates only**: source/node/geometry freeze,
  process/source closure, structural scale/adequacy, Layer-A rule freeze, Layer-B
  predictive representation freeze, comparator/metric freeze, runtime lock, and
  synthetic smoke;
- keep the prospective status explicitly `uncertain_pre_response`;
- do not inspect row-level outcomes merely to decide candidate eligibility.

If every response-blind gate is subsequently frozen, the candidate may enter the same
once-only empirical execution pattern already used by the Chiricahua attempt:

1. verify immutable response identity and the frozen runner/runtime;
2. open the response once inside the outcome runner;
3. compute the exact frozen calibration/heldout count quantities first;
4. if any minimum fails, emit a non-estimable result with **zero model fits and zero
   heldout scores**;
5. only if every exact count gate passes may the already-frozen models be fit and the
   already-frozen heldout endpoint scored.

No response-derived redesign is permitted between steps 3 and 5.

## Why this is not a weaker gate

The numerical minima do not change.

The correction concerns only what can be inferred from **missing published aggregate
reporting**.  Absence of a published count is not evidence that the true count is below
the minimum.  Treating every `uncertain_pre_response` state as known ineligibility made
public reporting style, rather than ecological estimability, a hidden admission
criterion.

The exact count gate remains stricter than the prospective screen because it is applied
to the frozen row-level endpoint before any model fitting or scoring.

## Independence / anti-tuning requirements

For an `uncertain_pre_response` candidate, all of the following must be frozen before
outcome access:

- immutable source and response identity;
- node universe and non-response geometry;
- response interpretation;
- calibration/heldout split;
- count minima and both-class requirement;
- process/source semantics;
- world-scale construction and structural adequacy rule;
- Layer-A rule identities and update policy;
- Layer-B predictive representation;
- external comparators;
- preprocessing/model-fitting policy;
- metrics and favourable/null/adverse rules;
- exact runtime / runner identity;
- non-estimable stop behavior.

The outcome runner must stop before fitting/scoring if the exact count gate fails.

## No retroactive rescue

This protocol applies prospectively to **new attempts after it is frozen**.

Previously stopped systems remain frozen under the contracts that governed those
attempts.  In particular, an old response is not reopened merely because
`uncertain_pre_response` now has an explicit response-blind continuation path.

A previously studied biological system can only constitute a new independent attempt if
it has a genuinely distinct response dataset/period and is selected under a new
prospective contract before that response is accessed.

## Executable policy

`prospective_estimability_disposition()` maps the three statuses to execution policy:

- `plausibly_eligible_pre_response` ->
  `continue_response_blind_with_pre_response_support`;
- `uncertain_pre_response` ->
  `continue_response_blind_exact_gate_required`;
- `ineligible_pre_response` ->
  `stop_known_ineligible_pre_response`.

Neither continuation status authorizes response access.  Response access is authorized
only by the fully frozen once-only empirical contract in the main validation protocol.
