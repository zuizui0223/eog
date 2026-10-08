# Dryad 2020 v8: offline exact-source verification following HTTP 401

## State and target

Merged [PR #634](https://github.com/zuizui0223/eog/pull/634) verified **Niskanen et al. 2020**, [Dryad 10.5061/dryad.m0cfxpp10](https://doi.org/10.5061/dryad.m0cfxpp10), **19 August 2020 v8** (internal ID **78498**) and independently froze its published 22-file metadata catalog. PR #635 attempted to download three exact 2020 v8 files using the public REST endpoint and received **HTTP 401 Unauthorized**; it was closed **unmerged**. Dryad download APIs may require OAuth even when public metadata is anonymous; the Dryad dataset web page's **Data files** section documents access to prior versions. Use authorized retrieval, never token bypass or the 2023 v10 revision.

This gate makes **no network request**. It only checks authentic v8 files when supplied locally; the project may merge this *synthetic-tested capability* without claiming the files were physically obtained.

| Source file from historical **v8** | Dryad file ID | Frozen bytes |
|---|---:|---:|
| `Dryad_readme.txt` | 358962 | 4,137 |
| `Pop_size_1997_2012.csv` | 358961 | 1,234 |
| `Pop_size_1998_2013.csv` | 358957 | 1,266 |

The v8 source-declared SHA-256 hashes and the full archived metadata are already pinned under `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json`.

## Using exactly the published v8 files

Use the 2020-08-19 version under [Dryad — Data files](https://datadryad.org/dataset/doi%3A10.5061/dryad.m0cfxpp10), selecting that dated version, rather than the newest download button, which can choose the 2023 version. Retrieve the three exact historical originals through a permitted browser download or institution-authorized Dryad API session. Do not paste access tokens into this repository or CI.

Put these three **unaltered raw files** together in a directory **outside this Git repo**, then run:

```bash
python -m pytest -q tests/test_helgeland_2020_v8_local_bytes_v1.py

python scripts/audit_helgeland_2020_v8_local_bytes_v1.py \
  --source-root /private/helgeland-2020-v8-raw \
  --output build/helgeland-2020-v8.header-only.json \
  --receipt build/helgeland-2020-v8.receipt.json
```

The script rechecks DOI, original v8 number/internal ID/publication date, exact three file IDs, source-declared sizes and digests, and independently streams **all three files as opaque bytes** through local SHA-256. It decodes **only the bounded first physical line** of each file. For the two CSVs, it reports the unclassified delimiter and number of first-line fields (not field values). The README first line is treated as unclassified text. No source row or firstline values are retained in output.

It refuses wrong-size/wrong-hash files, missing or symlinked source files, malformed/oversized/binary-looking first lines, redirects into the raw-source tree, existing output files, and outputs inside raw-source storage. No source data or GitHub credentials are accessed by Actions. The companion CI runs **synthetic local files only**, never a Dryad file download.

### Strict result boundary

Only after an actual local run yields `THREE_LOCALLY_PROVIDED_V8_FILES_HASH_MATCH__ECOLOGY_HOLD` may **exact physical-file identity** be claimed for these three 2020-published files. CI green by itself means the verifier logic passed *fabricated tests*, **not that the real v8 bytes passed**.

Even a verified header shape does **not** qualify semantic fields, original island-year denominators, island-code concordance (2020 8-island versus 2026 11-island scope), detection effort, or an EOG model. 2021–22 outcomes remain unopened for any new held-out exercise. See [Issue #626](https://github.com/zuizui0223/eog/issues/626).

## Why historical publication still matters

The complete 2026 archive is not demonstrated available to outside analysts in 2020. A later validation can use genuine pre-2021 published inputs, with a forecast and comparator frozen before inspecting outcome records. Whether those 2020 tables are actually suitable features is unresolved until the exact v8 originals, schema, values, and coding are validated. Do not retroactively assert a predictive result or add a manuscript based only on source metadata.
