# EOG v2 SW Finland institutional-mirror transport contract

## Status

**Response-free transport amendment frozen before any SW Finland `outcome` value is accessed by EOG v2.**

This document changes only lawful byte retrieval for the already-frozen SW Finland occurrence benchmark in `docs/eog_v2_finland_colonization_preoutcome_contract.md`. It does not change the 471-island universe, source reconstruction, Gabriel graph, R0/R1/R2/C predictors, propagation settings, folds, fit engine, inference unit, bootstrap, or GO/NO-GO rule.

## Why this amendment exists

The authoritative Dryad release remains:

- DOI `10.5061/dryad.ffbg79cr6`;
- file `colonization_select.csv`;
- one released file, approximately 129.16 MB on the public Dryad landing page.

Repeated automated access to the Dryad file stream has been blocked by the public AWS-WAF transport layer. Transport failure is not a scientific admission failure and does not authorize a different dataset.

Åbo Akademi University's public researcher profile for dataset creator Mikael von Numers lists the same Dryad dataset and explicitly provides Zenodo record `4942881` as an access route. That institutional link is the only mirror route authorized here.

## Required byte-identity proof

Zenodo record `4942881` may supply the raw bytes **only if every following condition passes before response-free admission**:

1. the public Åbo Akademi page still identifies Dryad DOI `10.5061/dryad.ffbg79cr6` together with Zenodo record `4942881`;
2. the public Dryad API resolves the same DOI and current published version;
3. the Dryad version file metadata contains exactly one `colonization_select.csv` record;
4. the Dryad file metadata exposes a cryptographic digest and byte size;
5. the public Zenodo API record identifies the expected dataset/file and exposes `colonization_select.csv`;
6. the Zenodo object is downloaded without parsing its CSV contents;
7. downloaded byte size exactly equals the Dryad file size;
8. the downloaded bytes' cryptographic digest exactly equals the Dryad file digest (SHA-256 preferred; another Dryad-declared digest is acceptable only if its algorithm is explicit and is computed independently on the downloaded bytes);
9. the downloaded bytes also satisfy Zenodo's own declared checksum/size metadata;
10. the provenance JSON records the institutional page, Dryad DOI/version/file metadata, Zenodo record/file metadata, and computed hashes.

Filename or size agreement alone is insufficient. If the Dryad digest is absent, ambiguous, or cannot be matched exactly, the mirror is **not admitted**.

## Outcome firewall

Byte retrieval and hashing do not authorize outcome inspection. Before the response-free feature bundle and its fingerprints are archived, code may inspect only:

- repository/API metadata;
- raw file size/checksums;
- CSV header names;
- fields used by `benchmarks/finland_colonization_preoutcome_admission.py` and `benchmarks/finland_colonization_prepare.py`.

The `outcome` column may be checked for existence but its values may not be parsed, counted, summarized, stratified, or modeled. The existing admission/prepare code remains authoritative for this firewall.

## Promotion boundary

A successful mirror transport proves only that the institutional mirror is byte-identical to the Dryad file represented by the public Dryad API metadata. It does not itself provide biological evidence.

Only after the byte-identical raw SHA-256, response-free admission result, row/completeness projection, graph/fold assignment, predictor bundle, operator and complete inference contract are archived may a separate one-time workflow attach and score `outcome`.

No result-dependent transport, graph, species, reference, propagation, fold, or threshold change is allowed after outcome access.
