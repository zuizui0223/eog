# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

Current empirical state:

> **exploratory-supported but independently unconfirmed**

Current methodological state:

> **The finite world-set core is a coherent conditional, set-valued inference framework. Independent inferential value and predictive added value remain unconfirmed and must be tested as separate estimands.**

Synthetic/generic operator growth is stopped by default.

Normative validation rules now live in [`method_validation_protocol.md`](method_validation_protocol.md). Frozen earlier empirical contracts are evidence and are not rewritten to match the improved protocol.

## Scientific center

EOG distinguishes local possibility from distributional realizability and historical truth.

Observed occurrences are realized positive states. They constrain admissible distribution-forming processes but do not identify one true route, colonisation history, ancestry, migration rate or movement process.

The active scientific question is:

> **Does retaining ecological and analyst-choice alternatives as explicit worlds preserve independently useful biogeographic distinctions that are lost by predeclared compression, while preserving underidentification and limiting robust claims to certified coverage?**

A separate question is whether exact world identity improves held-out predictive loss. That is no longer used as a synonym for method validity.

## Fixed novelty boundary

EOG is not positioned as a new general graph/connectivity/dynamic-reachability/inverse-problem algorithm.

The following are established prior art or comparators rather than EOG novelty claims:

- time-respecting reachability;
- critical geographic thresholds / stepping stones;
- least-cost / minimum cumulative environmental exposure;
- circuit-style redundancy;
- suitable + accessible functional habitat;
- consensus/ensemble summaries;
- history matching / NROY filtering;
- minimum-relaxation / Pareto falsification frontiers.

The remaining contribution hypothesis is a **biogeographic domain-framework/composition claim**: explicit world identity may preserve useful information that is lost by premature averaging/union, while keeping underidentification and coverage limits explicit.

## Core contracts

1. Occurrences are positive evidence, not route proof.
2. Anchor/source policy is conditioning information, not inferred ancestry.
3. Mutually exclusive worlds are not silently unioned before inference.
4. Per-world support remains attached to its generating world.
5. Geographic/IBD-like, environmental/IBE-like and barrier axes remain separately inspectable unless a one-dimensional family was declared in advance.
6. `Robust` means robust over the declared certified universe only.
7. Uncalibrated support is not called colonisation, dispersal, occupancy, migration or ancestry probability.
8. Analyst-choice sensitivity worlds are not called biological process worlds without external ecological calibration.
9. Catalogue non-record is not biological absence without an explicit observation/detection interpretation.

## Method-validation correction

The 2026-08 audit identified one important mismatch: previous independent-confirmation contracts made held-out predictive log loss the decisive endpoint even though EOG's remaining contribution hypothesis is primarily a **set-valued uncertainty/identifiability claim**.

Future validation therefore separates two estimands.

### Primary — identity-preserving inferential value

Predeclare a compression of the same world universe and identify cases where that compression maps distinct exact world identities to the same summary. Then predeclare independent evidence that can discriminate a consequence on which those worlds disagree.

A favourable result means exact world identity preserved an independently testable distinction erased by the compression.

It does **not** mean that EOG identified the true historical route.

### Secondary — predictive added value

If prediction is itself a target, compare exact world identity against:

- a strong compression of the same frozen world universe; and
- any external ecological method over which superiority is explicitly claimed.

A same-world `C_identity - R2` contrast tests identity beyond that compression. It does not, by itself, establish superiority over SDM, occupancy, dispersal, circuit, least-cost or other process models.

Predictive success and inferential-value success must be reported separately.

## World-universe adequacy

Finite enumeration makes set operations exact but does not make the universe ecologically complete.

Every future empirical world universe must classify each dimension as:

- **natural/process uncertainty**, or
- **analyst-choice uncertainty**.

The contract must state provenance/calibration, why levels are admissible, which plausible alternatives remain outside coverage, and how strong claims respond to universe expansion.

Quantile thresholds may be useful analyst-choice sensitivity levels; they are not automatically dispersal distances or tolerance limits.

## Validation ledger

### A-Islands — exploratory structural PASS; predictive extension adverse

A response-free 12-world adapter showed that scalar `connected_frequency` can collapse distinct exact world identities and geography-versus-environment support decompositions. Because A-Islands had already been viewed, this is exploratory development evidence only.

