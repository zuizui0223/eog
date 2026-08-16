# SIVFLORA independent world-set confirmation — pre-outcome contract

## Status

**Frozen design target before downloading or analysing the SIVFLORA species-by-island incidence file in EOG.**

This is the first independent confirmation allowed by the EOG mainline after the response-free A-Islands exploratory gate passed. A-Islands remains development evidence only. This contract must not be retuned after the SIVFLORA incidence outcome is inspected.

The confirmation asks one narrow question:

> **Does preserving the identity of mutually alternative geographic/environmental connectivity worlds predict held-out catalogued island incidence beyond strong compressed summaries of the same worlds?**

A favourable answer supports only the EOG domain-framework claim that retaining explicit analyst-choice worlds can preserve ecologically useful information. It does not establish a new graph algorithm, true dispersal history, occupancy probability, or universal biogeographic law.

## Why this is independent

SIVFLORA is a separately produced Southern Ocean vascular-plant catalogue, not an A-Islands outcome or adapter. The published data descriptor reports a flat open-access dataset spanning 22 islands/archipelagos and 62 localities, with georeferenced taxonomic records, island/location metadata, and establishment means.

Selection of this system used only public source/schema metadata and the published dataset design. No EOG world-set result, held-out prediction, or species-by-island model comparison from SIVFLORA was inspected before this contract.

## Frozen source identity

Primary source target:

- dataset: **SIVFLORA: Southern Islands Vascular Flora database**;
- Zenodo record selected for machine retrieval: `14639076`;
- file: `20250113_sivflora_v1.0.xlsx`;
- version label in file name: `v1.0`;
- published Zenodo MD5 shown before analysis: `146d67f6b6628e9f570a2325880f76e8`;
- data descriptor DOI: `10.1038/s41597-025-04702-9`.

The Scientific Data paper cites an earlier Zenodo DOI, `10.5281/zenodo.13997147`, also labelled version 1.0. The source-freeze step must record this provenance discrepancy. The analysis source is the exact file named above from record `14639076`; no silent substitution is allowed.

Before parsing incidence values, a source-freeze job must:

1. download that exact file;
2. verify the published MD5;
3. compute and record SHA-256, byte size, retrieval timestamp and Zenodo metadata;
4. stop if the file name or MD5 differs;
5. archive a machine-readable source manifest.

## Target estimand

The response is **catalogued native/endemic island incidence**, not latent ecological occupancy.

For each taxon-island pair:

- `1` = the frozen SIVFLORA file contains an eligible native/endemic record for that taxon on that island;
- `0` = the eligible taxon has no catalogued record on that island;
- non-native/introduced/ambiguous establishment records are not converted into biological absences and are excluded from the primary pair when they make status ambiguous.

A `0` therefore means **not catalogued in the frozen SIVFLORA incidence matrix under the primary natural-status rule**. The manuscript must not call it a surveyed absence or detection-corrected absence.

## Taxonomic and establishment rules

Primary analysis:

- use the dataset's reviewed/accepted taxon identity;
- retain species-rank records only;
- retain records whose establishment means are explicitly native or endemic;
- exclude alien/introduced records from positive anchors;
- exclude a taxon-island pair rather than force a negative when the same pair has conflicting natural versus introduced status;
- collapse duplicate eligible records to one taxon-island positive incidence.

If the frozen schema does not expose the required reviewed taxon rank and establishment fields described by the data descriptor, the confirmation is **schema-blocked**. Do not infer replacements after looking at incidence outcomes.

## Geographic units

Primary node = the 22 published island/archipelago units, not the 62 localities.

Node coordinates are derived without species weighting:

1. if the source provides one explicit island-level coordinate pair, use it;
2. otherwise deduplicate the published locality identities/coordinate pairs within each island and use their spherical/geodesic centroid;
3. never average occurrence rows directly because repeated taxon records would weight the node geometry by response density.

