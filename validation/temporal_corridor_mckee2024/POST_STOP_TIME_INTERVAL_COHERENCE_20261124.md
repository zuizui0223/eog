# McKee 2024 sparse 12h GPS — interval-valued timestamps and path coherence

**Date:** 2026-11-24. **Scope:** Source input-QC / method-identifiability audit only. No ecological prediction or time-of-migration inference.

## Why this matters

McKee et al. (2024), Ecosphere, DOI https://doi.org/10.1002/ecs2.4983, specify a maximum **12.5-hour** gap when drawing Brownian bridges from either 2h or 12h GPS. The publicly provided 12h ZIP (Dryad DOI https://doi.org/10.5061/dryad.15dv41p51) contains 28,953 records, including **10,835 date-only** timestamps (YYYY-MM-DD); the other 18,118 contain complete HH:MM:SS. The README states Mountain Time but does not resolve exact date-only clock values or DST conversion, and the original spatial CRS declaration conflicts with real coordinates. Those prior **source-QC STOPs remain in force**.

Previously, an exploratory midnight imputation yielded a high fraction of 10–14h gaps, but imputing midnight is not equivalent to knowing it. The new experiment asks which gap claims remain invariant across all clock interpretations in a declared interval and whether pairwise gap possibilities can be composed into one globally coherent timestamp assignment.

The [pair protocol](post_stop_time_interval_identifiability_protocol_v1.json) was committed **before new pair interval computations** at 0db021f77bbcf6bda0f434b01e7cc5f899287620. The [separate triplet protocol](post_stop_triplet_time_coherence_protocol_v1.json) was committed **before new three-record coherence computations** at 8221f67d86a03636a319005b58fd4c317836c42c. No withheld dense 2h data, coordinate rows, biological response or ecological forecast was accessed.

## Input definition and timing status

The SHA-verified original 1,539,661-byte 12h ZIP is partitioned by the fixed group key (Herd, AID, SeasnYr, Season), yielding **421 dependent individual-season groups**. Within each group, record ordering is fixed by the T0 lower timestamp bound, upper bound and physical DBF ordinal; it is reused unchanged for T1. There are **28,532 adjacent pairs** and **28,111 consecutive triples**.

The two explicitly different assumptions are:

- **T0, full-day ignorance:** a date-only record lies anywhere in its stated local civil date, from 00:00 inclusive to next midnight exclusive. No time is imputed.
- **T1, publication-inspired near-midnight window:** date-only record lies between 00:00 and 01:00 on its date. This is a *hypothesis*, motivated by the reported ~00/01 + 12/13 collar sampling schedule, **not independently confirmed clock information**.
- A complete timestamp remains a single observed local civil time in both cases. No conversion to UTC or correction for Mountain Time daylight-saving transitions is performed, so these are **nominal local-clock gaps**, not certified physical elapsed times.

Each pair's possible elapsed gap is bounded by [later.lower − earlier.upper, later.upper − earlier.lower]. A pair is **robust** under a scenario if every timestamp assignment in its declared intervals gives a strictly positive gap no longer than 12.5h; **contingent** if at least one allowed assignment does; **excluded from the 12.5h bridge** if no allowed assignment does. The last term is not ecological dispersal impossibility. Pairwise possible statements are NOT globally time-coherent path certificates.

## Result 1: pairwise temporal compatibility

| Adjacent pair status | T0 day-only time unknown | T1 hypothetical 00–01 |
|---|---:|---:|
| Robust (all times satisfy strict positive and <=12.5h) | 6,327 (22.2%) | 17,034 (59.7%) |
| Contingent (depends on allowed time choice) | 21,412 (75.0%) | 10,640 (37.3%) |
| Excluded by this local-clock gap rule | 793 (2.8%) | 858 (3.0%) |
| Ambiguous positive ordering under the interval bound | **10,707** (corrected one-second endpoint; legacy v1: 10,767) | 0 |

Types of original adjacent pairs: complete/complete **7,108**; complete/date-only **21,363**; date-only/date-only **61**. The T0→T1 analysis moves **10,707** contingent pairs to robust and **65** contingent pairs to excluded; 10,640 remain contingent. Changing the assumed clock interval changes the set of admissible transitions substantially.

The [pair receipt](post_stop_time_interval_pair_receipt_v1.json) records all count identities, the explicit 28,532 denominator, full time uncertainty, zero-outcome access and unchanged source STOP.

## Exact-second endpoint review (v2, after v1 audit)

A further audit found a mathematical boundary subtlety: T0 full-day intervals were described as upper-exclusive (ending *just before* next midnight), but the initial pair function compared against the unattainable next-midnight endpoint as though it were included. This affected the **ambiguous ordering flag for 60 pairs**, but **none of the robust/contingent/excluded pair classes and none of the 64 triple contradictions**.

Rather than silently edit the original evidence, a [separate exact-second correction protocol](post_stop_time_endpoint_seconds_protocol_v2.json) was committed at 4cc96cfbb60051b21bcddda7831436429448f3a4 **before** re-evaluating the full original 12h ZIP. At DBF timestamp resolution of one second, T0 is represented precisely by the closed integer-second interval from 00:00:00 to 23:59:59. Its true minimum positive gap to a subsequent next-midnight observation is at least one second, not zero. All main pair status totals remain exactly the same; T0 ambiguous-order count changes from 10,767 to **10,707**. T1 is unchanged. The original v1 receipt is retained for transparent provenance, while the [v2 receipt](post_stop_time_interval_pair_receipt_v2.json) is the canonical ordering-ambiguity count.