Separately, the prospectively frozen A-Islands strong-reference predictive extension was adverse: the candidate `C - R3` held-out log-loss contrast was positive rather than favourable. That result remains frozen and is not reinterpreted as a test of the newer exact-world-identity estimand.

### SIVFLORA — independent, non-estimable pre-outcome

The first independent attempt froze its design before outcome access, then stopped because WorldClim v2.1 2.5m had nodata at four frozen nodes. The frozen contract prohibited node movement, imputation, resolution change or product substitution after coverage was observed. No predictive outcome was run.

### Azores — independent, non-estimable pre-model

The second independent attempt was staged through:

1. source-byte freeze;
2. response-blind nine-node freeze;
3. climate freeze;
4. response-blind 20-world universe freeze;
5. response/comparator/model contract freeze;
6. once-only taxon estimability gate.

Gates 1–5 passed. Gate 6 read only the frozen Taxon core and found:

- 15,256 canonical taxa;
- 8,078 canonical species;
- 2,455 canonical Plantae species;
- **0 species satisfying the frozen literal `Tracheophyta` rule**.

Status:

`non_estimable_pre_model_taxon_scope_zero`

The source used vocabularies including `Magnoliophyta`, `Pteridophyta`, `Lycopodiophyta` and `Pinophyta`. Broadening the frozen rule after observing this vocabulary is prohibited.

Critically, Distribution rows were not read, response values were not scored, no R0/R1/R2/C model was fitted and no confirmation metric was computed.

The methodological lesson is prospective: a future generic eligibility screen may inspect response-blind categorical vocabularies needed for deterministic semantic mappings **before** the EOG-specific outcome contract is frozen. This does not rescue Azores.

Durable evidence is indexed at `validation/azores_confirmation/README.md`.

## Dependence and uncertainty rule

The independent unit must match the generalisation claim. If the target is a new island, species-island rows do not become independent island replicates merely because there are many species.

A large bootstrap replicate count cannot compensate for very few independent outer units. Confirmatory interval/test language with small cluster counts requires design-specific pre-outcome calibration or simulation; otherwise uncertainty is descriptive and outer-unit effects/directions are reported without artificial precision.

The frozen nine-island Azores contract is not retuned.

## Scientific decision

EOG currently has:

- exact finite-core behavior: **supported**;
- ecological interpretation: **conditional on world/anchor/response contracts**;
- independent identity-preserving inferential value: **unconfirmed**;
- predictive added value: **not established**;
- historical identification: **not claimed**.

Therefore:

- do not add a new operator to rescue the integrated line;
- do not repair SIVFLORA or Azores after their frozen stop conditions;
- do not interpret non-estimability as favourable or null EOG evidence;
- do not launch a third bespoke dataset search merely to get an estimable/favourable result;
- keep blocked-system machinery outside the production API.

A future independent test is admissible only through the generic eligibility and validation sequence in `method_validation_protocol.md`.

## Repository architecture

- root `eog`: frozen v0.1 compatibility surface;
- `eog.v2`: thin lazy compatibility namespace;
- `eog.v2.reachability`, `traversability`, `validation`: owning scientific facades;
- `benchmarks/` + `validation/`: system-specific prior-art/empirical evidence;
- `manuscript/`: frozen earlier structural publication/evidence line.

Do not create another facade or public EOG identity because a new conceptual phrase appears.

## Side-line policy

Allowed side lines require a distinct purpose and stop condition, e.g. frozen manuscript archive/release work, reproduction maintenance, or a pre-existing field validation once original inputs are archived.

Not allowed: novelty chasing, duplicate connectivity operators, blocked-system retuning, favourable-data search, or another public EOG architecture.

## Cleanup rules

1. Preserve scientific evidence before deleting implementation.
2. Preserve adverse/null/blocked/indeterminate results.
3. Reuse existing operators/facades before adding modules.
4. Package checks own package-wide regression; completed one-time scientific workflows should not remain active indefinitely.
5. System-specific validation stays outside eager package imports.
6. Do not whole-merge stale diverged branches across later scientific changes.
7. A completed branch should be merged or closed; remote branch existence is not active development.

## Stop rule

Do not add another operator or open another empirical dataset merely to obtain a favourable result. The next scientific work is a genuinely independent, pre-eligible test of the **identity-preserving inferential estimand**, with predictive performance evaluated separately when relevant.
