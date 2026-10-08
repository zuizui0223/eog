# EOG v23 observation-readout crossover — frozen matched synthetic exploration

**Status: POST-RESULT EXPLORATORY, NOT PREREGISTERED JOINT TEST.**

## One ecological question

> **Can the same spatial arrangement preserve a strong historical signature yet fail to reveal that history under one observation method—and become informative when a different historical coordinate is observed?**

The v18–v23 source layouts, latent landscape, three source identities and the three alternative activation histories are kept **identical** within each of **384 matched directed synthetic landscapes**. No new simulation, source removal, observation time, threshold or ecological alternative was introduced.

Two independent frozen *readout libraries* had already been defined in v23:

1. **Occupancy-only:** perfect binary transient occupancy snapshots after the final source activation, at t4, t5, t6, t8, excluding the source nodes. These are structural graph steps, not ecological years.
2. **Provenance-only:** idealized equilibrium first-arriving-source labels at eligible nodes. These are **not** genetic ancestry, parentage or migration estimates.
3. **Combined:** the union of the two fixed libraries.

The outcome is **whether the entire three-history activation-order class is exactly distinguishable**, not which actual history occurred in the wild or how cheaply it could be measured.

## The direct rank reversal

| Library resolving the three activation histories | Clustered placement | Dispersed placement |
|---|---:|---:|
| Occupancy snapshots only | **231/384** | **348/384** |
| Equilibrium earliest-source provenance only | **228/384** | **44/384** |
| Both kinds of observations | **338/384** | **349/384** |

Paired landscape classifications:

| Layout(s) identifiable | Occupancy only | Provenance only | Combined |
|---|---:|---:|---:|
| Neither | 14 | 155 | 9 |
| Only dispersed | **139** | 1 | 37 |
| Only clustered | 22 | **185** | 26 |
| Both | 209 | 43 | 312 |

**In 78/384 landscapes, the preferred geometry changed in the strictest possible way:**

- an occupancy-only library identified complete history **only for the dispersed sources**;
- a provenance-only library identified complete history **only for the clustered sources**.

The opposite strict crossover (occupancy-only clustered, provenance-only dispersed) occurred in **0/384**, under these specific frozen settings.

Within those 78 landscapes:

- all **78** had *greater latent equilibrium source-provenance history disagreement* under clustered placement;
- **75** also displayed the v18 **three-source coverage/structural-insurance trade-off**: dispersed sources covered more nodes while clustered sources retained more after worst-source deletion;
- the **combined** library identified complete history under **both** layouts in **78/78** cases.

The 78 strict crossovers are distributed across all preregistered landscape-factor settings (29/128 with barrier density 0.05; 27/128 with 0.20; 22/128 with 0.35; 25/192 rook and 53/192 queen; 48/192 low and 30/192 high environmental autocorrelation).

## Marginal information after accounting for baseline observability

The v23 combined library never loses a history that either individual library identifies. Therefore the count rescued by **adding provenance to occupancy** is `combined identified - occupancy identified`.

| Layout | Still unresolved after occupancy alone | Newly resolved by adding provenance | Fraction of unresolved rescued |
|---|---:|---:|---:|
| Clustered | **153/384** | **107** | **107/153 = 69.9%** |
| Dispersed | **36/384** | **1** | **1/36 = 2.8%** |

The reciprocal question **adding occupancy after provenance** gives clustered **110/156 = 70.5%** and dispersed **305/340 = 89.7%**.

This matters for interpretation: **107 versus 1** is not comparable in isolation because occupancy-only information already identified **348/384** dispersed-layout histories, leaving just 36 potentially rescuable cases, versus **231/384** clustered-layout histories leaving 153. Reporting unresolved-case denominators makes the ceiling explicit. The residual conditional contrast remains large under the fixed ideal libraries, but must not be interpreted as an equally priced field assay comparison.

Machine-calculated arithmetic and the exact source-blob fingerprint: `validation/eog_virtual_world_ecology_synthesis_v1/readout_marginal_value_v1.json`. No underlying simulation, target definition, first-pass claim, or archive changed.

## What produces the apparent 107-versus-1 gain?

The previous comparison counted everything identified after adding the ideal provenance library to the existing ideal occupancy library. It must distinguish **a second library that can solve the target by itself** from cases that require genuinely *mixed evidence*.

Exact classification of each frozen v23 three-history result gives:

| Occupancy alone insufficient: method of rescue | Clustered | Dispersed |
|---|---:|---:|
| Provenance library itself already identifies all histories | **90** | **0** |
| Neither full library identifies alone, but mixed observations do | **17** | **1** |
| **Total identified after adding provenance to occupancy** | **107** | **1** |
| Occupancy-unresolved designs | 153 | 36 |

