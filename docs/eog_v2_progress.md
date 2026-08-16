# EOG v2 prospective progress ledger

## Status

This ledger tracks only the **active integrated method line**. Frozen positive, adverse, null, failed and indeterminate results remain in their dedicated evidence ledgers, contracts, fingerprints and benchmark artifacts; they are not retuned here.

- scientific mainline: [`development_mainline.md`](development_mainline.md)
- API/facade ownership: [`eog_v2_package_layout.md`](eog_v2_package_layout.md)
- frozen claims/evidence: [`evidence_ledger.md`](evidence_ledger.md), [`claim_matrix.md`](claim_matrix.md)

**Current phase: ecological validation. Synthetic operator growth is stopped by default.**

## Implemented finite architecture

### Static worlds

Implemented and covered by known-truth tests:

- exact forward reachability envelopes;
- inverse compatible-world reconstruction from positive occurrences;
- world-indexed support/flow sets;
- finite-universe `reachable_in_all`, `contingent`, and `robustly_unreachable` classes;
- separate geographic/IBD, environmental/IBE and barrier relaxation axes;
- non-dominated minimum-relaxation frontier;
- declared one-dimensional monotone relaxation families only when scientifically predeclared;
- first-possible versus first-robust basin merge;
- positive-occurrence discrimination among underidentified worlds;
- archetype falsification across IBD, IBE, barriers, stepping stones, rare jumps, branching/reconvergence, analytical ambiguity and universe expansion.

### Temporal worlds

Implemented and covered by known-truth tests:

- ordered `TemporalWorld` transition sequences;
- exact-time support and cumulative reached-by-time kept distinct;
- world-indexed temporal support envelopes and finite reachability classes;
- positive time-stamped occurrence reconstruction;
- preservation of multiple compatible temporal histories;
- positive `(node,time)` survey discrimination without treating non-detection as absence;
- robust / contingent / inactive directed transition edges by interval;
- possible and robust corridor opening/closure summaries;
- exact nested temporal-world-universe monotonicity;
- axis-preserving temporal minimum-relaxation frontier.

These are finite known-truth capabilities, **not empirical superiority claims**. `Robust` means robust over the explicitly declared and exhaustively enumerated universe, not universal ecological certainty.

## Prior-art / negative-boundary gates

| Gate | Comparator / prior art | EOG claim boundary |
|---|---|---|
| 1 | endpoint-only, final-horizon, scalar relaxation | timing and axis identity can be lost; set-valued outputs can retain them |
| 2 | existing static cumulative/minimax bridge | static connectivity and time-constrained realizability are different estimands |
| 3 | independent Boolean dynamic connectivity | exact structural match; dynamic reachability / time-respecting path existence are **not** EOG novelty |
| 4 | consensus frequency | high agreement and universal finite-world invariance are different summaries |
| 5 | Keitt-style critical patch distance | exact 1D geographic threshold match; first merge / stepping-stone critical distance are prior art |
| 6 | Dobrowski/Parks minimum cumulative exposure | exact least-exposure-path match; path exposure and environmental bottlenecks are prior art |
| 7 | circuit theory | multiple pathways / redundancy are prior art; unioning mutually exclusive worlds can manufacture a structure occurring in no declared world |
| 8 | Van Moorter functional habitat | suitable + accessible and E/G/T-space integration are prior art; explicit alternative-world identity remains a separate question |
| 9 | history matching / NROY | exact finite special-case match; generic world filtering and compatible/NROY sets are prior art |
| 10 | Masten/Poirier falsification frontier | exact finite Pareto-frontier match; generic minimum relaxation / rescue frontier mathematics are prior art |

Detailed known-truth values belong in `benchmarks/` and matching `tests/`, not in this ledger.

## Remaining contribution hypothesis

After the negative boundaries, EOG is no longer positioned as a new general graph or inverse-problem algorithm.

The remaining candidate contribution is:

> **An auditable biogeographic framework that converts observed occurrence configurations into explicit geographic/environmental/barrier/temporal constraints, carries ecological and analyst-choice alternatives as declared worlds, preserves underidentified alternatives rather than averaging them away, and limits structural claims to the declared coverage/certificate.**

Potential scientific value must now come from **empirical usefulness of this composition**, not from renaming constituent algorithms.

## Exploratory development adapter — PR #181

PR #181 adds a response-free A-Islands adapter that exposes the frozen 12 reachability scenarios as explicit analyst-choice worlds rather than only their average `connected_frequency`.

The adapter:

- reuses the frozen A-Islands cohort/fold/climate/scenario contracts;
- uses outer-training occurrences as anchors;
- treats held-out islands as unlabeled candidate states;
- retains supporting and unsupported scenario IDs;
- reports robust / contingent / excluded-under-declared-scenarios classes;
- keeps geography-only and environmentally constrained scenario families separately inspectable;
- does not use held-out incidence, AUC, concordance or fitted pointwise support as an outcome.

This is **exploratory development evidence only**. A-Islands has already been viewed and cannot become a new confirmatory result for the integrated EOG line.

The immediate exploratory question is therefore narrow:

> **Does preserving scenario/world identity reveal non-trivial structure that is erased by the aggregate connected-frequency summary?**

If not, stop this direction. If yes, freeze an independent confirmation system before any promotion claim.

## Repository cleanup state

Completed:

- root `eog` and `eog.v2` compatibility roots are lazy;
- `eog.v2.reachability`, `traversability`, and `validation` are explicit lazy scientific facades;
- new prospective names remain on owning facades rather than widening the package root;
- package/facade refactors no longer rerun unrelated frozen scientific confirmations;
- package-wide regression remains in Package checks;
- `manuscript/` is explicitly a frozen earlier structural publication/evidence line;
- README, mainline, progress ledger and package-layout docs now have distinct roles;
- stale diverged cleanup work is not merged wholesale across later scientific changes.

Still intentionally conservative:

- historical implementation modules remain where frozen reproduction may import them directly;
- physical code deletion requires a repository-reference audit first;
- historical remote branch refs may remain because the available connector does not expose safe branch deletion; their existence does not make them active development.

## Next mainline decision — validate or stop

Do **not** add another EOG operator merely to chase a smaller novelty niche.

The next confirmatory work, if the exploratory world-set representation is informative, must freeze before outcomes are touched:

1. ecological question;
2. world universe with **natural** versus **analyst-choice** uncertainty separated;
3. strongest established comparator matching each estimand;
4. held-out or independent validation endpoint;
5. explicit **no-added-value** result;
6. coverage/certificate status for robust claims.

Candidate confirmation designs include:

- an independent island system where alternative environmental/resistance representations imply mutually exclusive reachability structures;
- a time-stamped colonisation/recolonisation record that eliminates some declared worlds;
- independently surveyed intermediate sites that test a predeclared bridge/world distinction;
- independent genetic or movement evidence only where it tests a predeclared structural hypothesis rather than being used to tune the worlds.

If no real ecological case benefits from retaining world identity beyond established methods, the integrated EOG line should stop rather than add complexity.

## Side-line rule

Meaningful side lines may continue when they have a separate purpose and stop condition, for example frozen manuscript release/archive work, reproduction maintenance, or a pre-existing field validation once its original inputs are archived.

A side line is not a reason to create another EOG architecture, facade, operator family or favourable-data search.

## Deferred until a concrete validation need exists

- surveyed absence / non-detection inference — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration is itself an estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous/enormous world spaces — require explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific ecological question and comparator are frozen.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate evidence. Preserve genuinely different worlds as a set whenever observations do not identify one history, and keep claim strength bounded by explicit coverage/certificate strength.
