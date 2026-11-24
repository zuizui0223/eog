# McKee sparse 12-hour GPS: BBMM clock-link fragmentation audit (2026-11-24)

## Scope and published source rule

**Conditional source-clock segmentation; NOT a fitted BBMM or observed animal migration route.** The SHA-verified original McKee Dryad 12h source (DOI 10.5061/dryad.15dv41p51; publisher file 3334125; 1,539,661 bytes; SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4) contains 28,953 GPS records from 421 dependent individual-season groups.

[McKee et al. (2024)](https://doi.org/10.1002/ecs2.4983) specifically did **not** draw Brownian bridges across successive GPS time gaps exceeding 12.5 hours. Therefore the preceding whole-group source-clock incoherence must be revisited with **segment breaks**, rather than interpreted as a failure of the published BBMM method.

The [segmentation protocol](post_stop_bbmm_clock_segmentation_protocol_v1.json) was committed at d1e28d23f6faf63ddc51729dd6671a9a05c7ccf7 **before any new source segmentation**. It freezes the 45,000-second limit, source file SHA, prior record ordering, group key, timestamp interpretations, segmentation definitions and aggregate outputs.

## Three input-only segmentation policies

1. **Optimistic pairwise:** keep an adjacent bridge if there exists an assignment of times for *that pair alone* with a positive gap no longer than 45,000 seconds. Split at all other links. Different pairs can silently require incompatible times for their shared middle fix.
2. **Coherent contiguous blocks:** propagate one reachable interval through the whole block; when an added fix makes that interval empty, cut immediately before that fix and restart. Longest-feasible-prefix splitting minimizes the number of contiguous blocks for this fixed order and these clock intervals. This is a mathematical time-gap test, not an animal motion model.
3. **Universally robust pairwise:** keep a link only when *every* combination of allowed times satisfies a strictly positive gap <=45,000 seconds. This very strict criterion penalizes the source's date-only timestamps.

T0 date-only = any integer second 00:00:00–23:59:59 (local civil day). T1 date-only = 00:00:00–01:00:00 as a **hypothetical** collar schedule sensitivity, not an established source correction. Complete timestamps are fixed local-wall-time instants. No UTC or daylight-saving conversion is asserted.

## Original 12h input results

| Source-clock segmentation | T0 full-day uncertainty | T1 conditional 00–01 |
|---|---:|---:|
| Pairwise optimistic cuts | 793 | 858 |
| **Globally coherent cuts** | **857** | **858** |
| Extra coherent cuts beyond optimism | **64 (41 dependent groups)** | **0** |
| Universally robust cuts | 22,205 | 11,498 |
| Coherently retained time links | 27,675 | 27,674 |
| Total coherent blocks, including singletons | 1,278 | 1,279 |
| Coherent blocks containing 2+ source fixes | 1,037 | 1,037 |
| Universally robust retained time links | 6,327 | 17,034 |

The 64 added coherent cuts align with the preceding source-only three-record temporal no-splicing result. Their distribution spans 41 dependent groups: 30 groups need one extra cut, five need two, three need three, one needs four, one needs five and one needs six. Among all 421 source groups, the previously frozen subset where **all pairwise edges were possible yet the full record sequence impossible** consists of 14 groups.

The conservative alternative is strikingly different: at T0 only 6,327 of 28,532 adjacent links are retained. This produces 22,626 segments including 21,871 singletons. Those singletons mostly reflect **unknown time-of-day**, not observed migration interruptions.

T0 coherent and T1 optimistic have very similar TOTAL cut counts (857 vs 858), but those totals **do not establish that the same bridges are retained**. This test did not select one scenario as the true one.

The [machine-readable receipt](post_stop_bbmm_clock_segmentation_receipt_v1.json) includes full cut, segment, group, and length-bin accounting. The [SHA-locked replay script](replay_post_stop_bbmm_clock_segmentation.py) accepts the exact user-supplied sparse source ZIP locally, reads only approved DBF clock/group fields, and emits aggregate summaries. No raw GPS ZIP is committed. An independent small-integer brute-force oracle checks the greedy minimal partition against all contiguous cut placements, without using the production segmentation helper.

## Inference boundary

The contrast illustrates two *source-data methodological* failure modes: independent pairwise eligibility may overconnect clock-inconsistent observations; requiring universal confidence in both uncertain clocks may overfragment the time axis. An exact coherent partition is a conditional intermediate, not an inferred physical migration route or calibrated BBMM corridor. The original paper may additionally apply censoring, geometric transformations and other movement model procedures not replicated here.

The original Dryad README and original PRJ explicitly declare EPSG:3742, whereas the coordinates are geographically consistent with Albers-family EPSG:5070/5071. Original author-intended CRS, exact date-only timestamp semantics and Mountain Time/DST handling remain unresolved. No SHP geometry, withheld 2h GPS, ecological model or prospective score was accessed here. Original EOG-WF remains strictly **3 scored (2 favorable/1 adverse), 31 scientific STOPs, 3 administrative exclusions**.

The user-facing science STOP stays open in [issue #745](https://github.com/zuizui0223/eog/issues/745). Before opening dense 2h holdout data, source semantics and an independent prediction protocol must be separately certified.
