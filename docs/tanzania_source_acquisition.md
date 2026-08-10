# Tanzania official-source acquisition

The primary non-island benchmark uses Dryad DOI `10.5061/dryad.p042h0c`. Public metadata are readable anonymously. Dryad's dataset-level archive endpoint currently requires an OAuth2 bearer token, while the frozen version-level archive endpoint for version `23134` is anonymously downloadable. Browser-facing individual downloads may still reject hosted runners with an authorization response or bot challenge.

This repository therefore separates **source discovery** from **source acceptance** and tries both public and authenticated routes without assuming that all endpoints share one access policy.

## Frozen source identity

`benchmarks/tanzania_source_contract.json` records the official Dryad version (`23134`) and, for all nine files, the Dryad file ID, exact byte size, MD5 digest, MIME type, API download endpoint, and public-stream endpoint. The contract is derived only from the open Dryad metadata API and contains no species outcome.

Every acquisition run first regenerates the open metadata manifest with `benchmarks/fetch_tanzania_dryad.py`. Any filename, version, size, digest, or download-link drift is a hard failure before binary acquisition.

## Authentication

The acquisition code supports Dryad's OAuth2 client-credentials flow when an endpoint requires it. It accepts either:

- `DRYAD_CLIENT_ID` and `DRYAD_CLIENT_SECRET`; or
- an already-issued bearer token in `DRYAD_API_TOKEN` (or `DRYAD_ACCESS_TOKEN`).

The production token URL defaults to `https://datadryad.org/oauth/token` and can be overridden with `DRYAD_TOKEN_URL`.

GitHub Actions may store these values as repository secrets with the same names. No credential or bearer token is written to reports or artifacts. Credentials are not required when the frozen version archive remains anonymously accessible.

## Acquisition order

`benchmarks/fetch_tanzania_verified_package.py` attempts, in order:

1. authenticated/anonymous full-dataset archive;
2. authenticated/anonymous frozen-version archive;
3. authenticated individual file endpoints, when a token exists;
4. browser-facing public individual streams as a last diagnostic fallback.

Downloaded HTML, JSON authorization responses, bot challenges, partial files, unsafe zip paths, duplicate expected basenames, and incomplete archives are never treated as source data.

A byte is accepted only when every one of the nine files matches the frozen size and MD5 exactly. A same-sized but different file is a hard integrity failure, not a recoverable mirror.

## Verified execution

Workflow run `31351807716` established the currently working route:

- dataset-level archive: HTTP 401, bearer token required;
- version `23134` archive: HTTP 200 without credentials;
- downloaded archive size: 12,432,920 bytes;
- all nine extracted files: exact frozen size and MD5 match.

The verified official scripts and tables then passed both the structural schema audit and the explicit semantics/CRS audit. The source contains 14 fragments, 89 species, 1,246 complete binary species-site records, and 60 species satisfying the pre-outcome `>=2 presences AND >=2 absences` rule.

## Workflow behavior

`.github/workflows/tanzania-source-acquisition.yml` always uploads an artifact containing the current open manifest, acquisition report, verified source bytes when available, and downstream audit reports.

- Without credentials, all anonymous routes are attempted and their exact response classifications are retained.
- When credentials are configured, `--require-success` makes any acquisition or integrity failure fatal.
- When all bytes verify, the workflow immediately runs `audit_tanzania_verified_bytes.py` and `audit_tanzania_semantics.py`.

Verified bytes are stored only in the workflow artifact and are not committed to the repository.

## Scientific gate after acquisition

Successful byte acquisition does not itself authorize EOG performance analysis. The remaining order is:

1. freeze geometry-only folds and graph scales;
2. freeze executable formulas for local area, the two simple isolation fields, source-faithful current flow, nearest training occurrence distance, and EOG reachability;
3. reproduce the published full-data analysis separately;
4. run the leakage-safe held-out current-flow versus EOG comparison under the already frozen scoring and species-cluster inference contracts.

No connectivity setting or model role may be changed after inspecting Tanzania held-out performance.
