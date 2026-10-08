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

## Interpretation: history content is not measurement access

High source-basin overlap can create a strong dependence of the **equilibrium provenance map** on source activation order. This need not yield highly distinguishable **transient occupancy signatures**. In more dispersed sources, source identity may have less influence on the equilibrium provenance composition, while the temporal occupation wavefront can make histories easier to tell apart.

The direct v23 provenance channel then recovers information inaccessible to occupancy-only surveys in many clustered landscapes. Combining both kinds of evidence substantially reduces the choice-of-readout dependency.

This supports a more precise synthetic structural statement than simply *history matters*:

> **The ranking of source arrangements by historical identifiability is jointly determined by spatial source geometry and the ecological state variable that the observation process actually measures.**

Crucially, this is **not** evidence that concentrated source populations retain more *total* history in an information-theoretic sense, that dispersal redundancy causes observational nonidentifiability, or that field observation under clustering is intrinsically more expensive. Both libraries are ideal and of different content/effort.

## Relation to existing work

Historical contingency, priority effects and alternative transient histories are established, including [Fukami (2011)](https://doi.org/10.1111/j.1461-0248.2011.01663.x), [Fukami (2015)](https://doi.org/10.1146/annurev-ecolsys-110411-160340), and [Song et al. (2021)](https://doi.org/10.1111/ele.13870). Thus the general claim that history can be difficult to reconstruct, or that time-resolved and state-resolved observations contain different information, is not a priority claim for EOG.

The specific EOG contribution remains the strict matching and explicit separation of: **geographic coverage, worst-source deletion retention, latent earliest-source historical provenance, and identification through two declared observation libraries** across already frozen comparable landscapes.

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
