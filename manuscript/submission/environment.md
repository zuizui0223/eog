# Reproducibility environment boundary

The repository contains two different reproducibility targets that should not be conflated.

## 1. Manuscript-facing offline submission build

Command:

```bash
python manuscript/build_structural_submission_package.py --output-dir build/structural_submission
```

This stage consumes only committed frozen projections, manifests, figure contracts, and sidecars. It does not download A-Islands, CHELSA, or Tanzania data and does not refit the empirical benchmark models. The package builder itself uses the Python standard library and calls the committed manuscript figure/table builders. CI verifies the package under the repository's supported Python versions.

Purpose: verify that the scientific numbers and plotted assets in the submission are a deterministic projection of the frozen evidence.

## 2. Upstream source-to-outcome reproduction

The full repository includes workflows that reacquire original source data, regenerate intermediate features, execute benchmark models, and confirm frozen results. Their dependency surface is broader than the submission package.

The package metadata in `pyproject.toml` currently declares:

- Python `>=3.10`;
- core: `numpy>=1.24`;
- development: `pytest>=8`, `pandas>=2`;
- raster workflows: `pandas>=2`, `rasterio>=1.3`;
- current-flow workflows: `scipy>=1.11`, `pandas>=2`, `rasterio>=1.3`.

Individual GitHub Actions workflows additionally pin numerical or geospatial versions when cross-run reproducibility requires it. Those workflow files remain the authoritative executable environment for the corresponding upstream benchmark stage.

## Archive requirement

Before minting the final archival release, record:

1. the exact release Git commit and tag;
2. `pyproject.toml`;
3. all manuscript-facing frozen manifests and expected projections;
4. all workflow definitions used for the authoritative A-Islands and Tanzania confirmations;
5. the offline submission-package manifest generated from the release tag;
6. the Python/platform information emitted by the release verification run.

A single universal lock file is not claimed for every historical upstream workflow. The release instead preserves each authoritative workflow's executable dependency contract plus the network-free manuscript projection. This distinction must remain explicit in the archive documentation.
