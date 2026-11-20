# Original toad `release-final` distance uses an east/west signed encoding — post-STOP source QC v4

**Status:** A post-exposure **source-data encoding** explanation was verified against the exact original publisher CSV; the original scientifically preregistered toad movement H1 remains **`STOP_GEO_UNIT_CONCORDANCE` / NOT_SCORED**, and **no ecological claim has been promoted**.

## Why a signed-source-field audit was justified

The original [geographic source-anchor experiment](independent_toad_source_anchor_geography_v1.md) stopped at `STOP_GEO_UNIT_CONCORDANCE`. [First post-STOP source-quality audit](independent_toad_geocoordinate_diagnostic_v2.md) found `capture-final` Euclidean distance **163/163** consistent, but `release-final` Euclidean **77/163**. The [SHA-verified original README](toad_release_distance_publisher_readme_v1.md) defined capture/release/final UTM positions and metric distances without documenting a signed distance convention.

A subsequent [treatment-stratified source QC](independent_toad_geocoordinate_treatment_qc_v3.md), conducted on the **same original source**, showed +100/+250/+500 nominal eastward classes had only **4/50** unsigned release-final matches, while the `other_or_missing` class had **45/52**. This motivated—but did not prospectively establish—a **signed distance field** hypothesis.

## Frozen v4 diagnostic (before testing signs)

The first branch commit `f6c7004378d59646f28e69e60b20edeb106e31c1` froze [signed-field protocol v4](../validation/independent_toad_geocoordinate_diagnostic_v4/protocol_v4.json) **before any v4 raw signed-field checks**. All 163 previously eligible nonduplicate source rows, original publisher SHA-256/byte count, original `max(2m,5%×distance)` tolerance, and both `77/163` and `163/163` source QC control counts were held unchanged. Nothing was removed on the basis of failed or successful signed matches.

The predeclared alternatives included (a) the original nonnegative Euclidean distance `r`; (b) **east-positive / west-negative signed Euclidean distance** `sign(ΔE)×r`, where `ΔE = Final_Easting − Released_Easting`; (c) the opposite sign; (d) the signed Easting component `±ΔE`; and (e) signed Euclidean distance based on the publisher's own `Direction moved` E/W label, both sign conventions. **All seven predeclared candidate results remain visible in the frozen receipt**, not only the best one.

## Result: published `Distance release-final` is signed by East/West movement

[GitHub Actions run #44838880057](https://github.com/zuizui0223/eog/actions/runs/44838880057) completed the synthetic guards and SHA-pinned source QC successfully. Full frozen aggregate: [v4 source result](../validation/independent_toad_geocoordinate_diagnostic_v4/frozen_aggregate_summary_v4.json); artifact ID `14680295214`, ZIP digest `13a9fc0db07cb13631fa4fc0787b53710159acbeb4a1df3329b6e09987c5e5d3`.

| Source field interpretation (release→final) | Numeric matches under original frozen tolerance | Claim |
| --- | ---: | --- |
| Original nonnegative `sqrt(ΔE²+ΔN²)` | **77/163 (47.2%)** | The original source quality STOP is reproduced |
| **East-positive, west-negative `sign(ΔE)×sqrt(ΔE²+ΔN²)`** | **163/163 (100%)** | Strong post-exposure diagnostic evidence of signed Euclidean encoding |
| Same signed radial distance using `Direction moved=E/W` | **163/163 (100%)** | Publisher's categorical movement label agrees with signed coordinate direction |
| Easting component `ΔE` alone | **151/163 (92.6%)** | Not the correct full radial distance metric under the original tolerance |
| Reversed radial signed convention | **0/163** | Wrong orientation |

All 163 eligible rows have a signed movement direction matching the eastward/westward sign of their original UTM Easting difference: **77 east-positive**, **86 west-negative**. Thus exactly the **86** rows that previously mismatched the unsigned positive distance are the west-negative observations. `Distance capture-final` remains **163/163** consistent with **unsigned** Euclidean initial capture→final location.

The previously mixed `other_or_missing` set of 52 records contains **24 at −100m, 13 at −250m, and 15 at −500m**, all labelled `Translocated direction=W`. The positive nominal classes contain **26 at +100m, 13 at +250m, and 11 at +500m**, all `Translocated direction=E`. There are **61** zero-distance controls, with eastward movement 28 and westward movement 33. There are **no remaining other/missing nominal signed classes**. The original 165 source rows included two byte-identical copies that the frozen parent dedup rule removed before QC, hence 163 qualified.

**This is a source-field encoding finding, not a biological homing effect.** The match certifies agreement **within the original 2m/5% source quality tolerance**, not equality at infinite numeric precision, and the README itself does not explicitly state the signed convention. It is identified from the original source-data values and an independent UTM movement-direction consistency check. It was tested *after* the initial discrepancy was seen; it is **not** an independent held-out validation of ecology.

## What changed and what absolutely did not

**Changed / resolved:** The original difference is consistent with comparing a signed east–west Euclidean movement field against an unsigned Euclidean magnitude. It is not necessary to allege that the underlying UTM locations were wrong or that global CRS units are inconsistent.

**Unchanged:** The original preregistered `STOP_GEO_UNIT_CONCORDANCE` and unscored source-anchor H1 stay frozen. This independent publication does **not** become a fourth EOG-WF endpoint. These data are from *experimental release and recapture*, not the natural founding-source process or three-axis geography/environment/barrier EOG-MRR. The seven diagnostic formula comparisons do not retroactively select a new H1 model or support a novel empirical generality.

Any genuine new ecological test must use **prospective independent source definitions and movement observations** with a protocol frozen before those outcomes are opened. The present v4 makes source provenance much clearer, but its positive signed match is strictly a post-exposure data-quality result.

## Reproduce from the original source (QC-only)

- [Source-locked diagnostic protocol](../validation/independent_toad_geocoordinate_diagnostic_v4/protocol_v4.json)
- [Signed source-field QC code](../benchmarks/independent_toad_release_distance_sign_qc_v4.py)
- [Offline synthetic controls](../tests/test_independent_toad_release_distance_sign_qc_v4.py)
- [Dedicated official-source GitHub Actions](../.github/workflows/eog-toad-release-distance-sign-qc-v4.yml)
- [Frozen aggregate result and source receipts](../validation/independent_toad_geocoordinate_diagnostic_v4/frozen_aggregate_summary_v4.json)

```bash
python -m pytest -q tests/test_independent_toad_release_distance_sign_qc_v4.py
python -m benchmarks.independent_toad_release_distance_sign_qc_v4 \
  --protocol validation/independent_toad_geocoordinate_diagnostic_v4/protocol_v4.json \
  --output results/independent_toad_geocoordinate_diagnostic_v4/source_sign_receipt.json
```

**EOG-WF closure unchanged: 3 scored / 31 scientific STOP / 3 administrative exclusions.**
