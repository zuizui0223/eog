# Nature Ecology & Evolution scientific frame for EOG-WF

Status checked: 2026-08-31.

This document fixes a **manuscript interpretation and submission frame**, not a new
primary endpoint. It does not change the frozen candidate gates, Layer A, unchanged
`symmetric_world_support_summary_v1`, learner, split, metric, favorable/null/adverse
rules, placebo, cross-ecosystem synthesis, STOP semantics, or endpoint-3 hard stop.

## The ecological proposition

The broad proposition to test is:

> Species occurrences can carry predictive information not only through local
> environmental viability, but through the accessibility-compatible worlds that prior
> observations exclude or retain.

A one-sentence manuscript summary is:

> Species occurrences do more than identify locally viable environments: by eliminating
> incompatible accessibility worlds, they create a changing possibility-set state that
> can improve future occurrence forecasts even when no single movement mechanism is
> identified.

EOG is the falsifiable implementation of this proposition. The software architecture is
not the protagonist of the paper.

## Three linked advances

### 1. Occurrence contains two information dimensions

The conventional arm predicts a future recorded occurrence from local/site covariates.
The augmented arm uses the same learner and the same covariates plus a label-invariant
summary of the surviving accessibility-compatible world set.

A valid heldout gain supports a narrow statement that the world-set state contains
non-redundant predictive information relative to that frozen conventional arm. It does
not establish exact mutual information, universal superiority, or causal accessibility.

### 2. Ecological falsification can become predictive state

Layer A removes declared worlds that later positive evidence makes incompatible while
retaining unresolved alternatives. The scientific object is therefore not only which
worlds survive, but also how observations contract the declared possibility set.

The secondary endpoint-3 analysis frozen in
`validation/paper_ready_replication/excluded_world_information_contract.json` asks
whether Layer-B gain is concentrated where:

- the conventional learner is locally uncertain; and
- surviving accessibility-compatible worlds disagree.

This analysis is explanatory only. It cannot rescue, reverse, or redefine the primary
terminal status.

### 3. Prediction need not imply mechanistic identification

A world-set summary may be predictively useful even when no exact Layer-A world can be
identified as true. Louisiana is the key existing example: all six frozen local worlds
were eventually falsified and only the permissive `external_open` alternative survived,
while Layer B still supplied a small favorable heldout increment.

The manuscript must use this decoupling to prevent the common but invalid inference
that predictive gain confirms a particular dispersal, connectivity, or historical route.

## Evidence needed for a Nature Ecology & Evolution first submission

Nature Ecology & Evolution is the first challenge only if all of the following are true
without rescue tuning:

1. endpoint 3 reaches a valid **favorable** predictive terminal decision;
2. the three fresh endpoints are materially heterogeneous in ecology and observation
   process;
3. all use the unchanged Layer-B representation and the same-learner paired comparison;
4. the prospectively frozen ten-feature placebo does not make the real Layer-B gain look
   like a generic feature-count effect;
5. the fresh excluded-world explanatory analysis is sufficiently coherent to support
   the broad proposition above, while remaining secondary;
6. all source, registry, geometry, estimability and other STOPs remain visible in the
   candidate funnel rather than being treated as negative predictive outcomes;
7. the manuscript can be read as a general ecological inference advance rather than a
   catalogue of graph operators or an EOG software report.

Three favorable datasets alone are not the Nature threshold. The field-level idea must
be supported by the combined prospective evidence.

## Interpretation when the explanatory pattern is absent

If endpoint 3 is favorable but Layer-B gain is not concentrated where local uncertainty
and world disagreement are high:

- the primary favorable status remains unchanged;
- no analysis is retuned or rebinned;
- the claim is narrowed to reproducible predictive complementarity;
- the manuscript should normally move to Methods in Ecology and Evolution rather than
  inventing a stronger Nature mechanism story.

If endpoint 3 is null or adverse, follow the already-frozen outcome-conditioned route.
If it reaches a source/non-estimable STOP, it is not a predictive replication and does
not count against Layer B.

## Candidate titles

Primary candidate:

> **Species occurrences predict through the ecological worlds they exclude**

More conservative alternatives:

> **Species distributions encode an accessibility state beyond local suitability**

> **Accessibility-compatible states provide predictive information beyond local environmental viability**

Do not lead the title with `EOG`, a package name, graph terminology, or a universal
superiority claim.

## Four main figures

### Figure 1 — Two information dimensions of occurrence

Show local environmental viability and accessibility-compatible world state as distinct
inputs to future occurrence prediction. Introduce Layer A and Layer B only as the
operational decomposition used to test the proposition.

### Figure 2 — Prospective falsification funnel

Show candidate source, transport, registry, geometry, effort, scale, estimability,
once-only response access and terminal disposition. STOPs are protocol-integrity
outcomes, not failed biological replications.

### Figure 3 — Fresh endpoint-wise performance

Show each ecosystem separately: baseline and augmented macro log loss, absolute and
relative difference, and paired heldout-unit differences. Do not pool observation rows
or hide effect-size heterogeneity.

### Figure 4 — Prediction without identification

Use Louisiana to juxtapose Layer-A world falsification with the small favorable Layer-B
predictive increment. Add the fresh endpoint-3 excluded-world uncertainty/disagreement
analysis only if it is interpretable under the frozen contract.

## Forbidden claims

The Nature-first framing does not authorize:

- universal or guaranteed EOG superiority;
- standalone Layer-B prediction;
- exact mechanism, route, ancestry or historical truth;
- causal identification;
- exact mutual-information estimation;
- post-outcome threshold, stratum, world or candidate redesign;
- deletion of null, adverse, unavailable or STOP evidence;
- a fourth dataset sought only to increase journal rank.

## Submission sequence

1. **Nature Ecology & Evolution** if the full trigger above is met;
2. **Nature Communications** only if editorial feedback indicates an important
   specialist advance but insufficient field-wide breadth for Nature Ecology &
   Evolution;
3. **Methods in Ecology and Evolution** for the strong methodological route.

A rejection may motivate exposition, figures and positioning changes. It may not reopen
consumed outcomes or trigger additional favorable-dataset hunting.

## Live scope references

- Nature Ecology & Evolution aims: https://www.nature.com/natecolevol/aims
- Nature Communications aims: https://www.nature.com/ncomms/ncomms/aims

Recheck live scope, article type and submission instructions immediately before
submission.
