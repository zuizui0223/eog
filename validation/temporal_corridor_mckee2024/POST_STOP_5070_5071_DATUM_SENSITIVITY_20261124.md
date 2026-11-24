# McKee 2024: EPSG:5070 vs EPSG:5071 datum/grid sensitivity (2026-11-24)

## Question and evidence level

The [existing source-QC STOP](SPARSE_SOURCE_QA_20261122.md) and [official WGFD Baggs geographic locator](POST_STOP_WGFD_CRS_LOCATOR_20261124.md) established that the original source-declared EPSG:3742 conflicts with the 12h GPS coordinates and that the Albers-family alternatives EPSG:5070 and EPSG:5071 both align with WGFD geography.

This new **input-only** test asks: using the already declared EPSG:5070 and EPSG:5071 alternatives, do original sparse GPS positions and predeclared grid cells materially differ? The protocol, original SHA and grid origin were [committed before new point transformation](post_stop_5070_5071_datum_grid_sensitivity_protocol_v1.json) at fa92cedd60378e48b477aa8b022d20d635c07423. No dense 2h GPS, DBF records, animal ID, timestamp, actual trajectory or model score was read.

## Major technical caution: missing geodetic transformation grids

The local offline pyproj 3.7.2 / PROJ 9.5.1 environment reports **TransformerGroup.best_available = false** for EPSG:5070 → EPSG:5071: the preferred NAD83→NAD83(HARN) datum grid us_noaa_nadcon5_nad83_1986_nad83_harn_conus.tif is absent. Its only available operation is a **ballpark geographic offset**, with no certified accuracy. Network downloads were disabled.

The following numbers describe **only the available offline transformation**, NOT the true maximum spatial datum uncertainty, GPS accuracy, or author intent. See [pyproj grids documentation](https://pyproj4.github.io/pyproj/stable/transformation_grids.html) and [EPSG:5070](https://epsg.io/5070) / [EPSG:5071](https://epsg.io/5071).

## Source-only conditional results

All 28,953 original 12-hour GPS Point records were processed, using the same raw XY under each candidate input CRS, then transformed to WGS84 and EPSG:3857 for comparison.

| Offline available transformation position difference | Minimum | Median | P95 | Maximum |
|---|---:|---:|---:|---:|
| WGS84 geodesic (m) | 1.148 | **1.156** | 1.197 | **1.201** |
| EPSG:3857 projected metres | 1.520 | **1.541** | 1.683 | **1.695** |

The spatial grid origin was frozen as the official WGFD full rectangle lower-left corner in EPSG:3857: X = -12021622.7691, Y = 5012625.0685. Both CRS candidate projections were assigned to floor((X-origin_X)/cell_width), floor((Y-origin_Y)/cell_width). This is one *fixed grid*, not an origin sweep.

| Cell width | Same cell in both CRS interpretations | Different cell |
|---|---:|---:|
| 100 m | 28,351 / 28,953 (97.92%) | 602 |
| 250 m | 28,720 / 28,953 (99.20%) | 233 |
| 500 m | 28,839 / 28,953 (99.61%) | 114 |
| 1,000 m | 28,891 / 28,953 (99.79%) | 62 |
| 5,000 m | 28,945 / 28,953 (99.97%) | 8 |

Cell stability **depends on the specified grid origin and the incomplete offline datum transform**. Do not generalize these percentages to all grids or exact datum conversion. By contrast, Euclidean pairwise distances in the same original raw planar XY are trivially identical no matter how those coordinates are *labelled*; this algebraic invariant does not validate the source CRS or environmental barrier overlays.

## Exact claim boundary and next method step

- EOG may preserve **both candidate CRS interpretations as distinct conditional input worlds** in an *input-only* representational audit. A common cell assignment is robust solely relative to the frozen two candidates, chosen grid origin, and available fallback transform; differing cell assignment is unresolved under those assumptions.
- The data author's original projection remains unknown. The Dryad README/PRJ still declares EPSG:3742; no correction, alternate datum, or acceptance of EPSG:5070/5071 as unique truth is authorized.
- Missing accurate datum grids prevent us from calling the 1.201m observed fallback difference a certified true uncertainty bound. Documenting this failure is more defensible than silently assuming centimetre-level datum equivalence.
- The separate **10,835 date-only timestamp** source ambiguity is unchanged, so full time-respecting ecological-world construction and confirmatory external score remain on HOLD.
- No dense 2-hour GPS was opened; no EOG model fit, ecological prediction, migration-history claim or fourth EOG-WF endpoint was produced. Original EOG-WF denominator remains 3 scored / 31 science STOP / 3 admin exclusions.

Raw coordinates and individual IDs are not committed. Reproduce from the exact-SHA local 12-hour ZIP via [the opt-in script](replay_post_stop_5070_5071_grid_sensitivity.py) and inspect the [aggregate receipt](post_stop_5070_5071_datum_grid_sensitivity_receipt_v1.json).
