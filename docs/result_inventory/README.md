# EOG evidence split — mathematical/known-truth vs empirical

> **最小制約緩和（2026-11-20追加監査）:** [数理Pareto前線・Glanville実測制約・潜在起源／遺伝推定の限界を分離](MINIMUM_REQUIRED_RELAXATION_AUDIT_20261120.md)。既知真値の検証成功と、実際の移動・起源推定成功は異なる。


> **精査版（2026-11-20）:** [数理・既知真値の詳細監査](MATHEMATICAL_DEEP_AUDIT_20261120.md) — T=集合・アルゴリズム上の必然、K=既知真値で非自明な効果量、X=構成的反例、D=事後診断、F=反証を分離。特に世界拡張境界・latent parameter・源policyの非単調性・EOG spanの非単調性を追加。

**Audit date:** 2026-11-20 (JST)  
**Audited main:** `f8028c50a28fb74faa4766347f05cd830655e075`  
**Status:** synthesis/index only; no new analysis, endpoint, hypothesis, promotion, re-fit, or post-outcome repair.

This index does **not** replace [the scientific mainline](../development_mainline.md), [the frozen evidence ledger](../evidence_ledger.md), or the original result files. Read those sources for authoritative wording, versioned protocols, frozen fingerprints, CI runs and STOP rules.

## Read these two ledgers separately

| Lane | What is actually evaluated | Primary ledger |
| --- | --- | --- |
| **M — mathematics / known-truth** | Set identities, finite-world certificates, synthetic generators with known truth, identifiability and exact experimental-design results | [MATHEMATICAL_AND_KNOWN_TRUTH.md](MATHEMATICAL_AND_KNOWN_TRUTH.md) |
| **E — empirical** | Heldout predictions, externally sourced manipulated experiments, occurrence/genetic/monitoring records, and descriptive readouts | [EMPIRICAL_RESULTS.md](EMPIRICAL_RESULTS.md) |

### Do not mix the denominators

- **M is not biological replication.** A theorem, a CI test, 768 generated truths, 64 random seeds and 12 virtual systems are not independent ecological field sites.
- **EOG-WF's frozen independent predictive denominator is exactly 3 scored endpoints** (Azores eel favorable, Louisiana King Rail favorable, Tampa seagrass adverse), **31 scientific/protocol STOPs and 3 administrative exclusions**. **No fourth EOG-WF endpoint is permitted.**
- The **separate** NEON small-mammal 16-site programme tests a biological continuity hypothesis, not a fourth EOG-WF predictive endpoint.
- Experimental **v28/v30/v31–v37 are repeated reanalyses of two external underlying experiments**, not ten independent ecological replications. Some follow-ups were post-exposure.
- Exploratory real-source results (e.g. Glanville minimum relaxation, Charaxes geometry) demonstrate applicability/conditional geometry; they do not automatically constitute prospective prediction improvements or direct mechanistic identifications.
- A successful workflow/transport/checksum/metadata gate is **technical validation**, not a positive ecological result.

## Status vocabulary

| Marker | Meaning |
| --- | --- |
| **LOGIC / EXACT** | Holds by explicit set definition, exhaustive finite enumeration, or an exact algorithm under its contract. Not a general ecological theorem about nature. |
| **KNOWN-TRUTH** | Predeclared synthetic/controlled result with declared generator and truth; quantitative evidence about that generator. |
| **EMP-PRED+ / EMP-PRED−** | A scored real-data heldout predictive contrast with favorable/adverse direction; the complete preregistered endpoint decision is retained. |
| **EMP-EXPERIMENT** | A reanalysis of observed manipulated experimental outcomes, with its own experimental unit, contrast and permutation/uncertainty rule. |
| **EMP-STRUCTURAL** | An empirically observed spatial/structural association or independently supported biological pattern; not necessarily model superiority. |
| **EXPLORATORY** | Real data but retrospective, post-exposure or otherwise outside the confirmatory endpoint. |
| **STOP / NO-PROMOTION** | No admissible scientific score or a failed promotion gate. Preserve; do not relabel as favorable or adverse when non-estimable. |
| **CONCEPT / FUTURE** | Proposed development, not yet a verified result. |

## Current take-home distinction

**Mathematically supported:** Conditional on a declared finite universe, occurrences can falsify some worlds without identifying the generating mechanism; target-specific additional evidence and observation channels can resolve some, but not all, consequential ambiguities; honest unresolved/certificate outputs can be computed.

**Empirically supported:** The unchanged EOG-WF symmetric summary sometimes complements a strong learner but also can harm it (2 favorable, 1 adverse). Independently, manipulated fungal/plant experiments show that assembly history is retained differently across present-state targets; island occurrence graphs carry conditional structural information, while stronger landscape references can remove EOG's incremental value.

The evidence **does not** show that EOG universally outperforms SDMs, reconstructs true dispersal routes, universally explains community history, or establishes causal A/B/M decomposition from observed occurrences.

## Related repository boundaries

- [N1–N4 fixed research spine](../../N1_N4_SPINE.md): N3/EOG answers WHERE supported local states can be realized; it does not absorb SDMR/ODSP/ACSP claims.
- [Paper-ready EOG-WF methods/results](../../manuscript/paper_ready/methods_results_core.md): frozen 3-endpoint mainline.
- [Known-truth development mainline](../known_truth_development_mainline.md): simulation programme outside the EOG-WF denominator.
- [v3 joint-world engine](../eog_v3_joint_world_engine.md): public experimental finite-world API and controls.
- [Structural validation synthesis](../structural_validation_synthesis.md): A-Islands positive versus Tanzania negative comparison. The standalone Structural manuscript has been migrated to `zuizui0223/Structural`; EOG retains historical provenance only.

## Next evidence gate (no retroactive changes)

1. Maintain this ledger as a **read-only map to authoritative results**, not a new score/endpoint registry.
2. Keep any new source gate or open PR in **unscored / pending** until it has an admissible, independently frozen biological response result.
3. If a future test needs new confirmatory evidence, freeze the target, unit, reference, source permissions, holdout, decision rule and hard STOPs before looking at response values **in a separate programme**.
