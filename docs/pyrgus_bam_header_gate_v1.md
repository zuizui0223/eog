# Pyrgus BAM fixed-source physical-header qualification (Gate1)

## Scientific role

This is a continuation of the **separately verified** Fourcade et al. 2018
Dryad metadata preflight, not a retest of the Gotland archive and not a
new EOG-WF validation endpoint.

The official Dryad API identified version **17929**, with exactly:

| File | ID | Frozen byte size | Repository MD5 |
|---|---:|---:|---|
| Monitoring_data.csv | 59822 | 8380 | f7d32e5cad93f08b08efbfee4fe59ac1 |
| Site_data.csv | 59823 | 2763 | 41eca42bc08eb4195b33b5fd30c2e4c3 |

The metadata gate's original GitHub Actions run is
`40859758110`; fingerprint
`e20509d4b841aa2a2b2c04ed78f4a194bd0a1131846375e008c71a970470ffad`.

## Frozen physical header contract

Protocol `validation/pyrgus_bam_header_gate_v1/protocol_v1.json`
(commit `e758455eebe1d223684f50318893766dfc472875`)
freezes one **HTTP Range `bytes=0-511`** request to each of the
two exact published file IDs, same host only. Require HTTP 206,
exact `Content-Range` matching the frozen file byte size,
no transparent decompression and no fallback.

The prefixes can contain biological row *bytes* after the newline;
they must **never be parsed, stored or used for scientific decisions**.
Only a complete first physical CSV header line is parsed.
The result records header tokens and a SHA256 of each 512-byte prefix,
but never raw CSV payloads. Because the transfer is partial,
the repository's full-file MD5 **cannot yet be independently verified**.

Both headers are screened for potential site-key, environmental,
host-plant and coordinate column names. Shared labels are merely
potential join keys: **no patch correspondence, uniqueness, temporal
alignment or A/B/M proxy qualification is inferred from headers alone**.

A 200 response to Range, redirect to unlisted host, 403/429,
incomplete header or invalid line returns a **terminal transport/schema
STOP**. No repeated requests or alternative download source in this
protocol. Source errors are neither butterfly occupancy failures nor
unfavourable EOG geometry results.

## Next science gate

If both headers are obtainable and appropriate fields exist, a
*separately frozen* Gate2 could read the physical tabular data **once**,
verify the entire file size and MD5, unique site/year keys,
missing-value semantics and actual host/site correspondence.

The scientific illustration must compare fixed EOG geometry against a
strong baseline containing area, independently measured microclimate,
host plant density and source-independent site geography, with a
predeclared survey/temporal split. The published abundance-weighted
connectivity index must not masquerade as independent movement M.
Without source or observation-process qualification, return
`B/M_UNQUALIFIED` or `STOP`, not a fitted result.
