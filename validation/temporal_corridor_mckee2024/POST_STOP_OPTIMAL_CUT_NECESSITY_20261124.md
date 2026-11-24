# McKee 2024: which sparse GPS clock cuts are unavoidable? (2026-11-24)

**Result:** **857 common greedily chosen source-clock breaks are NOT 857 mandatory link breaks.** Only **793** are forced in every minimum-cut partition across the four predeclared clock scenarios. This explicitly qualifies the [previous near-overlap observation](POST_STOP_CLOCK_CUT_OVERLAP_20261124.md) without altering its historical raw counts.

## Context and provenance

The user-supplied McKee et al. (2024) original sparse 12-hour Dryad ZIP was independently checksum-verified (DOI https://doi.org/10.5061/dryad.15dv41p51, publisher file ID 3334125, 1,539,661 bytes, SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4). It includes 28,953 original source fixes and 421 dependent animal-season groups (28,532 within-group adjacent links).

The paper [doi:10.1002/ecs2.4983](https://doi.org/10.1002/ecs2.4983) imposes a 12.5-hour maximum separation on fixes to be joined by a Brownian bridge. This is a data-input eligibility rule, NOT a demonstrated animal passage or ecological barrier.

Earlier [PR #750](POST_STOP_BBMM_CLOCK_SEGMENTATION_20261124.md) used one **longest-feasible-prefix greedy** clock-segmentation policy and found conditional coherent cut totals of 857 (full-day T0, local clock), 858 (near-midnight T1), 889 (full-day T0 with America/Denver DST), and 890 (T1 with DST). The [PR #751 overlap audit](POST_STOP_CLOCK_CUT_OVERLAP_20261124.md) found 857 greedily selected breaks in common under naive T0/T1. [PR #752](POST_STOP_DST_UNION_CLOCK_COHERENCE_20261124.md) preserved both legal UTC folds for repeated autumn clock hours.

One untested interpretation remained: **Are those specific greedy cut locations forced in EVERY equally optimal partition, or could the same minimal number of segments be obtained by cutting elsewhere?**

The [new protocol](post_stop_optimal_cut_necessity_protocol_v1.json) was committed at **5319159417d944586913a3abd06b54331a150af5 before any new minimum-partition-ensemble source calculation**. It freezes the exact GPS source, four clock worlds, original per-group record order, 1..45,000-second gap rule, and distinction between *selected* and *mandatory* cuts. The dense 2-hour reference remained sealed throughout.

## Method: enumerate all optimal partitions without enumerating GPS paths

For one group of N consecutive time-uncertain records, create a directed acyclic graph with N+1 boundary nodes (0 to N). A directed edge i→j means the original records from i through j−1 admit **one shared feasible clock assignment** within that segment. A source sequence partition is a boundary 0→N path. A minimum number of continuous clock blocks is a **shortest path** in this segment DAG.

The exact forward/backward shortest-path distances classify every original adjacent link between records at boundary k:

- **Forced cut (C):** every minimum-segment partition cuts at k; no optimal DAG block covers the link.
- **Optional cut (O):** at least one minimum-segment partition cuts at k AND at least one equally optimal partition retains it.
- **Forced retention (R):** every minimum-segment partition retains the link; boundary k never occurs on an optimal path.

This is a conditional *optimization/constraint* certificate, not an EOG animal movement path, and it depends on minimizing total cut positions. The old longest-prefix greedy mask is one such optimal path, not necessarily the only one.

All group-level status classifications were verified independently against **exhaustive enumeration of every time assignment and every contiguous partition** in 450 small synthetic 2–6-fix integer clock-world examples. No dense GPS outcomes or ecological prediction data were used.

## Results for all 28,532 source-adjacent links

| Frozen input-clock interpretation | Minimum/greedy cuts | Forced cuts | Optional link positions | Forced retained |
|---|---:|---:|---:|---:|
| **T0 full-day, naive Mountain local** | **857** | **793** | **128** | 27,611 |
| T1 hypothetical 00–01, naive local | 858 | 858 | 0 | 27,674 |
| T0 full-day, IANA America/Denver DST | 889 | 800 | 178 | 27,554 |
| T1 hypothetical 00–01, IANA DST | 890 | 865 | 50 | 27,617 |

The **128 optional T0 naive links** have an important composition: the greedy algorithm *chose* 64 of those as cuts, while 64 other optional links were retained and could replace those selected breaks in an alternative minimum-segment partition. Exactly **41 of the 421 dependent groups** have multiple minimum-cut masks under T0 naive. Corresponding nonunique-group counts are 0 for T1 naive, 65 for T0 IANA, and 25 for T1 IANA.

## Cross-world universal status

Across **ALL FOUR** frozen clock-input worlds and **ALL** minimum-cut solutions within each world:

| Universal link type | Number of original links | Meaning under declared clock models |
|---|---:|---|
| **Always forced cut** | **793** | Every one of the four models' optimal partitions cuts this source link |
| **Always forced retained** | **27,553** | Every optimal partition under every considered clock model retains this source link |
| **Not universally fixed either way** | **186** | A link changes class across models, and/or is optional within a model |
| Total | **28,532** | Original source-adjacent link universe |

Of those 186 nonuniversal links, **178** are optional in at least one clock world, and **8** are forced cut in one clock world but forced retained in another. The corresponding discrepancies occur in **70 of 421 dependent groups**. The fixed-MST clock is an exact negative control: all **421 groups'** optimal link classes and greedy masks agree with the matching naive local clock up to a constant seven-hour translation.

The historical greedy cut masks remain exactly as previously reported: 857 common cuts across all four worlds, 32 selected by the IANA worlds only, one additional T1 cut in both clock conventions, and 27,642 never selected by any greedy mask. But the **857 is an algorithm-chosen cut-mask overlap**, NOT the number of mandatory breaks.

The [aggregate, non-identifying evidence receipt](post_stop_optimal_cut_necessity_receipt_v1.json) records full status-pattern counts (e.g. the 64 T0-optional/T1-forced cut link positions) so the distinction can be audited without disclosing source animal IDs, exact timestamps, GPS coordinates, or which individual link differed.

## Why this is methodologically useful

A simple three-observation synthetic counterexample clarifies the difference: timestamp A fixed at 0, B allowed 1–20, C fixed at 25, with a maximum link gap of 10. A–B can be satisfied using an early B; B–C using a later B; the two links cannot be simultaneously satisfied. One cut is required, but **either A–B OR B–C** can be cut, and both choices are equally optimal. Thus a required *number* of breaks does not entail a uniquely required *location* of every break.

This matters directly for EOG-style finite-world quantifiers: an edge present in one chosen optimal time-segmentation world is not necessarily present in every optimal world. Treating the tie-broken greedy path as an all-world necessity statement would confuse existence with necessity and overstate what the sparse GPS timestamp information identifies.

## Hard scientific boundaries

- **Forced** and **optional** here refer only to *minimum-number-of-segments* clock partitions under each frozen data/clock world and the input BBMM 12.5-hour link rule. They do not imply actual migration barriers, directly observed disconnection, or an animal's realized path.
- The four time worlds are **conditional interpretations** of the same source. T1's date-only near-midnight assumption is not author-certified; Mountain local civil-clock DST handling is not confirmed. Preferred geodetic CRS remains unresolved (source README/.prj EPSG:3742 vs geographically coherent Albers EPSG:5070/5071), and accurate datum transformation grids are missing.
- No 2-hour holdout GPS source was downloaded/opened, no SHP point geometry was used, no BBMM or EOG landscape model was fit, and no predictive accuracy was scored.
- This is a **new source-data methodological sensitivity**, not an independent biological replication or a fourth EOG-WF endpoint. EOG-WF's frozen denominator remains **3 scored (2 favorable/1 adverse), 31 scientific STOPs and 3 administrative exclusions**.

Reproduce locally with the exact original 12h ZIP using [the SHA-locked DAG producer](replay_post_stop_optimal_cut_necessity.py) and [synthetic exhaustive oracle tests](../../tests/test_mckee2024_optimal_cut_necessity.py). The original ZIP remains outside the repository. The unresolved data-author provenance task remains open in [issue #745](https://github.com/zuizui0223/eog/issues/745).

## Addendum: optimizer-relative mandatory retention, NOT objective-independent source fact

A [subsequently precommitted +0/+1/+2 extra-cut budget audit](POST_STOP_ONE_EXTRA_CUT_BUDGET_20261124.md) shows that the **27,553 links classified forced-retained above refer strictly to partitions achieving each group's exact minimum cut count**. With **up to one more cut per group** any link can be cut voluntarily while keeping the partition feasible, so **none** remains forced-retained under that relaxed objective. Conversely, the **793 cross-world forced cuts remain** because each is an individually impossible pair under the 1–45,000s time-gap predicate in all four source-clock interpretations. The 857 common greedy-selected cuts remain a valid optimum-specific result, but neither those 857 nor any optimum-relative forced retentions are unconditional movement-route facts. This addendum does not overwrite the frozen original receipt or resolve actual source clock/CRS semantics.
