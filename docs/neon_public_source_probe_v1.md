# NEON fixed site-month public source retrieval probe

## Executed result

Fixed product: DP1.10072.001 (small mammal box trapping).
Fixed location and month: HARV, 2023-06.
Source endpoint:
https://data.neonscience.org/api/v0/data/DP1.10072.001/HARV/2023-06

The source-access GitHub Actions run
https://github.com/zuizui0223/eog/actions/runs/42456004133
completed successfully as a *diagnostic workflow*, but the
underlying unauthenticated NEON API request returned **HTTP 403**.

**Native CSVs downloaded: 0.** Neither `mam_perplotnight`
nor `mam_pertrapnight` was obtained. No source SHA256, trap
quality check, species data, occupancy estimate or empirical
EOG×BAM result is available from this attempt.

The API documentation now describes token authentication for
`/data/query` and release package access. HTTP403 is consistent
with restricted access, but does not by itself establish the
precise server-side cause. This probe used the historical
`/api/v0/data` route and did not use any user token.

## Reproducible status and next access dependency

The source selection and fail-closed design were frozen in
`validation/neon_public_download_probe_v1/contract.json`
before the network attempt, commit
`1e5a1beae5d79c0d3736e296c1a13867f75e187a`.

The actual observed HTTP status and zero-file result are
preserved in
`validation/neon_public_download_probe_v1/result_receipt.json`.

To continue empirical qualification, an authorized NEON
API connection or a verifiable public release URL is required.
Any token must be passed via a protected secret/environment
variable, **never** committed to GitHub or pasted into analysis
logs. Once original files exist, apply the merged
`benchmarks/neon_mammal_source_gate_v1.py`, and independently
audit trap deployment, capture/no-capture coding, missingness,
quality flags, recapture and geographic coordinates.

The original 768 synthetic EOG×BAM worlds, frozen EOG-WF
endpoints, and empirical Charaxes results are untouched.
