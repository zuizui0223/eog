# EOG development mainline

## Status

This document defines the **single active scientific development line** after the 2026-08 cleanup and prior-art audit. It does not alter, rerun, rescue or reinterpret frozen results.

- implementation / comparator status: [`eog_v2_progress.md`](eog_v2_progress.md)
- package ownership: [`eog_v2_package_layout.md`](eog_v2_package_layout.md)
- frozen claims and adverse/null results: [`evidence_ledger.md`](evidence_ledger.md), [`claim_matrix.md`](claim_matrix.md)

If another document conflicts with this file about the active development direction, this file is the mainline source of truth.

## Scientific center

EOG begins from one ecological distinction:

> **Local possibility is not the same inferential object as distributional realizability.**

Observed occurrences are realized positive states. They constrain distribution-forming processes but do not identify one true route, colonisation history, ancestry, migration rate or movement process.

The active question is:

> **Given an observed distribution and an explicitly declared set of ecological and analytical representations, which distribution-forming explanations remain compatible, what assumptions must be relaxed to realize the observations, and which structural conclusions survive disagreement among those representations?**

## Positioning after the prior-art audit

EOG is **not currently positioned as a new general graph, connectivity, dynamic-reachability, inverse-problem or sensitivity-analysis algorithm**.

Known-truth comparators have removed generic novelty claims for:

- time-respecting / dynamic reachability;
- critical geographic connection thresholds and stepping stones;
- least-cost / minimum cumulative environmental exposure paths;
- multiple pathways and circuit-style redundancy;
- suitability + accessibility / functional habitat;
- consensus versus unanimity as alternative summaries;
- history-matching / NROY world filtering;
- minimum-assumption relaxation, Pareto rescue sets and falsification-frontier mathematics.

These may remain useful operators inside EOG. They are not the main contribution.

The remaining scientific hypothesis is a **domain-framework / composition claim**:

> **Biogeographic inference may gain useful information when occurrence-conditioned ecological and analyst-choice alternatives are carried as explicit worlds, mutually exclusive worlds are not silently averaged or unioned, underidentification is preserved, and robust claims are restricted to the coverage actually certified.**

This hypothesis now requires empirical validation. It cannot be established by another synthetic operator.

## Core contracts retained

### Occurrence constraints

Occurrences are positive realized states. They constrain admissible worlds but do not prove a historical path.

Unobserved locations are not absences. Non-detection becomes evidence only under an explicit detection model.

### World identity

Ecological and analytical alternatives are declared as worlds. Mutually exclusive worlds must not be silently unioned or averaged before interpretation when that operation creates a configuration occurring in no declared world.

### Flow / support identity

Per-world flow/support outputs remain associated with the world that generated them. Lower/upper envelopes may summarize them but must not erase world identity.

Uncalibrated support is not called colonisation, dispersal, migration, occupancy or ancestry probability.

### Relaxation axes

Geographic/IBD-like, environmental/IBE-like and barrier relaxations remain separately inspectable unless a one-dimensional family was scientifically declared before seeing the result.

Pareto/minimum-relaxation frontiers are established sensitivity/falsification mathematics. EOG-specific value, if demonstrated, lies in the ecological interpretation and auditability of the declared axes and worlds.

### Coverage-limited robustness

`Robust` means robust over the declared certified universe, not universally true in nature.

Adding admissible worlds must make strong claims more conservative:

- robust sets may stay the same or shrink;
- possible sets may stay the same or expand;
- all-world exclusion may stay the same or shrink.

Claim strength must not exceed coverage/certificate strength.

## Distributional-watershed language

Watershed terminology is retained only as an interpretation layer:

- occurrence = realized anchor;
- basin = reachable set under a declared world;
- channel / tributary = supported transition sequence;
- confluence = reconvergence;
- bottleneck = critical transition/state;
- divide = disconnected reachability boundary;
- water level `lambda` = a declared monotone one-dimensional relaxation coordinate only;
- basin merge = first declared relaxation level yielding joint realizability.

Threshold sweeps, basin merges, stepping-stone critical distances and least-cost paths are established ideas. The watershed analogy is not a novelty claim.

## Repository architecture

### Frozen / stable compatibility layer

Root `eog` remains the v0.1 compatibility surface for environmental geometry, shared-reference comparison, support topology, bridge inference and survey tooling. Frozen reproduction paths remain valid.

