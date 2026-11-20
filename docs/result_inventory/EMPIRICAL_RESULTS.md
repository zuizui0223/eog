# EOG empirical positive results and frozen boundaries

**Read with:** [evidence split index](README.md) and [mathematical/known-truth ledger](MATHEMATICAL_AND_KNOWN_TRUTH.md).  
**Snapshot:** main `f8028c50a28fb74faa4766347f05cd830655e075`, 2026-11-20.  
**Rule:** A positive result is kept with its *full comparator*, unit, source and adverse/STOP control. Do not combine unrelated study units or turn a descriptive contrast into a confirmatory prediction.

## A. EOG-WF independent fresh heldout predictive programme (EMP-PRED)

**Frozen design:** same strong learner and conventional features in both arms; only the 10 symmetric Layer-B summary features are added. Primary binary log loss is macro-averaged over predeclared heldout units. Lower is better.

| Fresh scored endpoint | Baseline log loss | Baseline + frozen Layer B | Augmented − baseline | Heldout wins | Frozen verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| Azores yellow eel telemetry | 0.1422727 | **0.1322871** | **−0.0099856 (−7.0%)** | 5/5 blocks | **FAVORABLE** |
| Southwest Louisiana King Rail passive acoustics | 0.2463173 | **0.2453455** | **−0.0009718 (−0.39%)** | 7/8 occasions | **FAVORABLE (small)** |
| Tampa Bay seagrass transect monitoring | **0.3377354** | 0.4387640 | **+0.1010287 (+29.9%)** | 1/5 folds | **ADVERSE** |

Tampa's secondary 20×10-feature placebo median loss **0.3361758** also beat the real augmented model. The canonical external denominator is **3 scored / 31 scientific-protocol STOP / 3 administrative exclusions**, and the fourth endpoint is forbidden. No row-level cross-system pooling.

**Supported:** Layer A provides auditable *conditional* world-compatibility/falsification; Layer B can add heldout information in some systems, **not** uniformly. Louisiana also falsified the six frozen local Layer-A worlds while retaining an `external_open` world: structural falsification and predictive increment are distinct estimands.

**Not supported:** universal superiority, causal dispersal mechanism, actual world identity, a standalone EOG predictor, or retraining endpoint 3 until favorable.

Evidence: [EOG-WF paper-ready core](../../manuscript/paper_ready/methods_results_core.md), [mainline/closure](../development_mainline.md), [frozen evidence ledger](../evidence_ledger.md).

## B. External manipulated ecological experiments (EMP-EXPERIMENT)

Two *independent source experiments*, not a new independent experiment for each analysis version.

| Source experimental system | Supported result from frozen EOG reanalysis | Necessary negative/control | Source |
| --- | --- | --- | --- |
| **Fungal arrival order × plant hosts**; 233 plants, 12 genotypes, 5 arrival histories | Five-fungal community composition retained history beyond genotype-stratified permutation: excess `E=+0.1467`, **p=0.0001** | Host rust-lesion fraction `E=+0.0153`, **p=0.3893**: not a strong aggregate disease-history signal under the same metric | [v28](../eog_original_idea_leopold_history_retention_v28_result.md) |
| **Grassland above/belowground**; 19 rhizoboxes, F/G/L arrival orders | Aboveground functional-group composition retained history: `E=+0.8034`, **p=0.0001**; exact randomization over 31,104 label configurations agreed | Six-layer root composition `E=+0.0344`, **p=0.3765**; total shoot biomass also not significant | [v30](../eog_grassland_above_below_history_retention_v30_result.md) |
| **Different information-storage modes, reusing those same experiments** | Fungal rank-abundance retained identity-free memory `E=+0.1486`, **p=0.0001**; grassland rank-abundance `E=+0.1949`, **p=0.0769**, far below its labeled composition `E=+0.8034` | This is **not** two new independent biological replications; fungal histories can affect abundance *shape*, grassland histories more strongly the *identity-to-rank mapping* | [v31](../eog_identity_storage_rank_abundance_v31_result.md) |
| **Alternaria vs other fungal arrival histories, reusing v28** | Rank-1 dominance `E=+0.11812`, **p=0.0002** vs lower-rank tail `E=+0.04723`, **p=0.0316**; across host genotypes mean Alternaria-versus-other rank-1 difference **+0.06099**, positive **11/12**, **p=0.0001** | Interactions are not established: genotype-specific component **p=0.7548**; the mechanism suggested by v32 first-arriver role mapping was **not specific** under v33 placebo permutations | [v36](../eog_alternaria_binary_components_v36_result.md), [v37](../eog_alternaria_genotype_generality_v37_result.md), [v33 refutation](../eog_role_mapping_specificity_v33_result.md) |

