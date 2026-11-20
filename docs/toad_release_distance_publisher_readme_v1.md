# Original Dryad toad README vs archived release–final distance: documentation audit

**Status:** authentic source-document inspection completed; **original biological science STOP stays closed**. This audit does not re-run the original toad movement experiment, decode any of its 165 CSV records, or qualify a geographic/3-axis EOG-MRR validation.

## Progress: publisher-authenticated README obtained directly

The pre-retrieval [document-only protocol](../validation/toad_release_distance_publisher_readme_v1/protocol_v1.json) was committed **before inspecting README text** at `430b91f982522c69925c165d4ab40bc25bf8cf0b`. The source-only [GitHub Actions run 44837654149](https://github.com/zuizui0223/eog/actions/runs/44837654149) succeeded, verified the original Dryad version `198534` ZIP through the already frozen publisher redirect host, verified the CSV companion checksum **without decoding its rows**, and extracted only the public RTF README.

Published DOI: [Jreidini & Green 2022 (Dryad)](https://doi.org/10.5061/dryad.x3ffbg7ms). Public README `README_file.rtf`: **2,102 bytes**; SHA-256 `3d7b240bf323bb19fe32e57d99b8029e212d1da15d85c02b457a1d74053b3c5c`. Extracted text SHA-256 `15a1ef1166ed876c368d87ea15c6c0f0ad9063a63f47ea693b3cc907a73fac52`. The official companion CSV was verified as **18,702 bytes**, SHA-256 `c8ee049eb807af31660ffa28e11f6a66b07a85a5dda4e756bb1b06610edb3f17`. Document-only receipt SHA256 `e00e51749e00aa820246787ff35382a5180cf9c3b0c615fcedf661f5ff477dfe`. GitHub Actions artifact `14678418773`, ZIP digest `b847d43f7991387296c0dae64300b372105f2e50a9ee91902328825772e72718`.

Machine-readable source-provenance and semantic verdict: [frozen summary](../validation/toad_release_distance_publisher_readme_v1/frozen_summary_v1.json).

## What the README actually says

| Publisher README variable | Grounded original publisher meaning | Consequence for QC |
| --- | --- | --- |
| `Initial Easting and Northing` | UTM coordinates at the first encounter before experimental translocation | This is the pre-manipulation capture anchor `I` |
| `Released Easting and Northing` | UTM coordinates at the released location after translocation | This is the post-manipulation release anchor `R` |
| `Final Easting and Northing` | UTM coordinates at the later encounter after translocation/homing | This is the later recapture anchor `F` |
| `Translocated distance` | Distance between initial and released UTM positions, **rounded** to the experimental classes 0, 100, 250 or 500 m | **Different field** from release→final; do not substitute its rounded class for a continuous Euclidean distance |
| `Distance release-final or capture-final` | Distances **in meters** using corresponding/appropriate UTM coordinates | The README does **not** give a separate explicit formula or documented replacement rule for each of the two published distance columns |
| `Date of re-encounter` | Normally on the following day after first capture | Not a verified exact elapsed movement interval or founder clock |

The published article [Jreidini & Green, *Herpetologica* (2022)](https://doi.org/10.1655/Herpetologica-D-21-00031) states that the capture, release and final positions were recorded by GNSS as NAD83 UTM and that post-translocation movement distance was calculated between release and final points using planar Euclidean distances. This *independently published methods description* is consistent with the README's anchor labels, but not an independent quality verification of every archived data row.

**Critical result: the authenticated README gives no explicit control-specific formula, alternative unit conversion, rounding of release→final to nominal displacement classes, or correction step capable of resolving the earlier source-data discrepancy.** Absence of an explanation in the README does not prove whether the original release-coordinate entries, derived distances, or data dictionary are erroneous. Do not guess which field is wrong.

## The original numerical discrepancy remains

The **frozen earlier source-data diagnostic** [v2](independent_toad_geocoordinate_diagnostic_v2.md) compared two original reported distance fields against all three candidate planar pairs and predeclared scale multipliers. Of the 165 published rows, 163 complete nonduplicate rows qualified for numerical QC.

| Existing published distance | Appropriate original UTM pair | Rows within original 95%-concordance tolerance | Absolute residual median / q90 |
| --- | --- | ---: | ---: |
| `Distance capture-final (m)` | `I→F` | **163 / 163 = 100%** | 0.0024 m / 0.0047 m |
| `Distance release-final (m)` | `R→F` | **77 / 163 = 47.24%** | 22.00 m / 470.57 m |

The two other coordinate pairs and the predeclared scales `0.001`, `1` and `1000` do not restore the release→final column to the original 95% quality criterion. **The cause of its 86 discrepant rows is unresolved after inspection of the authentic README and article methods.**

## Research inference boundary and actual next gate

- The original [pre-outcome toad test](independent_toad_source_anchor_geography_v1.md) ended at `STOP_GEO_UNIT_CONCORDANCE`; original H1 was **NOT SCORED**, and stays so. README retrieval is not a route to retrospectively re-score it.
- The geographically defined experimental release point is **not** a natural founding source. Neither toad experiment nor the source-document audit can validate ecological geographic×environment×barrier Pareto MRR.
- A narrowly scoped post-STOP QC partition by **pre-existing experimental treatment** (zero translocation versus positive translocation classes) can test *which subset of publisher rows fails the original release→final distance concordance*, provided it is specified before running that diagnostic and includes **all rows**, not selected by residual sign. It must not re-estimate behavioral effect size, drop failed cases or replace the original source definition.
- If publisher documentation still cannot resolve the discrepancy, an author/data-curator clarification of whether `Released Easting/Northing` and `Distance release-final` use the same stored coordinate snapshot is the direct missing input.

EOG-WF original closed denominator remains **3 scored / 31 scientific STOP / 3 administrative exclusions**. No fourth endpoint or new biological movement finding is recorded here.
