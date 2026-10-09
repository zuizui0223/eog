# Zenodo preservation route for genuine pre-2021 Niskanen input files

## Why this route matters

The official Dryad source-metadata record (merged PR #639) proves that the three specific Niskanen et al. files already published on **2020-08-19 v8** have unchanged **registered SHA-256 and size** in the later 2023 v10 dataset. Attempts in PRs #635, #638 and #640 to retrieve exact Dryad files via anonymous REST and official web downloads failed with HTTP401/403. The v8 source bytes were not obtained.

The U.S. National Library of Medicine's dataset catalog lists **a Zenodo repository entry** for the same Niskanen paper as well as its Dryad repository entry. Zenodo's [Dryad community](https://zenodo.org/communities/dryad/about) says it stores preservation copies of Dryad data. That is a **separate lawful public repository candidate**, not permission to retrieve unpublished or restricted source data.

## Strict source and eligibility conditions

One read-only job searches public Zenodo **record JSON metadata** for exactly the study *Consistent scaling of inbreeding depression in space and time in a house sparrow metapopulation* and identifiable Niskanen/Dryad provenance. Even an identically titled but unrelated dataset does not qualify without creator and provenance evidence.

It then requests only these **three exact-named individual files** from Zenodo public content links, and only if their declared size matches the Dryad 2020 v8 archive:

| Historical source name | Original v8 Dryad file ID | Registered original byte size |
|---|---:|---:|
| `Dryad_readme.txt` | 358962 | 4,137 |
| `Pop_size_1997_2012.csv` | 358961 | 1,234 |
| `Pop_size_1998_2013.csv` | 358957 | 1,266 |

Full downloaded byte streams, at most 5 kB per file, must independently SHA-256 match the **original 2020 v8 frozen digest** in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json` (merged #634). Downloaded bytes are **never** serialized, parsed as biological records or stored in artifacts. No 2023-only field or newly added file is ever eligible as a 2020 source.

## Possible outputs

- `THREE_ZENODO_PRESERVATION_FILES_FULL_HASH_MATCH_ORIGINAL_2020_V8`: authentic actual-file byte equality for just these three historic inputs, regardless of later preservation timestamp. This still does **not** mean that site codes, surveyed-zero effort, ecological features or prediction performance are qualified.
- `HOLD_NO_MATCHING_ZENODO_SOURCE_RECORD`: no correctly identified public mirror was found.
- `HOLD_ZENODO_PRESERVATION_FILES_NOT_VERIFIED`: identified candidate lacks an exact individual file, has wrong size/hash or is not publicly downloadable.
- `HOLD_ZENODO_SOURCE_SEARCH_UNAVAILABLE`: public Zenodo API was unreachable or not parseable.

No opportunistic large ZIP download, no private credentials, no DOI or file-label substitution, and no force-passing digest assertion. The CI runs fabricated-source tests first. A **real** source PASS is necessary to merge this particular proof; otherwise close unmerged with a report and keep the merged #636 local offline verifier as the guaranteed future path.

The control issue is [#626](https://github.com/zuizui0223/eog/issues/626). The original ecological endpoint and historical eight-to-eleven source-code crosswalk remain on HOLD even if file bytes match.
