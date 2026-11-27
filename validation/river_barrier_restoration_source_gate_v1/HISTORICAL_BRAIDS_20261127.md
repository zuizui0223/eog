# Historical channel geometry qualification — 2026-11-27

## Source and metadata-only results

[Foxgrover, East and Ritchie (2025), DOI 10.5066/P13RXGHA](https://doi.org/10.5066/P13RXGHA), official [USGS FGDC metadata](https://cmgds.marine.usgs.gov/catalog/pcmsc/DataReleases/ScienceBase/DR_P13RXGHA/Elwha_margins_braids_metadata.faq.html), item 67102a7ad34edd269209626c. Independent physical geography; not the original fish survey CSV or a complete 65-km river network. The release has two polyline families: recently active river margins, and approximate main channel midlines plus surface-connected braids. Focus on the latter only in this gate. Metadata says main channel drawn as a single continuous line per study reach; thus a path through the mainline is partly a digitization convention, not independent evidence of barrier absence. Short sections were approximated in the 20121127 and 20130116 imagery. No formal logical consistency/topology tests. Estimated horizontal uncertainty below 7 m in favorable conditions; may be substantially larger under vegetation. These are not certified hard error bounds. The stated CRS is NAD83(NSRS2011), UTM10N, meters (EPSG:6339), distinct from the original reach-break metadata's NAD83 UTM10N (EPSG:26910). Require actual PRJ checks and explicit transformation before crosswalk. Imagery discharge varies (provider reports 8–56 m3/s); avoid assigning every morphological change to dam removal.

Derived metadata coverage, not actual file counts:
| Expected imagery labels | Lower | Middle | Control | All three | All three with valid date label |
|---|---:|---:|---:|---:|---:|
| All (30) | 30 | 29 | 22 | 22 | 21 |
| Before removal (5) | 5 | 4 | 4 | 4 | 3 |
| During/after (25) | 25 | 25 | 18 | 18 | 18 |

The control reach is missing in six PlaneCam dates (20121127, 20130116, 20130327, 20130430, 20140201, 20140930) and 20120407; the 20080403 image only has the lower reach. The source metadata also has a malformed date label 200800813; do not correct it by guesswork. 20130831 appears in both NAIP and PlaneCam source lists, counted once among distinct date labels. Date registry and transparent coverage arithmetic saved in historical_braids_metadata_coverage.json. No archive filenames, feature counts or lengths verified.

## Actual acquisition result

Protocol d3462461c39a78be84564731e610ee09e7243bfe frozen before any archive request. Exact official public braid ZIP URL:
https://www.sciencebase.gov/catalog/file/get/67102a7ad34edd269209626c?name=Elwha_River_braids_2006_to_2022.zip

One local request failed DNS. One CI request (run 45947061929, job 140334071765) returned HTTP 403. Offline geometry safety fixtures passed. Downloaded sanitized receipt ZIP 15175187105, 446 bytes, SHA256 22e8347756a92951e009f3a9573e178d6fe8d210c19d44fcc2b0b0a1810f8c53 verified against actual downloaded bytes. No geometry or fish records obtained. This is an access HOLD, not evidence that the public data do not exist. Do not repeatedly query this denied endpoint. The one-shot workflow will not perform another network request on documentation updates.

## Next gate and inference boundary

Request only the original public braid ZIP from an independent legitimate download, keeping publisher provenance and content SHA256. Run the existing historical_braids_gate.audit_zip on the uploaded bytes. It enforces size/member caps, safe paths, CRC, mandatory shapefile sidecars, explicit CRS, polyline type, date/section labels, finite coordinates and lengths. It is an experimental intake, not a full topology check; source checksums have not been supplied by publisher. Then reconcile actual date labels against metadata, compare contemporaneous river sections and only thereafter formulate a topology diagnostic with explicit positional tolerances and a common anchor definition. A date with a missing section is unavailable, not disconnected. Primary future method question: how much apparent route redundancy or continuity is introduced by pooling incompatible snapshots, as distinct from changing same-date physical geometry. Width/braiding metrics have already been studied by the source authors; do not claim those as a novel result. No fish passage, occupancy or movement score; no causal restoration effect or new EOG-WF endpoint. Original geometry CSV needed for authenticated 22-reach crosswalk. Main unmodified.
