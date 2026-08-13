# EOG design charter

## Status

This is the authoritative design charter for Environmental Occupancy Geometry. It governs
what may be proposed, implemented and claimed in this repository.

It is a **design document, not a result document**. It does not alter, reinterpret or
supersede any frozen empirical outcome. Where this charter and a frozen contract appear to
disagree, the frozen contract wins and the discrepancy must be recorded rather than edited
away. In particular this charter is subordinate to:

- `docs/evidence_ledger.md` — verified quantities and unsupported claims;
- `docs/structural_validation_synthesis.md` — cross-system evidence frame and the
  prospective development rule;
- `manuscript/submission/novelty_claim_matrix.md` — prohibited and approved novelty language;
- the frozen pre-outcome contracts under `docs/` and `validation/`.

## 1. Purpose

EOG is designed as an auditable ecological-informatics framework that separates observed
environmental state, geographic support structure, between-population reachability and
inferential limits. It is deliberately **not** positioned as an SDM extension and **not** as
a new distance index.

The central problem EOG exists to address is the conflation of two distinct questions:

> **Can the organism persist at that location?** (environmental suitability)
>
> **Can it be reached from a known population?** (reachability / accessibility)

Islands make this separation unavoidable. Two locations with near-identical environmental
conditions can differ greatly in accessibility because of straits, distance, stepping-stone
availability, geological history, wind and ocean currents. EOG therefore places that
separation at the centre of the method rather than treating it as a robustness check.

## 2. The four layers

The layers are ordered by what they consume, not by importance. Each layer owns a distinct
estimand. A new capability belongs to exactly one layer.

### Layer 1 — Environmental-state geometry

**Question:** what environmental states are actually occupied, and how are they structured
internally?

Occurrences are treated as a point cloud in environmental feature space. Under a shared,
frozen reference transformation the layer describes extent, internal structure and
differences using span, MST compactness and gap summaries.

**Prohibition:** compactness in environmental space must never be read as geographic
connectivity or dispersal. Comparative breadth requires a shared frozen transformation;
independent within-cloud scaling removes global dilation and therefore cannot support
absolute breadth comparison.

**Implementation:** `geometry.py`, `comparative.py`, `uncertainty.py`, `comparators.py`.

**Standing evidence constraint:** the multiaxial archetype benchmark falsified the original
broad four-axis interpretation, and the irrelevant-dimension audit showed that these
statistics are not robust to arbitrary feature matrices. This layer therefore carries
narrow, audited claims only (see `docs/evidence_ledger.md`).

### Layer 2 — Spatial support topology

**Question:** how are the geographic supports of those states structured relative to known
populations?

For a **frozen** support field produced independently of EOG, the layer tracks connected
components of superlevel sets across a predeclared threshold sequence and identifies
occurrence-anchored, persistent detached, transient detached and unresolved structure. Hard
masks mark cells that are unavailable, which is distinct from low support.

The layer extracts what cellwise suitability cannot show: **two equally suitable regions can
stand in different structural relations to known populations.**

**Prohibition:** the support field is an input. EOG does not fit it, does not relabel its
output as probability, and does not implement paths, bottlenecks or ranking here.

**Implementation:** `support_topology.py`, `support_topology_comparison.py`,
`support_model.py` (benchmark-side producer only).

### Layer 3 — Bridge / reachability inference

**Question:** which transitions between observed populations are ecologically plausible?

The estimand is widened from per-cell presence probability to the bridge that may exist
between a **declared source–target population pair**. For a pair A–B the following are
evaluated and reported **separately**:

- geographic transition;
- environmental transition;
- structural barrier;
- cumulative path cost;
- maximum bottleneck;
- alternative-path redundancy;
- sampling uncertainty.

"The two endpoints have similar environments" and "a propagation route between them can
exist" are treated as different hypotheses and are never merged into one statement.

**Prohibition:** path and reachability summaries are assumption-dependent graph diagnostics.
They are not dispersal, colonisation, demographic-connectivity or historical-route estimates.
Connected frequency is the fraction of declared scenarios linking a target to a training
anchor; no calibration converts it to a probability.

**Implementation:** `bridge.py`, `bridge_builder.py`, `bridge_sensitivity.py`,
`island_reachability.py`, `conditional_reachability.py`, `prepared_island_*.py`.

### Layer 4 — Hypothesis-discriminating survey

**Question:** what new observation would best discriminate among competing explanations?

The objective is explicitly **not** a ranking of high-suitability sites. Candidate sites are
scored by how strongly they separate competing hypotheses — environmental filtering,
dispersal limitation, barrier, stepping-stone colonisation, long-distance dispersal and
sampling gap — rather than by detection probability alone.

