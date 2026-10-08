# Helgeland 2026 Dryad source-identity gate — PUBLIC JSON ONLY

**Status: `SOURCE_DECLARED_METADATA_FROZEN__NO_BIRD_BYTES_VERIFIED` following the first successful public JSON inventory.** This audit **does not download any bird observations, read any physical file header, or assess a biological result**.

## Source

Hansson Frank et al. (2026), Dryad [10.5061/dryad.rr4xgxdnq](https://doi.org/10.5061/dryad.rr4xgxdnq), public page published 28 January 2026.

The public-facing page lists **18 files**, spanning observed 1994–2022 presence, capture–recapture and processed demographic data plus source code. The precise expected *filenames* (not biological row values or checksums) are declared in `scripts/audit_helgeland_2026_dryad_metadata_v1.py`.

The browser-facing listing is **not** sufficient to establish an immutable Dryad internal version ID or per-file SHA-256. GitHub blobs from [the authors' repository](https://github.com/torhanssonfrank/DensityRegulationHouseSparrows) are not the same as independently verified Dryad source bytes, and filenames differ in suffixes.

## Frozen public version (8 October 2026)

The original read-only GitHub Actions run **37793671450** uploaded artifact **11556844942**, ZIP SHA-256 `aa0a7f0ff034ac8d254f3633d5e7b2e2a8a32e5285520e4906d3071ca33d76d4`. The artifact contains one metadata-only JSON receipt, inspected independently.

- Official Dryad dataset ID: **177360**
- Published source version: **v6**, numeric version ID **421942**
- Exactly **18** registered file records with file IDs, source-reported sizes and syntactically valid `sha-256` digests.
- Relevant file IDs: `presence_data_1994_2022_ECY25-1341.txt` **4576411**; `juvenile_to_ad_surival_histories_long_ECY25-1341.txt` **4576414**; `cleaned_density_dependence_data_ECY25-1341.txt` **4576415**; `estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy_ECY25-1341.txt` **4576413**.

The full file-name/ID/size/source-declared digest inventory is **frozen, not guessed**, at `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_source_metadata_frozen_v1.json`. Each future live audit must match the exact frozen version and all 18 file identities, or be declared HOLD. GitHub package tests use synthetic fixtures only. **No registered SHA-256 has been verified against an actual Dryad data file's bytes.**

## Execution

Run offline unit tests first:

```bash
python -m pytest -q tests/test_helgeland_2026_dryad_metadata_v1.py
```

The live auditor accesses **only** the canonical public JSON endpoint `/api/v2/datasets/doi%3A10.5061%2Fdryad.rr4xgxdnq` and that dataset's returned numeric version `/api/v2/versions/{version_id}/files`. It explicitly refuses HTTP download endpoints, untrusted hosts, query bypass and paginated/incomplete file inventories. It never opens the listed source files.

```bash
python scripts/audit_helgeland_2026_dryad_metadata_v1.py \
  --verify-frozen validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_source_metadata_frozen_v1.json \
  --output build/helgeland-2026-dryad-public-json-v1.json
```

A read-only GitHub Actions job is defined in `.github/workflows/helgeland-2026-dryad-metadata-v1.yml`, reusing the 2024/2025 successful metadata audit infrastructure.

## Results and boundaries

If and only if the public API returns an exact **18-file** named inventory with canonical DOI/version and well-formed source-declared SHA-256, emit `PUBLIC_METADATA_IDENTITY_RETRIEVED_SHA256_DECLARED`. The receipt captures the dataset/version IDs, per-file metadata IDs, sizes and source-reported digest values. **The SHA-256 values are reported by Dryad; they are not local full-file hash verification**.

If the API is unreachable, the file set differs, the API returns paginated records, or a digest is missing, fail closed. Keep the receipt with `HOLD_SOURCE_METADATA_UNVERIFIED` or `HOLD_SOURCE_DIGEST_INCOMPLETE`. No automatic source substitution or guessed version.

The initial public-JSON receipt has now been reviewed and frozen. This does not authorize biological file access, which requires separate physical-byte/header, observation-process and temporal eligibility gates.

### Scientific status cannot be upgraded by source metadata

- `NO_SURVEYED_ZERO_PANEL_VERIFIED`: the published analysis groups **observed birds** to construct `N_obs`; missing island-year records cannot be interpreted as sampled absences.
- `NO_AS_OF_T_PREPROCESSING_CERTIFIED`: published code uses future-aware `fill(..., .direction="downup")`, and substitutes `NA/zero → 1` in model matrices.
- `NO_DRYAD_GITHUB_BYTE_IDENTITY_VERIFIED`: a GitHub blob hash is not a matching Dryad file SHA-256.
- `NO_INDEPENDENT_HELDOUT_EVENT_BENCHMARK`: exposed historical Aldra, Ytre Kvarøy, Sundøy and Selvær events remain exploratory, and island-roster matches are not fully qualified.
- Neither colonization histories, direct dispersal directions nor predictions at year `t` are certified by this metadata-only step.

Trace scientific source audit and stop rules at [EOG Issue #626](https://github.com/zuizui0223/eog/issues/626).
