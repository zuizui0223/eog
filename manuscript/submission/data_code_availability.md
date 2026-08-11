# Data and code availability

## Manuscript-ready statement

The analyses use openly archived or provider-hosted source data together with reproducible acquisition and integrity-checking scripts. A-Islands version 1.0 is available from Zenodo (doi:10.5281/zenodo.10775809). The climatic predictors used in the A-Islands benchmark were obtained from CHELSA v2.1; the repository records the selected variables and verifies the derived frozen island-level climate table before analysis. The Tanzania forest-fragment benchmark is based on the Dryad archive associated with Brodie and Newmark (2019) (doi:10.5061/dryad.p042h0c); the workflow reacquires the declared archive version and verifies all source files by size and digest before constructing any benchmark quantity.

All EOG analysis code, pre-outcome contracts, tests, workflow definitions, frozen result projections, manuscript figure builders, plotting sidecars, applicability tables, and cryptographic fingerprints are maintained in the public `zuizui0223/eog` repository. The structural manuscript can be rebuilt offline from the committed frozen inputs with:

```bash
python manuscript/build_structural_submission_package.py --output-dir build/structural_submission
```

The command reconstructs the manuscript figures and result tables into a separate package directory and verifies the scientific assets against the committed frozen outputs. The submission package records the exact Git commit and the frozen Tanzania result fingerprint.

Before submission, the final tagged repository release will be archived in a DOI-issuing repository. Replace the placeholders below only after that archive has been minted:

- Code release tag: `<RELEASE_TAG>`
- Archived code/results DOI: `<ARCHIVE_DOI>`
- Exact release commit: `<RELEASE_COMMIT>`

Third-party source files should be cited and reacquired from their original providers rather than redistributed when their original terms require that route. Frozen derived benchmark projections and manuscript sidecars will be included in the archival release to the extent permitted by the source-data terms.

## Source identifiers used in this paper

- A-Islands v1.0: doi:10.5281/zenodo.10775809
- A-Islands data paper: doi:10.1111/jvs.70019
- CHELSA climatology reference: doi:10.1038/sdata.2017.122
- Tanzania forest-fragment source archive: doi:10.5061/dryad.p042h0c
- Tanzania source paper: doi:10.1086/702589

## Claim boundary

Availability of code, hashes, manifests, and frozen results establishes provenance and rebuildability. It does not make a post-outcome archive preregistered and does not establish ecological causality, realised dispersal, or colonisation probability.
