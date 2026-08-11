# Structural manuscript submission package

This directory contains the submission-facing text files for the structural-reachability paper. Scientific figures and result tables are rebuilt from frozen repository inputs rather than edited here by hand.

## Offline rebuild

From a clean repository checkout:

```bash
python manuscript/build_structural_submission_package.py --output-dir build/structural_submission
```

The builder:

1. rebuilds Figure 1 from the frozen semantic/competitor contract;
2. rebuilds Figure 2 from the committed A-Islands frozen projections;
3. rebuilds Figure 3 from the frozen Tanzania result and archived species projection;
4. rebuilds Figure 4 from the two benchmark projections without putting incompatible endpoints on one axis;
5. rebuilds Table 3 and Table S1 from the frozen Figure 2/3 evidence;
6. rebuilds Figure 5 from the current evidence-to-result audit contract;
7. verifies scientific SVG, caption, accessibility, plotting-data, and table outputs against the committed manuscript assets;
8. copies the complete manuscript and submission-facing files into the separate package directory;
9. writes `submission_package_manifest.json` containing the exact Git commit and SHA-256 of every packaged file.

The command is designed to require no network access because source acquisition and biological outcome generation are upstream frozen stages. A package build therefore verifies the manuscript-facing projection of existing frozen evidence; it does not rerun the full A-Islands or Tanzania source-to-outcome pipelines.

## Files requiring author completion

Before journal upload, all authors must resolve the items listed in `submission_manifest.json`, especially:

- final author list and affiliations;
- corresponding-author details;
- contribution roles;
- funding and competing interests;
- originality/simultaneous-submission confirmation;
- final release tag, commit and archive DOI;
- the live journal requirements on the actual submission date.

## Scientific stop rule

Submission packaging must not change the frozen evidence direction. A-Islands remains the positive added-information benchmark. Tanzania remains adverse under primary LOSO after a strong matrix-aware current-flow reference, with an uncertain spatial-block sensitivity. A packaging or prose change that alters those directions is a hard failure, not an editorial update.
