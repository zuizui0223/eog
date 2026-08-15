# EOG v2 prospective progress ledger

## Status after the 2026-08 cleanup

This ledger tracks only the **active integrated method line**. Frozen positive, adverse, null, failed and indeterminate results remain preserved in their dedicated evidence ledgers, contracts, fingerprints and benchmark artifacts; they are not retuned or rewritten here.

Active scientific direction: [`development_mainline.md`](development_mainline.md).

## Finite inverse/reachability architecture — implemented

The explicit `eog.v2.reachability` facade now contains the finite known-truth core needed for the distributional-watershed / world-reconstruction program:

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
- [x] exact nested temporal-world-universe monotonicity: adding admissible worlds may weaken robust/exclusion claims but cannot strengthen them;
- [x] axis-preserving temporal minimum-relaxation frontier: earlier occurrence timing can eliminate a zero-relaxation slow world and require geographic-, environmental-, or barrier-specific rescue explanations without scalarizing them.

All of these are finite known-truth capabilities. `robust` means robust over the explicitly declared and exhaustively enumerated universe, not universal ecological certainty.

## Inverse-estimand separation gate — passed

`benchmarks/inverse_estimand_comparator.py` now tests the prerequisite claim that the integrated EOG output is a distinct inferential object rather than another connectivity score.

One frozen temporal world universe is summarized four ways:

1. **endpoint-only identity** — discarding time makes `C@t2` and `C@t3` identical;
2. **final-horizon compatibility** — looking only at C by `t3` retains slow and fast explanations together;
3. **scalar relaxation** — summing geographic + environmental + barrier relaxation gives the same minimum score to three ecologically distinct rescue explanations;
4. **EOG inverse** — `C@t2` eliminates the slow zero-relaxation world, removes an all-axis dominated explanation, and retains the geographic-only, environmental-only and barrier-only rescues as a Pareto set.

Known-truth Package checks pass across Python 3.10–3.12, wheel build and the frozen topology regression gate.

This benchmark is **estimand separation, not external-method superiority**. It does not claim to reproduce or beat dynamic occupancy, mechanistic SDMs, least-cost, circuit theory, functional habitat or other full competitor methods.

## Repository cleanup state

- [x] root `eog` and `eog.v2` compatibility roots are lazy;
- [x] `eog.v2.reachability`, `traversability` and `validation` are lazy scientific facades;
- [x] new prospective names remain on explicit owning facades rather than widening `eog.v2` root;
- [x] package/facade refactors no longer rerun unrelated frozen scientific confirmations;
- [x] package-wide regression remains in Package checks;
- [x] historical structural manuscript assets are explicitly labelled as a frozen publication/evidence line in `manuscript/README.md`, not as the active method architecture;
- [x] the stale `cleanup/post-temporal-mainline` branch is not merged wholesale because it diverged before later temporal and facade work; its still-valid manuscript-boundary cleanup has been ported onto current mainline work.

## Current phase — comparator / validation design

**Do not add another operator by default.** The finite architecture is already broad enough to express compatible-world reconstruction, set-valued flows, robust/contingent/excluded structure, basin merge, temporal corridor changes, positive observation discrimination, universe monotonicity and minimum-required relaxation.

The next task is to predeclare a comparator/validation design for the distinctive claim:

> **Observed occurrences constrain a set of distribution-forming worlds and the minimum geographic/environmental/barrier assumptions required to realize them; EOG preserves alternative explanations and underidentification instead of forcing one scalar score or one historical route.**

External comparator work should therefore test this inverse estimand directly rather than ask whether EOG merely predicts occurrence better.

Priority comparator families to implement or interface only when the exact estimand is frozen:

- endpoint/local-support or distance-to-source baselines;
- least-cost / bottleneck / circuit-style connectivity summaries;
- functional-habitat / accessible-habitat representations;
- dynamic occupancy or mechanistic range models when repeated temporal data make their process estimands identifiable;
- single-model or ensemble consensus approaches that collapse analyst-choice uncertainty.

The first external benchmark should report **where the estimands coincide and where they do not**. EOG does not need to win every predictive metric.

## Deferred until a concrete validation need exists

- surveyed absences / non-detection evidence — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration becomes a scientific estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous or enormous world spaces — requires explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological forecast question is frozen;
- new empirical promotion claims — only after comparator, endpoint and validation design are predeclared.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by the explicit coverage certificate.
