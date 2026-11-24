# McKee 2024: source clock-cut positions are almost identical under T0 and T1

**Data-QC and input-method comparison only; not biological movement validation.**
November 24, 2026.

## Why compare positions, not just aggregate cut counts?

The preceding [source-only BBMM 12.5-hour clock eligibility audit](POST_STOP_BBMM_CLOCK_SEGMENTATION_20261124.md) found **857 time-coherent breaks** under T0 full-day date-only uncertainty, versus **858 breaks** under T1 hypothetical 00–01 clock windows. Almost identical TOTALS could conceal entirely different breaks and potentially imply different modeled paths.

To test that hypothesis, the [cut-location protocol](post_stop_clock_cut_overlap_protocol_v1.json) was committed at d74eb7360a603fae790af5df9b8b95162cc2e7be **before** comparing actual frozen within-animal-season source link identities. Its two arms are precisely the PR #750 source T0-coherent and T1-coherent/optimistic segmentations. The data universe remains 28,532 within-group adjacent links across 421 groups from the same publisher SHA-verified McKee 12h original ZIP. No other herd/source/threshold was selected, and no individual link indices are exported.

## One-to-one paired source link comparison

| Paired link-level behavior | Count |
|---|---:|
| Both T0 coherent and T1 hypothetical cut | **857** |
| T0 coherent cuts only | **0** |
| T1 hypothetical cuts only | **1** |
| Both retain the link | **27,674** |
| **All 12h adjacent links** | **28,532** |

Therefore **100% of T0 coherent break locations are shared** with the T1 conditional segmentation. The T1 scenario cuts just **one extra** link, classified *contingent* (not robust or excluded) under the original T0 pairwise window. Only **1 of 421 dependent animal-season groups** has a difference.

The Jaccard overlap of CUT link sets is **857/858 = 0.9988345 (99.883%)**. The overlap of retained link sets is **27,674/27,675 = 0.9999639 (99.996%)**. These are **record-link identity overlaps**, not spatial corridor intersection, individual probability of migration, model accuracy, or out-of-sample prediction.

This explicitly resolves the previous ambiguity: almost-equal aggregate numbers in PR #750 do reflect almost-identical **conditional time-gap break locations** in this exact data set. Importantly, the equality is not simply because there are only a few missing time values: 10,835 of 28,953 source records are date-only and the T0 conservative and T1 conservative policies split 22,205 and 11,498 pairs respectively. The **global time-consistency** rule recovers most of the agreement without treating a date-only timestamp as a known midnight value.

## Scope, uncertainty and stopping rules

- All decisions use the same **deterministic, T0 lower-bound/upper-bound/DBF-ordinal source order** and a gap of 1–45,000 seconds in naive Mountain civil time. The correct historical ordering or daylight-saving offsets have not been independently established.
- T0 uses full-day time uncertainty and T1 assumes 00–01 locally as an unverified **alternative input scenario**. Near-identity of their cut masks neither proves T1 clock truth nor supports automatic midnight imputation.
- Both arms apply only the paper's maximum 12.5-hour time-gap criterion. No actual Brownian-bridge model, movement interpolation, spatial path or EOG prediction is executed. A source time link is not a geographic edge and does not establish biological connectivity.
- The original Dryad PRJ/README EPSG:3742 conflicts with source geographic data consistent with Albers EPSG:5070/5071. Author-intended CRS, missing accurate datum transformation grids and timestamp/DST semantics remain explicit source-QC STOPs.
- The withheld dense 2h GPS ZIP was **not** opened, and no individual animal ID, timestamp or coordinates are published. The original EOG-WF denominator remains **3 scored, 31 scientific STOPs, 3 administrative exclusions**.

The public [aggregate receipt](post_stop_clock_cut_overlap_receipt_v1.json), the [SHA-locked source-only replay](replay_post_stop_clock_cut_overlap.py) and [focused regression checks](../../tests/test_mckee2024_clock_cut_overlap.py) make the one-link difference inspectable without disclosing source records or fitting a model. Source confirmation remains requested in [issue #745](https://github.com/zuizui0223/eog/issues/745).

**Scientific status:** a striking input-method robustness result **conditional on two unverified clock windows**, not empirical validation of EOG prediction, the exact GPS timestamps, or a mapped migration corridor.
