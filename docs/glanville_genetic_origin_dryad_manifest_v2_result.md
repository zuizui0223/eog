# Dryad genetic-assignment source qualification — STOP record

## Validated public listing

The separate frozen source-only manifest gate returned **Dryad public version 2 / version ID 181375**, published 2022-06-04. GitHub Actions [44540284586](https://github.com/zuizui0223/eog/actions/runs/44540284586) completed with `DRYAD_VERSION_PINNED_FILE_METADATA_ONLY_EVENT_JOIN_NOT_VERIFIED`; result fingerprint `a003bde0841d5647cd628b0a2a4143d9f0fd91c8c064d5dbbac9c6551c175c64` was verified independently from the artifact ZIP.

Four public metadata entries: `README` (2,402 bytes), `fullsibfamLevelData.csv` (137,353), `nestLevelData.csv` (200,816), and `kinship_AGH.rds` (49,781,508). The publisher supplies SHA-256 for each; exact values are stored in `validation/glanville_genetic_origin_header_gate_v3/protocol_v3.json` and the source-only receipt.

## Actual content access stop

The third source-only gate, [run 44541096661](https://github.com/zuizui0223/eog/actions/runs/44541096661), passed its synthetic checks and produced an artifact with status `STOP_HTTP_SOURCE_401`. The GET to the publisher-provided download API path for the **first declared file, README**, returned HTTP 401. No data-file content, CSV headers, row values or inferred movement assignments were opened. This is an access/transport STOP, not ecological negative evidence.

The STOP receipt is fingerprinted `113966853b382a8649ab9045043692abdb5e9ec0f545dead0f82097873699e64`, independently verified from artifact ID 14538871569. The stable metadata-only summary is `validation/glanville_genetic_origin_header_gate_v3/source_stop_summary_v3.json`.

The next source-only, **distinct** possible route is to inspect the Zenodo **software** `mainAnalysis.R` for static input filenames / field tokens (no sample rows), using the publisher MD5. Software variable names can narrow an acquisition request, but **cannot** establish available event records, source-to-destination mapping, true historical origin or an independent biological validation endpoint.

Do not alter a previously closed EOG-WF endpoint or silently change the Dryad version/URL for a favorable result. A user-provided copy of the exact publisher-declared file (verified SHA-256) could later unlock an independent column-only check without assuming the recorded-zero patches were truly unoccupied.
