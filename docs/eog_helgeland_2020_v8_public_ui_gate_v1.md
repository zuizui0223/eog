# Helgeland 2020 v8: official public website's file-stream endpoint

## Why this branch exists

The Dryad **REST API** `/api/v2/files/358962/download` returned `HTTP 401 Unauthorized` under uncredentialed CI in closed PR #635. This does **not** show that the published 2020 v8 files are inaccessible through the website. The [Dryad official app's downloads controller](https://github.com/datadryad/dryad-app/blob/main/app/controllers/stash_engine/downloads_controller.rb) and [routes](https://github.com/datadryad/dryad-app/blob/main/config/routes.rb) define a distinct public-web-UI route, `/downloads/file_stream/:file_id`, for public files. Its controller checks `may_download?` before generating a presigned object-storage URL. Unlike REST OAuth calls, this is the intended public browser download route.

**This is a narrow, lawful attempt at public-web-site access, not authentication bypass:** no token, cookies, secrets, private data, or other credential is used. If the website returns 401/403, refuses a redirect, or supplies bytes inconsistent with the fixed 2020 v8 archive, the workflow must STOP.

### Immutable source pins

Niskanen et al. (2020), Dryad [10.5061/dryad.m0cfxpp10](https://datadryad.org/dataset/doi%3A10.5061/dryad.m0cfxpp10), original published **2020-08-19, v8 / internal version 78498**, *not* the 2023 v10 update.

| Old-version file | Frozen Dryad ID | Byte size |
|---|---:|---:|
| `Dryad_readme.txt` | 358962 | 4,137 |
| `Pop_size_1997_2012.csv` | 358961 | 1,234 |
| `Pop_size_1998_2013.csv` | 358957 | 1,266 |

Each SHA-256 is frozen in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json` (merged PR #634).

### Execution

The tool `scripts/audit_helgeland_2020_v8_public_ui_stream_v1.py` requests exactly the three file-ID-specific official web UI download links `https://datadryad.org/downloads/file_stream/{id}`, in an isolated temporary directory on GitHub Actions. It permits only HTTPS redirects, never uses a credential, enforces byte-size limits, and calls the merged PR #636 **offline v8 verifier** to independently hash all exact bytes and inspect **only first physical line shapes**. No data/README body values or raw file bytes are uploaded as CI artifacts. The source temp directory is destroyed whether the hash gate passes or fails.

The dedicated CI first runs synthetic tests. Real web UI file access and source hash matches must independently PASS before this PR may merge. **Do not regard synthetic CI success as source bytes obtained**. If public UI access remains unavailable, close this PR unmerged, leave `HOLD_2020_V8_PHYSICAL_SOURCE_BYTES_AUTH_REQUIRED`, and retain the PR #636 offline local path for user-authorized original 2020 v8 files.

### Biological interpretation

Even a successful exact file SHA-256 parity would not yet establish semantic column names, numeric island-code crosswalk, surveyed-zero field opportunities, temporal availability of fitted predictors, EOG reachability or 2021–2022 held-out performance. Those all remain STOP until separately qualified under Issue #626.
