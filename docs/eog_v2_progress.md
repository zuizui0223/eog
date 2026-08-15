# EOG v2 prospective progress ledger

## Status after the 2026-08 cleanup

This ledger tracks only the **active integrated method line**. Frozen positive, adverse, null, failed and indeterminate results remain preserved in their dedicated evidence ledgers, contracts, fingerprints and benchmark artifacts; they are not retuned or rewritten here.

Active scientific direction: [`development_mainline.md`](development_mainline.md).

## Finite inverse/reachability architecture — implemented

The explicit `eog.v2.reachability` facade contains the finite known-truth core for the distributional-watershed / world-reconstruction program.

### Static finite worlds

- [x] exact forward reachability envelopes;
- [x] inverse reconstruction of compatible worlds from positive occurrences;
- [x] world-indexed support-flow sets and lower/upper envelopes;
- [x] `reachable_in_all`, `contingent` and finite-universe `robustly_unreachable` classes;
- [x] geographic/IBD, environmental/IBE and barrier relaxation kept as separate axes;
- [x] non-dominated minimum-relaxation frontier;
- [x] declared monotone one-dimensional relaxation families only where scientifically predeclared;
- [x] first-possible versus first-robust basin merge across analytical variants;
- [x] positive-occurrence discrimination among compatible worlds;
- [x] compact archetype falsification matrix covering IBD, IBE, hard barriers, niche deserts, stepping stones, rare low-support jumps, branching/reconvergence, analytical ambiguity and finite-universe expansion.

### Temporal finite worlds

- [x] ordered `TemporalWorld` transition sequences;
- [x] source mass injected once at the initial state only;
- [x] exact-time support and cumulative reached-by-time kept distinct;
- [x] world-indexed temporal support envelopes and finite reachability classes;
- [x] positive time-stamped occurrence reconstruction;
- [x] explicit preservation of multiple compatible temporal histories;
- [x] positive `(node, time)` survey discrimination without treating non-detection as absence;
- [x] robust / contingent / inactive directed transition edges by interval;
- [x] possible and robust corridor opening/closure summaries;
- [x] exact nested temporal-world-universe monotonicity;
- [x] axis-preserving temporal minimum-relaxation frontier.

These are finite known-truth capabilities. `robust` means robust over the explicitly declared and exhaustively enumerated universe, not universal ecological certainty.

## Comparator / falsification gates

The active question is no longer whether another operator can be added. It is whether the integrated inverse/set-valued architecture contains inferential information that simpler or established representations do not already provide.

### Gate 1 — endpoint/final-horizon/scalar summaries: passed

`benchmarks/inverse_estimand_comparator.py` shows:

- discarding time makes `C@t2` and `C@t3` identical;
- final-horizon compatibility retains slow and fast explanations together;
- scalar geographic + environmental + barrier relaxation loses axis identity;
- the EOG inverse layer can eliminate a slow zero-relaxation world with earlier timing while retaining three non-dominated axis-specific rescue explanations.

This is estimand separation, not external-method superiority.

### Gate 2 — existing static bridge baseline: passed

`benchmarks/bridge_vs_temporal_reconstruction.py` reuses the existing v0.1 cumulative/minimax/redundancy bridge implementation.

Two temporal worlds have the same time-aggregated A-B-C graph. Static bridge inference correctly returns the same A-B-C path, cumulative cost and bottleneck for both. Only the world with A→B before B→C can satisfy the time-stamped positive observation `C@t2`.

Conclusion: **static connectivity and time-constrained realizability are different estimands**. The bridge result is not considered wrong.

### Gate 3 — time-respecting Boolean dynamic connectivity: negative boundary passed

`benchmarks/dynamic_connectivity_negative_boundary.py` independently propagates Boolean time-respecting connectivity.

At zero structural support tolerance it exactly reproduces:

- EOG cumulative reached-by-time structure across ordered, reversed, branching/confluence and low-positive-support scenarios;
- positive temporal compatible-world filtering for `C@t2`.

Therefore EOG must **not** claim novelty for forward dynamic reachability, time-respecting path existence, or positive temporal filtering by themselves.

### Gate 4 — consensus frequency versus universal certificate: current gate

`benchmarks/consensus_vs_universal_certificate.py` compares two valid but different summaries.

Final known-truth design:

- `A` is a fixed source;
- `R` is a common observed non-source target reachable in every declared world, so all worlds satisfy the same frozen occurrence contract;
- `T` is reachable in 99 of 100 worlds;
- `E` is unreachable in all 100 worlds.

Expected distinction:

- T has 0.99 reachability frequency and satisfies a 0.95 consensus rule;
- T is robust in the original 99-world universe but becomes `contingent` after adding the one excluding world;
- T remains possible and is not relabelled impossible;
- E remains finite-universe `robustly_unreachable` with frequency 0.

This tests **agreement frequency versus invariance**, not whether consensus methods are wrong.

## Repository cleanup state

- [x] root `eog` and `eog.v2` compatibility roots are lazy;
- [x] `eog.v2.reachability`, `traversability` and `validation` are lazy scientific facades;
- [x] new prospective names remain on explicit owning facades rather than widening `eog.v2` root;
- [x] package/facade refactors no longer rerun unrelated frozen scientific confirmations;
- [x] package-wide regression remains in Package checks;
- [x] historical structural manuscript assets are explicitly labelled as a frozen publication/evidence line in `manuscript/README.md`;
- [x] `README.md`, `development_mainline.md`, `eog_v2_progress.md`, and `eog_v2_package_layout.md` now have distinct roles rather than duplicating stale “next gate” narratives;
- [x] stale diverged cleanup work is not merged wholesale across later scientific changes; only still-valid changes are ported to current mainline work.

The repository still contains many historical branches. The available connector does not expose safe branch deletion, so branch refs are not force-reset merely to reduce their count.

## Next decision after Gate 4

If the consensus/certificate gate passes, the next step is **not another EOG operator**. Freeze one external established-method comparison around a matching estimand.

Priority candidates:

- functional / accessible habitat or least-cost/circuit summaries for static accessibility;
- a published dynamic-connectivity representation for time-respecting reachability, where agreement with EOG forward structure is expected;
- dynamic occupancy or mechanistic range models only when repeated observations/detection data make those process estimands identifiable;
- ensemble/consensus approaches specifically for analyst-choice uncertainty and world aggregation.

The external benchmark should report where estimands coincide, where they differ, and which additional EOG claim remains after the negative boundaries above. EOG does not need to win every predictive metric.

## Deferred until a concrete validation need exists

- surveyed absences / non-detection evidence — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration becomes a scientific estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous or enormous world spaces — requires explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological forecast question is frozen;
- new empirical promotion claims — only after comparator, endpoint and validation design are predeclared.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by the explicit coverage certificate.
