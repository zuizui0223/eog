# Is a later Dryad v10 copy byte-identical to a file already published in 2020 v8?

## Strict historical-availability test (metadata-only)

The genuine **2020-08-19 Dryad v8** Niskanen archive `10.5061/dryad.m0cfxpp10`, internal version **78498**, was source-inventory frozen in merged #634. Attempts to fetch its *actual files* through REST and the official public web UI yielded 401 and 403 respectively (closed unmerged PRs #635 and #638). The offline byte verifier in merged #636 remains available for authorized genuine original files.

The later **2023-01-19 v10** (internal **208617**) has some of the same filenames. But **filename or size coincidence is insufficient** to declare the newer copy a historically valid 2020 input. Only *identical whole-file byte content* can qualify the copy as a replica of what already existed in 2020.

This PR compares public Dryad **v10 registered source SHA-256 plus file size**, for exactly the **three v8-frozen historical file names**, against the independently source-frozen v8 registered values:
- `Dryad_readme.txt`, v8 file ID 358962
- `Pop_size_1997_2012.csv`, v8 file ID 358961
- `Pop_size_1998_2013.csv`, v8 file ID 358957

It fetches only the official **v10 `/api/v2/versions/208617/files?per_page=100` JSON**; **no data file bytes**, rows, genotype records, model results, or 2021–22 response data are read. A pass means both **source metadata assertions** identify identical digest and size for each file; it is **not independent byte computation**.

## Observed official source-metadata result — 2026-10-09

First dedicated read-only workflow run **37862858112** uploaded metadata-only artifact **11587525387**, ZIP SHA-256 `3e74a16b2a514824262068ba607cc834b1ccb76b1f1d23e830418f103c3852e2`. Its JSON was independently opened.

**All three** original 2020 v8 files have **the same Dryad-registered SHA-256 AND file size** as their later v10 records:

| 2020 source filename | v8 file ID | v10 file ID | Metadata check |
|---|---:|---:|---|
| Dryad_readme.txt | 358962 | 1952534 | Exact digest + size |
| Pop_size_1997_2012.csv | 358961 | 1952533 | Exact digest + size |
| Pop_size_1998_2013.csv | 358957 | 1952529 | Exact digest + size |

All source-declared identity relationships are frozen in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_niskanen_v8_v10_registered_digest_match_frozen_v1.json`. Repeat CI must obtain the same official v10 JSON identities and independently check against the original v8 metadata.

**Still unverified:** No actual original or later copy bytes have been acquired or hashed; Dryad's source declarations are evidence of registered parity, not proof of independent SHA-256 on downloaded files. No island records or biological outcome analyses are authorized.

### Interpretation

If all three registered values agree, a copy from the newer archive could be *considered for offline source verification* **only if its complete actual bytes independently hash to the frozen 2020-v8 SHA-256**. Such a matching copy would have v8-identical content but **does not license using any 2023-only variables or files as a 2020 input**.

If even one digest or file size differs, no such equivalence is claimed and the later copy must not substitute for v8.

Regardless of result, field survey effort, island-code crosswalk, annual time labels, biological model fit and prospective EOG performance all remain HOLD. The 2020 and 2023 copies may even share byte content but still have model-derived population-size values with retrospectively aggregated seasons; content equivalence alone cannot settle that.

This audit is a defensible alternate source-*identity* check following a pair of public-download HTTP errors, not an ecological finding. All evidence and stop rules are tracked in [Issue #626](https://github.com/zuizui0223/eog/issues/626).
