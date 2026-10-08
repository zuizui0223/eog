# Source-file byte attestations: Helgeland Niskanen's 2020 v8

**Scope:** the three specific historically published small files in **2020-08-19 v8**, Dryad `10.5061/dryad.m0cfxpp10`, numeric version ID **78498**. This is materially different from downloading the latest 2023 v10 snapshot and pretending it was public before 2021.

## Preregistered source IDs and source-declared hashes

Source metadata and archive publication date were frozen under merged EOG PR #634, `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json`.

| Filename | File metadata ID | Registered size |
|---|---:|---:|
| `Pop_size_1997_2012.csv` | 358961 | 1,234 bytes |
| `Pop_size_1998_2013.csv` | 358957 | 1,266 bytes |
| `Dryad_readme.txt` | 358962 | 4,137 bytes |

All three have source-declared SHA-256 checksums. The read-only script fetches **exactly these file-ID-specific public downloads**, caps the byte count to the frozen size, hashes all downloaded bytes, and requires size plus SHA-256 equality. It only decodes the **first physical line of each** and emits a first-line hash, a tentative CSV separator type and number of first-line fields. **Actual first-line values are not emitted**, because the first line might itself contain data rather than a genuine header. Every subsequent physical line remains opaque, and the script neither parses nor publishes any bird, demographic, or population records.

This is the first deliberate **historic actual-file byte** access beyond public metadata. The source file bytes are not retained in GitHub Actions artifacts or checked into EOG. Failure to download, redirects to non-HTTPS, unexpected file size/hash, or malformed first line must stop the dedicated CI. Do not automatically switch to latest v10, use website attachments with similar names or change the source hash to force a pass.

## What it could qualify

The physical identity of small **historically published pre-2021** inputs. It does *not* yet prove the 8-island numeric coding, whether abundance values represent adjusted/posterior estimates, an annual surveyed-zero denominator, parity with the 2026 11-island source, or any EOG prediction/reachability result. Positive ecological response rows for 2021–22 must remain unopened until an actual source-compatible frozen model and comparator exist.

The 2014 v1 `DemographicNe-Datafile.csv` remains metadata-only in this PR, with Dryad declaring **MD5** rather than a source SHA-256. No inferred cross-archive row join is authorized.

See [Issue #626](https://github.com/zuizui0223/eog/issues/626) for the broader scientific and temporal information contract.
