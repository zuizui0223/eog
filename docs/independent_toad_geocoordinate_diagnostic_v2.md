# Independent toad coordinate-source quality diagnostic v2

> **実行済み（2026-11-20、事後QC）:** [専用Actions #44759696421](https://github.com/zuizui0223/eog/actions/runs/44759696421) は成功し、[18セルの凍結集計・ソースSHA・STOP証跡](../validation/independent_toad_geocoordinate_diagnostic_v2/frozen_aggregate_summary_v2.json) を保存した。**元の `STOP_GEO_UNIT_CONCORDANCE` とH1未評価は不変。** 原CSV165行、完全重複除去後163行、82個体ID（個体情報は保存していない）。
 
| 元の報告距離 | 凍結した座標ペア | 原95%閾値での一致 | 残差中央値 / q90 |
| --- | --- | ---: | ---: |
| `Distance capture-final (m)` | initial→final | **163/163 (100%)** | 0.0024m / 0.0047m |
| `Distance release-final (m)` | release→final | **77/163 (47.24%)** | 22.00m / 470.57m |

どの事前列挙済みの代替ペア・倍率も、release→final報告列で95%以上の一致を回復しない。**単純な全体単位倍率・距離列入れ替えだけではない**。元データのrelease地点と報告距離の関係は不明であり、最も適合した設定を結果に合わせて選び直すことはしない。専用CIのoriginal-source算術STOPを再現しているが、生態学的結果ではない。


**Status: Post-exposure source-only diagnosis, original scientific STOP retained.** This is *not* a second attempt to obtain a favorable ecological result. The [original independently frozen toad analysis](independent_toad_source_anchor_geography_v1.md) ended as `STOP_GEO_UNIT_CONCORDANCE` ([Actions #44756566395](https://github.com/zuizui0223/eog/actions/runs/44756566395)), so its preregistered directional H1 was **not scored**. The prior scientific STOP remains authoritative.

## Why this step is needed

The original file is independently published [Jreidini & Green 2022 Dryad](https://doi.org/10.5061/dryad.x3ffbg7ms), official version `198534`; the published `Jreidini_and_Green_homing_toads_2021.csv` is **18,702 bytes / 165 data rows**, SHA256 `c8ee049eb807af31660ffa28e11f6a66b07a85a5dda4e756bb1b06610edb3f17`. The original scientifically frozen comparison required **≥95%** of rows with reported distance values to agree within `max(2m,5% of computed)` with Euclidean distances from the released→final or initial→final coordinate pairs. It failed.

We must not rerun the H1 biological outcome, alter the unit, rename columns, exclude mismatch rows or silently choose whichever distance convention looks best after seeing data. This new work only clarifies **which numerical source-data comparisons are consistent or inconsistent**.

## Protocol frozen before diagnostic values

First branch commit [v2 QC protocol](../validation/independent_toad_geocoordinate_diagnostic_v2/protocol_v2.json) froze the original publisher and result identifiers, all comparison pairs and scale candidates, sample eligibility, source SHA/transport rules, and full output schema *before* the present diagnostic computation.

**For each originally eligible re-encounter row** with an ID, nonmissing date, 6 coordinate fields and at least one reported distance, compute three planar Euclidean distances:

```text
IR = ||initial capture -> experimentally released||
RF = ||experimental release -> final recapture||
IF = ||initial capture -> final recapture||
```

Compare each of the 2 originally reported distance fields against all 3 geometric pairs and **all three predetermined coordinate multipliers (0.001, 1, 1000)**, a fixed **18-cell QC matrix**. At every cell report only number compared, matches under the original tolerance, match fraction, median absolute residual and q90 residual. The fixed original cells are `(release-final, RF, 1)` and `(capture-final, IF, 1)`.

**These alternatives are not scientific fixes.** An apparently better matching pair/scale may indicate a data dictionary difference, original rounding/transformation, source coding issue or some other discrepancy. It cannot retroactively authorize source-anchor biological scoring, even if some particular diagnostic cell meets 95%.

## Source and privacy controls

Use the exact [source v2 official Dryad transfer](../validation/independent_movement_source_gate_v2/protocol_v2.json), including the previously attested publisher redirect host, version and SHA256; no alternate downloads, data substitute or unverified redirect. First validate ZIP member checksums and 165 original rows. Do not change the parent v1 analysis/protocol/tests/results.

All original individual records, IDs, capture/recapture coordinates, exact dates and per-row comparisons stay inside the short-lived CI runner. Only aggregate QC matrix and counts enter the artifact. No phenotype, behavior, direction of homing, dispersal limit, mechanism, causal effect, or EOG-WF predictive performance is scored.

The final allowed status is `POST_EXPOSURE_SOURCE_QC_ONLY_RETAINS_ORIGINAL_SCIENTIFIC_STOP` only if the original STOP can be reproduced under its original two cells. If it cannot, report `STOP_DIAGNOSTIC_CANNOT_REPRODUCE_ORIGINAL_SCIENTIFIC_STOP` and preserve the original STOP regardless.

## Outputs and next inferential boundary

- [Frozen protocol](../validation/independent_toad_geocoordinate_diagnostic_v2/protocol_v2.json)
- [Aggregate-only QC implementation](../benchmarks/independent_toad_geo_source_quality_diagnostic_v2.py)
- [Offline synthetic validation](../tests/test_independent_toad_geo_source_quality_diagnostic_v2.py)
- [Single-source-run workflow](../.github/workflows/eog-independent-toad-coordinate-qc-v2.yml)

**Claim boundary:** A scientific source-quality STOP can be diagnosed but not overturned by post-outcome selection. Any future independently validated geographic-only test must be independently registered and use verified source coordinate meanings *before* outcome scoring; the current independent experiment cannot confirm EOG's geographical×environmental×barrier MRR. Original EOG-WF frozen denominator **3 scored / 31 scientific STOP / 3 administrative exclusions** is unchanged.