All 22 units remain in the declared node universe. Island area may be retained as metadata but is not a primary transition variable.

## Environmental representation

Use exactly five bioclimatic variables, transferred from the earlier frozen EOG environmental specification rather than selected on SIVFLORA outcomes:

- BIO1;
- BIO5;
- BIO6;
- BIO12;
- BIO15.

Use two analyst-choice climate products:

1. CHELSA v2.1;
2. WorldClim v2.1.

For each product:

- extract the five variables at each unique SIVFLORA locality;
- average locality climate values within an island/archipelago, giving each unique locality equal weight;
- standardize each variable across the 22 island nodes using mean and sample standard deviation;
- stop if any declared variable has zero/non-finite standard deviation or missing node values;
- use Euclidean distance in the resulting five-dimensional standardized environmental space.

Climate-source URLs, versions, raw-object checksums where available, and the final 22-node climate-table SHA-256 must be frozen before incidence scoring.

## Declared finite world universe

No world is selected after seeing the SIVFLORA response.

### Geographic scale family

Compute all non-zero pairwise great-circle distances among the 22 frozen node coordinates. Declare four nested geographic edge thresholds at the empirical:

- q25;
- q50;
- q75;
- q90.

These are **structural transition scales**, not fitted species dispersal distances.

### Environmental continuity family

For CHELSA and WorldClim separately, compute all non-zero pairwise standardized five-variable environmental distances and declare two nested edge thresholds:

- q50;
- q75.

An environmentally constrained edge must satisfy both the declared geographic threshold and the declared environmental threshold.

### Exactly 20 worlds

The finite universe contains:

- 4 geography-only worlds: `G[q25,q50,q75,q90] x env_none`;
- 8 CHELSA worlds: 4 geographic thresholds x `CHELSA_env_[q50,q75]`;
- 8 WorldClim worlds: 4 geographic thresholds x `WorldClim_env_[q50,q75]`.

Do not duplicate geography-only worlds once per climate product. The complete universe therefore has exactly **20 distinct worlds**.

Every world is an undirected island graph. A candidate island is structurally reachable for a taxon in a world when it belongs to a connected component containing at least one training occurrence anchor.

No weighted average path, inferred movement rate, circuit current, or post-hoc world weight is added.

## Leakage-safe outer validation

Use **leave-one-island-out (LOIO)** validation across the 22 island/archipelago nodes.

For outer held-out island `h`:

1. remove all incidence information from `h` before constructing taxon anchors or any response-derived feature;
2. build each taxon's anchor set from the other 21 islands only;
3. compute the 20 binary world-reachability indicators for `h`;
4. reveal the held-out catalogue incidence only after features/predictions are frozen for that fold.

A taxon is eligible in an outer fold using **outer-training data only** when it has:

- at least 4 eligible natural positive islands in the 21-island training universe; and
- at least 4 evaluable catalogue non-record islands in that same training universe.

The held-out outcome must not determine eligibility.

## Leakage-safe training rows inside each outer fold

Predictive comparators require training examples without self-leakage.

Within outer fold `h`, for every training island `j`:

- construct the feature row for taxon x island `j` using anchors from the outer-training universe excluding `j`;
- never allow `j`'s own incidence to create its reachability feature;
- never allow outer held-out island `h` to enter any inner training anchor set.

This nested construction is mandatory even if it is slower.

## Base covariates

Every predictive comparator receives the same leakage-safe base information:

1. training natural-incidence prevalence for the taxon;
2. `log1p` nearest-training-occurrence great-circle distance;
3. nearest-training-occurrence CHELSA environmental distance;
4. nearest-training-occurrence WorldClim environmental distance.

Continuous predictors are standardized from the outer-fold training rows only and then applied unchanged to the held-out island.

## Comparator hierarchy

All models use the same L2-penalized logistic regression implementation, with fixed regularization `C=1.0`, intercept enabled, no class reweighting, and no outcome-driven hyperparameter search.