In the **18** genuine mixed-library cases (17 clustered, 1 dispersed), the frozen exact minimum combination contains **one complete occupancy snapshot and one ideal earliest-source provenance tag**. Under the declared v23 action library, neither the full set of occupancy snapshots nor the full set of provenance tags alone identifies all three activation histories.

The complete five-state classification, in the order `occupancy-identifiable / provenance-identifiable / combined-identifiable`, is:

| Classification | Clustered | Dispersed |
|---|---:|---:|
| 000 — no library suffices | 46 | 35 |
| 001 — **mixed information required** | **17** | **1** |
| 011 — provenance alone suffices, occupancy fails | 90 | 0 |
| 101 — occupancy alone suffices, provenance fails | 93 | 304 |
| 111 — either individual library suffices | 138 | 44 |

**Interpretive correction:** the 69.9% versus 2.8% conditional gain should not be described as 107 versus 1 cases of emergent cross-channel synergy. The strict mixed-evidence result is **17/153 (11.1%) of occupancy-unresolved clustered layouts** versus **1/36 (2.8%) of occupancy-unresolved dispersed layouts**. Most of the clustered improvement is exclusive information already recoverable from provenance measurements alone (**90/153, 58.8%**).

This decomposition follows solely from the original v23 exact action-selection results. It changes neither the preregistered v23 findings nor the exploratory 384-landscape source-geometry results, and does not imply one full-landscape occupancy scan and one pointwise provenance assay have equal field cost or biological feasibility.

Audit: `scripts/audit_eog_v23_readout_synergy_v1.py`. Frozen machine record: `validation/eog_virtual_world_ecology_synthesis_v1/v23_readout_synergy_decomposition_v1.json`.

## Exact witness and an important target–observation scope mismatch

A direct check of all **18** previously classified strict mixed-evidence cases in the original archived v23 rows finds that:

- Every exact minimal evidence set is **two actions**: the **`O_t4` transient occupancy snapshot** and exactly **one `P_node` earliest-source provenance tag**.
- The chosen provenance action is history-informative at **a source-basin confluence node**. Across the original v23 panel, provenance tags at static unique-source-origin nodes never carried activation-order information.
- Therefore each of the 18 cases needs the union of *two different kinds of history contrast*, rather than simply adding more occupancy snapshots or more provenance tags under the frozen action library.

This identifies the **informational witness** but not a new ecological mechanism. With exactly three candidate activation histories, any two individually incomplete observations that jointly distinguish all three must separate different history pairs. The frozen output contains their exact action IDs, but not the original per-history action-value matrix; do **not** claim to know which named pair each action uniquely separated.

### The inference target includes more than the provenance assays observe

An additional audit found **35/768 source-layout cases** (clustered **34/384**, dispersed **1/384**) where:

1. the idealized **complete equilibrium source-provenance target** had **three distinguishable classes** across the histories, but
2. the *entire permitted provenance-only observation library* could not identify all three.

This is not a contradiction. In the original v23 implementation, the target (`provenance_class_count`) is defined from provenance over **all equilibrium-reachable nodes**, including the source nodes. However, the actual `P_node` assays are defined **only for non-source nodes**. Consequently, a difference in the target may be hidden in node locations that the permitted assay library never measures. Two of the 18 strict mixed cases fall into this category.

**Interpretation:** the identifiability ceiling depends not only on the ecological state variable, but also on the **spatial support of the measurements permitted for that variable**. The missing source-node observations are a declared observation-design boundary, not evidence that natural source histories were erased.

This audit does **not** invent an extra measurement at a source node, relax v23's predefined source-exclusion rule, or rescore the original hypotheses. Raw per-history action signatures were not stored in the v23 result summary; establishing each exact source-node contrast would require separate access to those signatures and is **not claimed here**.

Machine receipt: `validation/eog_virtual_world_ecology_synthesis_v1/v23_readout_witness_boundary_v1.json`. The standalone verifier reads the **unchanged original v23 artifact** with its SHA-256 and must exactly reproduce all 18 witnesses and 35 target–observation mismatches.

## Interpretation: history content is not measurement access

High source-basin overlap can create a strong dependence of the **equilibrium provenance map** on source activation order. This need not yield highly distinguishable **transient occupancy signatures**. In more dispersed sources, source identity may have less influence on the equilibrium provenance composition, while the temporal occupation wavefront can make histories easier to tell apart.

The direct v23 provenance channel then recovers information inaccessible to occupancy-only surveys in many clustered landscapes. Combining both kinds of evidence substantially reduces the choice-of-readout dependency.

This supports a more precise synthetic structural statement than simply *history matters*:

