# McKee 2024: exact DST-fold conditional temporal coherence audit (2026-11-24)

**Evidence level: original 12-hour GPS input semantics only, not a biological route or predictive result.**

## Why revisit the near-identical 857/858 clock cut masks?

The prior source-only clock segmentation [PR #750](POST_STOP_BBMM_CLOCK_SEGMENTATION_20261124.md) and paired-link overlap [PR #751](POST_STOP_CLOCK_CUT_OVERLAP_20261124.md) used **naive Mountain local wall-clock seconds**, yielding 857 coherent breaks under full-day T0 uncertainty and 858 under hypothetical near-midnight T1. Both cut masks almost coincided (857 shared cuts out of 858).

But the [source paper](https://doi.org/10.1002/ecs2.4983) describes GPS fixes near 00/01 and 12/13 hours **Mountain Time** and excludes successive fixes with gaps above 12.5h when drawing Brownian bridges. It does not prove whether the exported character timestamps were normalized to UTC, fixed MST (UTC−07), or local civil time observing Mountain daylight saving. In the autumn repeated local hour, a printed 01:30 can denote **two different actual instants**. A simple wall-clock subtraction can be off by one hour across such transitions.

Before inspecting any new source UTC conversion, the [new protocol](post_stop_dst_fold_coherence_protocol_v1.json) was frozen at commit faac1fad698e88807386819e6c84d9800a87f64f, pinning the original Dryad file identity, three interpretation scenarios, naive-vs-fixed control, exact disjoint-interval semantics, 1–45,000s BBMM gap rule and aggregate-only output.

## Three competing clock models

1. **NAIVE_MOUNTAIN_LOCAL:** prior local wall-clock arithmetic. Does not establish physical elapsed time.
2. **FIXED_MST_UTC_MINUS_07:** every civil-clock second shifted to UTC by exactly seven hours, with **no DST**. Since this is a constant translation, each eligible gap and cut mask must exactly reproduce NAIVE. It is a negative control.
3. **AMERICA_DENVER_IANA:** independently interprets each local clock reading using historical America/Denver civil timezone rules, preserving the two valid UTC instants for ambiguous repeated autumn 01:xx clock readings.

For date-only T0, the full local civil day maps to a **continuous 23h, 24h, or 25h real UTC interval**, depending on its DST transition. For hypothetical near-midnight T1 (00:00–01:00 inclusive), an autumn fall-back day maps to the first uninterrupted allowed UTC interval plus a **disconnected singleton** corresponding to the second 01:00. This disjoint interval union must not be replaced by a convex hull spanning otherwise forbidden instants.

Globally coherent time linkage is checked by propagating the exact **union of attainable integer-second intervals** through consecutive observations. Each reachable [a,b] permits [a+1,b+45000] at the next observation; intersect with the next allowed time windows, then union only intervals that truly overlap. When empty, a new input clock block starts. The same 421 source-defined individual-season groups and frozen deterministic record order are retained across all clocks.

No timestamp is imputed as midnight, nor is source UTC or daylight-saving treatment inferred as established fact.

## Source-only audit results

The exact public Dryad v2 12-hour ZIP (1,539,661 bytes; SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4) contains 28,953 records, including 10,835 date-only entries. For America/Denver IANA conversion, the source clock patterns include:

- **25 fully specified timestamps with two possible UTC instants** at a repeated DST fall-back hour;
- **74 date-only records on autumn 25-hour local days**;
- **36 date-only records on spring 23-hour local days**;
- **zero fully specified nonexistent spring-forward local times** under the tested timezone.

| Condition | Pairwise optimistic cut positions | Joint time-coherent cuts | Extra cuts due to no-splicing |
|---|---:|---:|---:|
| T0, naive Mountain local time | 793 | 857 | 64 |
| T0, fixed MST UTC−07 | 793 | 857 | 64 |
| **T0, America/Denver with DST** | **800** | **889** | **89** |
| T1, naive Mountain local time | 858 | 858 | 0 |
| T1, fixed MST UTC−07 | 858 | 858 | 0 |
| **T1, America/Denver with DST** | **865** | **890** | **25** |

The naive and fixed-MST source **cut masks agree exactly**, as they must under a constant time translation.

Comparing naive to IANA-aware, **32 additional distinct link cuts** occur for each of T0 and T1; *none* of the naive cut positions is restored, and the differences affect **32 of 421 dependent individual-season groups**:

| Paired coherent cut status | T0 | T1 |
|---|---:|---:|
| Cut under both naive and America/Denver | 857 | 858 |
| Naive-only cuts | 0 | 0 |
| **Additional America/Denver-only cuts** | **32** | **32** |
| Both retain the link | 27,643 | 27,642 |

**Unexpected method-level consequence:** Even the hypothetical narrow T1 window, previously free of pairwise-only timestamp splicing under naive seconds, now requires **25 coherent cuts beyond 865 pairwise-optimistic cuts** when repeated local-hour ambiguity is carried as genuinely alternative UTC instants. This is a conditional time-identity issue, not physical evidence that 25 animals or routes failed.

The [aggregate receipt](post_stop_dst_union_coherence_receipt_v1.json) records time-source and cohort identity, full 2×2 cut tables, the actual reference clock, exact observed full-hour ambiguity counts and safety flags. Source analysis used system TZDB version **2025b**, offline; a different system tzdb version should be reported and tested before treating numeric differences as identical.

## Independent correctness and limits

The [offline source replay](replay_post_stop_dst_union_coherence.py) only imports the previously SHA-locked **five-field 12h DBF decoder**. It never opens the dense 2-hour holdout, raw geographic positions or individual-level output, and it uses no geospatial datum transformations.

An independent brute-force oracle enumerates all integer-second choices in multiple disjoint time windows, and all valid contiguous partitions in small finite cases; the production interval-union propagation is checked against that independent truth. Synthetic tests also verify a real autumn repeated 01:xx local clock has two UTC instants, a spring transition civil day has 23 physical hours, and near-midnight T1's fall-back UTC allowed set is **nonconvex**.

**Strict claim ceiling:** The Dryad README does not establish whether stored times were daylight-saving-aware America/Denver instants. This audit is therefore a **sensitivity under an alternative interpretation**, not a correction of the published data or a new BBMM benchmark. The author-intended source CRS (declared EPSG:3742, but geographically consistent with Albers alternatives 5070/5071), the actual full/datestamp clock semantics and accurate datum grids remain unresolved. Source-QC STOP in [issue #745](https://github.com/zuizui0223/eog/issues/745) is preserved. No ecological movement route, EOG forecast, or fourth EOG-WF endpoint was inferred; original 3 scored /31 science STOP /3 administrative exclusions unchanged.

**Decision:** A robust workflow must keep IANA civil time/fold handling and fixed-MST assumptions as *different declared clock worlds* until the original clock encoding is authenticated. Reporting only naive 857/858 cuts as absolute physical-time truth is not justified.

## Addendum: DST-altered greedy cuts vs every-optimum necessity

The original IANA 889/890 coherent break totals and 32 added selected breaks remain as stated, but a [later shortest-path ensemble audit](POST_STOP_OPTIMAL_CUT_NECESSITY_20261124.md) shows not all these link positions are compulsory in every minimum-segment partition: **T0 IANA = 800 forced / 178 optional / 27,554 forced retained**; **T1 IANA = 865 forced / 50 optional / 27,617 forced retained** source-adjacent links. The IANA-vs-naive difference is still a conditional *timezone treatment sensitivity*, not confirmation of exact source clock or an animal route. A selected greedy break can move while preserving the same minimal count.
