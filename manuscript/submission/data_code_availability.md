# Data and code availability

## Manuscript-ready statement

The analyses use openly archived or provider-hosted source data together with reproducible acquisition and integrity-checking scripts. A-Islands version 1.0 is available from Zenodo (doi:10.5281/zenodo.10775809). The climatic predictors used in the A-Islands benchmark were obtained from CHELSA v2.1; the repository records the selected variables and verifies the derived frozen island-level climate table before analysis. The Tanzania forest-fragment benchmark is based on the Dryad archive associated with Brodie and Newmark (2019) (doi:10.5061/dryad.p042h0c); the workflow reacquires the declared archive version and verifies all source files by size and digest before constructing any benchmark quantity.

All EOG analysis code, pre-outcome contracts, tests, workflow definitions, frozen result projections, manuscript figure builders, plotting sidecars, applicability tables, and cryptographic fingerprints are maintained in the public `zuizui0223/eog` repository. The structural manuscript can be rebuilt offline from the committed frozen inputs with:

```bash
python manuscript/build_structural_submission_package.py --output-dir build/structural_submission
```

The command reconstructs the manuscript-facing figures and result tables into a separate package directory and verifies the scientific assets against committed frozen outputs. It does not rerun the one-time biological A-Islands strong-reference analysis. The generated `submission_package_manifest.json` records the exact source Git commit automatically together with all submission-facing result identities.

The original A-Islands conditional-ordering benchmark and the prospective A-Islands strong-reference predictive benchmark are archived as separate estimands. The latter was executed exactly once under the frozen `eog_aislands_isolation_adequacy_v1_3` contract after an outcome-free smoke gate and is identified by result fingerprint:

`5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a`

The Tanzania strong-reference benchmark remains identified by result fingerprint:

`6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`

The A-Islands one-time execution provenance, aggregate result, independent QA, and output checksums are committed under `validation/aislands_isolation_adequacy_20260812/`. Raw held-out predictions, fold applicability/scores, and species summaries from the authoritative execution are retained in the frozen workflow artifact identified by the committed provenance record and are to be included in the final archival release when source-data terms permit.

Before submission, the final tagged repository release will be archived in a DOI-issuing repository. Replace the remaining placeholders only after a DOI has been reserved for the final archive:

- Code release tag: `<RELEASE_TAG>`
- Archived code/results DOI: `<ARCHIVE_DOI>`

The exact release commit is recorded by the generated submission-package manifest and by the immutable repository tag rather than hard-coded into this source file.

Third-party source files should be cited and reacquired from their original providers rather than redistributed when their original terms require that route. Frozen derived benchmark projections and manuscript sidecars will be included in the archival release to the extent permitted by the source-data terms.

## Source identifiers used in this paper

- A-Islands v1.0: doi:10.5281/zenodo.10775809
- A-Islands data paper: doi:10.1111/jvs.70019
- CHELSA climatology reference: doi:10.1038/sdata.2017.122
- Tanzania forest-fragment source archive: doi:10.5061/dryad.p042h0c
- Tanzania source paper: doi:10.1086/702589

## Claim boundary

Availability of code, hashes, manifests, one-time execution provenance, and frozen results establishes provenance and rebuildability. It does not make post-outcome material preregistered and does not establish ecological causality, realised dispersal, historical colonisation routes, or colonisation probability.