**Prohibition:** discrimination scores are decision support. They are not occurrence
probability, posterior model probability or expected information gain.

**Implementation:** `hypothesis_discrimination.py`, `survey_priority.py`,
`hypothesis_survey_*.py`, and the `eog-hypothesis-survey*` CLIs.

## 3. Estimand separation rule

Environmental state, geography, dispersal and sampling uncertainty must not be collapsed
into a single all-purpose score. Each estimand is stored separately. Integration, where
required, happens downstream and is declared as such.

This rule is why the repository keeps raw gap strength, silhouette and core-bridge evidence
separate, and why conditional-ordering endpoints and predictive-loss endpoints are never
placed on one common effect-size scale.

## 4. Absence is not barrier

An absence or a blank region is never automatically interpreted as a barrier. At minimum the
following states are distinguished:

| State | Meaning |
|---|---|
| `environmentally_unsupported` | declared support model does not support the location |
| `reachability_limited` | supported, but not reachable under declared graph assumptions |
| `surveyed_empty` | sufficiently surveyed and genuinely empty |
| `unsurveyed` | not surveyed, or surveyed too poorly to inform |
| `unresolved` | available evidence cannot separate the states above |

Collapsing these into a binary absence is a design violation, not a simplification.

## 5. Comparability is itself an audit target

Feature set, reference, scaling, support definition, sample-size matching, thresholds, mask,
neighbourhood and anchor definition are declared and frozen **before** the outcome they
apply to. Manifests, fingerprints and sensitivity analyses secure reproducibility and the
claim boundary.

Fingerprints establish identity and provenance. They do not make an ecological conclusion
true.

When a comparison is developed after an earlier result already exists, its timing is
recorded explicitly rather than being relabelled as part of the earlier design.

## 6. Answerability over statistic count

EOG prioritises

> stating which question can be answered under which data and assumptions, and returning
> `unresolved` / `unsupported` for questions that cannot be answered

over adding new statistics. A method that produces a confident number where the design
cannot support one is worse than a method that declines.

Non-estimable species, folds and strata are retained and reported, never silently dropped.

## 7. Differentiation stance

Overclaims against existing methods are prohibited. "SDMs do not handle dispersal" and
"SPDE does not handle connectivity" are both forbidden framings. Dynamic SDMs, occupancy
models, diffusion models, landscape resistance, graph connectivity and SPDE approaches are
acknowledged as established and, in several cases, as stronger references than EOG.

EOG's distinctiveness is placed in one sentence:

> separating and connecting — within a single auditable framework — the geometry of observed
> environmental states, support-region topology, source-conditioned population-pair bridges,
> and the inference contract that governs them.

Not in local suitability estimation, and not in being first to combine suitability with
connectivity.

## 8. Admission checklist for new work

Every proposed feature, analysis or extension must answer all of the following before
implementation:

1. Which of the four layers' questions does it belong to?
2. Does it duplicate the estimand of an existing layer?
3. Does it conflate suitability with reachability?
4. Does it conflate spatial correlation with propagation?
5. Does it conflate absence with sampling gap?
6. Is it more than a recombination of existing methods — does it strengthen an inference
   target specific to EOG?
7. Is it verifiable on held-out empirical data or independent information, not only on
   synthetic benchmarks?
8. Can it preserve failure conditions, sensitivity and claim boundary alongside the result?

A proposal that cannot answer 1–3 is rejected. A proposal that fails 7 or 8 may be
implemented only as a declared synthetic-stage component and may not carry an empirical
claim.

The prospective development rule in `docs/structural_validation_synthesis.md` continues to
apply on top of this checklist: any extension motivated by an existing adverse outcome must
be independently motivated, frozen before its own outcome is inspected, compared against an
equal or stronger reference, and reported alongside — never instead of — the frozen results.

## 9. The framing question

EOG does not ask only:

> "Where could the species occur?"

It asks:

> "What environmental states are actually occupied, how are their geographic supports
> structured, which transitions between observed populations are ecologically plausible, and
> what new observation would best discriminate among competing explanations?"

## 10. Conformance status

Current implementation state against this charter, as audited on 2026-08-13. This section
records gaps; it does not authorise closing them without the section 8 checklist.

