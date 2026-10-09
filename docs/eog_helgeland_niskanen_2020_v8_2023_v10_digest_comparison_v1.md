# Is a later Dryad v10 copy byte-identical to a file already published in 2020 v8?

## Strict historical-availability test (metadata-only)

The genuine **2020-08-19 Dryad v8** Niskanen archive `10.5061/dryad.m0cfxpp10`, internal version **78498**, was source-inventory frozen in merged #634. Attempts to fetch its *actual files* through REST and the official public web UI yielded 401 and 403 respectively (closed unmerged PRs #635 and #638). The offline byte verifier in merged #636 remains available for authorized genuine original files.

The later **2023-01-19 v10** (internal **208617**) has some of the same filenames. But **filename or size coincidence is insufficient** to declare the newer copy a historically valid 2020 input. Only *identical whole-file byte content* can qualify the copy as a replica of what already existed in 2020.

This PR compares public Dryad **v10 registered source SHA-256 plus file size**, for exactly the **three v8-frozen historical file names**, against the independently source-frozen v8 registered values:
- `Dryad_readme.txt`, v8 file ID 358962
- `Pop_size_1997_2012.csv`, v8 file ID 358961
- `Pop_size_1998_2013.csv`, v8 file ID 358957

It fetches only the official **v10 `/api/v2/versions/208617/files?per_page=100` JSON**; **no data file bytes**, rows, genotype records, model results, or 2021–22 response data are read. A pass means both **source metadata assertions** identify identical digest and size for each file; it is **not independent byte computation**.

### Interpretation

If all three registered values agree, a copy from the newer archive could be *considered for offline source verification* **only if its complete actual bytes independently hash to the frozen 2020-v8 SHA-256**. Such a matching copy would have v8-identical content but **does not license using any 2023-only variables or files as a 2020 input**.

If even one digest or file size differs, no such equivalence is claimed and the later copy must not substitute for v8.

Regardless of result, field survey effort, island-code crosswalk, annual time labels, biological model fit and prospective EOG performance all remain HOLD. The 2020 and 2023 copies may even share byte content but still have model-derived population-size values with retrospectively aggregated seasons; content equivalence alone cannot settle that.

This audit is a defensible alternate source-*identity* check following a pair of public-download HTTP errors, not an ecological finding. All evidence and stop rules are tracked in [Issue #626](https://github.com/zuizui0223/eog/issues/626).
