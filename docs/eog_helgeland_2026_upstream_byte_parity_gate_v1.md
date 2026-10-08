# Helgeland 2026: authors' GitHub ↔ Dryad v6 byte parity (strictly SHA-256 only)

**Purpose:** Establish whether two *specific* author-published GitHub source files are byte-identical to their registered Dryad v6 counterparts, without interpreting a single individual record, island-year response, census count or genetics result.

Author source repository: [torhanssonfrank/DensityRegulationHouseSparrows](https://github.com/torhanssonfrank/DensityRegulationHouseSparrows), pinned commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5`.

Official frozen source: Dryad `10.5061/dryad.rr4xgxdnq`, dataset ID 177360, **v6** / version ID **421942**, metadata frozen by PR #627 and independently recorded in GitHub Actions run 37793671450. The SHA-256 values are source **declarations** until a file's actual bytes are independently hashed.

## Exactly two declared mappings

| Public authors' GitHub path | Dryad v6 registered file | Dryad file metadata ID |
|---|---|---:|
| `Data/presence_data_1994_2022.txt` | `presence_data_1994_2022_ECY25-1341.txt` | 4576411 |
| `Data/estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt` | `estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy_ECY25-1341.txt` | 4576413 |

No other GitHub ↔ Dryad file equivalence is claimed. Other files differ markedly in apparent sizes and must be independently qualified before assuming they are identical.

## Run contract

Read-only GitHub Actions uses two checkouts: EOG main/PR for the audit code and the **exact full SHA** of the authors' public repository. The script streams the complete two upstream files only as *opaque binary chunks* for SHA-256, checks physical size and digest against the Dryad registered v6 values, and outputs a metadata-only JSON receipt.

It **does read entire source-file bytes into the SHA-256 function**. It **does not parse or decode ecological rows**, make claims about their content, download any Dryad source file, join individuals, infer island occupancy/absence or run scientific models. Do not assert that the raw source file was never accessed. Only two explicitly mapped paths can be read.

```bash
python -m pytest -q tests/test_helgeland_2026_upstream_byte_parity_v1.py
python scripts/audit_helgeland_2026_upstream_byte_parity_v1.py \
  --upstream-checkout upstream_public \
  --output build/helgeland-2026-upstream-parity-v1.json
```

A `MATCHES_TWO_FROZEN_DRYAD_V6_FILES` receipt would establish local byte parity for **only the two listed files** (relative to Dryad's v6 registered hashes). `HOLD_UPSTREAM_DRYAD_BYTE_MISMATCH` means no such identity may be claimed. All other source identities remain unqualified.

**This is not a physical header attestation**, even if SHA-256 matches. Future work must separately inspect only physical first-line column names under the same pinned byte identity and then qualify the prospective `as-of-t` observation process.

## Hard scientific HOLD remains

- No surveyed-zero island-year panel or encounter effort denominator verified
- No prospective `as-of-t` correction of bidirectional `downup` imputation or posterior `N_corr`
- No 2026 dataset direct nestling→adult dispersal event values read
- No colonization/recolonization direction, source population or held-out ecological endpoint authorized

Track at [Issue #626](https://github.com/zuizui0223/eog/issues/626). The EOG-WF frozen denominators and pre-existing observations remain unchanged.
