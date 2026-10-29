# Pyrgus armoricanus: independent-source BAM metadata qualification (v1)

## Position relative to the EOG scientific mainline

This is a **distinct dataset candidate** from the closed Gotland `Euphydryas aurinia`
Dryad DOI, not a retry, mirror or source substitution for that failed source.
The existing EOG × BAM PRs #668, #669 and the 1,344-pair exploratory replay
use known-truth virtual landscapes, not independent field tests.

The aim is to determine whether the **independently published** Swedish
`Pyrgus armoricanus` patch-level dataset can support a *retrospective,
proxy-level* A/B/M geometry demonstration.

## Published context

Fourcade, Ranius & Öckinger, *Journal of Animal Ecology* (2017),
DOI `10.1111/1365-2656.12740` and publicly deposited Dryad data
DOI `10.5061/dryad.b563d` (2018).

The published study includes 50 monitored patches over 2004–2016, patch
microclimate/solar irradiance, host-plant density, patch area/connectivity,
and temporal butterfly abundance. Dryad lists `Monitoring_data.csv`
(~8.38 KB) and `Site_data.csv` (~2.76 KB).

**The article already found associations between colonisation/extinction
and patch connectivity and host density.** These results are prior art, not
new EOG findings. This candidate is for measurement/linkage feasibility
and potential incremental geometry against a strong declared baseline,
not a new discovery of those associations.

## Axis definitions and circularity boundary

- A: independently measured **site microclimate**, primarily mean/SD
  solar irradiance, if confirmed in the physical site-data dictionary.
  Grazing and patch area are separate structural controls, not automatically
  physiological tolerance.
- B: direct **host-plant density**, associated with
  `Filipendula vulgaris` and `Helianthemum nummularium`. Candidate
  habitats were selected partly by host presence: B cannot be interpreted
  as an unconditional host-absence gate across all surrounding landscape.
- M: first choose **source-independent patch coordinates, geographical
  distance and a predeclared dispersal kernel**, if physical coordinates
  exist. The published `S_i` connectivity index uses contemporaneous
  neighbour butterfly abundance `N_j`, so it is **not an independent
  movement-only measurement** and is not permissible as an unlagged
  predictor of G or independent BAM M.
- G: reported 2004–2016 adult butterfly abundance and within-patch
  detection. Do not automatically promote zero counts to proven absence.
  Future responses cannot enter M construction or training references.

The dataset's purported A/B/M variables remain **source-publication
claims** until physical columns and sampling units are qualified. All
candidate data come from one previously published analysis and are
therefore not a new independent validation of the paper's headline.

## Source lock, current Gate 0

Frozen before response/file inventory access:
`validation/pyrgus_bam_metadata_gate_v1/protocol_v1.json`
(protocol commit `2d8bf050b1197b9c5e387264da2941d539a1a214`).

The only authorized network calls are the Dryad API version list for
exact DOI `10.5061/dryad.b563d` and, if exactly one public submitted
version is returned, its version file metadata endpoint.

The runner reuses the existing `eog.v2.dryad_metadata` identity
validator for repository file IDs, byte sizes and digests. No CSV bytes
or biological response rows are downloaded or parsed by this gate.
An HTTP/identity/roster error is a **terminal SOURCE_STOP** with an
archived fingerprint. No retry/mirror/new source choice without a new,
separately reviewed protocol.

A successful metadata result does **not** yet qualify A/B/M or authorize
biological data access. Gate1 would need to freeze the exact CSV header
schema, patch/year join, survey effort, independent A/B/M derivation, and
strong benchmark comparator before any data outcome scoring.

## Executable gates

```bash
python -m pytest -q tests/test_pyrgus_bam_metadata_gate_v1.py
python benchmarks/run_pyrgus_bam_metadata_gate_v1.py \
  --receipt /tmp/eog_pyrgus_gate/metadata_receipt_v1.json
```

The GitHub workflow archives the terminal `metadata_receipt_v1.json`.
No new species-level EOG result, survey count, detected colonisation,
or EOG-WF predictor score is allowed at this stage.
