# Environmental Occupancy Geometry (EOG)

EOG is an auditable ecological framework for asking a broader question than local suitability alone:

> **Given an observed distribution, what declared distribution-forming worlds are compatible with it, what constraints must be relaxed to realize it, and which reachability claims survive disagreement among plausible worlds?**

The repository contains a frozen v0.1 evidence line plus a prospective finite-world / temporal reconstruction line. The active method is **not** another parallel EOG variant: existing geometry, topology, bridge, reachability and validation components are treated as operators inside one distributional-realizability / world-reconstruction framework.

- Scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- Current implementation/validation status: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- Package boundary: [`docs/eog_v2_package_layout.md`](docs/eog_v2_package_layout.md)
- Frozen claims/evidence: [`docs/evidence_ledger.md`](docs/evidence_ledger.md), [`docs/claim_matrix.md`](docs/claim_matrix.md)

## Scientific center

EOG keeps four statements separate:

1. **local possibility** — a state is environmentally or otherwise locally supported;
2. **reachability** — a declared transition process can reach that state;
3. **distributional realizability** — an observed configuration is compatible with a declared world;
4. **historical truth** — what actually happened in nature.

Observed occurrences constrain admissible distribution-forming processes. They do **not** identify one true route, colonisation sequence, ancestry or movement rate.

The prospective inverse object is

```text
W(O) = { declared worlds compatible with observations O }
```

and the world-indexed flow object is

```text
K_t = { p_t^(w) : w in W(O) }.
```

World identity is retained rather than averaged away by default.

## Distributional-watershed interpretation

The watershed language has explicit structural meanings:

- occurrence = realized anchor;
- basin = reachable set under declared constraints;
- channel / tributary = supported transition sequence or edge family;
- confluence = route reconvergence;
- bottleneck = critical transition/state;
- divide = disconnected reachability boundary;
- water level `lambda` = only a **predeclared one-dimensional monotone relaxation coordinate**;
- basin merge = first declared relaxation level that jointly realizes previously separated occurrence groups.

Geographic/IBD, environmental/IBE and barrier relaxation remain separate axes unless a genuinely one-dimensional family was specified before seeing the result.

A minimum-relaxation or basin-merge result is a **necessary-condition diagnostic**, not evidence that the corresponding historical event actually occurred.

## Robust, contingent and excluded structure

For an explicitly declared finite world universe, EOG distinguishes:

- supported/reachable in every world;
- contingent on world or analytical representation;
- unsupported/unreachable in every enumerated world.

`robust` always means robust under the **declared certified universe**, not universally true in nature.

World-universe expansion is monotone in claim strength:

- robust claims may stay the same or weaken;
- possible claims may stay the same or expand;
- all-world exclusion may stay the same or shrink.

High consensus is not the same estimand as universal robustness. A 99/100-world agreement may be useful consensus while remaining contingent if the 100th admissible world disagrees.

## Implemented architecture

### Stable root `eog`

The v0.1 compatibility surface retains:

- environmental-state geometry and shared-reference comparison;
- support topology;
- bridge / bottleneck inference;
- survey/hypothesis-discrimination utilities.

These paths remain available for frozen reproduction and earlier empirical work.

### Prospective `eog.v2`

`eog.v2` is a thin compatibility namespace. New scientific work stays behind three explicit lazy facades:

- `eog.v2.reachability` — static/temporal transition flow, compatible-world reconstruction, world-indexed support sets, relaxation/frontier diagnostics, basin merge, positive survey discrimination and temporal transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental/barrier and pathwise transition constraints;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation.

New prospective APIs stay off the `eog.v2` package root unless release compatibility requires them.

## Finite known-truth status

The finite architecture already covers:

- exact static and temporal compatible-world reconstruction;
- world-indexed flow/support sets;
- robust / contingent / finite-universe excluded node and edge structure;
- separate IBD/IBE/barrier minimum-relaxation frontiers;
- first-possible versus first-robust basin merge;
- positive occurrence and positive `(node,time)` discrimination;
- temporal corridor opening/closure;
- exact nested-world-universe monotonicity;
- temporal minimum-relaxation frontiers;
- archetype falsification for IBD, IBE, hard barriers, niche deserts, stepping stones, rare low-support jumps, branching/reconvergence and analytical ambiguity.

These are **known-truth capabilities, not empirical superiority claims**.

## Current phase: comparator / validation

Feature growth is paused by default. Current work asks which parts of the EOG architecture are genuinely additional inferential objects rather than renamed connectivity machinery.

Completed comparator boundaries include:

- **endpoint/final-horizon/scalar summaries** — lose timing or axis identity that the inverse Pareto world set retains;
- **existing static bridge inference** — correctly describes the time-aggregated A-B-C path but cannot encode the ordering constraint that determines whether `C@t2` is realizable;
- **time-respecting Boolean dynamic connectivity** — reproduces EOG structural reached-by-time states and positive temporal world filtering, so forward dynamic reachability itself is explicitly **not** an EOG novelty claim.

Current comparator work tests:

- **consensus frequency versus universal finite-world certificate** — high agreement (for example 99/100 worlds) is kept distinct from invariance across every declared world.

External least-cost, circuit, functional-habitat, dynamic-connectivity, occupancy or mechanistic-range comparisons should be opened only for a frozen matching estimand. EOG does not need to win every predictive metric.

## Frozen evidence is preserved

Cleanup does not erase adverse, null, failed or indeterminate results. Earlier A-Islands, Tanzania, Finland, genetic/reference and synthetic validation lines remain evidence boundaries with their contracts, fingerprints and artifacts intact.

The `manuscript/` directory is explicitly an earlier structural-reachability publication/evidence line, not the active package architecture. See [`manuscript/README.md`](manuscript/README.md).

## Repository rules

- Preserve evidence before removing implementation.
- Reuse an existing operator/facade before creating a module family.
- Keep benchmark/comparator work in `benchmarks/` and `tests/` unless it exposes a genuinely reusable estimand.
- Keep presentation/system-specific code out of eager scientific imports.
- Keep frozen claim-specific workflows reproducible but narrowly dependency-scoped.
- Do not treat low positive support as impossibility.
- Do not infer absence from non-detection without an explicit detection model.
- Do not return one history when observations leave several worlds compatible.
- Claim strength must not exceed coverage/certificate strength.

## Installation

```bash
python -m pip install .
```

For CHELSA/raster benchmark work:

```bash
python -m pip install ".[raster]"
```

## Scientific boundary

EOG does not currently justify calling uncalibrated reachability support an occupancy probability, colonisation probability, dispersal probability, migration rate, demographic connectivity or ancestry estimate.

The strongest active claim is narrower:

> **Observed distributions can constrain a set of admissible distribution-forming worlds and the minimum assumptions required to realize them, while preserving alternative explanations and explicitly limiting robust claims to the declared certified universe.**

## Provenance

The original environmental-state implementation was extracted from ACSP. Support-topology work incorporated defensible frozen-field, occurrence-anchor, component, recovery and audit ideas previously developed in ODSP while avoiding duplicate path implementations. Later structural, empirical and prospective validation lines remain reproducible through their frozen contracts and evidence ledgers.

## License

MIT.