**Biological positive inference:** the **same experimentally manipulated assembly history** can be strongly preserved in one final community state and weakly preserved in another. Its *representation* as named composition, unnamed rank architecture, dominance or belowground distribution can alter how much history is visible.

**Not inferred:** universal ecological law across taxa, unique causal interaction mechanism, fungal physiology, fitness or actual colonization paths. The source publications already reported priority effects; EOG's added result is the *target- and representation-specific quantified retention* under the frozen comparison.

## C. Real occupancy / landscape association and structural prediction (EMP-STRUCTURAL)

| System and unit | Retained positive or informative result | Frozen boundary | Source |
| --- | --- | --- | --- |
| **A-Islands:** 842 islands, 886 declared plant taxa, 845 species with estimable conditional statistic | Conditional concordance of occurrence-anchored graph reachability within local CHELSA support × nearest-source-distance strata **0.6177466**, species-bootstrap 95% CI **0.6086806–0.6269445** | Positive *conditional structural information*, **not** colonization probability or proof that EOG beats a fully matrix-aware comparator | [structural synthesis](../structural_validation_synthesis.md) |
| **NEON small mammals:** prospectively scored **16** sites | After the preregistered **turnover-generated continuity** hypothesis failed (**0/16 positive null-adjusted**), post hoc identity audit found **13/16 sites** with multiple individually continuous species; 32 species served that role across sites | Retained ecological finding = **redundancy of individual-species occupancy continuity**, not turnover-created continuity or directly measured animal movement. Post hoc identity counts are descriptive | [NEON fixed manuscript](../../manuscript/neon_small_mammal_continuity/MANUSCRIPT_V1.md), [closure receipt](../../validation/neon_metacommunity_connectivity_v1/programme_closure_v1.json) |
| **Six CHELSA taxon–region pairs**; 240 observations per pair | The forced two-cluster silhouette and density-core bridge score can rank actual environmental clouds differently (e.g., high silhouette/low bridge for `Bombus terrestris`; reverse for `Quercus robur`) | Diagnostic divergence, not demonstrated multiple niches, population breaks, causal fragmentation or superior prospective prediction | [real-taxon mode audit](../real_taxon_mode_audit_results.md) |

**Important negative comparator:** Tanzania forest birds (60 species, 14 fragments) had **worse** heldout species-macro log loss when EOG connected frequency was added above selected matrix-aware current flow + patch area + nearest training occurrence: **+0.0321131**, 95% CI **+0.0174580–+0.0486750**. This must accompany the A-Islands positive to delimit *when* incremental graph information remains after a strong reference. [Tanzania](../tanzania_heldout_result.md), [synthesis](../structural_validation_synthesis.md).

## D. Real-source exploratory or conditional application (EXPLORATORY; do not promote)

