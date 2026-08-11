# Structural manuscript release readiness

Verification date: **2026-08-12**

Repository package version: **0.1.0** (`pyproject.toml`).

At the time this checklist was written, the GitHub repository had no existing tags and no existing GitHub releases. The recommended first submission archive tag is therefore **`v0.1.0`**, provided no intervening versioning decision changes the package version before release.

## Why the DOI must be reserved before the final tag

The submission manuscript should cite the archive DOI, but a source file cannot contain the SHA of the commit that contains itself: changing the file to add that SHA creates a different commit. EOG therefore uses two separate provenance mechanisms:

1. the manuscript-facing Data/Code Availability statement contains the stable release tag and archive DOI;
2. `submission_package_manifest.json`, generated from the final checkout, records the exact source Git commit automatically.

Zenodo supports reserving a DOI while an upload is still a draft, specifically so the DOI can be inserted into files before publication. Official documentation:

- https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/
- https://help.zenodo.org/docs/deposit/create-new-upload/

This makes the following order preferable for the submission archive.

## Hard gates before reserving/publishing the release

Do **not** create the final `v0.1.0` tag until all of these are resolved:

- [ ] author list and affiliations fixed;
- [ ] corresponding-author details fixed;
- [ ] author-contribution roles approved;
- [ ] funding statement approved;
- [ ] competing-interests statement approved;
- [ ] ethics/permit relevance checked;
- [ ] originality / simultaneous-submission statement approved;
- [ ] generative-AI disclosure reviewed against the live journal policy;
- [ ] live *Ecological Informatics* Guide for Authors checked in a normal browser;
- [ ] final figure file-format/resolution and visual-QA requirements checked.

Scientific outcome gates are already frozen and must not be reopened by release preparation.

## Preferred DOI-first release sequence

### 1. Create a Zenodo draft manually

Create a new Zenodo upload and fill the creator/title/resource metadata. Do not publish it yet.

Use **Get a DOI now** to reserve a DOI. Keep the draft: deleting the draft loses the reservation.

Record the reserved DOI exactly as returned by Zenodo.

### 2. Finalize release identifiers in the repository

In `manuscript/submission/data_code_availability.md` replace:

- `<RELEASE_TAG>` → `v0.1.0`
- `<ARCHIVE_DOI>` → the reserved Zenodo DOI

Do not add a hard-coded `<RELEASE_COMMIT>` field. The final package manifest records the exact commit automatically.

If software citation metadata (`CITATION.cff` or `.zenodo.json`) is added, creators and affiliations must come from the author-approved metadata; do not infer them from Git history. Note that Zenodo's GitHub documentation states that `.zenodo.json` takes precedence if both `.zenodo.json` and `CITATION.cff` are present.

### 3. Merge the identifier-only release PR

Require all repository CI to pass. The PR must not alter:

- A-Islands frozen result or direction;
- Tanzania frozen result or direction;
- graph/fold/source contracts;
- result fingerprints;
- manuscript numeric values except DOI/tag metadata.

The resulting `main` commit is the release candidate commit.

### 4. Build the submission package from the final commit

Run from a clean checkout:

```bash
python manuscript/build_structural_submission_package.py --output-dir build/structural_submission
```

Check `build/structural_submission/submission_package_manifest.json` and require:

- `source_commit` equals the final `main` commit;
- A-Islands declared/estimable counts remain 886/845;
- A-Islands primary concordance remains 0.6177465917820878;
- Tanzania species count remains 60;
- Tanzania result fingerprint remains `6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`;
- Tanzania primary LOSO log-loss difference remains +0.032113119;
- all packaged file hashes are present.

### 5. Run and record final CI

Require the normal package matrix and all benchmark/audit workflows triggered by the final release-candidate commit to be green. Record the commit and workflow run identifiers in the release notes or archive metadata.

### 6. Create tag and GitHub release

Create tag **`v0.1.0`** at exactly the verified release-candidate commit, then create the GitHub Release from that tag.

There is no GitHub release-write action available in the current ChatGPT connector, so this step requires the GitHub UI or an authenticated local GitHub CLI/API workflow.

### 7. Upload the exact release object to the reserved Zenodo draft

Upload/archive the source release and the rebuilt structural submission package or its declared archival contents into the same Zenodo draft whose DOI was reserved in step 1. Confirm the metadata and creators, then publish the record.

The DOI in the published Zenodo record must equal the DOI already inserted into the repository manuscript files.

### 8. Verify the public archive

After publication, verify:

- the DOI resolves;
- the archived files correspond to tag `v0.1.0`;
- the archived submission package reports the same `source_commit` as the tag target;
- the frozen Tanzania fingerprint matches;
- repository release and Zenodo record are mutually discoverable in their metadata where practical.

Only then mark the DOI/release checkboxes complete in `manuscript/structural_submission_checklist.md`.

## Alternative: Zenodo GitHub integration

Zenodo can automatically ingest enabled GitHub repositories when a GitHub release is created:

- https://help.zenodo.org/docs/github/enable-repository/
- https://help.zenodo.org/docs/github/archive-software/github-upload/

That route is convenient, but the DOI is normally produced as part of release archiving. For this manuscript, reserving a DOI before the final tag is preferable because it allows the final tagged manuscript files to contain the DOI without a follow-up source edit.

## Current tooling boundary

The connected GitHub app can inspect and modify repository files, branches, PRs, issues and CI, but it does not expose a GitHub Release-creation action. No Zenodo connector is installed. Consequently DOI reservation/publication and final GitHub Release creation are deliberate manual gates; they must not be reported as completed until their public records exist.