| Charter element | Status | Evidence |
|---|---|---|
| Layer 1 implemented | present, claims narrowed by audit | `geometry.py`; `docs/multiaxial_archetype_results.md` |
| Layer 2 implemented | present; validated on synthetic landscapes only | `support_topology.py`; `docs/support_topology_heldout_comparison.md` states it is not evidence of transfer to ecological data |
| Layer 3 implemented | present, with empirical held-out evaluation | `island_reachability.py`, `conditional_reachability.py`; A-Islands and Tanzania outcomes |
| Layer 3 estimand separation | partial | `bridge.py` reports cumulative cost, bottleneck, redundancy and cost components separately; **sampling uncertainty is not carried as a per-pair estimand** |
| Layer 4 implemented | present, with CLIs and audit contract | `hypothesis_discrimination.py`; `docs/hypothesis_survey_contract.md` |
| Layer 4 hypothesis vocabulary | partial | hypotheses are caller-declared support surfaces; the charter's named hypothesis classes (filtering, dispersal limitation, barrier, stepping stone, long-distance dispersal, sampling gap) are not first-class types |
| Support field is an input, never fitted by EOG | conformant in substance, blurred at the API surface | Layers 2–4 consume a frozen field and no EOG function converts structure to an occurrence probability. However the top-level API exports `fit_penalized_logistic_support`, a benchmark-side support producer, next to the structural entry points; only its module docstring marks the boundary |
| Estimands not collapsed into one score | conformant | separate endpoints; conditional-ordering and predictive-loss results are never pooled |
| Absence five-state taxonomy | **partial** | the v2 simulator and validation I/O separate `surveyed_mask`, `current_occurrence`, `historical_reached` and an `unsurveyed_intermediate` scenario, and `v2_empirical_occurrence_validate_cli` treats blanks as unsurveyed rather than as zeros. The states are **not** first-class node types in the propagation operator, so no inference rule prevents an unsurveyed node from being scored like a surveyed-empty one |
| Comparability audit machinery | **partial** | `manifest.py` and `reference_policy.py` validate Layer 1 metrics only; Layers 2–4 each emit independent ad-hoc fingerprints with no shared manifest |
| Non-estimable states retained | conformant | A-Islands and Tanzania outcomes report non-estimable species and folds explicitly |
| No overclaiming against existing methods | conformant | `manuscript/submission/novelty_claim_matrix.md` enumerates prohibited framings |

### Relationship to EOG v2

The v2 line merged into `main` in PR #142 subdivides Layer 3 rather than adding a fifth
layer. Its `V` / `R` / `C` / `P` / `O` separation is a refinement of this charter's
suitability-versus-reachability rule: `V` is local viability, `R` is source-conditioned
reachability, and `C`, `P`, `O` keep target capture, establishment and detection from being
folded into either. `DynamicReachabilityEdge` keeps geographic, environmental, barrier,
directional and target-capture support as separate multiplicative components, which
satisfies the estimand-separation rule of section 3 at the edge level.

Two charter requirements remain unmet by v2 and define the current development frontier:

- **transit viability is not represented.** Edge support and node viability are separate
  objects in v2, but the operator does not require intermediate nodes to be viable, so a
  route through a state the species cannot occupy is not distinguished from a route through
  habitable intermediates. This conflates continuous propagation with long-distance jumps —
  a section 3 violation.
- **environmental transition support is exogenous.** `environmental_support` is supplied
  per edge by the caller. Nothing derives which environmental transitions are traversable
  for the species from the occurrence configuration itself, so the charter's framing
  question — what occurrence records constrain beyond viability — is only half answered.

### Open gaps, in priority order

1. **The absence taxonomy is not enforced in inference.** The states exist in v2 simulation
   and I/O but not as node types the operator reasons over. Nothing currently stops an
   unsurveyed node from being treated as evidence of absence, which is the interpretation
   section 4 forbids.
2. **No unified comparability manifest.** Section 5 requires declaration and freezing across
   all four layers, but the manifest and reference-policy modules only cover Layer 1. Layers
   2–4 self-fingerprint in mutually incompatible formats.
3. **Sampling uncertainty is not a Layer 3 estimand.** Section 2 lists it among the seven
   quantities to evaluate separately for a declared pair; `BridgeInference` does not carry it.
4. **Layer 4 hypothesis classes are untyped.** The competing explanations named in the
   charter are supplied as arbitrary caller-declared support surfaces, so the framework
   cannot check that a survey design actually spans the intended hypothesis space.
5. **The support-producer boundary is documented but not enforced.** `fit_penalized_logistic_support`
   sits in the same public namespace as the structural entry points, so nothing at the API
   surface stops a caller from treating an EOG-fitted support field as an EOG result.

None of these gaps may be closed by editing a frozen result, and each closure must pass the
section 8 checklist before implementation.
