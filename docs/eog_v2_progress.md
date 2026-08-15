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
- finite archetype falsification across IBD, IBE, barriers, stepping stones, rare jumps, branching/reconvergence, analytical ambiguity, and universe expansion.

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

| Gate | Comparator / prior art | Result for EOG claim boundary |
|---|---|---|
| 1 | endpoint-only, final-horizon, scalar relaxation | timing and axis identity can be lost; set-valued inverse frontier retains them |
| 2 | existing static cumulative/minimax bridge | static connectivity and time-constrained realizability are different estimands |
| 3 | independent Boolean dynamic connectivity | exact structural match; **dynamic reachability / time-respecting path existence are not EOG novelty** |
| 4 | consensus frequency | 99/100 support can remain contingent; high agreement and universal finite-world invariance differ |
| 5 | Keitt-style critical patch distance | exact 1D geographic threshold match; **water-level threshold / first merge / stepping-stone critical distance are prior art** |
| 6 | Dobrowski/Parks minimum cumulative exposure | exact low-exposure-path match; **path exposure / least-exposure route / bottleneck are prior art** |
| 7 | circuit theory | multiple pathways and route redundancy are prior art; unioning mutually exclusive worlds can manufacture simultaneous redundancy |
| 8 | Van Moorter functional habitat | suitable + accessible and E/G/T-space integration are prior art; averaging alternative analytical worlds can manufacture a state occurring in no declared world |
| 9 | history matching / NROY | exact finite special-case match; **generic model-world filtering, compatible/NROY sets, and sequential set contraction are prior art** |
| 10 | Masten/Poirier falsification frontier | exact finite Pareto-frontier match; **minimum-assumption relaxation / Pareto-minimal rescue / falsification-frontier mathematics are prior art** |

Benchmark implementations are under `benchmarks/` with matching tests under `tests/`. Detailed known-truth values belong there rather than being duplicated here.

## Gate 10 — falsification-frontier result

`benchmarks/falsification_frontier_boundary.py` uses a falsified baseline `(0,0,0)` plus compatible geographic-only, environmental-only, barrier-only, mixed, and all-axis rescue worlds.

An independent componentwise Pareto calculation and EOG `minimum_relaxation_frontier` return exactly the same four non-dominated relaxation vectors. The `(1,1,1)` all-axis rescue is dominated and removed by both.

This is only a discrete deterministic special case, not the linear-IV identification theory in Masten & Poirier. It is sufficient to establish that the **generic mathematics of minimum relaxation and a Pareto/falsification frontier is not an EOG invention**.

## What remains after the negative boundaries

The candidate EOG contribution is now a domain framework/composition claim, not a claim of new general graph or inverse-problem mathematics:

> **An auditable biogeographic framework that turns observed occurrence configurations into explicit geographic/environmental/barrier/temporal reachability constraints, carries both ecological and analyst-choice alternatives as declared worlds, preserves underidentified alternatives rather than averaging them away, and reports only structural conclusions justified by the declared coverage/certificate.**

Potential scientific value must therefore come from **how these established ideas are combined for biogeographic questions and whether that combination yields useful ecological information**, not from renaming any constituent algorithm.

EOG does **not** claim novelty for, by themselves:

- suitable versus reachable;
- graphs, stepping stones, bridge/bottleneck paths;
- dynamic/time-respecting reachability;
- critical connection thresholds;
- least-cost or minimum environmental exposure;
- multiple pathways / route redundancy;
- functional habitat or suitability + accessibility integration;
- consensus ensembles;
- generic history-matching elimination / NROY sets;
- generic minimum-relaxation, Pareto-frontier, or falsification-frontier mathematics.

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

## Next decision — stop algorithm expansion, freeze ecological validation

The prior-art audit has now removed most claims of generic methodological novelty. Do **not** add another EOG operator merely to chase a smaller novelty niche.

Next work should freeze one ecological validation question where the combined framework might be useful, for example:

- an island system where equally suitable endpoints differ in which ecological versus analytical worlds can connect them;
- a case where mutually exclusive raster/resistance assumptions produce different connectivity structures and averaging would hide that distinction;
- a time-stamped colonisation/recolonisation record where observations rule out some world families and shift the minimum required ecological relaxation;
- a survey design case where a positive observation would discriminate among still-compatible biogeographic worlds.

Before touching a new dataset, predeclare:

1. the ecological question;
2. the world universe and which dimensions are **natural** versus **analyst-choice** uncertainty;
3. the established comparator matching each estimand;
4. the held-out or independent validation endpoint;
5. the result that would count as **no added value** for EOG.

If no real ecological case benefits from retaining the world set / constraint frontier beyond established methods, the integrated EOG line should stop rather than add complexity.

## Deferred until a concrete validation need exists

- surveyed absence / non-detection inference — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration is itself an estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous/enormous world spaces — require explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological question and comparator are frozen.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by explicit coverage/certificate strength.
