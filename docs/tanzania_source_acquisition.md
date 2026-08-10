# Tanzania official-source acquisition

The primary non-island benchmark uses Dryad DOI `10.5061/dryad.p042h0c`. Public metadata are readable anonymously, but the current Dryad v2 binary-download endpoints require OAuth2 credentials. Browser-facing individual downloads may also reject hosted runners with an authorization response or bot challenge.

This repository therefore separates **source discovery** from **source acceptance**.

## Frozen source identity

`benchmarks/tanzania_source_contract.json` records the official Dryad version (`23134`) and, for all nine files, the Dryad file ID, exact byte size, MD5 digest, MIME type, API download endpoint, and public-stream endpoint. The contract is derived only from the open Dryad metadata API and contains no species outcome.

Every acquisition run first regenerates the open metadata manifest with `benchmarks/fetch_tanzania_dryad.py`. Any filename, version, size, digest, or download-link drift is a hard failure before binary acquisition.

## Authentication

The acquisition code follows Dryad's OAuth2 client-credentials flow. It accepts either:

- `DRYAD_CLIENT_ID` and `DRYAD_CLIENT_SECRET`; or
- an already-issued bearer token in `DRYAD_API_TOKEN` (or `DRYAD_ACCESS_TOKEN`).

The production token URL defaults to `https://datadryad.org/oauth/token` and can be overridden with `DRYAD_TOKEN_URL`.

GitHub Actions may store these values as repository secrets with the same names. No credential or bearer token is written to reports or artifacts.

## Acquisition order

`benchmarks/fetch_tanzania_verified_package.py` attempts, in order:

1. authenticated/anonymous full-dataset archive;
2. authenticated/anonymous frozen-version archive;
3. authenticated individual file endpoints, when a token exists;
4. browser-facing public individual streams as a last diagnostic fallback.

Downloaded HTML, JSON authorization responses, bot challenges, partial files, unsafe zip paths, duplicate expected basenames, and incomplete archives are never treated as source data.

A byte is accepted only when every one of the nine files matches the frozen size and MD5 exactly. A same-sized but different file is a hard integrity failure, not a recoverable mirror.

## Workflow behavior

`.github/workflows/tanzania-source-acquisition.yml` always uploads a diagnostic artifact containing the current open manifest and acquisition report.

- Without credentials, a blocked report is an expected pre-outcome result and the workflow remains usable for diagnosis.
- When credentials are configured, the workflow requires complete verified acquisition and fails on any download or integrity problem.
- When all bytes verify, the workflow immediately runs `audit_tanzania_verified_bytes.py` to freeze CSV/TIFF structural schema.

Verified bytes are stored only in the workflow artifact and are not committed to the repository.

## Scientific gate after acquisition

Even successful byte acquisition does not authorize EOG analysis. The remaining order is:

1. inspect the three verified official scripts;
2. populate the explicit semantics/CRS mapping without header guessing;
3. pass `audit_tanzania_semantics.py` for the 14-fragment / 89-species structure and deterministic class-support eligibility;
4. freeze geometry-only folds, graph scales, and executable source formulas;
5. reproduce the published full-data analysis separately;
6. run the leakage-safe held-out current-flow versus EOG comparison.

No species-level outcome may be inspected before those gates pass.
