# McKee 2024: original sparse ZIP + DBF header provenance audit (24 Nov 2026)

**Source-hash-confirmed input metadata; no animal GPS rows, no 2h reference.**

## Main result — two archived metadata clocks agree, but are not authenticated creation time

The exact Dryad McKee et al. original sparse 12-hour file (DOI https://doi.org/10.5061/dryad.15dv41p51, file ID 3334125, 1,539,661 bytes, SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4) contains four ZIP members. **All four ZIP central-directory DOS modification dates are 2024-06-28 13:23:08**, with no timezone recorded in the ZIP metadata. The internal dBASE **DBF last-update field independently parses as 2024-06-28** (raw YY/MM/DD bytes 124/6/28). The dates are therefore internally consistent and precede the Dryad [original publication on 2024-07-18](https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p51).

However, the DOS ZIP dates may have been preserved from imported files or set by the ZIP writer, and the DBF last-update field is mutable. **These matching stamps are not independent proof of when the authors generated the coordinates, which computer/software wrote them, which version of R was used or what local timezone offset applied.** They merely constrain the historical metadata state of these published bytes.

The [pre-inspection freeze](post_stop_archived_zip_dbf_header_protocol_v1.json) was committed at 52c99bea76d55cf308551cb46fcf96b7f886408a **before reading the DBF header and ZIP member times**. The exact source hash is verified by the [local replay](replay_post_stop_archive_headers.py), which opens **only ZIP central-directory fields, the 385-byte DBF header/field descriptors, SHP+SHX 100-byte headers and PRJ projection text**. It never reads an animal's GPS record or the dense 2h holdout.

## Raw header evidence

| Original ZIP member | ZIP DOS modification timestamp | Uncompressed bytes |
|---|---|---:|
| GPS12hrs_Locs.dbf | 2024-06-28 13:23:08 | 22,265,243 |
| GPS12hrs_Locs.shp | 2024-06-28 13:23:08 | 810,784 |
| GPS12hrs_Locs.shx | 2024-06-28 13:23:08 | 231,724 |
| GPS12hrs_Locs.prj | 2024-06-28 13:23:08 | 440 |

The DBF header is a dBASE variant with format byte **0x03**; it specifies 28,953 records, header length 385 bytes, record length 769 bytes and 11 field descriptors. Nine fields, including **Timstmp**, are **Character type C, width 80**; UTM_E and UTM_N are Numeric type N, width 24 and decimal precision 15. The SHP and SHX headers declare Point shape type 1; their original uncompressed lengths reconcile with 28,953 Point records (SHP = 100 + 28 × 28,953; SHX = 100 + 8 × 28,953).

Critically, **Timstmp is C(80), sufficient to hold the 19 characters of YYYY-MM-DD HH:MM:SS**. Therefore the observed 10,835 date-only strings cannot be explained simply as inevitable truncation caused by the physical DBF field width. This check does NOT identify whether they were intentionally formatted as dates, genuinely missing clock time, or shortened by R's as.character.POSIXt midnight behavior.

The original PRJ text begins with projected WKT name **NAD_1983_HARN_UTM_Zone_12N**, while [prior geographic locality analysis](POST_STOP_WGFD_CRS_LOCATOR_20261124.md) found Albers-family EPSG:5070/5071 interpretations much more plausible for the source XY. The archive headers contain no independently authoritative EPSG correction or processing-chain manifest.

The full [nonidentifying aggregate evidence receipt](post_stop_archive_header_receipt_v1.json) records central-directory timestamps, CRC32 values, byte lengths, DBF field types/widths, original shape header types, and explicitly false provenance claims. No full DBF rows, coordinates, individual IDs or raw original ZIP bytes are uploaded to GitHub.

## How this changes the source-provenance timeline

| Date | Independently supported event |
|---|---|
| Aug 2023 | [R 4.3 midnight representation documented](https://stat.ethz.ch/pipermail/r-devel/2023-August/082814.html) |
| 2024-03-05 | [Public Migration Mapper app3 code](https://github.com/jmerkle1/Migration-Mapper/blob/affaea1ee55830638e20fe712908de188214e2ac/app3_sequenceWriting/scripts/app3_calcSequences.R) already applied as.character to sequence times, but output **lon/lat geometry and other fields** |
| 2024-03-25–26 | [App1 x/y export and CRS assignment correction](https://github.com/jmerkle1/Migration-Mapper/commit/6d45fb5126264f72735c7c26d7b7e246a3490a49) existed pre-publication, not linked to the exact Dryad writer |
| **2024-06-28** | **Original published ZIP member DOS date and DBF internal last-update date agree** (timestamps mutable; not source-generation proof) |
| 2024-07-18 | [Dryad original dataset publication](https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p51) |
| 2024-08-06 | [App1 explicit as.character addition](https://github.com/jmerkle1/Migration-Mapper/commit/dc32cf3618c079057d067783cf9f1de903d152a692) **postdates original publication** |
| 2024-09-06 | [App3 shift to projected x/y export](https://github.com/jmerkle1/Migration-Mapper/commit/4786f018b8283f030b9092275d7399499365b8ce) **postdates original publication** |

These timeline observations are compatible with a source archive generated by an R/POSIX-to-character conversion sometime before July 2024, but **do not prove an actual R runtime version or exactly what the archived Timstmp values represented before export**. It also remains possible that an analysis-specific conversion used a different script from Migration Mapper's generic app3 output. The field names and projected XY layout in this original ZIP differ from the March app3 geographic exporter.

## Decision and stopping rule

- **Supported:** The 2024 original source has a matching set of ZIP/DBF pre-publication header dates, and an 80-character timestamp field. The source's 10,835 date-only values are **not physically forced by short DBF character width**.
- **Still unverified:** whether date-only times are exact 00:00:00, whether R >=4.3 as.character was actually used in the original source export, whether the stored Mountain Time was fixed MST or DST-aware, and the original source XY CRS (EPSG:3742 label versus geographically plausible Albers).
- **Scientific interpretation:** Prior T0/T1/H3 source-clock calculations remain correctly labeled conditional *input worlds*. Do not score any ecological/Brownian-bridge forecast by treating a metadata possibility as a verified observation.
- **No outcome access:** No dense 2h GPS ZIP opened; no EOG or BBMM model fitted or scored. Frozen EOG-WF **3 scored /31 scientific STOP/3 administrative exclusions** remains unchanged; [issue #745](https://github.com/zuizui0223/eog/issues/745) stays open.

To actually remove the original source time/CRS STOP, the remaining decisive evidence is a versioned **pre-string original timestamp field + writer script/sessionInfo and original projected XY CRS/WKT** from the data authors. The [prepared author query](SOURCE_AUTHOR_QUERY_DRAFT_20261124.md) is **UNSENT**.
