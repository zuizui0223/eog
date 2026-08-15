# EOG development mainline

## Status

This document defines the active scientific and repository-development direction after the 2026-08 cleanup and prior-art audit. It does **not** alter, rerun, rescue, or reinterpret frozen results recorded elsewhere.

Detailed implementation and comparator status belongs in [`eog_v2_progress.md`](eog_v2_progress.md). Frozen claims and negative results belong in their evidence ledgers/contracts. This file exists to keep **one scientific mainline**.

## Scientific center

EOG begins from a valid ecological distinction:

> **Local possibility is not the same object as distributional realizability.**

Observed occurrences constrain distribution-forming processes but do not identify one true route, colonisation history, ancestry, or movement rate.

The active question is:

> **Given an observed distribution and an explicitly declared set of ecological and analytical representations, what distribution-forming explanations remain compatible, what constraints must be relaxed to make the observations realizable, and which structural statements survive disagreement among those representations?**

## Positioning after the prior-art audit

EOG is **not currently positioned as a new general graph, connectivity, inverse-problem, or sensitivity-analysis algorithm**.

Known-truth comparators now show that the following ideas already reduce to established prior art in their corresponding special cases:

- dynamic/time-respecting reachability;
- critical geographic connection thresholds and stepping stones;
- minimum cumulative environmental exposure / least-exposure paths;
- multiple pathways and circuit-style redundancy;
- suitability + accessibility / functional habitat;
- consensus versus unanimity as different summaries;
- history-matching/NROY model-space reduction;
- minimum assumption relaxation / Pareto falsification frontiers.

These components may still be useful operators inside EOG, but they are not themselves novelty claims.

The remaining hypothesis is a **domain-framework/composition claim**:

> **EOG may provide ecological value by making occurrence-conditioned biogeographic world construction, ecological versus analyst-choice uncertainty, world identity, multi-axis rescue interpretation, underidentification, and coverage-limited structural claims explicit in one auditable workflow.**

This claim now requires empirical validation. It cannot be established by adding another synthetic operator.

## Core contracts retained

### Occurrence constraints

Occurrences are positive realized states. They constrain admissible worlds but do not prove a historical path.

Unobserved locations are not absences. Non-detection becomes evidence only under an explicit detection model.

### World identity

Ecological and analytical alternatives are declared as worlds. Mutually exclusive worlds must not be silently unioned or averaged before interpretation when that operation creates a configuration occurring in no declared world.

### Flow/support identity

Per-world flow/support outputs remain associated with the world that generated them. Lower/upper envelopes may summarize them but must not erase world identity.

Uncalibrated support is not called colonisation, dispersal, migration, occupancy, or ancestry probability.

### Relaxation axes

Geographic/IBD-like, environmental/IBE-like, and barrier relaxations remain separately inspectable unless a one-dimensional family was scientifically declared in advance.

A Pareto/minimum-relaxation frontier is treated as established sensitivity/falsification mathematics. EOG-specific interpretation, if useful, is the ecological meaning of those axes for an occurrence-conditioned biogeographic explanation.

### Coverage-limited robustness

`Robust` means robust over the declared certified universe, not universally true in nature.

Adding admissible worlds must make strong claims more conservative:

- robust sets may stay the same or shrink;
- possible sets may stay the same or expand;
- all-world exclusion may stay the same or shrink.

Claim strength must not exceed coverage/certificate strength.

## Distributional-watershed language

The watershed language is retained only as an ecological interpretation layer:

- occurrence = realized anchor;
- basin = reachable set under a declared world;
- channel / tributary = supported transition sequence;
- confluence = reconvergence;
- bottleneck = critical transition/state;
- divide = disconnected reachability boundary;
- water level `lambda` = a declared monotone one-dimensional relaxation coordinate only;
- basin merge = first declared relaxation level yielding joint realizability.

Threshold sweeps, basin merges, stepping-stone critical distances, and least-cost paths are established ideas. The watershed analogy is therefore **not a novelty claim**.

## Repository architecture

### Frozen/stable compatibility layer

Root `eog` remains the v0.1 compatibility surface for environmental geometry, shared-reference comparison, support topology, bridge inference, and survey tooling. Frozen reproduction paths remain valid.

### Prospective operator layer

`eog.v2` remains a thin compatibility namespace. New work stays behind three explicit lazy facades:

- `eog.v2.reachability` — static/temporal flow, compatible-world reconstruction, relaxation/frontier diagnostics, survey discrimination, and transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental/barrier/pathwise transition constraints;
- `eog.v2.validation` — independent occurrence, genetic, and directional-evidence validation.

Do not create another scientific facade because a new conceptual phrase appears.

### Empirical/system-specific layer

A-Islands, Tanzania, Finland, Ryukyu, Zhoushan, and similar code are validation/adapters, not the generic API.

### Manuscript layer

`manuscript/` preserves the earlier structural-reachability empirical/submission line. It is publication provenance and evidence, not the active package architecture. See [`../manuscript/README.md`](../manuscript/README.md).

## Current phase — freeze one ecological validation contract

Synthetic operator growth stops here by default.

The next work must ask whether the **combined framework** adds useful ecological information beyond established methods in a predeclared case.

Before touching an outcome, freeze:

1. **Ecological question** — e.g. what current distribution requires a geographic versus environmental versus barrier relaxation, or which analytical representations remain compatible with an observed island configuration.
2. **World universe** — list natural/ecological uncertainties separately from analyst-choice uncertainties.
3. **Comparators** — match each estimand with the strongest established method rather than a weak baseline.
4. **Validation endpoint** — held-out occurrence, time-stamped colonisation/recolonisation, independently surveyed intermediate site, or independent genetic/movement evidence only where scientifically appropriate.
5. **No-added-value outcome** — specify what result would show the combined EOG framework provides no useful additional information.
6. **Claim certificate** — state whether the universe is exhaustively enumerated, sampled, bounded, or otherwise incomplete.

A favourable result may justify a biogeographic methods/framework paper. A null result is equally admissible and must remain in the evidence record.

## Cleanup rules

1. Preserve scientific evidence before removing implementation.
2. Do not retune adverse/null/indeterminate results.
3. Reuse an existing facade/operator before adding a module family.
4. Keep new workflows narrowly dependency-scoped; Package checks own package-wide regression.
5. Keep presentation/manuscript code out of eager scientific-core imports.
6. New prospective names stay off root compatibility namespaces unless compatibility requires them.
7. Physically remove/move legacy code only after repository search shows no frozen reproduction path depends on it.
8. Do not merge stale diverged branches wholesale across later scientific changes; salvage only still-valid changes onto current main.
9. Benchmark/prior-art comparisons belong in `benchmarks/` and `tests/`, not the public API.

## Deferred until a concrete validation need exists

- surveyed absence / non-detection inference — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration is itself an estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous/enormous world spaces — require explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific forecast question and comparator are frozen.

## Stop rule

Do not add another operator merely to chase a smaller novelty niche. Do not open another occurrence/genetic dataset merely to obtain a favourable result. Preserve genuinely different worlds as a set whenever observations do not identify one history, and stop the integrated line if a predeclared ecological validation shows no useful added value beyond established methods.
