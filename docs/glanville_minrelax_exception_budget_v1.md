# Glanville conditional minimum-relaxation tail and exception-budget audit v1

## Status
Post-outcome exploratory **sensitivity audit only**, frozen before any new
target-distance tail calculations. It must not revise the previously merged
strict full-target EOG minrelax estimate, source definition, or 3/31/3 EOG-WF
prospective denominator.

- Frozen protocol: `validation/glanville_minrelax_exception_budget_v1/protocol_v1.json`
- Original result (must be exactly reproduced first):
  `validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json`
- Parent full precision fingerprint:
  `e5e4da4088aef5ca9337f913e644d324190a230934ac0dcf2bbc360fb09dd68a`
- Both source archives are pinned by SHA256, and 2019 EPSG3067 centroid
  coordinates continue to be multiplied by 1,000 to convert documented
  **kilometers** to **meters**, before Euclidean distance is returned in km.

## Why this scientific check is needed

The previously reported `r*(delta)` is the maximum of the nearest compatible
source distances over **all** eligible recorded-positive transitions.
Therefore even a single exceptional recorded target may determine the entire
annual maximum. That maximum is an exact *conditional compatibility*
requirement, not an empirical maximum dispersal capacity or the typical
distance needed by most patches.

The new audit deliberately does not seek a favorable p-value. It investigates
whether the prior maxima describe a broad set of records or a small high tail.

## New estimand

For one year, source-policy and host tolerance `delta`, let `D_i(delta)`
be each recorded-positive transition patch's distance in km to its nearest
allowed source; if no source meets that host score requirement, define
`D_i(delta) = +Infinity`.

Let `n` be the complete **unchanged** target roster, and `k` a predeclared
*exception budget*. Define

```
r_k(delta) = kth-from-largest order statistic of
             {D_1(delta), ..., D_n(delta)}
           = sorted(D)[n-k-1].
```

This is the minimum one-hop radius needed to explain **at least n-k of the
recorded positive targets**, leaving the others explicitly *unexplained by
the declared local source model*. An exception does not mean a false-positive
record. It may reflect an unmodeled origin, rare long-distance event,
detection history, a changing niche or incomplete source roster. None of
those mechanisms is identified by this sensitivity test.

Predeclared budgets are `k=0`, `k=1`, `floor(0.01*n)`, and
`floor(0.05*n)` for each original year/source roster. Missing compatible
sources remain `+Infinity`; if `k` is smaller than their count,
`r_k` must remain non-estimable.

Additional distribution summaries are median, q90, q95, q99 **among targets
with at least one allowable source** (and the count of targets without any
source is always reported separately). Only `delta=1,3` are primary
descriptive panels; `delta=0,2` are required secondary safeguards.

## Non-retroactivity and independent checks

1. Reconstruct all 12 year × source-policy original target/source rosters
   without changing either of their eligibility rules.
2. Regenerate the original 12 × 4 strict radii, missing-source counts,
   target counts and source counts and require agreement with the frozen
   parent JSON (rounded radius tolerance `1e-5 km`). Abort otherwise.
3. At each year/source/host panel verify that increasing `k` never
   raises `r_k`; increasing host tolerance `delta` never raises it.
4. At each year/host/k verify expanding source history from `t-1` to
   `t-1 or t-2` never raises `r_k`, because the target set must remain
   identical and candidate sources are nested.
5. Retain `non-estimable` explicitly when a source class is missing.
6. Do not export any patch identifiers, original coordinates, genotypes,
   occupied/unoccupied row labels, or unaggregated target distances.
7. No new predictive model, inference of true colonization, independent
   ecological validation, or generic model superiority claim.

The predeclared decision descriptive threshold is whether `k=1` produces
a reduction of at least 25% in a **primary** host-gap panel. The count is
only a compact diagnostic of tail concentration, not a statistical test.

## Reproducibility

```bash
python -m pytest -q tests/test_glanville_minrelax_exception_budget_v1.py
python benchmarks/glanville_minrelax_exception_budget_v1.py \
  --protocol validation/glanville_minrelax_exception_budget_v1/protocol_v1.json \
  --parent validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json \
  --output results/glanville_minrelax_exception_budget_v1/result.json
```

Raw archives are only streamed into a temporary runner directory. An archive
failure or a parent-reproduction mismatch returns a scientific STOP rather
than automatically changing a source, tolerance or observation definition.

## What comes next

If high maxima are driven by one or a few remote target patches, a direct
`maximum required local step` should not be generalized as an overall
geographic dispersal constraint. Report both the strict bound and the tail
diagnostic. A stronger future result requires independent multi-year
detection effort, verified source/parentage direction, and a process-based
baseline predicting a *held-out* recorded transition without outcome retuning.
