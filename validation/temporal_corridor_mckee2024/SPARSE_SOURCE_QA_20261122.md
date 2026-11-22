# McKee 2024 public sparse 12-hour GPS: source qualification and independent QC

**Evidence date:** 2026-11-22. **Outcome:** `SOURCE_QC_STOP__TIME_PRECISION_AND_PUBLISHER_CRS_CONFLICT`. No EOG prediction has been fit or scored.

## 1. Exact source identity and no-holdout rule

User-supplied `GPS12hrs_Locs.zip`: **1,539,661 bytes**, independent local SHA-256 `556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4`, exactly matching the file ID 3334125, Dryad numeric version 305836, precommitted [Gate0 source receipt](gate0_publisher_metadata_frozen_v1.json).

No 2h data were downloaded, read or scored. No raw coordinates, exact timestamps, animal identifiers, geometry records or model outputs were published to GitHub. Input ZIP remains outside repository version control.

Historical publisher file-stream 403s in [issue #743](https://github.com/zuizui0223/eog/issues/743) were *transport-method* failures. User-provided, checksum-verified bytes resolve this specific acquisition problem, but do NOT cure source-data semantics.

## 2. Shapefile structure (pre-row frozen Gate1)

The ZIP contains exactly one basename with `.shp`, `.shx`, `.dbf`, `.prj`. Shape type Point; all 28,953 SHX index entries equal 28,953 DBF declared records. Declared PRJ parses as EPSG:3742 (NAD83(HARN) / UTM zone 12N). The physical DBF column names are `State`, `Herd`, `SpcsCmm`, `SpcsScn`, `AID`, `SeasnYr`, `Season`, `Year`, `Timstmp`, `UTM_E`, `UTM_N`; longer publisher names were shortened by the shapefile/DBF format.

The [Gate1 protocol](gate1_sparse_zip_schema_protocol_v1.json) preceded member/header access. The [schema receipt](gate1_sparse_zip_schema_receipt_v1.json) preserves real physical names and the explicit initial alias review requirement. `Timestamp` → `Timstmp`, `SeasonYr` → `SeasnYr` were explicitly pinned in the separate [pre-row Gate2 QC contract](gate2_sparse_only_aggregate_qc_protocol_v1.json).

## 3. Sparse-only aggregate QC (pre-row contract frozen)

The entire **12h input** has 28,953 active records and zero missing values across the 11 physical fields. Four public herds: AtlanticRim 17,248; ClarksFork 3,132; Dubois 4,624; Jackson 3,949. Species totals: MuleDeer 25,004; Elk 3,949. `Herd×AID` has 144 distinct combinations. The analysis unit must be individual × migration sequence (and herd as a higher dependence cluster), **not GPS fix**.

The initial exact time-format parser recognized 18,118 / 28,953 (62.6%), because the other 10,835 strings are **date-only** `YYYY-MM-DD` rather than full `YYYY-MM-DD HH:MM:SS`. All 28,953 numeric UTM_E values were negative and outside the prespecified 0–1,000,000 easting range. The [original Stage2 receipt](gate2_sparse_only_aggregate_qc_receipt_v1.json) therefore records STOP without changing thresholds.

## 4. Explicit post-STOP source diagnostics, not retroactive success

The [format/coordinate diagnostic contract](post_stop_field_diagnostic_protocol_v1.json) was committed before rereading records. It established that all unparsed records have the single date-only syntax, and both DBF aggregate coordinate ranges and SHP header extents are similar, with a negative first coordinate (-1,180,000 to -910,000 when rounded to 10km).

The [independent hypotheses](post_stop_semantics_hypotheses_v1.json) fixed two incompatible treatments for date-only values before comparison. Under a **hypothetical midnight** interpretation, 27,678 / 28,532 (97.0%) within-group consecutive gaps were in 10–14 hours with zero duplicate times. Under a hypothetical **noon** interpretation only 6,334 / 28,532 (22.2%) fell in that band, with 10,421 duplicate time pairs. The actual timed records occur at hours 00, 01, 12 and 13. This strongly favors midnight as a *source interpretation*, independently consistent with the published McKee et al. (2024) description of 12-hour fixes around midnight/01:00 and noon/13:00 Mountain Time (https://doi.org/10.1002/ecs2.4983). It does **not** establish daylight-saving offsets or license unreported conversion to UTC.

The predeclared CRS comparison on the **rounded aggregate bounding-box center** found:

| CRS applied to the existing coordinates | Coarse center (lon, lat) |
|---|---|
| Publisher/PRJ EPSG:3742 | (-126°, 20°) |
| Candidate EPSG:5070 | (-109°, 43°) |
| ESRI:102003 | (-112°, 57°) |
| EPSG:3857 | (-9°, 20°) |

The distinct [pre-geometry-read protocol](post_stop_crs_geometry_protocol_v1.json) then fixed Wyoming+buffer bounds (lon -114.5 to -102, lat 39 to 47) and those four CRSs **before** the first SHP point record was inspected. Its [receipt](post_stop_crs_geometry_receipt_v1.json) confirms that point geometries match physical DBF UTM_E/N values within 1e-6 for **28,953 / 28,953** records. Under EPSG:5070, **28,953 / 28,953** fall in the predeclared region; under the declared EPSG:3742 and the two other candidates, **0 / 28,953** do.

**Diagnosis:** The official Dryad README/PRJ declares EPSG:3742 (https://doi.org/10.5061/dryad.15dv41p51), but the actual coordinates are geographically consistent with **EPSG:5070**, not with the declared projection. This is powerful independent input-domain evidence for CRS metadata mislabeling, **not proof that EPSG:5070 was the authors' intended CRS**. No source PRJ was overwritten; no new coordinate interpretation was silently promoted.

## 5. Binding scientific stop and next data contract

Until independent source documentation or a verified external spatial reference resolves the coordinate interpretation, source-dependent ecological geometry claims and corridor comparisons remain **on HOLD**. The posted source files cannot identify the actual path between GPS fixes. A positive location is not proof of the specific route or time spent between fixes; a missing fix is not a true absence.

Next allowed work is source-provenance clarification (including author contact or independent trusted spatial reference), plus an **outcome-blind 12h-only prototype** that explicitly labels EPSG:5070 and midnight as *conditional input scenarios* rather than ground truth. No withheld 2h source should be opened before a complete frozen external evaluation protocol fixes the actual grid, source/transition worlds, uncertainty buffers, spatial denominator, strong comparator, individual/season split, accuracy–area metrics, and STOP rules.

The original EOG-WF empirical results remain **3 scored / 31 scientific STOP / 3 administrative exclusions** (2 favorable, 1 adverse). This source-QC audit contributes **zero additional independent forecast endpoints**.

## Canonical non-record receipts

- [Gate1 archive schema](gate1_sparse_zip_schema_receipt_v1.json)
- [Gate2 original QC STOP](gate2_sparse_only_aggregate_qc_receipt_v1.json)
- [Post-STOP time/coordinate patterns](post_stop_field_diagnostic_receipt_v1.json)
- [Midnight/noon and candidate-CRS comparison](post_stop_semantics_hypothesis_receipt_v1.json)
- [Full 12h geometry vs attribute consistency](post_stop_crs_geometry_receipt_v1.json)
