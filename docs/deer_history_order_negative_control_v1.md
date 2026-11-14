# Detection order negative control: switching is not an identified mechanism

## Why this test was necessary

The exploratory history-feature analysis in PR #694 reported
a negative Spearman correlation between adjacent observed-day
detection switches and beta-mixture held-out predictive gains
(ρ=−0.36194; naive exploratory p≈0.000572).

But the compared constant-p and beta-site-p occupancy models
are **exchangeable across observed daily occasions within a
site**. Their site-level likelihoods depend only on n observed
occasions and k detected occasions, not their order. Thus
a switching correlation can arise through the same detection
counts that drive the model score, without temporal effects.

## Pre-score conditional null

Protocol commit `4a75d6a6195e1bc5b8c440a22811dbaff492897d`.
Original source SHA256
`bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.

Across 87 sites, permute each site's 0/1 outcomes 199 times
(seed 20261114), keeping missing-day positions and exact
n,k fixed. Recalculate switching and its Spearman correlation
with the **unchanged** out-of-fold predictive score deltas.
The direct constant-p and beta-site likelihood evaluations
must remain invariant under every permutation.

## Verified results

Canonical run:
https://github.com/zuizui0223/eog/actions/runs/43576990997

| Statistic | Value |
|---|---:|
| Original switches–heldout gain Spearman ρ | −0.361941 |
| Conditional permutation null mean ρ | −0.371871 |
| Conditional null 2.5–97.5% interval | −0.430398 to −0.313323 |
| Conditional order-permutation p | **0.625** |
| Permutations changing site switching counts | 199/199 |
| Maximum change in model likelihood under fixed n,k | **0** |

**Conclusion:** the previously highlighted switching
correlation is not unusual under the conditional order null.
It is **not** independent evidence for a temporal ecological
mechanism. The earlier unconditioned p-value cannot support
such a claim. The model advantage remains a statistical
improvement in the distribution of detection histories,
especially sparse detections, not evidence that either
model captures day-to-day transitions.

This corrects the biological interpretation of PR #694
without altering its reported descriptive calculations.

## Boundary

This is a structural negative control within the same
publicly available example, not external ecological
replication. Independent effort, closure, site geography
and A/B/M variables remain unavailable. No EOG geometry
or new EOG-WF endpoint was added.

Result fingerprint:
`4f6a75036070821570ae7863f4ee9ce5f3f56903dd72dd1a296ea98f5710fcfc`.
The machine-readable receipt is in
`validation/deer_history_order_negative_control_v1/result_receipt.json`.
