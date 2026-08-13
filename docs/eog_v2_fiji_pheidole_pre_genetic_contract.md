# EOG v2.1 Fiji Pheidole pre-genetic contract

## Status

**Stage 1 response-free transport/schema audit only. Genetic response access is prohibited.**

This candidate follows #143 / PR #144 and may only be used under the future-dataset nested conventional-reference contract. It is independent of the frozen Zhoushan result and cannot be used to reinterpret Zhoushan.

Primary study: Darwell et al. (2020), *Genomic and phenomic analysis of island ant community assembly*, DOI `10.1111/mec.15326`.

Primary data DOI: `10.5061/dryad.xd2547dcp`.

Candidate public mirror to verify: Zenodo record `4965569`.

## Stage 1 purpose

Stage 1 answers only:

1. does Zenodo record `4965569` actually correspond to the declared Dryad dataset/study?;
2. what immutable archive/file does the record expose and what is its byte identity?;
3. what member names exist in the archive?;
4. what are the released schemas of explicitly allowlisted population/GPS/locality metadata files?;
5. is there enough response-free metadata to design a later node/predictor freeze without opening genetic values?

Stage 1 does **not** choose a focal species, construct an EOG graph, compute any genetic distance, inspect a VCF, inspect a genotype matrix, inspect FST/WC values, or evaluate EOG.

## Permitted archive operations before response freeze

The complete immutable public ZIP may be downloaded only for provenance/checksum and ZIP-directory inspection.

Permitted operations:

- record Zenodo record JSON and SHA-256;
- record archive file name, byte size and SHA-256;
- inspect the ZIP central directory: member path, uncompressed/compressed byte size and CRC;
- read only allowlisted metadata members by **exact basename**:
  - `sequenceMetaData.csv`;
  - `global_locality_full.csv`;
  - `pops.csv`;
  - `pop.csv`;
- for those allowlisted CSVs, record header names, row counts, encoding/dialect and simple distinct-count summaries for columns whose names indicate geography/population identity (`lat`, `lon`/`long`, `gps`, `locality`, `population`/`pop`, `egpa`, `species`/`taxon`).

The audit may report values only for aggregate counts and schema; it must not publish individual/sample identifiers as an artifact unless later needed under a separately frozen metadata contract.

## Forbidden member-content access before Stage 2 freeze

No member content may be opened if its basename is not on the allowlist above.

In particular, Stage 1 may not read contents of members whose names indicate:

- `.vcf` / VCFs;
- SNP or genotype matrices;
- pairwise FST;
- `WC` / Weir-Cockerham/popgen outputs;
- STRUCTURE/cluster outputs;
- migration estimates;
- any focal-species RAD sequence matrix.

Member **names and byte metadata** remain visible through the ZIP central directory; this does not authorize opening member contents.

The raw ZIP is deleted before GitHub artifact upload. Only checksums, central-directory inventory and aggregate metadata-schema audit may be uploaded.

## Admission rule

Stage 1 is admitted only if all are true:

- the Zenodo record title corresponds to `Genomic and phenomic analysis of island ant community assembly`;
- the record metadata contains the Dryad DOI `10.5061/dryad.xd2547dcp` or an unambiguous equivalent related identifier;
- an immutable ZIP/archive is downloaded successfully and SHA-256 recorded;
- the archive contains `sequenceMetaData.csv` by exact basename;
- at least one allowlisted file exposes plausible population/group identity columns;
- at least one allowlisted file exposes plausible GPS/latitude-longitude information, directly or through a locality table that can be joined response-free in Stage 2;
- the audit explicitly records `genetic_member_contents_accessed = false`.

If metadata are insufficient, this dataset is a Stage-1 NO-GO. Genetic files are not opened to repair missing geography.

## Stage 2 boundary

Only after a Stage-1 PASS may a new commit freeze:

- response-free focal species/group selection rule;
- node/population identities and coordinates;
- EOG graph/operator and exact-eventual predictors;
- the complete conventional-reference candidate family for #143;
- response transform, ridge penalty, nested folds and empirical uncertainty/GO rule.

All Stage-2 predictors/manifests must be byte-archived before any focal-species genetic response is opened.

## Stage 3 boundary

Only after Stage 2 may the focal-species genetic member be opened exactly once under a separate schema/provenance contract. Any GO, null, adverse or indeterminate result remains visible.