This is a method-definition correction, not observational evidence for midnight, the source CRS, actual animal movement, or model forecasting.

## Result 2: two individually possible links may not share one time assignment

For records (A,B,C), define two pairwise possibilities:

- There exists an assignment to (A,B) with 1s <= time_B − time_A <= 12.5h.
- There exists an assignment to (B,C) with 1s <= time_C − time_B <= 12.5h.

Those two existential assignments need not assign **the same time_B**. To certify a three-record route, one must find a *single* triple (time_A,time_B,time_C) satisfying both constraints. A separate precommitted exact integer-second interval algorithm checks that shared time_B, and its independent 10,000-case bounded integer brute-force oracle agrees in all cases.

| Triple status | T0 full-day ignorance | T1 hypothetical 00–01 |
|---|---:|---:|
| Total within-group triples | 28,111 | 28,111 |
| Both adjacent pairs individually possible | 26,764 | 26,637 |
| All three records jointly possible | 26,700 | 26,637 |
| **Pairwise possible but no joint triple** | **64** | **0** |
| Groups containing at least one false chain | **41** | **0** |

**Ordering limitation and follow-up check:** the initial triples are defined by a fixed sort on *lower time bounds*, upper bounds and DBF ordinal. Because date-only records have unknown true clock times, their actual chronological order can differ. To distinguish a sorting artifact from an unavoidable three-window incompatibility, a **separate six-permutation audit** was frozen and run as described below; no withheld 2h fixes were used.

The T0 false chains have only timestamp precision patterns **FDD (59)** or **FDF (5)**, where F is a full timestamp and D is date-only. This is a conditional *real-input instance* of a general quantifier-composition failure, not an observed failed migration or independent biological replication. The T1 outcome demonstrates that the phenomenon can disappear under a stronger clock assumption; it does **not** demonstrate that T1 is the correct underlying time.

Example of the logical problem in integer hours, using a 10h threshold: record A fixed at t=0, B unknown in [1,20], C fixed at t=25. The A→B pair can be realized using B≤10, and the B→C pair using B≥15, but no single B timestamp satisfies both. This counterexample contains **no animal's locations or individual identities**.

The [triplet receipt](post_stop_triplet_time_coherence_receipt_v1.json) retains the exact 64/0 comparison and the group-level count without any exact timestamp, original point coordinate or animal ID.

## Result 3: exact sensitivity to all six record orders

The [separate ordering protocol](post_stop_triplet_order_permutation_protocol_v1.json) was committed at c2e8e87e5c5fbd46e322b32204fb00ef640b34d0 **before** enumerating all 3! record permutations. It reuses the originally selected triple set, one-second closed interval endpoints, source-Dryad SHA and 12.5h gap limit. It does **not** infer the actual chronological order or fit a movement model.

| Triplet ordering feasibility | T0 full-day uncertainty | T1 hypothetical 00–01 |
|---|---:|---:|
| Triples not feasible under frozen order | 1,411 | 1,474 |
| Of these, feasible under another of six orders | **167** | 0 |
| Triples impossible under all six orders | 1,244 | 1,474 |
| **Original pairwise-only false chains remaining impossible under all six orders** | **64 / 64** | **0 / 0** |
| Groups with an order-rescuable triple | 75 | 0 |

This is a substantive distinction. Some failures *are* artifacts of the fixed sort (167 under T0), but **none of the 64 pairwise-only false chains is rescued** by permuting the same three intervals. The 64 are therefore an **ordering-invariant incompatibility inside the declared T0 full-day clock-world**, not merely a mistake in sorting uncertain timestamps. They are still not real migration failures: T1's stronger *unverified* 00–01 assumption eliminates the pattern, and Mountain Time / daylight-saving semantics are unresolved.

The [permutation receipt](post_stop_triplet_order_permutation_receipt_v1.json) preserves the full denominator and aggregate records, with no individual route, timestamp, or coordinate disclosure.

## Evidence boundary and next inference gate

These are **source-interpretation and finite-window logical checks**, not a fitted EOG finite-world ecological transition model, observed animal migration history, or prospective predictive performance. A 12.5h time gap is necessary for the paper's BBMM rule but does not establish reachability through an ecological landscape.

More importantly, even globally coherent triples do not imply one coherent full migration sequence, especially when timestamps are uncertain across many intervals. A global temporal-path model must retain a shared assignment to every uncertain timestamp rather than pooling possible edges. One can build such a model prospectively only after defining the source's time and spatial interpretation; it should not silently equate data-quality scenarios with biologically admissible worlds.

The original source's declared EPSG:3742 conflicts with geographically plausible EPSG:5070/5071 and the preferred NAD83-HARN datum transformation grid is unavailable locally. Exact date-only clock time and DST handling also remain unverified. The **source-QC STOP is not lifted** by these conditional calculations. The 2h heldout ZIP is unopened and no score is computed; EOG-WF remains **3 scored, 31 scientific STOPs, 3 administrative exclusions**.

Reproducibility: the [SHA-verified local replay](replay_post_stop_time_interval_qc.py) reads only the five approved sparse 12h DBF fields in memory, and produces aggregate pair or triplet receipts. No user-supplied GPS bytes are ever committed into GitHub.