> **The ranking of source arrangements by historical identifiability is jointly determined by spatial source geometry and the ecological state variable that the observation process actually measures.**

Crucially, this is **not** evidence that concentrated source populations retain more *total* history in an information-theoretic sense, that dispersal redundancy causes observational nonidentifiability, or that field observation under clustering is intrinsically more expensive. Both libraries are ideal and of different content/effort.

## Relation to existing work

Historical contingency, priority effects and alternative transient histories are established, including [Fukami (2011)](https://doi.org/10.1111/j.1461-0248.2011.01663.x), [Fukami (2015)](https://doi.org/10.1146/annurev-ecolsys-110411-160340), and [Song et al. (2021)](https://doi.org/10.1111/ele.13870). Thus the general claim that history can be difficult to reconstruct, or that time-resolved and state-resolved observations contain different information, is not a priority claim for EOG.

The specific EOG contribution remains the strict matching and explicit separation of: **geographic coverage, worst-source deletion retention, latent earliest-source historical provenance, and identification through two declared observation libraries** across already frozen comparable landscapes.

### Existing real-world genetic data: a different observation class, not source-of-first-arrival truth

A **public genetic-kinship source** exists for the same Åland Glanville fritillary metapopulation: [Fountain et al., Dryad 10.5061/dryad.d461s](https://doi.org/10.5061/dryad.d461s) reconstructs cross-patch maternal full-sib families from 2007–2012, while EOG's separately frozen [annual occupancy source](../validation/glanville_eogwf/README.md) covers 1999–2018. This is a genuine independent *data modality*, but **NOT a new independent external validation** and **NOT the v23 ideal directional earliest-source tag**. A cross-patch full-sib dyad is undirected without additional timing, and the genetic sampling does not cover the EOG-WF heldout target years 2013–2018.

**[Response-free cross-source qualification](eog_glanville_genetic_provenance_preflight_v1.md)** documents original source identities and hard non-independence / first-arrival-direction gates. No genotype records or old Glanville response data were opened by this qualification.

## What this cannot establish

- **Nature:** there are no real colonization dates, independently observed founder-source labels, demographic extinctions, field-measured detection probabilities or experimentally removed source populations.
- **Causality:** the joint dependence does not isolate source-basin overlap from every correlated feature changed by clustered/dispersed source placement; do not claim a mediating mechanism.
- **Generality:** all 384 cases originate from the same previously used directed generator family and same frozen three histories. Counts are not an ecological prevalence estimate.
- **Protocol:** the v23 observation libraries were fixed before v23 scoring, **but the v18–v23 cross-phase comparison was defined after seeing earlier results**. It is exploratory and cannot be relabelled as v23 preregistered support.
- **Measurement burden:** unlike an actual genetic/provenance assay, ideal equilibrium origin tags are provided without laboratory expense or classification error. Do not equate library minima or classification rates with sampling cost.
- **Publication:** no new third-paper mainline is authorized by this exploratory virtual-world result. The previously frozen EOG-WF, JBI inverse-BAM and Ecology Letters assembly-history articles remain separate and unmodified.

## Authoritative source and reproducibility

This audit reopens only five already-scored synthetic JSON artifacts, never any biological survey data. SHA-256 of the **exact source archive**, the result's original fingerprint, the matching 384 landscape keys and the three source identifiers are all verified. The v23 occupancy arm must reproduce v22 bit-for-bit on identification.

- v18 archived artifact `11321111760`;
- v19 `11321161763`;
- v21 `11322163376`;
- v22 `11324282807`;
- v23 `11324893031` — original archive SHA-256 `a859e7b6ec5e8af47b56a67a10b89ae7ab65ca3e1a70aed9317f663f863eaae9`.

Machine receipt: `validation/eog_virtual_world_ecology_synthesis_v1/matched_readout_crossover_v1.json`.

Reproducer: `scripts/audit_eog_history_readout_crossover_v1.py`. Dedicated CI downloads the exact frozen archives and verifies that recomputation matches the machine receipt. GitHub Actions artifact retention may limit future fresh downloads; verified source hashes, result fingerprints and summary remain recorded.

## Decision

**SUPPORTED AS A REPRODUCIBLE POST-HOC SYNTHETIC OBSERVATION-CHANNEL CROSSOVER, NOT AS AN EMPIRICAL OR PREREGISTERED MECHANISM.**

The next external ecological advance would require independently sampled time-resolved occupancy **and** true or calibrated source-origin evidence in the same patch network—alongside a qualified natural source-loss/recolonization response. The previously closed Glanville and NEON endpoints, and the pre-response *Lepanthes* STOP, must not be retrospectively promoted to supply that missing confirmation.
