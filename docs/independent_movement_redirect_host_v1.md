# Independent Dryad movement source: header-only redirect provenance follow-up

**Status:** Transport diagnosis only. No biological observation row, movement, path, prediction or model fit is accessed. Source qualification remains **STOP** unless the original Dryad download's final storage host and original publisher digest can be verified under a separately frozen follow-up.

## Previous source gate — exact facts

The earlier [source qualification protocol](../validation/independent_movement_source_gate_v1/protocol_v1.json) pinned two independent public Dryad DOI records **before** attempted source download.

[Run 44751841678](https://github.com/zuizui0223/eog/actions/runs/44751841678) and aggregate-only [receipt artifact 14636106078](https://github.com/zuizui0223/eog/actions/runs/44751841678/artifacts/14636106078) returned:

| Study | Verified official Dryad version | Publisher date | Result |
| --- | ---: | --- | --- |
| [Moura 2021 Heliconius movement/translocation](https://doi.org/10.5061/dryad.34tmpg4m6) | **148124** | 2021-11-14 | Metadata and listed file SHA-256 obtained, **`STOP_UNEXPECTED_SOURCE_REDIRECT`** before ZIP body |
| [Jreidini & Green 2022 toad translocation](https://doi.org/10.5061/dryad.x3ffbg7ms) | **198534** | 2022-09-27 | Metadata and listed file SHA-256 obtained, **`STOP_UNEXPECTED_SOURCE_REDIRECT`** before ZIP body |

The official publisher metadata reported five small files across those studies, with file SHA256 digests. Neither CSV header nor any biological result was observed in the initial stop. The source script correctly treated an unlisted storage host as a refusal, not as a signal of ecological nonexistence.

## This predeclared hostname-only follow-up

The [frozen follow-up protocol](../validation/independent_movement_redirect_host_v1/protocol_v1.json) pins the **two exact original version-specific API download endpoints** and first-gate source digests. Its first commit precedes any redirect probe. A pre-probe amendment allows at most three no-follow requests through **official same-host (datadryad.org) redirects only**, so a local Dryad route cannot conceal which external host was requested.

The [diagnostic script](../scripts/eog_independent_movement_redirect_host_v1.py) requests only HEAD, with GET **only** when HEAD is explicitly rejected by the official publisher as 405/501; in all cases **zero payload-body bytes are read**. An external `Location` target is reported only as an HTTPS hostname. It is **never followed**. Signed URLs and query parameters are never logged.

A successful diagnostic reveals the storage hostname; it does **not** verify that the hostname belongs to Dryad or the listed dataset, or qualify any CSV schema.

## Scientific interpretation gates

- **`STOP_UNVERIFIED_REDIRECT_HOST`:** A third-party hostname was disclosed; it requires publisher-backed verification and a new explicit allowlist before attempting any byte download.
- **`STOP_DIRECT_ZIP_RESPONSE_200_UNREAD`:** There was no redirect, but file body deliberately not read.
- **Other STOP statuses:** API method not allowed, source endpoint changed, invalid hostname or hop budget exhausted.

Do not reinterpret any of these as an actual movement test. The next ecological evaluation would still require independent source–target IDs, time, coordinates, and a predeclared estimand; environment/barrier constraints remain **NOT QUALIFIED** until measured.

Original EOG-WF 3 scored / 31 science STOP / 3 administrative exclusion denominator unchanged. No new field endpoint or ecological model run.
