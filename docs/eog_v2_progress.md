# EOG v2 prospective progress ledger

## Current status

The active EOG prospective line is no longer a sequence of separate island/genetic promotion experiments. Existing v2 work is retained as operators inside the integrated direction in [`development_mainline.md`](development_mainline.md):

> **observed occurrences constrain a set of distribution-forming worlds; EOG keeps that set explicit, propagates world-indexed reachability, and makes strong exclusions only over a declared/certified universe.**

This ledger preserves historical outcomes but makes the current implementation boundary explicit.

## Integrated finite loop — implemented

Behind `eog.v2.reachability`, the finite known-truth core now supports:

- [x] directed sub-stochastic transition operators and finite-horizon first passage;
- [x] exact finite `world -> reachability envelope` forward evaluation;
- [x] positive-occurrence `O -> W(O)` inverse reconstruction;
- [x] world-indexed flow sets rather than one averaged support surface;
- [x] finite-universe `reachable_in_all`, `contingent`, and `robustly_unreachable` classes;
- [x] geographic/IBD, environmental/IBE and barrier relaxation kept as separate axes;
- [x] non-dominated minimum-relaxation frontier;
- [x] compatible-world contraction after additional positive evidence;
- [x] positive static survey discrimination among compatible worlds;
- [x] predeclared monotone one-dimensional relaxation families;
- [x] first-possible versus first-robust basin merge across declared analytical variants;
- [x] finite temporal worlds as ordered sequences of existing transition operators;
- [x] exact-time temporal support plus cumulative `reached by time` structure;
- [x] time-stamped positive observations constraining temporal worlds;
- [x] positive `(node,time)` survey discrimination among still-compatible temporal worlds;
- [x] all new prospective names kept on the explicit owning facade rather than widening `eog.v2` root.

The positive-only finite temporal loop is therefore closed:

```text
declared temporal worlds
        -> world-indexed temporal flow
        -> time-stamped positive observations
        -> compatible temporal worlds
        -> next positive (node,time) discriminator
        -> added positive evidence
        -> contracted world set
```

This is a structural inference loop, not an occupancy/detection model.

## Known-truth falsification — passed

### Static finite archetype matrix

`benchmarks/finite_world_archetype_matrix.py` and its tests verify one common core across:

- geographic/IBD-dominated rescue;
- environmental/IBE-dominated rescue;
- barrier-dominated rescue;
- niche-desert tradeoff with both environmental-crossing and geographic-jump explanations retained;
- stepping-stone versus direct-route underidentification;
- world-set contraction after a discriminating positive occurrence;
- rare long-distance jump retained as possible at very low support;
- branching and reconvergence;
- analytical-representation-dependent versus robust basin merge;
- robust exclusion surviving explicit finite-universe expansion.

### Temporal known truths

The temporal layer additionally verifies:

- identical edge sets can differ under different temporal order;
- a bridge must open in the required order to transmit support downstream;
- source mass is injected once and not silently re-injected;
- exact-time mass is distinct from cumulative `reached by time`;
- robust reachability can hold across worlds with different support magnitude;
- hard temporal barriers remain excluded across the declared temporal universe;
- an earlier time-stamped positive observation can eliminate a world that reaches the same endpoint later;
- unobserved reachable nodes are not treated as absences;
- a candidate positive `(node,time)` observation can discriminate early versus late compatible worlds;
- a candidate unsupported by every remaining world is identified as a challenge to the declared universe, not ranked as ordinary discrimination.

## Important development failures retained as diagnostics

The finite/temporal work intentionally records failures instead of hiding them:

- a benchmark output initially returned `numpy.bool_` rather than Python `bool`; the benchmark boundary was normalized without changing scientific logic;
- an early temporal known-truth fixture attempted to represent “waiting” with an empty transition interval, which correctly destroyed source mass under the no-reinjection contract. The fixture was replaced by a genuinely longer route rather than modifying the production operator to recover the expected answer;
- a test collection failure from an unclosed tuple was fixed as syntax only.

These were diagnostic/test-definition failures, not reasons to retune frozen biological outcomes.

## Frozen historical evidence — preserved, not active promotion tasks

Earlier empirical/synthetic v0.1/v2 outcomes remain evidence boundaries. In particular:

- fixed-source synthetic reachability showed added information only in known-truth cases containing bottleneck magnitude or directionality unavailable to simpler references;
- source-expansion leakage/negative boundaries remain frozen;
- symmetric pairwise FST did not automatically recover directional migration information;
- Ryukyu, Zhoushan, Thalassia and SW Finland adverse/indeterminate/non-promoting results remain unchanged;
- A-Islands/Tanzania structural empirical results remain publication evidence, not proof that the newer world-reconstruction framework is empirically superior.

The earlier fixed-source occurrence confirmation keeps its recorded contract fingerprint:

`1b2c5e550019c1e73e8f7199dfcc952dfeed3bbbbc3232d173e811fcd21438e6`

and artifact digest:

`sha256:f77d020cd2617d45894662bfc8f7fd88e522866832f4ae7dc6cd378d2d1479e7`.

Historical claim-specific gates may be resumed only if the integrated method genuinely requires them; they must not trigger another dataset search merely to obtain a favourable result.

## Scientific boundaries that remain active

- Transition/reachability values are **model support**, not calibrated colonisation, dispersal, migration or occupancy probabilities.
- Positive occurrence evidence provides necessary reachability constraints; non-detection is not absence.
- `reached by time` is not persistence or exact-time occupancy.
- Time labels are ordered states, not calibrated calendar time or generations.
- IBD/geographic, IBE/environmental and barrier relaxation remain separate unless a one-dimensional family is declared in advance.
- `robustly_unreachable` is always relative to the exhaustively declared finite universe/certificate.
- Multiple compatible worlds remain explicitly underidentified rather than being replaced by one best history.

## Deferred work

Do **not** open these automatically just because the finite positive-only loop is complete:

- surveyed absence / imperfect-detection inference;
- calibrated calendar time and transition duration models;
- hypothetical/unobserved historical source states;
- continuous or enormous world spaces requiring optimization, sampling or formal enclosure;
- large-raster forecasting;
- another empirical promotion dataset;
- another top-level namespace, CLI family or confirmation workflow.

## Current development gate

Feature growth is paused after the positive-only finite loop. The next work should be **consolidation and end-to-end falsification**, not another process assumption.

Before opening detection models or large-raster forecasting:

1. keep README, package-layout and manuscript provenance consistent with the current architecture;
2. ensure no new prospective names leak onto compatibility roots;
3. preserve frozen empirical/manuscript assets as historical evidence rather than active API drivers;
4. build one compact end-to-end temporal feedback benchmark showing that a ranked positive `(node,time)` observation, when applied, produces exactly the predicted compatible-world contraction;
5. only then decide whether the next scientific need is detection/absence evidence, calibrated time, or continuous-world certification.

## Stop rule

Do not run another occurrence or genetic dataset merely to obtain a favourable result. Do not retune frozen adverse/null/indeterminate outcomes. If several worlds remain compatible, EOG must keep them as a set.