### R0 — local/base reference

Base covariates only.

### R1 — scalar consensus

R0 + total reachability frequency across the 20 declared worlds.

### R2 — strong compressed decomposition reference

R1 + five world-family support counts:

- geography-only support count (0–4);
- CHELSA q50 support count across geographic scales (0–4);
- CHELSA q75 support count across geographic scales (0–4);
- WorldClim q50 support count across geographic scales (0–4);
- WorldClim q75 support count across geographic scales (0–4).

R2 therefore already knows whether support comes primarily from geography, CHELSA, WorldClim, stricter or looser environmental continuity. It deliberately removes only the **exact world identity within those summaries**.

### C — explicit world identity

R2 + the complete 20-bit world reachability vector.

The primary scientific contrast is **C minus R2**. R1 and R0 are secondary context, not weak straw-man promotion gates.

## Primary metric

For each outer island with at least 20 evaluable held-out taxon pairs, calculate mean binary log loss for R0, R1, R2 and C.

Primary effect:

`delta_identity = logloss(C) - logloss(R2)`

Aggregate by giving each evaluable outer island equal weight.

Uncertainty:

- paired bootstrap over evaluable islands;
- 10,000 replicates;
- fixed seed `20260816`;
- percentile 95% interval.

At least 15 of 22 outer islands must meet the >=20-pair requirement. Otherwise the confirmation is **non-estimable**, not favourable or adverse.

## Confirmation / no-added-value rule

The independent confirmation is favourable only if all are true:

1. mean `delta_identity < 0`;
2. the 95% paired-island bootstrap upper bound for `delta_identity` is `< 0`;
3. C has lower log loss than R2 on at least 12 evaluable outer islands;
4. C is not worse than R1 in mean island-macro log loss;
5. exact world identity is not a deterministic one-to-one function of the R2 compressed decomposition across all evaluable held-out rows.

If conditions 1–5 are not all satisfied, the result is **no confirmed added value for explicit world identity**. Do not rescue it by adding worlds, changing climate variables, changing thresholds, weakening R2, or opening another favourable dataset.

If coverage/eligibility requirements fail, classify the result as **indeterminate / non-estimable** and do not promote EOG.

## Secondary diagnostics

Predeclared descriptive secondaries:

- island-macro Brier score differences;
- number/fraction of held-out rows whose exact world identity differs despite identical R1 scalar frequency;
- number/fraction whose exact identity differs despite identical R2 decomposition;
- R0/R1/R2/C island-level log-loss table;
- support-signature frequency table;
- native-positive versus catalogue-nonrecord calibration summaries.

No secondary can overturn an adverse or indeterminate primary gate.

## Strong interpretation boundary

Even if favourable, this confirmation permits only:

> In an independently produced Southern Ocean island flora catalogue, retaining the identities of declared alternative connectivity worlds provided held-out catalogue-incidence information beyond strong compressed summaries of the same worlds.

It does **not** permit:

- historical route reconstruction;
- species-specific dispersal-distance estimation;
- biological absence claims;
- occupancy/detection probability claims;
- a claim that CHELSA or WorldClim is the true environmental representation;
- universal robustness outside the enumerated 20-world universe;
- novelty claims for graph connectivity, functional habitat, ensemble methods, history matching, or falsification-frontier mathematics.

## Certificate boundary

`robust`, `contingent`, and `excluded` labels are exact only over the explicitly enumerated 20-world finite universe.

The analysis does not certify continuous parameter spaces or every plausible ecological/analytical model. Claim strength must remain bounded by this finite coverage.

## Stop rule after the run

Run the frozen confirmation once.

- favourable primary gate -> the integrated EOG line may proceed to manuscript/product consolidation without adding another algorithm by default;
- no-added-value -> stop the explicit-world-identity promotion claim;
- indeterminate -> report the limitation and stop promotion unless a genuinely independent, pre-existing reason for another validation system existed before seeing this outcome.
