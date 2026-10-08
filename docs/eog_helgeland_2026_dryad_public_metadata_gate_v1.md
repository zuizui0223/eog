# Helgeland 2026 Dryad source-identity gate — PUBLIC JSON ONLY

**Status: `HOLD_SOURCE_METADATA_UNVERIFIED` until live official Dryad JSON is returned and reviewed.** This audit **does not download any bird observations, read any physical file header, or assess a biological result**.

## Source

Hansson Frank et al. (2026), Dryad [10.5061/dryad.rr4xgxdnq](https://doi.org/10.5061/dryad.rr4xgxdnq), public page published 28 January 2026.

The public-facing page lists **18 files**, spanning observed 1994–2022 presence, capture–recapture and processed demographic data plus source code. The precise expected *filenames* (not biological row values or checksums) are declared in `scripts/audit_helgeland_2026_dryad_metadata_v1.py`.

The browser-facing listing is **not** sufficient to establish an immutable Dryad internal version ID or per-file SHA-256. GitHub blobs from [the authors' repository](https://github.com/torhanssonfrank/DensityRegulationHouseSparrows) are not the same as independently verified Dryad source bytes, and filenames differ in suffixes.

## Execution

Run offline unit tests first:

```bash
python -m pytest -q tests/test_helgeland_2026_dryad_metadata_v1.py
```

The live auditor accesses **only** the canonical public JSON endpoint `/api/v2/datasets/doi%3A10.5061%2Fdryad.rr4xgxdnq` and that dataset's returned numeric version `/api/v2/versions/{version_id}/files`. It explicitly refuses HTTP download endpoints, untrusted hosts, query bypass and paginated/incomplete file inventories. It never opens the listed source files.

```bash
python scripts/audit_helgeland_2026_dryad_metadata_v1.py \
  --output build/helgeland-2026-dryad-public-json-v1.json
```

A read-only GitHub Actions job is defined in `.github/workflows/helgeland-2026-dryad-metadata-v1.yml`, reusing the 2024/2025 successful metadata audit infrastructure.

## Results and boundaries

If and only if the public API returns an exact **18-file** named inventory with canonical DOI/version and well-formed source-declared SHA-256, emit `PUBLIC_METADATA_IDENTITY_RETRIEVED_SHA256_DECLARED`. The receipt captures the dataset/version IDs, per-file metadata IDs, sizes and source-reported digest values. **The SHA-256 values are reported by Dryad; they are not local full-file hash verification**.

If the API is unreachable, the file set differs, the API returns paginated records, or a digest is missing, fail closed. Keep the receipt with `HOLD_SOURCE_METADATA_UNVERIFIED` or `HOLD_SOURCE_DIGEST_INCOMPLETE`. No automatic source substitution or guessed version.

After a successful metadata artifact, **review the returned identities and freeze the result in a separate explicitly version-pinned record before biological file access**. This PR does not assume or fabricate version IDs, file IDs, or checksums.

### Scientific status cannot be upgraded by source metadata

- `NO_SURVEYED_ZERO_PANEL_VERIFIED`: the published analysis groups **observed birds** to construct `N_obs`; missing island-year records cannot be interpreted as sampled absences.
- `NO_AS_OF_T_PREPROCESSING_CERTIFIED`: published code uses future-aware `fill(..., .direction="downup")`, and substitutes `NA/zero → 1` in model matrices.
- `NO_DRYAD_GITHUB_BYTE_IDENTITY_VERIFIED`: a GitHub blob hash is not a matching Dryad file SHA-256.
- `NO_INDEPENDENT_HELDOUT_EVENT_BENCHMARK`: exposed historical Aldra, Ytre Kvarøy, Sundøy and Selvær events remain exploratory, and island-roster matches are not fully qualified.
- Neither colonization histories, direct dispersal directions nor predictions at year `t` are certified by this metadata-only step.

Trace scientific source audit and stop rules at [EOG Issue #626](https://github.com/zuizui0223/eog/issues/626).
