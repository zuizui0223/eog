# Toad original release-final distance: nominal translocation-stratum source QC (v3)

**Status:** SOURCE QUALITY DIAGNOSTIC ONLY, **prior `STOP_GEO_UNIT_CONCORDANCE` remains authoritative**. Earlier [pre-outcome geographic anchor experiment](independent_toad_source_anchor_geography_v1.md) has **no scored biological H1**. This is not a new geography×environment×barrier EOG-MRR test.

## Protocol and publisher identity

This *post-exposure* source quality question was frozen **before new nominal-treatment strata were inspected**: [v3 protocol](../validation/independent_toad_geocoordinate_diagnostic_v3/protocol_v3.json), first commit `fc00d0cd5c1c8e68b688ce71ed05618daf110b8f`. The source is exactly [Jreidini & Green Dryad](https://doi.org/10.5061/dryad.x3ffbg7ms) version `198534`; its 18,702-byte CSV is SHA256 `c8ee049eb807af31660ffa28e11f6a66b07a85a5dda4e756bb1b06610edb3f17`, already authenticated in the original work. Original 165 data rows, with exactly duplicated lines removed under the existing frozen rule, left **163** source-QC rows. Per-row biological outcomes and original coordinates are **not exported**.

The [authentic README audit](toad_release_distance_publisher_readme_v1.md) confirms `Translocated distance` is the initial→release displacement nominally rounded to `0,100,250,500` metres. It is *not* `Distance release-final` and cannot be substituted for a movement distance.

We grouped only exact numeric `0,100,250,500` and an explicit **`other_or_missing`** bucket, keeping every original qualified row and the original `max(2m,5% computed)` quality criterion. The `other_or_missing` bucket is **not yet proven** to mean westward, missing data, negative displacement, or a particular error.

## Verified source-QC result

The scientific source-only [GitHub Actions run #44838369315](https://github.com/zuizui0223/eog/actions/runs/44838369315) passed. The aggregate with no individual records is frozen at [source-QC v3 result](../validation/independent_toad_geocoordinate_diagnostic_v3/frozen_aggregate_summary_v3.json). Artifact ID `14678294975`, ZIP SHA256 `a2d595d4647025a49d71a4794cc72ec2d93fa1556cd4eed1d139a509eee0391b`, receipt SHA256 `74cb98c081a05f54c4780c87042c20e273aa4f0fad8765a6d35b5fc4ffe2fa43`.

| Exact original `Translocated distance` class | Original deduplicated rows | Published release-final vs computed RF matches | Published capture-final vs computed IF matches | Release-final absolute residual median |
| --- | ---: | ---: | ---: | ---: |
| 0 m | 61 | **28/61 (45.9%)** | 61/61 | 18.12 m |
| +100 m | 26 | **3/26 (11.5%)** | 26/26 | 222.02 m |
| +250 m | 13 | **1/13 (7.7%)** | 13/13 | 456.22 m |
| +500 m | 11 | **0/11 (0%)** | 11/11 | 927.44 m |
| `other_or_missing` | 52 | **45/52 (86.5%)** | 52/52 | 0.0029 m |
| **All original qualified rows** | **163** | **77/163 (47.2%)** | **163/163** | prior [v2 QC](independent_toad_geocoordinate_diagnostic_v2.md) |

Every zero-class row has coordinate-derived initial→release distance at most 5 m (**61/61**), but the *reported release-final distance column* agrees with the same expected RF geometry in only **28/61**. The three exact positive nominal translocation classes jointly agree in **4/50**, whereas `other_or_missing` agrees in **45/52**. In all groups the `capture-final` channel remains essentially perfect.

**Interpretation:** These large, metadata-dependent differences undermine a uniform unit-conversion explanation. The increasing positive-class absolute residual medians (**222, 456, 927 m**) are consistent with the *possibility* of signed rather than absolute movement distance values, but the present v3 **did not inspect the numerical sign** of the reported column, the sign of any nonstandard nominal displacement, or the `Translocated direction` E/W label. Thus **a signed-direction encoding explanation is a new testable hypothesis, not a result**.

The source READMEs and published article describe distances from location pairs in meters, but do not spell out a signed movement metric for this particular reported CSV field. The output cannot retrospectively alter the interpretation of original stopped biological H1.

## Failure and repair record

The first test workflow [#44838294783](https://github.com/zuizui0223/eog/actions/runs/44838294783) failed solely because a test tried to treat `nan` as invalid, whereas the **unchanged original frozen missing-value contract explicitly allows it**. The new synthetic test was corrected to classify `nan` as `other_or_missing`, while unrecognized text and infinity remain a STOP. No source rows, thresholds, categories or analysis code were changed. The successful later workflow is the authoritative receipt.

## Next diagnostic (not a new ecology result)

Freeze and test a **source-only signed-direction hypothesis**: whether `Translocated distance` has negative numerical levels `−100,−250,−500` associated with `Translocated direction=W`, and whether the *published* `Distance release-final (m)` is a signed east/west Euclidean displacement that agrees with `sign(F_E−R_E)×||F−R||`. This must be a **separate explicitly post-exposure diagnostic** and retain all originally failing cases and the original STOP regardless of any match.

**Scientific boundary:** No individual homing, dispersal, causal response, source-origin identification or new EOG-WF predictive endpoint has been computed. This exploratory data-quality finding is not independent external support for natural EOG three-axis minimum required relaxation. Existing frozen **3 scored /31 scientific STOP /3 administrative exclusions** remain unchanged.
