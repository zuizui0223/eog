# EOG v2.1 Plestiodon marginatus pre-genetic admission contract

## Status

**Stage 1 response-free admission only. Genetic workbook contents are prohibited.**

Candidate study: Kurita, Hikida & Toda (2014), Journal of Heredity 105:867–877, DOI `10.1093/jhered/esu055`.

Data DOI: Dryad `10.5061/dryad.7gs71`.

Public transport mirror to verify: Zenodo record `5001548`, expected file `Microsatellite genotype of Plestiodon marginatus.xlsx`.

## Stage 1A — raw genetic member existence / provenance only

The released microsatellite workbook is response-bearing. Before the complete response-free geography mapping is frozen, the file may only be treated as an opaque byte object.

Permitted:

- read Zenodo record metadata;
- verify study/Data-DOI relation;
- verify exactly one expected `.xlsx` file entry exists by file metadata;
- download that immutable file only to compute/verify byte size, MD5 and SHA-256;
- delete the file before artifact upload.

Prohibited before Stage 1B PASS:

- opening the XLSX as a ZIP archive;
- listing workbook members or worksheets;
- reading workbook XML;
- reading sheet names;
- reading any cell, population/locality label, sample ID or genotype;
- inferring geography from the workbook;
- computing any genetic response.

The Stage-1A result must explicitly certify `genetic_workbook_contents_accessed = false`.

## Stage 1B — complete response-free geography mapping

Before workbook access, recover all 21 published population-number/locality mappings from a lawful non-genetic source.

Accepted source classes:

- the published Journal of Heredity Table 1 if lawfully accessible;
- journal supplementary geography material;
- an author/institutional manuscript copy;
- another publication only if equivalence of locality numbering is explicit and auditable.

Current public source evidence already establishes:

- 21 populations from 11 land-bridge islands + 4 isolated islands;
- 235 microsatellite-genotyped individuals and 10 loci;
- the released genotype locality names correspond to Table 1 numbers.

Those facts are insufficient to reconstruct the full 1–21 geography mapping. No island/locality order is guessed from geography or published genetic results.

Stage 1B PASS requires:

- exactly 21 population numbers/IDs;
- unique canonical locality/island mapping for all 21;
- source provenance for every mapping;
- coordinates from the source or a separately frozen deterministic geocoding step;
- a response-free mapping fingerprint;
- no genetic workbook content access.

If the complete mapping cannot be lawfully recovered, the candidate closes as `non_estimable_response_free_geography_unavailable`; the workbook is not opened to repair geography.

## Stage 2 / Stage 3 boundary

Only after Stage 1A + 1B PASS may a later commit authorize genetic-schema inspection and freeze node admission, EOG predictors, the complete nested conventional-reference family, response transform, ridge penalty, nested folds and empirical inference rule.

Exact genetic response computation remains prohibited until those response-free predictors are byte-frozen.