### Prospective operator layer

`eog.v2` remains a thin compatibility namespace. New work stays behind three lazy facades:

- `eog.v2.reachability` — static/temporal flow, compatible-world reconstruction, world-indexed support sets, relaxation diagnostics, survey discrimination and transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental/barrier/pathwise transition constraints;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation.

Do not create another scientific facade because a new conceptual phrase appears.

### Empirical / system-specific layer

A-Islands, Tanzania, Finland, Ryukyu, Zhoushan and similar code are validation/adapters, not generic API families.

### Manuscript layer

`manuscript/` preserves the earlier structural-reachability publication/evidence line. It is publication provenance, not the active package architecture.

## Current phase — validate or stop the integrated framework

Synthetic operator growth stops here by default.

### Immediate development target

The next mainline target is to answer one question:

> **Does retaining explicit ecological + analyst-choice world identity produce useful ecological information beyond established matching methods?**

PR #181 provides a response-free A-Islands world-set adapter as an **exploratory development representation only**. A-Islands has already been viewed and therefore cannot become a new confirmatory result for this integrated line.

The mainline sequence is now:

1. **Exploratory usefulness check** — inspect whether the frozen A-Islands scenario family produces non-trivial robust/contingent/excluded structure and meaningful geography-versus-environment representation disagreement without using held-out outcomes.
2. **Freeze an independent confirmation contract only if Step 1 is informative** — select a system that was not used to shape the framework.
3. **Predeclare the confirmation** — ecological question, natural vs analyst-choice world axes, strongest matching comparators, independent/held-out endpoint, no-added-value outcome, and coverage/certificate boundary.
4. **Run the confirmation once** — favourable and null outcomes are both admissible.
5. **Decision** — if explicit world retention adds no useful ecological information, stop the integrated EOG line rather than add complexity. If it adds value, only then simplify/package the framework around the demonstrated estimand.

### Valid confirmation endpoints

Examples include:

- held-out positive occurrences;
- time-stamped colonisation or recolonisation observations;
- independently surveyed intermediate sites;
- independent genetic or movement evidence only where its interpretation matches the declared hypothesis.

AUC superiority is not required. The test is whether EOG adds a defensible inferential object that the matched comparator does not already provide.

## Side-line policy

Side lines are allowed, but only when they have a distinct purpose, an owner and a stop condition.

### Allowed side lines

- frozen structural-manuscript archive/release work;
- maintenance needed to reproduce frozen evidence;
- an independent empirical validation required by the mainline;
- a previously defined field-recovery analysis **only after the required original input tables are actually archived**;
- a scientific branch whose estimand is genuinely different from the mainline and whose relationship to EOG is explicit.

### Not allowed as active development

- a branch opened only to chase a smaller novelty niche;
- another connectivity/path/threshold operator already covered by prior art;
- another public EOG identity or facade;
- an empirical dataset opened because it looks favourable;
- retuning an adverse/null/indeterminate frozen result;
- a side branch with no explicit merge/close condition.

A useful side line may coexist with the mainline, but it must not redefine the EOG center.

## Cleanup rules

1. Preserve scientific evidence before removing implementation.
2. Do not retune adverse/null/indeterminate results.
3. Reuse an existing facade/operator before adding a module family.
4. Keep workflows narrowly dependency-scoped; Package checks own package-wide regression.
5. Keep presentation/manuscript code out of eager scientific-core imports.
6. New prospective names stay off root compatibility namespaces unless compatibility requires them.
7. Physically remove or move legacy code only after repository search shows no frozen reproduction path depends on it.
8. Do not merge stale diverged branches wholesale across later scientific changes; salvage only still-valid changes onto current main.
9. Benchmark/prior-art comparisons belong in `benchmarks/` and `tests/`, not the public API.
10. A completed branch should be merged or closed; historical remote refs are not treated as active development merely because they still exist.

## Deferred until a concrete validation need exists

- surveyed absence / non-detection inference — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration is itself an estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous/enormous world spaces — require explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific forecast question and comparator are frozen.

## Stop rule

Do not add another operator merely to chase novelty. Do not open another occurrence/genetic dataset merely to obtain a favourable result. Preserve genuinely different worlds as a set whenever observations do not identify one history, and stop the integrated line if a predeclared ecological validation shows no useful added value beyond established methods.
