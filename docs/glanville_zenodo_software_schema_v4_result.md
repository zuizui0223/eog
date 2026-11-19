# Source audit v4 — verified Zenodo R-code structure, genetic events still inaccessible

## Execution and permanent receipt

Dedicated static source-only [GitHub Actions run 44541968460](https://github.com/zuizui0223/eog/actions/runs/44541968460) **success**, plus all-package Python 3.10/3.11/3.12 and topology CI success at the pre-result commit `5c1aa54c46aec1389f377b5ff3550ee1f9af0876`.

The Zenodo 6610910 software record's `mainAnalysis.R` (26,693 bytes) was authenticated with publisher MD5 `f75ce54da557c221ee0a09f9fb1aaee2`, source SHA-256 `d86dead259d66ad0c3f09c47b66dbd03d3ceaefa0d45be64003a4c0cb055f2e4`. **The R code was never executed**, and no genetic observation row, source probability, dispersal-event distance or patch-year target was inspected. Full original receipt JSON fingerprint without its self-hash is `1be5c9688d506371201fc0a8b2ca620b3576e23fa28a74e6753236d8f0cf7886`, verified directly from downloaded Actions artifact ID `14537509181`. Permanent limited source receipt: `validation/glanville_zenodo_software_schema_v4/frozen_metadata_summary_v4.json`.

## Confirmed structural clues, not ecological outcomes

The source file includes 595 code lines. Extracted identifier strings include `PatchFrom`, `Source`, `Destination`, `YearTo`, `dispersalDistance`, and `fullsibfam_withpatch`. The static filename literals include `fullsibfamLevelData.csv`, `nestLevelData.csv`, `kinship_AGH.rds` and `mod1.rds` through `mod5.rds`. These **exact names** corroborate that the publisher's open Dryad version-2 metadata includes two candidate family/nest tables and an RDS file. They do **not** verify the actual dataset columns, completeness, assignment confidence, year-specific source/destination relationships or any dispersal trajectory.

The static scanner found **no explicit assignment/Geneclass/confidence symbol cue** among its targeted symbol matches. This is *not* evidence that GENECLASS2 scores are absent from the original dataset; only the token scanner's scope is known.

## Cross-source constraint

- Dryad DOI `10.5061/dryad.7h44j0zws`, published version 2, version ID 181375 (2022-06-04): exactly four public file metadata entries were authenticated by API. Public listing SHA256s and sizes are in `validation/glanville_genetic_origin_header_gate_v3/protocol_v3.json`.
- SHA-pinned README and two candidate CSV header reads were attempted once in separate run 44541096661 and **stopped at HTTP 401** on the first publisher download link; no header read. That scientific STOP is preserved in `validation/glanville_genetic_origin_header_gate_v3/source_stop_summary_v3.json`.
- The study's genetically assigned “origin” is a model-inferred assignment constrained to its **previous-year sampled reference patches**, not a directly tracked natal source. The paper reports considering assignments scored 100; any verification using actual records must audit assignment filtering and possible unsampled reference sources before treating paths as independent directional evidence.

**Gate state: `SOURCE_SCHEMA_HINTS_ONLY_NO_VERIFIED_GENETIC_DIRECTION`.**

Neither the original 2007–2012 EOG minimum-relaxation radii nor the hypothetical t−1 zero-source alternatives can be validated as actual movement from these code symbols. The scientific next input is a byte-exact original `fullsibfamLevelData.csv` or `nestLevelData.csv` with publisher SHA-256 match and a **separately frozen header-only audit**, followed by explicit source/destination/year crosswalk and uncertainty checks. A source file downloaded or shared by the user may satisfy this gate; do not silently substitute an unverified archive version or reverse-engineer source labels from patch proximity.

This preflight **does not** add a fourth prospective EOG-WF endpoint; original closure stays 3 scored, 31 scientific STOP and 3 administrative exclusions.
