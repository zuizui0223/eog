# EOG v2.1 Periploca laevigata pre-genetic admission contract

## Status

**Stage 1 response-free geography admission + opaque genetic-member provenance only.**

Study: García-Verdugo et al. (2015), *Do island plant populations really have lower genetic variation than mainland populations? Effects of selection and distribution range on genetic diversity estimates*, DOI `10.1111/mec.13060`.

Data DOI: Dryad `10.5061/dryad.9nc22`.

Candidate public archival mirror: Zenodo record `4994024` (must be verified from record metadata before file use).

The Dryad release separates geography from genetic response:

- `Periploca pops data.txt` — population geography, coordinates, vouchers and collectors;
- `Periploca_nSSR.txt` — 661 individuals genotyped at 13 nuclear microsatellite loci, population codes corresponding to the geography file;
- `Periploca99samples_4cpDNAregions.txt` — plastid sequence data, not needed for this validation.

## Response firewall

Before Stage-2 predictors/references are frozen, only the geography file may be opened/read.

Permitted:

- read Zenodo record metadata;
- verify study/Data-DOI identity;
- verify released file names, sizes and checksums;
- download `Periploca pops data.txt` and inspect its full contents;
- download `Periploca_nSSR.txt` only as an opaque byte stream for provenance/checksum;
- delete the opaque microsatellite byte object before artifact upload.

Prohibited:

- reading any byte of `Periploca_nSSR.txt` as text or structured genetic data;
- inspecting microsatellite population/sample rows, loci or alleles;
- opening/reading the cpDNA file;
- using published genetic diversity/differentiation results to choose nodes or graph/reference candidates;
- computing any genetic response.

Stage-1 evidence must record `microsatellite_contents_accessed = false` and `genetic_response_computed = false`.

## Stage 1 admission

Stage 1 must establish from the geography release only:

- a stable population identifier/code;
- locality/geographic-position information;
- finite latitude and longitude for at least six unique populations;
- coordinate convention and any island/mainland/location label columns exposed by the released file;
- geography-file SHA-256 and a canonical geography fingerprint;
- exact opaque microsatellite filename/size/checksum and existence.

The first Stage-1 implementation is intentionally schema-descriptive: it records delimiter/header/row structure and geography-like columns rather than silently correcting or guessing the release schema.

If the geography file cannot be parsed into at least six uniquely identified finite-coordinate populations without genetic-file help, status is `non_estimable_response_free_geography_unavailable` and genetic contents remain unopened.

## Stage 2 boundary

Only after Stage-1 PASS may a later commit freeze:

- a deterministic island-focused validation subset from geography only;
- any population-admission rule available without genetic values;
- node coordinates;
- EOG graph/operator + exact-eventual predictors;
- the complete conventional-reference family used by #143 nested selection;
- response transform, ridge penalty, nested folds and bootstrap/GO rule;
- byte-identical response-free predictor artifact.

## Stage 3 boundary

Only after Stage 2 may `Periploca_nSSR.txt` be opened once under a schema/provenance contract, aligned to the frozen population codes, converted to a predeclared symmetric population-genetic response, and scored once.

Any GO, null, adverse, non-estimable or indeterminate result remains visible.