| Source and result | What it actually supports | Do **not** claim | Source |
| --- | --- | --- | --- |
| **Glanville fritillary**, 2007–2012: six-year conditional one-hop source–target exercise; 12/12 year × source-policy panels scored after documented km↔m coordinate fix | With frozen previous-positive candidate sources, the maximum nearest host-compatible-source radius depends on host-score tolerance and source-year eligibility. At unrestricted host tolerance (`delta=3`), one-year-source requirements ranged **2.6796–8.0498 km** across the six years | These are **not measured dispersal distances**, true founders, colonization rates, multi-hop historical routes, or a newly scored EOG-WF endpoint | [Glanville unit-fixed v2](../glanville_minrelax_empirical_unitfix_v2_result.md) |
| **Charaxes jasius**, 1,544 reduced trap records, 167 detections | District×year×oak matched capture cloud: centroid dispersion ratio **0.8899**, exploratory p **0.002**; upper-pairwise-span ratio **0.9649**, p **0.146** | This supports concentration differences *without* confirmed breadth contraction; not EOG superiority over centroid dispersion or direct BAM inference | [Charaxes](../charaxes_empirical_geometry_v1.md) |
| **Ryukyu published binary FST**, 16 populations | Against a predeclared **weak** current-flow reference, adding EOG improved retrospective heldout log loss by **−0.0266902** | Strong-reference superiority or independent raw-genetic validation; IBD alone was better than current flow | [Ryukyu](../eog_v2_ryukyu_published_binary_connectivity_result.md) |
| **Glanville original forecast** | Symmetric world-summary heldout macro log loss **0.187983**, compared with RF **0.191725**, IFM logistic **0.200242** and exact-world-ID **0.230197** | Because the original frozen external prospectively tested identity, that compression comparison is **not** an independent prospective EOG superiority claim | [README](../../README.md), [mainline](../development_mainline.md) |

## E. Frozen NO-PROMOTION and STOP results (mandatory context)

These are *not* mathematical positives or empirical predictive successes.

- **Finland strict-source occurrence:** 180 species, weak favorable mean EOG increment **−0.0001380** but species-bootstrap 95% CI upper **+0.0000000148**, so the predefined gate **FAILED**, no promotion. [result](../eog_v2_finland_strict_source_empirical_result.md).
- **Zhoushan frog genetic:** 27 populations / 351 FST pairs. The secondary IBD+EOG MSE improved by **−0.0003054**, but the primary current-flow reference failed to beat IBD and the predeclared EOG primary comparison deteriorated by **+0.40495**; **indeterminate strong-reference failure**, not genetic confirmation. [result](../eog_v2_zhoushan_frog_independent_genetic_result.md).
- **NutNet Hodapp Y3:** 30 eligible sites, site-heldout 8; unanimous nonzero sign in 3/8, correct in **2/3**, all three positive and not better than simple sign baseline. No generalization of mechanistic target-sign prediction. [result](../nutnet_hodapp_y3_scored_result_v1.md).
- **v27 ecological history:** permissions and missing experimental-unit IDs caused an **administrative/inferential STOP before target scoring**. [result](../eog_original_idea_empirical_history_retention_v27_result.md).
- **v29 wood decomposers:** archived original bytes not transportable; **STOP before biological scoring**. [result](../eog_wood_decomposer_history_retention_v29_result.md).
- Source metadata, checksum, CSV-header and schema gates (including pending source-only forest introduction / herbivore-protection work) are **not** biological positive outcomes.
- **Do not** add an extra EOG-WF fresh endpoint, pool method-paper rows across systems, tune a failed external reference after response, or rebrand a post hoc reanalysis as independent validation.

## Empirical headline suitable for writing

> **EOG's predictive contribution is context dependent (two favorable, one adverse fresh endpoint), while independent manipulated-community experiments reveal that assembly history can survive strongly in some present ecological state representations but weakly in others. Structural observations support conditional reachability information on islands and redundant individual-species continuity in NEON mammals, with explicit comparator boundaries.**

This is **not one pooled causal effect**. EOG-WF performance, experimentally manipulated history retention, spatial occupancy structure and exploratory real-data geometry are separate estimands.
