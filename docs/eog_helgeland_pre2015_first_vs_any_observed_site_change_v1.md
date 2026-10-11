# Helgeland 1994–2014: when the first recapture hides later observed site changes

**Analysis type: exploratory, post-exposure, positive-detection only.** First-followup pre-2015 real source outcome **223 changed / 4,164 linkable** was already inspected and merged in PR #642. This follow-up was frozen **before examining any subsequent (after-first) code switches**. The question is NOT whether island dispersal exists (established by Ranke et al., 2021); it is **whether restricting to the first direct followup systematically fails to describe site-code changes subsequently observed in the same pre-2015 individuals**.

## Original data and chronological firewall

- Official 2026 Dryad `10.5061/dryad.rr4xgxdnq` v6 / 421942, file ID 4576411. Public authors' GitHub `torhanssonfrank/DensityRegulationHouseSparrows` commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5` was independently byte-SHA-256-matched against original Dryad and physical header in merged PRs #628–#629.
- **Only records with physical encounter dates from 1994-01-01 to 2014-12-31 may contribute any ID, Island, Location or stage.** `date` is inspected before all other fields. 2015–2022 ID/site/stage values are NEVER consulted. This is a forward-observation firewall in code, not evidence the 2026 raw file existed publicly in 2014.
- Do not read source `Year` (April–March reporting label), inferred `Least_age`, `Least_hatchyear`, `scriptsex`, `filled`, genotypes, full-period `downup` island interpolation or posterior `N_corr`.

## Frozen estimand

For an ID with `stage=nest` directly observed on **exactly one Island code** in the period, let baseline be that one code and birth observation the **earliest** directly observed nest date. Collect all **strictly later** directly observed `capt` or `obs` events in the period. First-followup is the **earliest date**, and the recorded Island codes on that date must agree; otherwise it is first-date-ambiguous.

Count:

- **First-different:** first followup's unique Island code differs from the nest code (published first exploration: **223**).
- **Ever-different:** any direct followup at any date in 1994–2014 records an Island code different from the nest code.
- **First-same → later-different:** individuals with an unambiguous first followup on the nest code but some later encounter (strictly after that date) on a different code. This is the **missed-positive quantity** attributable to the first-followup rule, conditional on the observed followup sequence.
- **First-different → later-same:** a later recorded return to the nest code; this flags why even a first-different event does not prove permanent dispersal.
- Number of distinct followup encounter **dates** (exactly 1 versus ≥2) to document unequal observational exposure, **not** as an independently verified survey-effort adjustment.

All output is **aggregate counts only**. ID, site codes, dates and movement paths are not exported. Zero records/survey absence, true natal-to-adult dispersal, recruitment and source→sink founding are NOT inferred. A same-code first followup can precede a genuine subsequent change; a different-code event can precede return. All comparisons are conditional on detection and do not estimate actual dispersal probabilities.

## Previously exposed totals frozen before this exploration

The new protocol `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_first_vs_any_switch_contract_v1.json` fixes 73,593 original rows, 51,162 eligible pre-2015 observations, 1,070 before 1994, 21,361 after 2014, 10,737 IDs with one nest code, 5 ambiguous nest IDs, 4,164 with subsequent direct encounter, 6,573 with no later encounter, and first-followup codes **3,941 same / 223 different / 0 ambiguous**. A real run must agree on every one or STOP.

The 2026 source provenance and source/firstline SHA256 remain unchanged. The synthetic tests include adversarial 2015+ records (attempting to expose ID/island/stage), site reversals, contradictory same-day destinations, non-calendar `Year` and retrospectively derived ages. The new audit is eligible for merge only after **real source output and fresh repeat CI** confirm all prior totals and new aggregate receipts.

## Interpretation and decision gate

If first-same/later-different is substantial, the first-observation-only measurement understates **ever-observed site-code variation**. That observation can motivate a later careful comparison of *dated and observation-corrected* movement versus directional reachability, but is not independently novel biological selection, cause, mechanism, population founding or EOG model performance. More followup dates raise the opportunity to see a change, so any observation-depth gradient is confounded by encounter effort and individual longevity.

If first-same/later-different is near zero, retaining first-followup may be a simpler exploratory proxy, still not a recruited-adult endpoint. In either case, 2015–2022 outcomes remain unread by this exercise. All true held-out and observation-effort scientific gates remain HOLD. Track the evidence at [Issue #626](https://github.com/zuizui0223/eog/issues/626).
