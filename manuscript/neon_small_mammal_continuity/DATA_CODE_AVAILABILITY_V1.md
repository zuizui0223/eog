# Data and code availability

## Data

This study uses the NSF National Ecological Observatory Network (NEON) **Small mammal box trapping** data product, DP1.10072.001, RELEASE-2026. The NEON release citation reports DOI **10.48443/A83H-TB34**.

The confirmatory programme used 16 prospectively fixed fresh NEON sites. The repository does not redistribute the downloaded NEON response files. Instead, it preserves the fixed site roster, response-blind node and world fingerprints, target-taxon contract, authenticated query contract, response-file checksums, immutable once-only terminal result, and programme closure needed to reproduce the analysis from the authoritative NEON source.

The once-only response run consumed 639 response files and 299,965,029 biological-response bytes. All 16 fixed sites were scorable; no site replacement or post-response registry repair was performed.

## Code

Analysis code, frozen contracts, response receipts, claim boundaries and deterministic manuscript-asset builders are maintained in the public EOG repository:

https://github.com/zuizui0223/eog

Canonical scientific files for this paper include:

- validation/neon_metacommunity_connectivity_v1/protocol_v1.json
- validation/neon_metacommunity_connectivity_v1/analysis_implementation_v1.json
- validation/neon_metacommunity_connectivity_v1/fresh_roster_lock_v1.json
- validation/neon_metacommunity_connectivity_v1/response_lock_v1.json
- validation/neon_metacommunity_connectivity_v1/programme_closure_v1.json
- src/eog/v2/metacommunity_connectivity.py
- manuscript/neon_small_mammal_continuity/

The current manuscript figures and supplementary tables are generated deterministically from the frozen scientific closure. The corresponding GitHub Actions artifact digest is recorded in ASSET_RECEIPT_V1.json.

Before journal submission, the final manuscript commit should be archived in a permanent repository release and its DOI inserted here.

## Integrity boundary

No additional biological response access is authorized for this consumed programme. The 16-site denominator, target guild, spatial worlds, confirmatory test and once-only response result are closed. The occupancy-continuity redundancy identity audit is explicitly post hoc descriptive evidence and does not alter the preregistered confirmatory rejection of turnover-generated emergent continuity.
