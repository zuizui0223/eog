# Structural manuscript release readiness

Verification date: **2026-08-12**

Repository package version: **0.1.0** (`pyproject.toml`).

At the time of the release audit, the GitHub repository had no existing tags and no existing GitHub releases. The candidate first submission archive tag remains **`v0.1.0`**, provided no intervening versioning decision changes the package version.

## Current scientific HOLD before DOI reservation

The DOI/release sequence is **not yet active**. The project has selected a prospectively frozen A-Islands island-isolation adequacy test before final submission positioning.

Do not reserve the final Zenodo DOI, create the final tag or treat the current manuscript as a release candidate until all of the following scientific gates are complete:

- [x] final `eog_aislands_isolation_adequacy_v1_3` reference hierarchy frozen before species outcomes;
- [x] 842-island polygon-area input frozen and fingerprinted;
- [x] Natural Earth v5.1.1 continental-mainland geometry frozen and fingerprinted;
- [x] 842-island mainland-distance input frozen and fingerprinted;
- [ ] island-isolation adequacy outcome executed exactly once;
- [ ] raw matched held-out predictions, applicability, species summaries, uncertainty and result fingerprint frozen;
- [ ] result incorporated without weakening R3 or retuning graph scales/taxa;
- [ ] journal route selected by the predeclared `C − R3` decision rule;
- [ ] final title, manuscript, figures and reference ledger rewritten for that route.

The original authoritative A-Islands and Tanzania outcomes remain frozen throughout.

## Why the DOI is still reserved before the final tag — after the scientific HOLD clears

The final submission manuscript should cite the archive DOI, but a source file cannot contain the SHA of the commit that contains itself: changing the file to add that SHA creates a different commit. EOG therefore uses two separate provenance mechanisms:

1. the manuscript-facing Data/Code Availability statement contains the stable release tag and archive DOI;
2. `submission_package_manifest.json`, generated from the final checkout, records the exact source Git commit automatically.

Zenodo supports reserving a DOI while an upload remains a draft, allowing the DOI to be inserted into files before publication. Therefore the DOI-first sequence remains appropriate **only after the island result and journal route are frozen**.

Official Zenodo documentation used by the project:

- `https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/`
- `https://help.zenodo.org/docs/deposit/create-new-upload/`

## Human/live-policy gates before reserving the DOI

After the scientific HOLD clears, also require:

- [ ] author list and affiliations fixed;
- [ ] corresponding-author details fixed;
- [ ] author-contribution roles approved;
- [ ] funding statement approved;
- [ ] competing-interests statement approved;
- [ ] ethics/permit relevance checked;
- [ ] originality / simultaneous-submission statement approved;
- [ ] generative-AI disclosure reviewed against the **selected journal's** live policy;
- [ ] selected journal's live Guide for Authors checked in a normal browser;
- [ ] final figure file-format/resolution and visual-QA requirements checked.

## Preferred DOI-first release sequence after all gates clear

### 1. Create a Zenodo draft manually and reserve a DOI

Create a new Zenodo upload using the final title, creators and resource metadata. Do not publish it yet. Reserve a DOI and keep the draft.

### 2. Finalize identifiers in the repository

In `manuscript/submission/data_code_availability.md` replace:

- `<RELEASE_TAG>` → `v0.1.0`;
- `<ARCHIVE_DOI>` → the reserved Zenodo DOI.

Do not add a hard-coded release-commit placeholder. The package manifest records the exact final commit automatically.

Any `CITATION.cff` or `.zenodo.json` creators/affiliations must come from author-approved metadata rather than Git history.

### 3. Merge the identifier-only release PR

Require all repository CI to pass. The PR must not alter:

- original A-Islands frozen result/direction;
- Tanzania frozen result/direction/fingerprint;
- island-isolation frozen result/direction/fingerprint;
- graph/fold/source/reference contracts;
- manuscript numeric evidence except DOI/tag metadata.

### 4. Build the final submission package from a clean checkout

Run:

```bash
python manuscript/build_structural_submission_package.py --output-dir build/structural_submission
```

The builder must be extended before release to package and validate the final island-extension evidence in addition to the original A-Islands/Tanzania evidence.

Require the generated package manifest to record the exact final `source_commit` and every authoritative result fingerprint.

### 5. Require final CI green

The normal package matrix, original benchmark/audit workflows and the final island-extension verification workflow must all be green at the release-candidate commit.

### 6. Create tag and GitHub Release

Create tag **`v0.1.0`** at exactly the verified release-candidate commit and create the GitHub Release from that tag.

The current GitHub connector does not expose release creation, so this step remains a deliberate manual/UI or authenticated CLI/API gate.

### 7. Publish the exact archive through the reserved Zenodo draft

Upload/archive the exact source release plus the final submission package or declared archival contents, verify creators/title/metadata and publish.

The published DOI must equal the DOI already inserted into the repository manuscript files.

### 8. Verify public provenance

Verify:

- DOI resolves;
- archived files correspond to tag `v0.1.0`;
- archive/package reports the same source commit as the tag target;
- original A-Islands, Tanzania and island-extension fingerprints all match;
- repository release and Zenodo record are mutually discoverable where practical.

Only then mark release/DOI items complete in `manuscript/structural_submission_checklist.md`.

## Tooling boundary

The connected GitHub app can inspect and modify repository files, branches, PRs, issues and CI, but it does not expose GitHub Release creation. No Zenodo connector is installed. DOI reservation/publication and final GitHub Release creation therefore remain manual gates and must not be reported as complete until the public records exist.