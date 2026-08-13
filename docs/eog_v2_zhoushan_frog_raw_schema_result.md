# EOG v2 Zhoushan pond-frog raw microsatellite schema result

## Status

**Post-freeze raw-genotype schema audit — PASS. Pairwise FST was not computed during this audit.**

The raw workbook was first opened only after the complete 27-population / 351-pair EOG predictor artifact had been generated and byte-frozen in the repository.

## Raw provenance

Source: Zenodo record `5012316`, `Microsatellite data.xls`.

- released MD5: `0f9d9b36bb0c481f41170ad2d6cc6344`;
- observed SHA-256: `52ee37e431aff3303d58685cfef064a7ee34cf0117f52eaca3889e21eacebb17`;
- schema-audit workflow run: `31656132251`;
- artifact ID: `9164500280`;
- artifact digest: `sha256:335dd78dde74d5b8e3f201cf6ac908139fd37ac49319e8e11c1565dafefe9524`.

During this audit EOG did **not** compute pairwise FST, allele frequencies, heterozygosity, clustering or migration.

## Workbook structure

One worksheet, `Microsatellite data`:

- 813 rows;
- 19 columns;
- 810 individual genotype rows plus three header/category rows;
- nine microsatellite loci;
- two allele columns per locus;
- locus names: `Rnh-1`, `Rnh-2`, `Rnh-3`, `Rnh-4`, `Rnh-6`, `Rnh-9`, `Rnh-10`, `Rnh-12`, `Rnh-13`;
- no explicit string missing token was observed;
- blank cells occur and are therefore treated as missing diploid locus values according to the predeclared contract;
- observed numeric allele cells are positive and are treated as categorical microsatellite alleles.

Every population block contains exactly 30 individuals. The 24 island prefixes match the frozen article population IDs directly.

## Mainland raw-prefix identity adapter

The raw workbook uses higher-level mainland administrative names rather than the article's three local sampling-site names:

| Raw prefix | Frozen article node | Response-free mapping basis |
|---|---|---|
| `Haining` | `Yuanhua` | Yuanhua Town is within Haining City |
| `Zhenhai` | `Xiepu` | Xiepu Town is within Zhenhai District |
| `Beilun` | `Guoju` | Guoju Subdistrict is within Beilun District |

This mapping was established from administrative geography **before any pairwise FST was computed**. It does not use allele values, genetic clustering, migration or FST.

The machine-readable mapping is frozen in:

`benchmarks/frozen/zhoushan_frog_response_free/raw_population_mapping.csv`

The graph node identities and coordinates are not changed by this adapter: it only maps the raw-workbook population prefix onto the already frozen article-level node.

## Raw row blocks

After skipping workbook category/header rows, the released individual blocks are:

- Haining 30 -> Yuanhua;
- Zhenhai 30 -> Xiepu;
- Beilun 30 -> Guoju;
- Meishan 30;
- Fodu 30;
- Liuheng 30;
- Xiashi 30;
- Huni 30;
- Taohua 30;
- Dengbu 30;
- Mayi 30;
- Damao 30;
- Zhujiajian 30;
- Putuoshan 30;
- Zhoushan 30;
- Cezi 30;
- Jintang 30;
- Dapengshan 30;
- Changbai 30;
- Xiushan 30;
- Daishan 30;
- Dayushan 30;
- Dongji 30;
- Qushan 30;
- Sijiao 30;
- Shengshan 30;
- Huaniao 30.

Total: `27 × 30 = 810` individuals, matching the published study total.

## Decision

The raw-genotype provenance/schema gate is admitted for the predeclared Weir–Cockerham fallback.

The next and first response-computing stage must, in one frozen run:

1. verify the byte-identical Stage-2 predictor artifact;
2. verify raw workbook MD5/SHA and this identity adapter;
3. parse exactly the 27 × 30 individuals and nine allele-pair loci above;
4. compute all 351 Weir–Cockerham pairwise theta values without clipping;
5. apply the already-frozen `FST/(1-FST)` admissibility rule;
6. run the already-frozen leave-one-population-out IBD/current-flow/EOG ladder;
7. apply the fixed 10,000-resample population bootstrap and GO/NO-GO rule.

No graph, coordinate, locus, population, response transform or reference choice may be changed after that response is computed.
