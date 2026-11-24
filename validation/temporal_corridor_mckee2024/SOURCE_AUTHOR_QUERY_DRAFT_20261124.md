# Draft to Dryad source author: GPS12hrs_Locs timestamp and coordinate provenance

**DRAFT ONLY — NOT SENT.** The Dryad dataset https://doi.org/10.5061/dryad.15dv41p51 publicly lists corresponding author Jennifer L. McKee and her address (jennylynnmckee@gmail.com). Email identity and deliverability are not independently verified beyond the publisher dataset page. This is a ready-to-review source-data inquiry, not outreach already performed.

**Subject:** Source data clarification: GPS12hrs_Locs midnight formatting, Mountain Time and native CRS (McKee et al. 2024)

Dear Dr. McKee,

I am reviewing the reproducibility of the publicly archived source data for McKee et al. (2024), *Estimating ungulate migration corridors from sparse movement data* (Ecosphere; Dryad DOI 10.5061/dryad.15dv41p51). I appreciate the availability of the original 12-hour GPS files.

I verified the Dryad file GPS12hrs_Locs.zip against its published SHA-256 and found three source-format questions:

1. **Date-only timestamps.** Of 28,953 12-hour records, 10,835 are printed as YYYY-MM-DD without HH:MM:SS, and none of the other 18,118 full timestamp strings is exactly 00:00:00; complete 00-hour nonmidnight times still occur. R 4.3's as.character.POSIXt behavior can print an exact-midnight timestamp without its time portion. Public Migration Mapper code also calls as.character() on date-time values during Shapefile export. In the exact archived file, do date-only strings represent real observations at local 00:00:00, or are their clock times genuinely unknown? If available, could you identify the R/sf version and exact export script used?

2. **Mountain Time convention.** The Dryad README says MT. Did the archived timestamps use fixed MST (UTC−07) throughout, or daylight-saving-aware local civil time (MDT/MST)? On autumn repeated 01:xx clock hours, is there an authoritative UTC offset or timezone convention?

3. **Native projected XY coordinates.** The README and Shapefile PRJ both declare NAD83(HARN) / UTM zone 12N, EPSG:3742, whereas the archived point X coordinates are negative and geographically register in Wyoming under NAD83 CONUS Albers alternatives EPSG:5070/5071 rather than the declared UTM interpretation. What was the original XY CRS (EPSG or WKT), and was a projection assigned or a transformation performed during export?

An original file-generation script, R version, or simple source-processing manifest would resolve these questions. No additional sensitive animal locations are needed. I have kept the archived binary unchanged, have not opened the 2-hour reference for prediction scoring, and am distinguishing conditional formatting hypotheses from confirmed source corrections.

Thank you very much for any clarification you can provide.

Best regards,

[Researcher name and affiliation]

---

## Evidence links for the author or internal review

- Exact original 12h file: Dryad https://doi.org/10.5061/dryad.15dv41p51, file ID 3334125, SHA-256 556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4.
- R 4.3.1 versus R 4.2.3 midnight example: https://stat.ethz.ch/pipermail/r-devel/2023-August/082814.html.
- Current Migration Mapper candidate export code: https://github.com/jmerkle1/Migration-Mapper/blob/main/app3_sequenceWriting/scripts/app3_calcSequences.R, app1_dataCleaning/scripts/app1_ui.R. Do not claim it is the original Dryad exporter.
- Source-only audit: POST_STOP_MIDNIGHT_SERIALIZATION_PROVENANCE_20261124.md.
- Open source-qualification STOP: https://github.com/zuizui0223/eog/issues/745.

**Response required to lift STOP:** A sufficiently authoritative mapping from archived timestamp strings to true observed GPS times, including fixed MST versus DST handling, and original x/y projection identity. The author response may resolve either question separately; do not automatically lift the other. Do not download/open the withheld dense 2h GPS before a separately frozen scoring protocol.


## Historical-lineage follow-up for sender review (2026-11-24)

The source inquiry above is still **UNSENT**. Versioned GitHub evidence now shows Migration Mapper's app3 as.character(date) sequence-export step existed in **March 2024**, before Dryad publication, but it exported geographic lon/lat with a different field schema. The current app1 as.character change was only committed **August 6, 2024** and the app3 projected x/y export update **September 6, 2024**, both after Dryad July 18. When contacting the author, do not assert that either later code change caused the original file. Ask explicitly whether the archived source was written by the public app3 sequence exporter at a specified historical SHA, an analysis-specific manuscript script, or a separate data-cleaning/export step. A reproducible script plus sessionInfo and original coordinate WKT would be decisive. No email has been sent by this project.


## Additional nonauthoritative file-header evidence (not a reason to send without review)

A subsequent SHA-verified read of the original 12h ZIP's central directory and DBF header found **all four ZIP members stamped 2024-06-28 13:23:08** (ZIP local DOS time, offset unspecified) and an internal DBF update date of **2024-06-28**. The Timstmp field is **C(80)**, wide enough for complete HH:MM:SS values, so the date-only strings are not forced by character-field width. Because these dates are mutable packaging/header metadata, they should not be presented in the email as proof of creation date or R version. The central questions remain the original pre-string source times, R script/sessionInfo, timezone handling, and actual XY CRS/WKT. **UNSENT**.
