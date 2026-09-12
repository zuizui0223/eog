# Structural manuscript release readiness

Verification date: **2026-09-12**

Repository package version: **0.1.0** (`pyproject.toml`).  
The candidate first submission archive tag remains **`v0.1.0`**, unless the package version is deliberately changed before release.

## Scientific and repository-presentation HOLD — cleared

The scientific and repository-side presentation gates that previously blocked release preparation are now closed.

- [x] final `eog_aislands_isolation_adequacy_v1_3` reference hierarchy frozen before species outcomes;
- [x] 842-island polygon-area input frozen and fingerprinted;
- [x] Natural Earth v5.1.1 continental-mainland geometry frozen and fingerprinted;
- [x] 842-island mainland-distance input frozen and fingerprinted;
- [x] island-isolation adequacy outcome executed exactly once;
- [x] raw matched held-out predictions, applicability, species summaries, uncertainty and result fingerprint frozen;
- [x] adverse `C − R3` result incorporated without weakening R3 or retuning graph scales/taxa;
- [x] journal route selected by the predeclared decision rule: **Ecological Informatics**;
- [x] manuscript framing rewritten around reference-conditioned structural adequacy;
- [x] Figure 1 reference-conditioned inference diagram committed and fingerprinted;
- [x] Figure 2 shows restricted-reference conditional concordance and strong-reference `C − R3` log-loss increment on separate axes;
- [x] R0/R1/R2/R3/C ladder is explicit and `C − R3` remains the sole primary extension contrast;
- [x] presentation-v2 renderers regenerate the committed Figure 1/2 assets exactly;
- [x] repository-side visual QA completed at 1200 px and 800 px widths plus 800 px grayscale rendering, with no clipping/overlap or colour-only sign interpretation detected;
- [x] structural submission package v2 rebuilds the frozen scientific evidence and overlays only the presentation-v2 assets.

Canonical presentation QA receipt:

`manuscript/submission/STRUCTURAL_VISUAL_QA_RECEIPT_2026-09-12.md`

## Human/live-policy gates still blocking DOI reservation and final release

Do **not** reserve/publish the final Zenodo record or create the final `v0.1.0` tag until these are resolved:

- [ ] author list and affiliations fixed;
- [ ] corresponding-author details fixed;
- [ ] author-contribution roles approved;
- [ ] funding statement approved;
- [ ] competing-interests statement approved;
- [ ] ethics/permit relevance checked;
- [ ] originality / simultaneous-submission statement approved;
- [ ] generative-AI disclosure approved by all authors;
- [ ] current Ecological Informatics Guide for Authors checked on the submission date;
- [ ] live accepted vector/raster formats, physical-size/DPI requirements and final publisher-rendered preview checked.

The repository-side grayscale/down-scaling QA does not substitute for the publisher-rendered submission preview.

## DOI-first release sequence after the remaining gates clear

### 1. Create a Zenodo draft and reserve a DOI

Create a new Zenodo upload using the final title, creators and author-approved metadata. Reserve a DOI but do not publish the record yet.

Official Zenodo references retained by the release audit:

- https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/
- https://help.zenodo.org/docs/deposit/create-new-upload/

### 2. Finalize identifiers in the repository

In `manuscript/submission/data_code_availability.md` replace:

- `<RELEASE_TAG>` → `v0.1.0`;
- `<ARCHIVE_DOI>` → the reserved Zenodo DOI.

Any `CITATION.cff` or `.zenodo.json` creators/affiliations must come from author-approved metadata rather than Git history.

### 3. Merge an identifier-only release change

Require repository CI to pass. The identifier-only change must not alter:

- original A-Islands frozen result/direction;
- Tanzania frozen result/direction/fingerprint;
- island-isolation frozen result/direction/fingerprint;
- graph/fold/source/reference contracts;
- manuscript numeric evidence except DOI/tag metadata.

### 4. Build the final submission package from a clean checkout

Run:

```bash
python manuscript/build_structural_submission_package_v2.py --output-dir build/structural_submission_v2
```

The v2 package rebuilds/validates the frozen scientific evidence, uses the committed reference-conditioned Figure 1/2 presentation assets, and records exact source provenance in its generated manifest.

### 5. Require final CI green

Require the normal package matrix and the structural second-paper presentation/package workflow to pass at the release-candidate commit.

### 6. Create tag and GitHub Release

Create tag **`v0.1.0`** at exactly the verified release-candidate commit and create the GitHub Release from that tag.

### 7. Publish the exact archive through the reserved Zenodo draft

Upload/archive the exact source release plus the declared final submission package, verify creators/title/metadata, and publish. The published DOI must equal the DOI already inserted in the repository.

### 8. Verify public provenance

Verify:

- DOI resolves;
- archived files correspond to tag `v0.1.0`;
- archive/package reports the same source commit as the tag target;
- original A-Islands, Tanzania and island-extension fingerprints all match;
- repository release and Zenodo record are mutually discoverable where practical.

Only then mark release/DOI items complete in `manuscript/structural_submission_checklist.md`.

## Tooling boundary

The connected GitHub tooling can inspect and modify repository files, branches, PRs, issues and CI, but it does not expose GitHub Release creation. No Zenodo connector is installed. DOI reservation/publication and final GitHub Release creation therefore remain manual gates and must not be reported as complete until the public records exist.
