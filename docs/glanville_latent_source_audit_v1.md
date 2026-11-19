# Observed zero ≠ impossible source: Glanville latent-source audit

## Status

Research-only **post-exposure sensitivity**, not new independent Glanville
validation or a fourth EOG-WF endpoint. All 2019+2017 source archive SHA256,
unit conversion, 2007–2012 year/target rules and the 12×4 parent strict-radius
checks are pinned in
[`validation/glanville_latent_source_audit_v1/protocol_v1.json`](../validation/glanville_latent_source_audit_v1/protocol_v1.json).

The previous EOG minimum-radius result was conditional on every `t−1`
recorded-zero site being **disallowed as a source**. That is a defensible
*observed-positive-source-only* scenario but not demonstrated truth.

## Independent survey-method evidence

The [Ojanen et al. (2013) Åland survey methods paper](https://doi.org/10.1002/ece3.733)
reports approximately 0.5–0.6 **larval nest** detection in regular searches.
It also describes repeated surveys: 67 patches in 2008, 180 in 2009, 80 in
2011, plus earlier calibration. In a subset of 2009/2011 patch controls,
approximately 28% of initially recorded empty meadows contained one or
more detected larval nests after re-search.

These measures must not be conflated:
- a larval-nest detection fraction is not the probability of detecting the
  species in an entire patch;
- 28% of a particular revisited initially-empty control group is not the
  regional patch false-negative rate for every year;
- this source audit does **not** fit a detection model, impute true presences
  or assign a probability that a given zero was a hidden occupied patch.

The family reconstruction of Fountain et al. (2017) gives relatedness
and geographic separation, but does not establish the direction of
colonisation or prove a specific recorded-zero site was historically
occupied. No personal identifiers or source-site keys are published.

## New question and estimands

For each frozen target roster `T_t`, keep prior-year observed positive
sources `S^+_{t−1}` and the previous host-gap threshold `delta`.
For two fixed candidate one-hop radii `r in {2,5} km` ask how many
observed target positives can be covered by adding `k=0,1,5,10`
**hypothetical** source patches from recorded zeros at `t−1`.

Candidate source universes are:

- **All eligible zeros:** all actually surveyed `t−1` patches recorded
  zero, with mapped centroid and complete host-plant scores;
- **History-supported zeros:** the strict subset of those zeros with a
  recorded positive in the same patch at `t−2`.

Each has two source identities:

- **Same-site persistence allowed:** a target recorded zero at `t−1`
  may have been missed and remained occupied, so the candidate source
  *is that target itself* (0 km route). It is **not immigration**.
- **Same-site excluded:** a hypothetical source must be at another
  patch, so 0 km self-rescue cannot drive the result.

The fixed host transitions remain `delta=1,3` on max absolute
Plantago/Veronica ordinal scores. We do not optimize thresholds to fit
previous results; the declared radius 2 km is near the earlier
95%-tail scale, and radius 5 km is a broad sensitivity threshold.
Both were specified **after prior responses were known**, so these are
not confirmatory effect cutoffs.

## Computational rules

Each target is covered if at least one t−1 **recorded positive** source
is within `r` and satisfies `delta`. Build a fixed baseline
coverage mask.

For every eligible `t−1` recorded zero, construct the set of previously
uncovered targets that would be geometrically/habitat-compatible if
that zero had in fact been occupied.

Return only *aggregate* figures:

1. **Baseline coverage:** no hypothetical hidden sources.
2. **Optimistic union upper bound:** all eligible zero patches are
   counterfactually treated as sources; this is *not a plausible posterior
   claim*.
3. **Best single new source:** the exact maximum rescue gain after
   exhaustive candidate enumeration.
4. **Greedy additional k=5/10 sources:** a feasible heuristic covering
   at least the reported number, **not** the globally optimal minimum
   number of missed source patches.
5. **Unexplained targets remain recorded positives**. Their identity,
   actual movement and ecological cause remain unknown.

The optional same-site allowed/excluded difference is a direct
**observation vs movement ambiguity diagnostic**: apparent colonisation
can be reconciled by local persistence/false negatives without
dispersal, but only under explicit hypothetical occupancy assumptions.

For computational efficiency, only candidates within the fixed
one-hop radius are considered via deterministic grid buckets, and
the target coverage sets are integer bitsets. No stochastic model is fit.

## Preregistered safeguards

- Re-open the **exact** frozen publisher archives by SHA256 and
  reproduce all **48** original strict radius/unsupported cells on
  12 year × source-policy parent panels **before** reading new
  source-repair score outputs. A mismatch is a scientific STOP.
- Host, radius, latent-candidate pool and same-site monotonicity must
  hold. An optimistic union is **upper**, not expected coverage.
- `t−1` survey *missingness* must not become `t−1` observed zero;
  `t−1` positive sources cannot enter the latent zero pool.
- Neither a genetic family pair nor a changed radius can identify a
  historical source.
- The original closed EOG-WF 3 scored / 31 scientific STOPs / 3
  administrative exclusions do not change.

## Why this is a more useful next step than fitting another movement kernel

The previous `r_0(delta)` and `r_k(delta)` values are conditional
*minimum assumption requirements*. A missing observed source and a
wider movement radius can produce exactly the same recorded t−1 zero →
t positive pattern. Without independent evidence on the true t−1
source occupancy or actual migration, selecting between the two from
the same targets would be circular.

This audit can quantify the **size of that ambiguity**, but cannot
measure which process actually occurred. The next empirical evidence
requirement is the **patch-specific replicate detection history** for
these target years (not an average nest detection rate), or direct
mark–recapture/parentage capable of assigning origin direction. Such
data should be qualified without opening new outcomes or silently
reclassifying historical zeros.

## Reproduce only after independent validation of the protocol

```bash
python -m pytest -q tests/test_glanville_latent_source_audit_v1.py
python benchmarks/glanville_latent_source_audit_v1.py \
  --protocol validation/glanville_latent_source_audit_v1/protocol_v1.json \
  --output results/glanville_latent_source_audit_v1/result.json
```
