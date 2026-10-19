# EOG: 2021 genetic-origin evidence versus later direct bird re-observation

**Status:** Official public metadata and independently deposited *methods source code* verification. This is not an independent EOG ecological heldout endpoint or a validated genotype-to-2026 individual join.

## Newly identified independent evidence type

Saatoglu et al. (2021), *Dispersal in a house sparrow metapopulation: An integrative case study of genetic assignment calibrated with ecological data and pedigree information*, Molecular Ecology, DOI [10.1111/mec.16083](https://doi.org/10.1111/mec.16083), published a calibration study using genetic assignment and ecological capture/mark/recapture evidence. The source measurements differ from *mere next-year positive site codes*:

- **natal.island** — source origin, with supporting ecological and/or genetic evidence depending on the specific subanalysis and whether the natal island is directly known;
- **adult.island** — later observed adult island, not interchangeable with EOG's *first* physical \`capt/obs\`;
- **hatch.year**, **sex**, and **dispersal.status** — recorded demographic and observation variables;
- \`Pairwise_Fst.txt\`, \`Misassignments_givenaway.txt\`, \`Misassignments_received.txt\` and the 2021 authored R script show how genetic differentiation, baseline sample size and sampling fraction affect the genetic-assignment **observation/error** process.

Crucially, the genetic paper already investigated classification accuracy and links to sampling fraction. A simple correlation between genetic assignment errors and sample size, or natal/adult island differences, is **prior published ecology/methodology**, not an EOG discovery. A genetic call of source origin is not automatically historical truth or a new founding event.

## Official original source inventory (no biological rows read)

[Official 2021 Dryad archive](https://datadryad.org/dataset/doi:10.5061/dryad.xgxd254h1): dataset ID **72603**, version **130231**, published **2021-07-15**. The [official file inventory](https://datadryad.org/api/v2/versions/130231/files) contains five registered source files:

| File | Official file ID | Bytes | Role |
| --- | ---: | ---: | --- |
| \`Dispersaldata.txt\` | 815561 | 59,268 | Candidate individual/ecological dispersal classifications |
| \`Geneticassignment_README.txt\` | 815564 | 1,687 | Needed to establish actual column meanings |
| \`Misassignments_givenaway.txt\` | 815563 | 3,817 | Genetic assignment error, origin-side summary |
| \`Misassignments_received.txt\` | 815562 | 3,818 | Genetic assignment error, recipient-side summary |
| \`Pairwise_Fst.txt\` | 815560 | 13,247 | Pairwise genetic differentiation and assignment-mismatch summaries |

All five original **source-declared SHA256** values are frozen in the machine-readable provenance contract. No real Dryad biological file bytes, headers, individual IDs, genetic outcomes or pairwise FST observations were loaded here. Authenticated byte access to those files is a separate later evidence gate.

[Zenodo author software record 5095667](https://zenodo.org/records/5095667), DOI [10.5281/zenodo.5095667](https://doi.org/10.5281/zenodo.5095667), separately publishes the single analysis script \`Error_sources_dispersal_patterns.R\`, **10,758 bytes**, source-declared MD5 \`80d138c79960684fa85379c09cd17727\`. The script contains an explicit \`read.table("Dispersaldata.txt")\`, use of natal/adult island, dispersal status, hatch year and sample-fraction diagnostics. This public **code** can be attested by exact byte size and MD5 without accessing any individual bird data. Its internal use of preprocessed dispersal-status labels does **not** itself establish independent source truth.

## The important study-design mismatch, now visible in the actual author script

The author script contains **two different ecological groups**:

1. A broader natal-origin-code group \`20,22,23,24,26,27,28,38,77,88\` for spatiotemporal summaries.
2. A restricted eight-SNP-island subset \`20,22,23,24,26,27,28,38\` for its farm/nonfarm comparison, described in the source comments as sampling **2004–2012**, excluding \`1998–2003\` to harmonize nonfarm sampling. The comments explicitly say original sampling of nonfarm islands before 2004 differs. This eight-island restriction is a *code/documentation-level* choice; no year-by-year eligibility was validated on original data rows.

The source-internal 2026 EOG crosswalk (#648) contains all **eight** as named 2021 study population labels: Nesøy, Myken, Træna, Selvær, Gjerøy, Hestmannøy, Indre Kvarøy, Aldra.

It also contains **three extra named study island codes** in the eleven-island Ranke roster: Lurøy-Onøy \`33\`, Lovund \`34\`, Sleneset \`35\`. They are **not members of the genetic paper's eight-SNP-island habitat comparison**. In particular, retaining \`33\` in EOG #649 was correct for the eleven-population positive-detection analysis but does not permit using it as though it had been sampled identically in the 2021 eight-island SNP comparison.

The code \`77\` and \`88\` origin categories should remain **unmapped** until independently verified; do not silently recode to an island already in the 2026 source. A matching integer \`20\` in two published studies does not by itself guarantee compatible *individual* ID domains, study populations, effort or life-stage definitions.

## Nontrivial ecological hypothesis this might eventually test

> **Does source-provenance evidence narrow uncertainty in between-island connection histories beyond the occurrence/first-followup patterns, and does its additional information depend on genetic differentiation and sampling coverage?**

This is motivated by the existing known-truth EOG v23 result that provenance information and occupancy evidence can be complementary. **No real-world genetic validation of v23 has occurred in the Helgeland data**.

Minimum valid future comparison would require: (i) actual SHA256-matched 2021 Dryad files and physical README/header; (ii) documented direct CMR vs assigned genetic origin for specific individuals, with assignment error/uncertainty; (iii) exact same-ID/natal-year and raw site-key correspondence to any other archive, proven rather than assumed; (iv) a prospective observation contract or explicitly retrospective comparator, and (v) an island-year baseline sampled fraction, including surveyed-zero effort if ecological absence is invoked.

Without those, the strongest currently authorized result is **source-code-method and site-code/period alignment**, not a dispersal estimate, source–sink dynamics, founding, a quantified EOG improvement or a causal claim.

## Executable source-only check

The audit reads and SHA-checks only the openly deposited official author R script supplied as a file path (no credentials or network access in the validator). It cross-checks the original EOG #648 code-name dictionary and issues an aggregate metadata receipt without any bird IDs or biological rows.

\`\`\`bash
python -m pytest -q tests/test_helgeland_saatoglu2021_provenance_preflight_v1.py

python scripts/audit_helgeland_saatoglu2021_provenance_preflight_v1.py \
  --author-r-source path/to/authorized/Error_sources_dispersal_patterns.R \
  --output build/saatoglu2021-source-script-audit.json
\`\`\`

The CI may fetch **only** the declared publicly available Zenodo R script from its official URL. It never fetches raw Dryad bird/genotype files and stops if the URL, exact size, MD5, code vocabulary or previously frozen eight-island dictionary is inconsistent. The 2021 author-script checksum is a **source artifact** check, not a claim of restored 2021 biological data.

EOG-WF remains strictly three scored endpoints, 31 scientific STOPs and three administrative exclusions. This is a separate source-readiness bridge for later independently justified biological work.
