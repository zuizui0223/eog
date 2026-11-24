# McKee sparse 12h GPS: how much of link necessity is caused by the minimum-cut objective? (2026-11-24)

## Main result

**A link that is forced retained only because we require the *exact* minimum number of BBMM-style time-gap splits can cease to be mandatory after allowing just ONE additional split per animal-season group.**

The prior [optimal-partition audit](POST_STOP_OPTIMAL_CUT_NECESSITY_20261124.md) identified 793 links forced cut and 27,553 links forced retained **across four clock models and every minimum-segment partition**. The current source-only audit distinguishes those optimization-relative classifications from a more basic clock-time statement: whether two consecutive GPS observation windows can satisfy the paper's **1 to 45,000-second maximum link gap**, for *any* choice of local clock time.

The original McKee et al. (2024) public 12h source was independently SHA-verified before the new source analysis (Dryad doi:10.5061/dryad.15dv41p51; publisher v2 file 3334125; 1,539,661 bytes; SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4). It contains 28,953 fixes in 421 source-defined animal-season groups, with 28,532 adjacent source links. Only five previously approved DBF group/time fields are used. No source SHP geometry, exact dates, animal IDs or individual links are exported.

The [new protocol](post_stop_one_extra_cut_budget_protocol_v1.json) was **committed before the new 12h pair-feasibility and budget analyses** at 17d3611d0333893e9d23e72eeeb261c568020c04. The budgets and all four clock interpretations were fixed there; no new time threshold, data subgroup or source was selected after observing results.

## Exact claim and method

We work with an ordered set of consecutive source GPS records whose reported time fields define sets of possible integer seconds. A *contiguous block* is clock-feasible only when there exists ONE shared assignment of local clock instants through the whole block, with each successive positive gap no more than 45,000 seconds. For America/Denver, a repeated 01:xx civil time may have two **disjoint** legal UTC possibilities; those are preserved as alternatives, never silently converted into a convex hull. The original source did not independently authenticate daylight-saving or exact date-only clock semantics, so all clock worlds remain conditional.

For each source group, let m be the **minimum number of cuts** needed to partition the record sequence into feasible contiguous blocks. We compare all feasible partitions with cut budgets m+0, m+1 and m+2 (upper bounds, **not exact-budget requirements**).

A source-adjacent link is:
- **C, forced cut** if every partition within budget cuts there.
- **R, forced retain** if every partition within budget retains that link.
- **O, optional** if there exist both a within-budget partition that cuts there and one that retains it.

This is a *partitioning objective* classification, not a probability of animal movement, geographic reachability or observed transit.

### One-extra-cut theorem (constructive, not a new biological finding)

Two elementary constructions explain the sharp budget transition. Each individual source time window is nonempty, so singleton blocks are always valid.

1. Take any exactly minimum-cut partition. If a link is retained in that partition, inserting **one extra cut at that link** produces another valid partition. Thus with m+1 cuts available, *no* link is necessarily retained under all allowed partitions.
2. For an adjacent link that is individually feasible, take any exactly minimum-cut partition. If it already retains the link, no change is needed. If it cuts that link, remove this one cut and place cuts immediately before and after the two records so they form a feasible two-record block. This adds **at most one net extra cut**. Hence every individually feasible pair can be retained in some partition using at most m+1 cuts.

Consequently, under these exact constraints, **at m+1 (and also m+2), a link is a forced cut if and only if its two source time windows are individually incompatible**. Every other link is optional; forced retention disappears entirely. This statement concerns feasible timestamp assignments under the declared time-gap model, not real movement tracks.

The [SHA-gated local replay producer](replay_post_stop_one_extra_cut_budget.py) independently computes the exact shortest source-block DAG, and calculates the least number of blocks needed to retain or cut each link using forward/backward shortest-path costs and an interval-sweep. It cross-checks the theorem and the entire frozen m+0 result from PR #753.

## Empirical input-only results: 28,532 adjacent source links

| Conditional clock world | Minimum cuts m | At m+0: C / O / R | At m+1 or m+2: C / O / R |
|---|---:|---:|---:|
| T0 full-day, naive Mountain | 857 | 793 / 128 / 27,611 | **793 / 27,739 / 0** |
| T1 hypothetical 00–01, naive Mountain | 858 | 858 / 0 / 27,674 | **858 / 27,674 / 0** |
| T0 full-day, America/Denver DST | 889 | 800 / 178 / 27,554 | **800 / 27,732 / 0** |
| T1 hypothetical 00–01, America/Denver DST | 890 | 865 / 50 / 27,617 | **865 / 27,667 / 0** |

C = forced cut; O = can cut or retain under the budget; R = forced retained.

The previous frozen m+0 results and the original greedy cut counts are unchanged. The new m+1 and m+2 columns are **not new observations**; they are feasible-budget classifications applied to those source time windows.

### Intersection across all four clock worlds

| Status across the four worlds | Exactly optimal m+0 | At most one additional cut m+1 |
|---|---:|---:|
| Forced cut in all four | **793** | **793** |
| Forced retained in all four | **27,553** | **0** |
| Not universally fixed either way | **186** | **27,739** |

At m+1, the four-world source link patterns are:
- **793** CCCC (time-gap incompatible under all four conditional clock interpretations);
- **65** OCOC (possible under T0, incompatible under T1, both naive/IANA);
- **7** OOCC (possible under naive, incompatible under IANA, both T0/T1);
- **27,667** OOOO (individually time-gap feasible under all four).

Thus exactly **72 original source links** have a clock-interpretation-dependent *pairwise* eligibility (65 + 7). For the other links, the four-world pairwise clock predicate is identical. This does **not** imply all 27,667 can be retained simultaneously in one globally coherent sequence or in one partition shared between the clock worlds.

The count of groups having at least one optional link changes from 41/0/65/25 under m+0 (T0 naive, T1 naive, T0 IANA, T1 IANA) to **421/421/421/421** under m+1. This is an explicit signature of **objective relaxation**, not evidence that animal movement became biologically uncertain.

## Independent correctness and reproducibility

The [offline regression](../../tests/test_mckee2024_one_extra_cut_budget.py) enumerates *every concrete clock assignment* and *every possible contiguous source cut mask* for **500 small 2–6-record synthetic nonconvex time-window worlds**, then compares all C/O/R link classifications at m+0/m+1/m+2 to the DAG producer. These synthetic finite-clock checks verify the derivation without opening any 2-hour GPS outcomes. The original 12h aggregate receipt retains all source denominators, prior m+0 comparisons and no-leakage/no-score flags.

The existing input source issue [#745](https://github.com/zuizui0223/eog/issues/745) remains open. Dryad's declared EPSG:3742 does not agree with Albers-family geographically plausible coordinates, the exact source time-zone/date-only conventions are unknown, and preferred NAD83↔HARN datum grids are unavailable. All comparisons are conditional source-QC/method identifiability, **not a BBMM reconstruction, animal barrier, observed migration path, independent predictive EOG validation, or fourth EOG-WF endpoint**. Dense 2h GPS remains sealed. EOG-WF is unchanged at **3 scored (2 favorable / 1 adverse), 31 scientific STOPs, 3 administrative exclusions**.

**Decision:** The defensible strongest claim without extra assumptions is **793 unavoidable local time-gap disconnections across the four explicitly considered clock interpretations**. Calling any link necessarily *retained* requires an explicit partition-minimization objective or another extra constraint. Neither statement establishes actual ecological path viability.
