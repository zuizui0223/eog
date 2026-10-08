# Helgeland 2026: two byte-verified PHYSICAL FIRST-LINE HEADERS only

**Stage: two physical first-line headers successfully attested, with biological inference still HOLD.** PR #628 independently verified the entire source bytes of **exactly two** author-GitHub files against Dryad 2026 **v6 / version 421942** registered SHA-256 digests. PR #628 was merged at commit `f5080fa3277fe56ebc82eb4b5a1e55b77426420d`. The other 16 Dryad files and all ecological outcomes are unqualified.

This step restricts interpretation further: the 1994–2022 presence file and the 11-island estimated abundance file have a physical **first header line** accessible in the pinned authors' GitHub revision. The workflow first rehashes those **whole file bytes**, then reads and decodes **only the first physical line of each**. The first line is parsed with the **semicolon** separator demonstrated in the public R readers; optional quoted column names are handled. No second or subsequent physical line is decoded, and no individual data row is parsed, joined, exported or scored.

## Declared schema minimum, to check against ACTUAL physical headers

- `Data/presence_data_1994_2022.txt`: `ID`, `Year`, `date`, `Island`, `Location`, `stage` (observed in published R code as source variables).
- `Data/estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt`: `Location`, `Island`, `Year`, `N_corr`, `.lower`, `.upper`, `.width`, `N_obs` (public GitHub source first-line structure).

A missing/renamed expected column, duplicate header, malformed quote, wrong delimiter, byte mismatch, invalid source version or header greater than 4096 bytes is a **STOP**, not an invitation to infer a synonym. The result artifact may contain source **column names only** and the SHA-256 of the first line, never any bird or demographic records.

## First positive physical-header result

Dedicated workflow run **37797505583** verified two full-file byte streams against Dryad v6 and attested both physical first lines. The exported **header-only** JSON artifact **11559381569** (ZIP SHA-256 `402c01b4ffae08b6f351d6d407e9dfbfad45f745c714e4fd8fe2ca99a6a71c82`) was opened and checked. It contains:

- Presence file physical columns in order: `Year`, `date`, `scriptsex`, `Island`, `Location`, `stage`, `Least_age`, `Least_hatchyear`, `ID`.
- Posterior abundance file physical columns in order: `Location`, `Island`, `Year`, `N_corr`, `.lower`, `.upper`, `.width`, `N_obs`.

The first-line SHA-256 hashes, exact column names and artifact ID are frozen in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_two_file_physical_headers_frozen_v1.json`. Repeat dedicated CI must match those exact first-line values and maintain the biological HOLD.

`scriptsex` is a **physical column name only**; no claim is made about whether it denotes genetically corrected sex or an observation-time characteristic. The presence of `ID` and `date` does not prove that source–destination transitions, sample effort, or future information can be distinguished from the records.

## Execution

- Frozen Dryad version: `10.5061/dryad.rr4xgxdnq`, v6, internal version ID `421942`.
- Author repo commit: `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5`.
- Module: `scripts/audit_helgeland_2026_two_file_headers_v1.py`.
- Dedicated workflow: `.github/workflows/helgeland-2026-physical-headers-v1.yml`.
- Tests: `tests/test_helgeland_2026_two_file_headers_v1.py` (entirely fabricated headers/rows), alongside existing opaque-parity tests.

Even if both real physical headers pass, **do not** promote any of the following: observation-effort denominator, surveyed-zero island-year grid, ringed nestling→first later recruit movement, present-time availability (`as-of-t`), independent held-out forecast or first-island colonization. Both actual source whole-byte hashing and first physical-line reading occur; the former is not reading observation rows as data, and the latter must not be confused with the full body content.

Track at [Issue #626](https://github.com/zuizui0223/eog/issues/626). No EOG-WF frozen result is modified.
