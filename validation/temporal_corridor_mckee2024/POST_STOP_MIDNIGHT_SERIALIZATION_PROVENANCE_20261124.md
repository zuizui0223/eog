# McKee 2024 sparse 12-hour GPS: R 4.3 midnight string serialization as a concrete source mechanism

**2026-11-24. Source-provenance finding only, NOT an author-confirmed correction or biological prediction.**

## Main finding: apparent missing hours can be exact midnight that the formatter suppressed

The original Dryad [McKee 2024 GPS source](https://doi.org/10.5061/dryad.15dv41p51) was verified at 1,539,661 bytes, SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4. Its 28,953 sparse fixes include 10,835 YYYY-MM-DD strings without HH:MM:SS. The earlier conditional T0 and T1 source-clock analyses treated these date-only values as potentially unknown hour values.

An [R Core mailing-list discussion (August 2023)](https://stat.ethz.ch/pipermail/r-devel/2023-August/082814.html) documents that **R 4.3.1 as.character.POSIXt() converts an exact 00:00:00 POSIXct value to only YYYY-MM-DD**, but retains HH:MM:SS for other times. R 4.2.3 did not have that same vector behavior.

The [Migration Mapper](https://github.com/jmerkle1/Migration-Mapper) software linked by the Dryad README has **a plausible explicit pipeline**: current code at [app3_sequenceWriting/scripts/app3_calcSequences.R](https://github.com/jmerkle1/Migration-Mapper/blob/main/app3_sequenceWriting/scripts/app3_calcSequences.R), lines about 56–65 and 290–297, converts a POSIX date to character with as.character(), then creates point features using st_as_sf(coords=c("x","y"), crs=configOptions$masterCrs) before shapefile export. The [app1 data export](https://github.com/jmerkle1/Migration-Mapper/blob/main/app1_dataCleaning/scripts/app1_ui.R), lines about 241–245, also applies as.character() to a time field before st_write. [CalcBBMM.R](https://github.com/jmerkle1/Migration-Mapper/blob/main/app4_uds/wmiScripts/CalcBBMM.R), explicitly cited in Dryad, requires POSIXct time input and transforms points to the population grid.

**Historical provenance limit:** The current public Migration Mapper code is NOT proven to be the precise script and commit that exported the 2024 Dryad ZIP. The field names in those generic application output files differ from the McKee source. Thus these code paths provide a mechanistic hypothesis, not a certified lineage chain.

## Pre-access-frozen physical source pattern test

The [new source timestamp-shape protocol](post_stop_midnight_serialization_protocol_v1.json) was committed at 24bb56e8c62e298d91196e3ac2361d0e2ac93314 **before** inspecting new source minute/second patterns. Only original sparse 12h DBF grouping/time fields were read. No raw animal IDs, precise dates, coordinates or GPS fixes were exported.

| Original source timestamp pattern | Count |
|---|---:|
| Date-only YYYY-MM-DD | **10,835** |
| Complete YYYY-MM-DD HH:MM:SS | **18,118** |
| **Complete time exactly 00:00:00** | **0** |
| Complete values in 00 hour but **not** exactly midnight | **379** |
| Complete exactly 01:00:00 | 3,105 |
| Complete exactly 12:00:00 | 11,037 |
| Complete exactly 13:00:00 | 2,958 |
| Complete timestamps with minute and second both zero | 17,100 |
| Complete timestamps with nonzero minute and/or second | 1,018 |
| Source groups containing both date-only and complete time formats | 277 / 421 |

This is **very strong pattern consistency** with the R 4.3 midnight-shortening mechanism; not proof another writer could not produce the same output. If the 10,835 dates truly represented midnight, 27,678 of the 28,532 within-group nominal time gaps (97.0%) fall within 10–14h, without duplicate local timestamps. See [physical timestamp evidence receipt](post_stop_midnight_serialization_receipt_v1.json).

## New H3 conditional hypothesis: date-only means exactly midnight

Before comparing any new time-cut masks, a distinct [H3 protocol](post_stop_exact_midnight_candidate_cut_protocol_v1.json) was committed at 04b5992b8e32bad79415c32c9a745e1b1cbdc93a. It treats date-only strings as **exact local 00:00:00**, but labels this a COUNTERFACTUAL until author confirmation. All full clock strings retain their exact printed time and, in the IANA model, both legal autumn repeated-hour UTC folds.

| Clock model | Previous T0 day uncertainty | Previous T1 00–01h uncertainty | **H3 exactly midnight** |
|---|---:|---:|---:|
| Naive Mountain local | 857 cuts | 858 cuts | **858 cuts** |
| IANA America/Denver | 889 cuts | 890 cuts | **959 cuts** |

Under naive local time, **H3 and prior T1 cut masks are exactly identical on all 28,532 links**. Under conditional IANA America/Denver, the exact-midnight candidate requires **69 additional cuts** beyond T1, and affects 69 of 421 dependent groups; all 890 T1 IANA cuts remain. For H3 IANA, 938 time-adjacent pairs are individually ineligible but a full sequence-consistent clock requires 959 cuts: 21 extra due to no-splicing.

These numbers are reproducible via the [local source-SHA-gated replay](replay_post_stop_midnight_serialization.py) and [non-identifying H3 cut receipt](post_stop_exact_midnight_candidate_cuts_receipt_v1.json). No dense 2h GPS was opened.

## CRS metadata: a parallel but not causally proven exporter mechanism

The original Dryad README and physical PRJ label coordinates **NAD83(HARN) UTM zone 12N, EPSG:3742**, although the original data align geographically with Albers EPSG:5070 or EPSG:5071. The current Migration Mapper code above uses st_as_sf with a configurable CRS on preexisting x,y coordinates. [sf documentation](https://r-spatial.github.io/sf/reference/st_as_sf.html) defines that argument as the **CRS to assign**, rather than a command to transform coordinates; actual reprojection is done via [st_transform](https://r-spatial.github.io/sf/reference/st_transform.html). An incorrectly configured CRS during export could therefore label unchanged x,y values wrongly. **This is a plausible failure mechanism, NOT proof of the actual Dryad exporting code or intended CRS.**

## Scientific interpretation and next action

1. If the date-only strings arose from R 4.3 POSIX conversion, then the earlier T0 full-day uncertainty studies (64 nonspliceable triples, 590 24-record false chains, optimization-sensitive mandatory cuts) remain correct **mathematical counterfactuals**, but **not a demonstration that the original GPS had 10,835 physically unmeasured clock times**. Do not publish that interpretation without evidence.
2. The actual exporter version, whether those 10,835 are exactly local midnight, Mountain fixed MST vs DST-aware clock semantics, and intended native coordinate CRS remain **unconfirmed**. The generic published app code is not the complete historical file-generation provenance.
3. Ask the data author for original export script and R version, date-only true timestamp values, timezone/DST convention, and exact native CRS/WKT versus supplied EPSG:3742. Do not silently replace or rewrite the original source.
4. The source-QC STOP remains open in [issue #745](https://github.com/zuizui0223/eog/issues/745). No 2h dense reference was opened, no Brownian bridge or EOG landscape model was fit, and no new independent scored EOG-WF endpoint was added. Frozen EOG-WF remains exactly **3 scored /31 scientific STOP /3 administrative exclusions**.

**Decision:** The most valuable next step is to verify original source **formatting/projection provenance**, not to continue deriving seemingly independent ecological conclusions from hypothetical timestamp ambiguities.


## Historical code-dating correction (separate follow-up, 2026-11-24)

A [dated historical commit audit](POST_STOP_HISTORICAL_MAPPER_LINEAGE_20261124.md) supersedes any suggestion above that **the current** app1 or app3 export code is itself prepublication proof of the specific Dryad file writer.

**Confirmed:** The public Migration Mapper app3 sequence exporter **already called as.character(date) on March 5, 2024**, before the Dryad publication of July 18, 2024, so the specific POSIX-to-character mechanism was available in related software beforehand. But its March 2024 geometry construction was **longitude/latitude with masterCrs4326**, and its export field layout differs from the archived Dryad 11-column source, so that snapshot is *not* the identified original writer.

**Important negative chronology:** The app1 data cleaning export's as.character addition was committed **August 6, 2024**, *after* the original Dryad publication; the app3 sequence export's shift to projected x/y geometry was committed **September 6, 2024**, also after original Dryad publication. The current post-July statements must not be attributed to the original July ZIP. An app1 x/y CRS-assignment correction on March 26 documents a real related-software bugfix, but does not prove the actual Dryad PRJ error was caused by it.

The exact original source exporter, R version, date-only clock meaning, Mountain/DST convention and original CRS remain unknown. The R 4.3 mechanism remains **strongly compatible but NOT confirmed for this data**, and the original source-QC STOP remains binding.
