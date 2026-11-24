# McKee 2024: historical Migration Mapper exporter provenance (2026-11-24)

## Decision

**An R-compatible midnight-string-shortening mechanism was present in public Migration Mapper code *before* the July 2024 Dryad release, but the exporter that actually produced the archived GPS12hrs_Locs.zip remains unidentified.** Two export changes previously cited from current code were in fact committed **after the dataset release**, and should not be presented as causes of the original data.

This is a chronology/source-provenance review of dated immutable GitHub commits and an existing SHA-verified original 12h source. It is NOT a novel movement result, an independently confirmed R version, or permission to open the withheld 2h reference.

## Primary chronology

| Date (UTC where supplied) | Direct archival evidence | What it establishes |
|---|---|---|
| **Aug 2023** | [R-devel: R 4.3.1 versus 4.2.3 as.character.POSIXt](https://stat.ethz.ch/pipermail/r-devel/2023-August/082814.html) | R 4.3's character serialization can omit exactly midnight 00:00:00 while preserving non-midnight clock strings |
| **Mar 5, 2024** | [Migration Mapper version-3.1 merge, immutable commit affaea1e](https://github.com/jmerkle1/Migration-Mapper/commit/affaea1ee55830638e20fe712908de188214e2ac) and [source file at that SHA](https://github.com/jmerkle1/Migration-Mapper/blob/affaea1ee55830638e20fe712908de188214e2ac/app3_sequenceWriting/scripts/app3_calcSequences.R) | App3 **already called as.character on the date** before writing sequences as ESRI Shapefiles; its coordinate path used lon/lat + masterCrs4326, not projected XY |
| **Mar 25, 2024** | [file export fix 87b00491](https://github.com/jmerkle1/Migration-Mapper/commit/87b00491eef9d753703515cb9f1de903d152a692) | Related app1 data-cleaning export began making Point geometry from numeric x/y while (initially) assigning masterCrs4326 |
| **Mar 26, 2024** | [export errors 6d45fb51](https://github.com/jmerkle1/Migration-Mapper/commit/6d45fb5126264f72735c7c26d7b7e246a3490a49) | App1 changed that x/y coordinate-label argument from masterCrs4326 to masterCrs. Shows a *historical code correction for CRS metadata assignment*, NOT the source of the Dryad Albers-vs-UTM discrepancy |
| **Jul 18, 2024** | [McKee 2024 Dryad dataset original publication](https://datadryad.org/dataset/doi%3A10.5061/dryad.15dv41p51) | Original archived GPS12hrs_Locs.zip existed by this date; this is the causal chronology cutoff |
| **Aug 6, 2024** | [data as character before exporting, dc32cf36](https://github.com/jmerkle1/Migration-Mapper/commit/dc32cf3618c079057d067783cf9c8bbf3592dcb5) | The specific **app1** date-column as.character export statement was added **after** Dryad publication. It cannot by itself be the documented prepublication file-generation step |
| **Sep 6, 2024** | [Sequence files are now written in UTM meters, 4786f018](https://github.com/jmerkle1/Migration-Mapper/commit/4786f018b8283f030b9092275d7399499365b8ce) | The **app3** exporter switched from lon/lat + masterCrs4326 to x/y + masterCrs **after** Dryad publication. The current projected XY sequence code is not the March prepublication version |

The full immutable commit SHA, date, touched filename and source links for each event are retained in the [machine-readable history receipt](post_stop_historical_mapper_lineage_receipt_v1.json). These are GitHub public commit **creation timestamps** in the connector, not an independently retrieved laboratory execution log.

## What the original 2024 files support directly

The exact sparse original in this session is 1,539,661 bytes with SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4, checked again before the archival comparison. Its DBF contains **28,953 original records** and physical fields State, Herd, SpcsCmm, SpcsScn, AID, SeasnYr, Season, Year, Timstmp, UTM_E, UTM_N.

Among timestamp strings, **10,835 are date-only**; **18,118 are complete**; exactly **zero** of those complete strings is midnight 00:00:00; **379** complete strings are other times within 00-hour. This independently reproduces the pattern in [PR #755](POST_STOP_MIDNIGHT_SERIALIZATION_PROVENANCE_20261124.md).

The archived Dryad README says the researchers used **Migration Mapper to identify the spring and fall migration period boundaries**, *then* subsampled 2h observations to 12h. It links the CalcBBMM.R procedure for **BBMM fitting**. Importantly, the README does **not** establish that Migration Mapper's generic app1 or app3 Shapefile export exactly generated the named original ZIP or its particular schema.

The March 5 app3 file does contain as.character(date) (direct source mechanism), but produces an output object with fields like id, bioYearFull, date, id_yrbio_season, lon, lat and **geographic lon/lat geometry**, whereas the Dryad ZIP has the named 11-column source schema and projected XY geometry. The two are **not identical output formats**. The current app3 projected x/y form became publicly present only in September; it also has different schema fields.

Therefore, the strongest currently supported statement is: an applicable **code-level mechanism** existed in the public software before release, and the archived data are **consistent** with the mechanism. The **actual writer and actual R runtime version remain unknown**. This does not prove whether 10,835 dates are precisely midnight or truly clock-truncated missing values.

## Separate CRS implication

The March app1 commits demonstrate that the related software had an x/y versus coordinate-reference-assignment bug or correction in March 2024. But the exact archived Dryad geometry (strongly aligned with Albers EPSG:5070/5071 under independent geographic checks) and declared .prj/README EPSG:3742 are **not linked by evidence to that specific bug**. Likewise, March app3's EPSG4326 lon/lat writer does not explain the projected source geometry, and September app3's x/y writer postdates July release.

Thus the root cause of the original CRS mismatch is **still unresolved**. Do not rewrite the PRJ, assume EPSG:5070 over 5071, or certify author projection intent.

## Methodology and explicit next gate

This note corrects the **strength** of the previous source-provenance claim, not its source timestamp counts and not any of the conditional T0/T1/H3 mathematical calculations:

- Valid: R 4.3 behavior and archived format pattern support an exact-midnight serialization hypothesis; source-clock input worlds require consistent assignments; DST handling matters under the alternative IANA interpretation.
- Unverified: original 2024 exporter script, R version, true interpretation of date-only values, fixed MST versus civil Mountain DST, author-intended native source XY CRS and datum transform lineage.
- False attribution to avoid: that the **August app1 as.character addition** or **September app3 projected export revision** actually created the original July ZIP. Their commits were later.
- This dataset remains a **source-QC STOP** for confirmatory spatial/temporal scoring. The 2h heldout ZIP remains unopened, no BBMM or EOG performance was fit, and EOG-WF is frozen at **3 scored /31 scientific STOP /3 administrative exclusions**.

A separate [UNSENT author-question draft](SOURCE_AUTHOR_QUERY_DRAFT_20261124.md) asks for the actual 2024 source conversion script/R version, exact meaning of YYYY-MM-DD-only values, source Mountain/DST convention and original CRS/WKT. **No message has been sent.**

### Direct evidence links

[Dryad original publication](https://datadryad.org/dataset/doi%3A10.5061/dryad.15dv41p51) · [Historical March app3 code](https://github.com/jmerkle1/Migration-Mapper/blob/affaea1ee55830638e20fe712908de188214e2ac/app3_sequenceWriting/scripts/app3_calcSequences.R) · [Aug app1 post-publication change](https://github.com/jmerkle1/Migration-Mapper/commit/dc32cf3618c079057d067783cf9c8bbf3592dcb5) · [Sep app3 post-publication change](https://github.com/jmerkle1/Migration-Mapper/commit/4786f018b8283f030b9092275d7399499365b8ce) · [R-devel change](https://stat.ethz.ch/pipermail/r-devel/2023-August/082814.html).
