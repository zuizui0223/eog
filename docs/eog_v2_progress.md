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
- [x] compact archetype falsification matrix.

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

`benchmarks/inverse_estimand_comparator.py` shows that endpoint-only and final-horizon summaries lose timing information, scalar relaxation loses axis identity, and the inverse EOG layer can retain a non-dominated set of geographic-only, environmental-only and barrier-only rescue explanations without selecting one history.

### Gate 2 — existing static bridge baseline: passed

`benchmarks/bridge_vs_temporal_reconstruction.py` reuses the existing v0.1 cumulative/minimax/redundancy bridge implementation. The static bridge is correct for a time-aggregated A-B-C graph, while a time-stamped `C@t2` observation distinguishes worlds with different transition order. Static connectivity and time-constrained realizability are different estimands.

### Gate 3 — time-respecting Boolean dynamic connectivity: negative boundary passed

`benchmarks/dynamic_connectivity_negative_boundary.py` independently reproduces EOG cumulative reached-by-time structure and positive temporal compatible-world filtering at zero support tolerance.

Therefore EOG must **not** claim novelty for forward dynamic reachability, time-respecting path existence, or positive temporal filtering by themselves.

### Gate 4 — consensus frequency versus universal certificate: passed

`benchmarks/consensus_vs_universal_certificate.py` establishes the distinction between agreement frequency and invariance across every declared world.

Known truth:

- `A` is the fixed source;
- `R` is a common observed non-source target reachable in every world;
- `T` is reachable in 99 of 100 worlds;
- `E` is unreachable in all 100 worlds.

Result:

- T has 0.99 reachability frequency and satisfies a 0.95 consensus rule;
- T is robust in the original 99-world universe but becomes `contingent` after adding the one excluding world;
- T remains possible and is not relabelled impossible;
- E remains finite-universe `robustly_unreachable` with frequency 0.

Consensus and universal robustness are both valid but different estimands.

### Gate 5 — Keitt-style critical geographic distance: negative boundary passed

`benchmarks/keitt_critical_distance_boundary.py` compares EOG's one-dimensional geographic relaxation family with the critical patch-distance logic of Keitt, Urban & Milne (1997).

Known truth uses A=0, B=4, C=10:

- direct A-C distance = 10;
- A-B = 4 and B-C = 6;
- the patch graph first connects A to C at threshold 6 via stepping stone B;
- EOG `first_possible_level` and `first_robust_level` are also 6.

Therefore EOG must **not** claim novelty for varying a geographic connection threshold, detecting the first threshold where components merge, or a stepping-stone-mediated one-dimensional critical dispersal distance.

The remaining candidate distinction is narrower: **multi-axis occurrence-conditioned relaxation sets, explicit ecological + analytical world universes, underidentification, and finite-universe certificate/monotonicity rules.**

## Repository cleanup state

- [x] root `eog` and `eog.v2` compatibility roots are lazy;
- [x] `eog.v2.reachability`, `traversability` and `validation` are lazy scientific facades;
- [x] new prospective names remain on explicit owning facades rather than widening `eog.v2` root;
- [x] package/facade refactors no longer rerun unrelated frozen scientific confirmations;
- [x] package-wide regression remains in Package checks;
- [x] historical structural manuscript assets are explicitly labelled as a frozen publication/evidence line in `manuscript/README.md`;
- [x] `README.md`, `development_mainline.md`, `eog_v2_progress.md`, and `eog_v2_package_layout.md` have distinct roles rather than duplicating stale “next gate” narratives;
- [x] stale diverged cleanup work is not merged wholesale across later scientific changes; only still-valid changes are ported to current mainline work.

The repository still contains many historical branches. The available connector does not expose safe branch deletion, so branch refs are not force-reset merely to reduce their count.

## Next external boundary

Do **not** add another EOG operator. The next comparator should target the other well-established part of the intuition: environmental/path exposure or resistance, not generic reachability.

Priority candidates:

- environmental barrier / minimum cumulative exposure path summaries;
- circuit/resistance or functional-habitat accessibility;
- published dynamic-connectivity formulations where forward reachability equivalence is expected;
- dynamic occupancy/mechanistic range models only when repeated observations and detection data make their process estimands identifiable.

The external benchmark should report where estimands coincide and which additional EOG claim remains after the negative boundaries above. EOG does not need to win every predictive metric.

## Deferred until a concrete validation need exists

- surveyed absences / non-detection evidence — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration becomes a scientific estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous or enormous world spaces — requires explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological forecast question is frozen;
- new empirical promotion claims — only after comparator, endpoint and validation design are predeclared.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by the explicit coverage certificate.
