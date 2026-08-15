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

`benchmarks/bridge_vs_temporal_reconstruction.py` reuses the existing v0.1 cumulative/minimax/redundancy bridge implementation. Static connectivity and time-constrained realizability are confirmed as different estimands.

### Gate 3 — time-respecting Boolean dynamic connectivity: negative boundary passed

`benchmarks/dynamic_connectivity_negative_boundary.py` independently reproduces EOG cumulative reached-by-time structure and positive temporal compatible-world filtering at zero support tolerance.

Therefore EOG must **not** claim novelty for forward dynamic reachability, time-respecting path existence, or positive temporal filtering by themselves.

### Gate 4 — consensus frequency versus universal certificate: passed

`benchmarks/consensus_vs_universal_certificate.py` shows that a state reachable in 99/100 worlds can satisfy a 0.95 consensus rule while remaining `contingent` rather than robust after the one excluding world is admitted. A state unreachable in all worlds retains the finite-universe exclusion certificate.

Consensus and universal robustness are valid but different estimands.

### Gate 5 — Keitt-style critical geographic distance: negative boundary passed

`benchmarks/keitt_critical_distance_boundary.py` reproduces the critical patch-distance result in a one-dimensional geographic EOG family: A=0, B=4, C=10 connects at threshold 6 through stepping stone B, and EOG `first_possible_level = first_robust_level = 6`.

Therefore EOG must **not** claim novelty for geographic threshold sweeps, first component-merge distance, or one-dimensional stepping-stone critical dispersal distance.

### Gate 6 — Dobrowski/Parks minimum cumulative environmental exposure: negative boundary passed

`benchmarks/mce_environmental_exposure_boundary.py` shows equal-climate endpoints can have different intermediate exposure. The independent least-exposure baseline and the existing EOG pure-environmental bridge both select the longer low-exposure route and recover the same accumulated exposure.

Therefore EOG must **not** claim novelty for endpoint-similarity/path-feasibility mismatch, cumulative environmental exposure, least-exposure path selection, or environmental bottleneck by themselves.

### Gate 7 — circuit theory / multiple pathways: negative boundary plus world-aggregation distinction passed

`benchmarks/circuit_world_aggregation_boundary.py` uses two mutually alternative worlds, each with one A-C corridor and effective resistance 2. Unioning the two world graphs creates two simultaneous edge-disjoint paths and effective resistance 1 even though no declared world contains that union network.

Circuit theory is correct for the union graph when that union graph is the declared landscape. EOG therefore must **not** claim novelty for recognizing or integrating multiple dispersal pathways or route redundancy. The remaining question is whether mutually exclusive ecological/analytical world representations may be aggregated before connectivity inference.

### Gate 8 — Van Moorter functional habitat: negative boundary plus analytical-world distinction passed

`benchmarks/functional_habitat_world_boundary.py` implements the functional-habitat special case `m_st = q_s * q_t * k_st` for two equally admissible analytical connectivity representations.

All nodes have the same local habitat quality `q=1`. Candidate C has functional score 2 when connected to A and score 1 when isolated; functional habitat therefore correctly distinguishes suitable + accessible from suitable but isolated habitat.

Both analytical representations remain compatible with the common observed A-R relation. EOG keeps C `contingent` across the world set. Averaging the two functional-habitat outputs gives C=1.5, a value occurring in no declared world.

Therefore EOG must **not** claim novelty for combining habitat suitability with movement/accessibility, integrating E-space with G/T-space through a network, or down-ranking isolated high-quality habitat. The remaining question is how to retain alternative analytical worlds and their underidentification instead of collapsing them into one chosen or averaged landscape.

## What remains after the negative boundaries

The remaining candidate contribution is deliberately narrow:

> **Occurrence-conditioned inference over an explicitly declared ecological + analytical world universe, retaining mutually alternative world-indexed explanations and non-dominated geographic/environmental/barrier relaxations, with underidentification and finite-universe robustness/exclusion certificates made explicit.**

The individual ingredients of geographic thresholding, stepping stones, dynamic reachability, least-cost exposure, bottlenecks, multiple pathways, route redundancy, suitability/accessibility integration and consensus are not claimed as new.

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

## Next external boundary — history matching / NROY

Do **not** add another EOG operator. The next closest prior art is generic model-world elimination based on observations.

History matching rules out model parameter/world regions inconsistent with observations and uncertainty and retains a Not-Ruled-Out-Yet (NROY) set. The next negative-boundary benchmark should therefore test whether finite EOG compatible-world reconstruction and sequential world-set contraction are exact special cases of finite history matching when the simulator output is structural reachability.

Expected negative boundary if they agree:

- ruling out finite model worlds inconsistent with observations is not unique to EOG;
- retaining a compatible/NROY world set is not unique;
- sequential contraction after additional observations is not unique.

The remaining ecological contribution would then have to lie in the **biogeographic structure of the world universe and constraints**: occurrence-anchored reachability, explicit ecological versus analyst-choice alternatives, axis-preserving rescue/Pareto diagnostics, and finite-universe certificate/monotonicity rules.

## Deferred until a concrete validation need exists

- surveyed absences / non-detection evidence — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration becomes a scientific estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous or enormous world spaces — requires explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological forecast question is frozen;
- new empirical promotion claims — only after comparator, endpoint and validation design are predeclared.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by the explicit coverage certificate.
