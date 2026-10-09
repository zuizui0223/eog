# Can a public 2023 copy recover exactly the bytes already published in 2020?

The archived **2020 Niskanen Dryad v8 / numeric 78498** is genuinely dated 2020-08-19 (merged PR #634). Unauthenticated v8 file downloads were 401 REST (#635) and 403 official web UI (#638). Both were closed unmerged.

**New qualifying evidence in PR #639:** Official 2023 v10 / 208617 source metadata reports exact same **SHA256 and size** as v8 for exactly three historically published individual files. This authorizes only an *independent actual-byte check* of their v10 published copies, not any 2023-only biological features.

| Historical v8 file | Original file ID | Identical-by-registered-hash later copy ID |
|---|---:|---:|
| Dryad_readme.txt | 358962 | 1952534 |
| Pop_size_1997_2012.csv | 358961 | 1952533 |
| Pop_size_1998_2013.csv | 358957 | 1952529 |

This read-only trial uses Dryad's separate public website `/downloads/file_stream/:file_id` route for just the **later current-version three copies**, hoping they are accessible when archived-v8 copies are blocked. It streams bytes directly through SHA256, never parses or records any bird, island or population observation row, and demands exact equality with *original 2020 v8 frozen hashes* and sizes.

**STOP rules:** HTTP 401/403, redirected non-HTTPS, missing files, short/oversized body or different SHA256 immediately fail CI. No authentication workaround, no using current-only data, no retrofitting v8 hashes to fit the latest version. Real bytes are not emitted in CI artifacts.

If all three succeed, the later copies have been independently verified to be *content identical to 2020-published data*, making their raw content potentially useful for a genuine pre-2021 input specification. **Even then** the time/year denominators, numeric site codes, surveyed-zero opportunity, model and 2021–2022 holdout remain entirely unqualified. This is source authenticity verification, **not ecological validation**.

The 2020 actual-data use remains on scientific HOLD unless the SHA256 gate passes. See [Issue #626](https://github.com/zuizui0223/eog/issues/626).
