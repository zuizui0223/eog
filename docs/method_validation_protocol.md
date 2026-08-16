# EOG method-validation protocol

## Status

This document defines how the active EOG method claim is to be validated after the 2026-08 methodological audit.

The audit does **not** reopen or retune any frozen empirical result. In particular, the A-Islands strong-reference result, the SIVFLORA climate block, and the Azores pre-model taxon-scope block remain unchanged historical evidence.

Current verdict:

> **EOG is a coherent conditional, set-valued biogeographic inference framework over an explicitly declared world universe. Its predictive superiority is not established, and predictive superiority is not the same estimand as validity of the world-set inference.**

The active contribution claim is therefore narrower than a new SDM, dispersal algorithm, or universal forecasting product.

## 1. The inferential object

EOG must keep four objects distinct:

1. **local possibility** — locally supported under a declared environmental/process representation;
2. **reachability** — reachable from a declared anchor/source set under a declared transition rule;
3. **distributional realizability** — compatible with the observed positive occurrence configuration inside a declared world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate, or demographic process in nature.

The first three may be computed conditionally. The fourth is not identified merely because a world is compatible.

For a declared finite world universe `W`, observations `O`, and compatibility predicate `C(w, O)`, the primary inverse object is

```text
W(O) = {w in W : C(w, O)}
```

This is an **unranked compatible set** unless an independently justified ranking model was declared.

Observed occurrences are positive realized constraints. Unobserved locations are not biological absences without an explicit observation/detection interpretation.

## 2. What is methodologically valid now

### 2.1 Conditional world reconstruction

The current finite core explicitly conditions on declared source/anchor policy and declared transition operators. It does not infer one true historical route. This is a valid conditional inverse question.

### 2.2 World identity preservation

If two admissible worlds imply different structures, EOG may retain them separately rather than average, union, or select them before interpretation. An aggregate is allowed only when the scientific estimand itself is the aggregate.

### 2.3 Finite-universe robustness

For compatible worlds, node/state conclusions may be classified as:

- reachable/supported in every compatible world;
- contingent across compatible worlds;
- unsupported/unreachable in every compatible world.

These statements are exact only over the enumerated, certified universe. They are **conditional robustness**, not universal ecological certainty.

### 2.4 Underidentification is an output

If several worlds remain compatible, the correct output is the set of alternatives and their disagreement structure. Failure to identify one history is not an algorithmic failure.

## 3. What the method must not claim

EOG must not claim novelty for, or superiority simply by containing:

- dynamic/time-respecting reachability;
- critical connection thresholds or stepping stones;
- least-cost/minimum-exposure paths;
- circuit-style redundancy;
- suitability + accessibility / functional habitat;
- ensemble/consensus summaries;
- history matching / NROY filtering;
- minimum-relaxation/Pareto/falsification-frontier mathematics.

Likewise, a probability-like reachability support is not called occupancy probability, colonisation probability, migration rate, ancestry probability, or demographic connectivity unless a calibrated stochastic model supports that interpretation.

## 4. The key correction: separate two validation estimands

The previous independent-confirmation contracts emphasized whether a complete world-identity vector improves held-out binary log loss over compressed summaries. That is a legitimate **predictive increment** test, but it is not the whole method claim.

Future validation must separate:

### A. Primary method estimand — identity-preserving inferential value

Question:

> **Does retaining exact world identity preserve a scientifically actionable distinction that is erased by a predeclared compression of the same world universe, and can independent evidence discriminate that distinction?**

A valid test requires a predeclared collision or equivalence class in which two candidates have the same compressed summary but differ in exact supporting-world identity or decomposition. Independent evidence must then test the consequence that differs between those worlds.

Examples of admissible independent discriminators include:

- a later positive occurrence at a site reachable in only a subset of colliding worlds;
- time-stamped colonisation/recolonisation evidence that eliminates some worlds;
- an independently surveyed intermediate site when the survey outcome has an explicit detection interpretation;
- genetic or movement evidence only when its interpretation was declared before inspecting the EOG outcome.

Success here validates the **set-valued inferential object**, not predictive superiority and not historical truth.

### B. Secondary estimand — predictive increment

Question:

> **Does exact world identity improve held-out predictive loss beyond a strong predeclared compression/reference?**

A design such as `C_identity - R2` is appropriate for this narrower claim because it isolates identity beyond summaries of the same frozen worlds.

However:

- `R2` is a strong **same-world compression comparator**, not automatically a state-of-the-art ecological-method comparator;
- external SDM, dispersal, connectivity, occupancy, or process-model comparators must be declared separately when superiority over those methods is claimed;
- predictive failure does not by itself invalidate a useful uncertainty/identifiability representation;
- predictive success does not establish historical truth.

## 5. World-universe adequacy is part of the method

A mathematically exact finite-world result can still be ecologically weak if the declared world universe is poorly justified.

Every future world universe must therefore carry an adequacy record with each dimension typed as one of:

- **natural/process uncertainty** — alternatives intended to represent biologically plausible processes or parameter regimes;
- **analyst-choice uncertainty** — alternative products, thresholds, preprocessing choices, graph constructions, or other defensible analytical decisions.

For each dimension record:

1. provenance or external rationale;
2. whether values are ecologically calibrated or only sensitivity-grid values;
3. why the enumerated levels are admissible;
4. which plausible alternatives remain outside the certificate;
5. how conclusions change when admissible worlds are added.

Quantile-based geographic/environmental thresholds are acceptable as analyst-choice sensitivity worlds. They are **not** automatically species-specific dispersal limits or biological tolerance thresholds.

No `robust` or `impossible` wording may exceed this adequacy record.

## 6. Anchor/source conditionality

Training or observed occurrences may be used as realized anchors under an explicit policy, including fixed-source or self-excluded evaluation.

They must not silently become inferred ancestral sources.

Every empirical result must state the conditioning explicitly, for example:

> reachable from the outer-training realized occurrences under the declared world universe

rather than:

> the species historically dispersed from these locations.

Held-out targets must not contribute to their own anchor set.

## 7. Response and absence semantics

A catalogue non-record may be used as a negative class only when the prediction target is explicitly **catalogue-record status under the frozen catalogue rule**.

It is not a biological absence by default.

Claims about occupancy, extinction, failed colonisation, or unsuitable habitat require an observation/detection or survey-completeness model appropriate to that claim.

## 8. Pre-outcome eligibility screen

Before freezing an EOG-specific confirmation contract, a candidate dataset must pass a **generic eligibility screen** that does not inspect the world-identity outcome.

The screen may inspect source/schema metadata and non-response vocabularies needed to make deterministic semantic mappings. It must establish:

1. immutable source identity and licence/provenance;
2. unambiguous node/spatial-unit mapping;
3. environmental/input coverage under the intended representation;
4. taxonomic/rank/establishment vocabulary sufficient to implement the intended semantic population;
5. response semantics and whether non-records can support the planned target;
6. enough independent held-out units for the planned inference;
7. no dependence of eligibility on EOG world-identity results.

This corrects the Azores design lesson: a preregistration should freeze the **semantic taxonomic population and deterministic mapping**, after a response-blind vocabulary audit, rather than betting the entire confirmation on an unverified literal taxonomy string.

The frozen Azores contract is not changed retroactively.

## 9. Dependence and uncertainty

Ecological observations are often spatially, temporally, taxonomically, or hierarchically dependent. Validation units must match the intended generalisation target.

For a claim that generalises to new islands, island-level holdout remains the primary independence unit; thousands of species-island rows must not be treated as thousands of independent island replicates.

A large number of bootstrap draws does not create additional independent units. Therefore:

- a percentile bootstrap over a very small number of outer islands is descriptive unless its operating characteristics are justified for the planned design;
- confirmatory interval/test language requires a pre-outcome simulation or other design-specific justification showing acceptable error/coverage under the actual cluster count and dependence structure;
- otherwise report paired outer-unit effects, direction counts, and uncertainty descriptively rather than converting a small set of islands into artificial precision.

The frozen nine-island Azores contract remains historical and is not retuned.

## 10. Required future validation sequence

### Gate 0 — generic eligibility

Pass the source/schema/node/input/taxonomy/response/independent-unit screen before an EOG-specific outcome contract is frozen.

### Gate 1 — world-universe adequacy freeze

Freeze world IDs, natural versus analyst-choice dimensions, provenance, parameter/threshold rationale, anchor policy, coverage boundary, and universe-expansion sensitivity rule.

### Gate 2 — primary structural/identity test freeze

Predeclare:

- the compressed comparator of the same world universe;
- the exact collision/disagreement object lost by that compression;
- the independent evidence that can discriminate the alternatives;
- the result that counts as no added inferential value.

### Gate 3 — optional predictive increment freeze

Only if prediction is itself a target, predeclare external and same-world comparators, holdout structure, loss, dependence-aware inference, and no-added-value rule.

### Gate 4 — run once

No retuning after independent evidence/outcomes are opened.

## 11. Decision rules

The following statements must remain separate:

- **mathematical/core validity** — finite world-set operations behave as declared;
- **ecological interpretability** — world dimensions and response semantics correspond to stated ecological concepts;
- **independent inferential value** — independent evidence discriminates world-identity distinctions erased by a predeclared compression;
- **predictive added value** — held-out predictive loss improves over a stated comparator;
- **historical identification** — actual history is identified; this normally requires stronger evidence and is not implied by the previous four.

Current EOG status is:

- mathematical/core validity: **supported by exact finite-world implementation/tests**;
- ecological interpretability: **conditional on declared world/anchor/response contracts**;
- independent inferential value: **unconfirmed**;
- predictive added value: **not established; prior frozen strong-reference extensions include adverse results**;
- historical identification: **not claimed**.

## 12. Stop rules

- Do not add an operator to rescue a failed validation.
- Do not weaken a comparator after outcome inspection.
- Do not call analyst-choice quantiles biological dispersal limits.
- Do not call catalogue non-record biological absence without an observation model.
- Do not use small-cluster resampling to manufacture apparent replication.
- Do not broaden a frozen blocked contract on the same opened dataset and call it independent confirmation.
- Do not require predictive superiority as proof of a set-valued inferential representation, and do not use set-valued usefulness as proof of predictive superiority.
- Do not claim universal robustness outside the declared adequacy certificate.
