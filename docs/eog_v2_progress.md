# EOG v2 prospective progress ledger

## Status

This ledger tracks only the **active integrated method line**. Frozen positive, adverse, null, failed and indeterminate results remain preserved in their dedicated evidence ledgers, contracts, fingerprints and benchmark artifacts; they are not retuned or rewritten here.

- Scientific mainline: [`development_mainline.md`](development_mainline.md)
- API/facade ownership: [`eog_v2_package_layout.md`](eog_v2_package_layout.md)
- Frozen claims/evidence: [`evidence_ledger.md`](evidence_ledger.md), [`claim_matrix.md`](claim_matrix.md)

## Implemented finite architecture

### Static worlds

- exact forward reachability envelopes;
- inverse compatible-world reconstruction from positive occurrences;
- world-indexed support/flow sets and lower/upper envelopes;
- `reachable_in_all`, `contingent`, and finite-universe `robustly_unreachable` classes;
- separate geographic/IBD, environmental/IBE, and barrier relaxation axes;
- non-dominated minimum-relaxation frontier;
- declared one-dimensional monotone relaxation families only when scientifically predeclared;
- first-possible versus first-robust basin merge across analytical variants;
- positive-occurrence discrimination among underidentified worlds;
- finite archetype falsification covering IBD, IBE, hard barriers, niche deserts, stepping stones, rare low-support jumps, branching/reconvergence, analytical ambiguity, and universe expansion.

### Temporal worlds

- ordered `TemporalWorld` transition sequences with source mass injected only at the initial state;
- exact-time support and cumulative reached-by-time kept distinct;
- world-indexed temporal support envelopes and finite reachability classes;
- positive time-stamped occurrence reconstruction;
- preservation of multiple compatible temporal histories;
- positive `(node, time)` survey discrimination without treating non-detection as absence;
- robust / contingent / inactive directed transition edges by interval;
- possible and robust corridor opening/closure summaries;
- exact nested temporal-world-universe monotonicity;
- axis-preserving temporal minimum-relaxation frontier.

These are finite known-truth capabilities, **not empirical superiority claims**. `Robust` means robust over the explicitly declared and exhaustively enumerated universe, not universal ecological certainty.

## Comparator / prior-art boundaries

The comparator program intentionally tries to remove overbroad novelty claims before new empirical work.

| Gate | Comparator / prior art | Result for EOG claim boundary |
|---|---|---|
| 1 | endpoint-only, final-horizon, scalar relaxation | timing and axis identity can be lost; set-valued inverse frontier retains them |
| 2 | existing static cumulative/minimax bridge | static connectivity and time-constrained realizability are different estimands |
| 3 | independent Boolean dynamic connectivity | exact structural match; **dynamic reachability / time-respecting path existence are not EOG novelty** |
| 4 | consensus frequency | 99/100 support can remain contingent; high agreement and universal finite-world invariance differ |
| 5 | Keitt-style critical patch distance | exact 1D geographic threshold match; **water-level threshold / first merge / stepping-stone critical distance are prior art** |
| 6 | Dobrowski/Parks minimum cumulative exposure | exact low-exposure-path match; **path environmental exposure / least-exposure route / bottleneck are prior art** |
| 7 | circuit theory | multiple pathways and route redundancy are prior art; unioning mutually exclusive worlds can manufacture simultaneous redundancy |
| 8 | Van Moorter functional habitat | suitable + accessible and E/G/T-space integration are prior art; averaging alternative analytical worlds can manufacture a state occurring in no declared world |
| 9 | history matching / NROY | exact finite special-case match; **generic model-world filtering, compatible/NROY sets, and sequential set contraction are prior art** |

Benchmark implementations are under `benchmarks/` with matching tests under `tests/`. Detailed known-truth values belong there rather than being duplicated in this ledger.

## Gate 9 — history matching result

`benchmarks/history_matching_nroy_boundary.py` uses three deterministic finite worlds:

- `world_B`: A -> B -> C;
- `world_D`: A -> D -> C;
- `world_fail`: A -> B only.

Independent finite history matching and EOG reconstruction agree exactly:

- observations `A,C` retain `world_B, world_D` and rule out `world_fail`;
- adding B (`A,B,C`) contracts the retained set to `world_B`;
- both eliminate `world_D` between waves with contraction fraction 0.5.

This is only the deterministic finite special case. Full history matching also addresses emulation, observation uncertainty, model discrepancy, implausibility measures, and large/continuous parameter spaces.

## What remains after the negative boundaries

The candidate EOG contribution is now deliberately narrow and ecological rather than a claim of new graph mathematics:

> **Occurrence-conditioned biogeographic constraint inference over an explicitly declared ecological + analytical world universe, with mutually alternative worlds kept separate, geographic/environmental/barrier rescue requirements retained as a non-dominated set, underidentification reported explicitly, and structural claims limited by finite-universe coverage/certification rules.**

EOG therefore does **not** claim novelty for any of the following by themselves:

- suitable versus reachable;
- graphs, stepping stones, bridge/bottleneck paths;
- dynamic/time-respecting reachability;
- critical connection thresholds;
- least-cost or minimum environmental exposure;
- multiple pathways / route redundancy;
- functional habitat or suitability + accessibility integration;
- consensus ensembles;
- generic history-matching elimination of worlds inconsistent with observations.

## Repository cleanup state

- root `eog` and `eog.v2` compatibility roots are lazy;
- `eog.v2.reachability`, `traversability`, and `validation` are explicit lazy scientific facades;
- new prospective names remain on owning facades rather than widening the package root;
- package/facade refactors no longer rerun unrelated frozen scientific confirmations;
- package-wide regression remains in Package checks;
- `manuscript/` is explicitly a frozen earlier structural publication/evidence line, not the active architecture;
- `README.md`, `development_mainline.md`, this progress ledger, and `eog_v2_package_layout.md` have distinct roles;
- stale diverged cleanup work is not merged wholesale across later scientific changes;
- historical branch refs remain because the available connector does not expose safe branch deletion; they are not force-reset simply to reduce branch count.

## Next decision

**Do not add another EOG operator by default.**

Before any empirical promotion, the remaining claim should be audited against the closest generic inferential precedents:

1. **partial identification / identified sets** — does “retain all compatible worlds and report underidentification” add anything mathematically new?
2. **falsification frontier / minimal relaxation / robust optimization** — are multi-axis rescue and Pareto-minimal relaxations generic prior art, leaving only the ecological world construction and interpretation as EOG-specific?
3. **model/analysis multiverse uncertainty** — is explicit analyst-choice world uncertainty already formalized in ways that subsume the proposed analytical-world layer?

If those boundaries also match, EOG should be positioned as a **biogeographic application/framework that composes established inferential ideas around occurrence-conditioned reachability constraints**, not as a new general mathematical algorithm.

Only after this boundary is honest should one freeze a real ecological validation case and ask whether the framework adds useful ecological information.

## Deferred until a concrete validation need exists

- surveyed absence / non-detection inference — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration is itself an estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous/enormous world spaces — require explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological question and comparator are frozen;
- new empirical promotion claims — only after endpoint, comparator, and validation contracts are predeclared.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by explicit coverage/certificate strength.
