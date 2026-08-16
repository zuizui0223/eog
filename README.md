# Environmental Occupancy Geometry (EOG)

EOG is an auditable ecological framework for asking a broader question than local suitability alone:

> **Given an observed distribution, which declared distribution-forming worlds remain compatible with it, what assumptions must be relaxed to realize it, and which structural conclusions survive disagreement among those worlds?**

## Status

There is now **one active EOG method line**. Feature growth is paused by default.

The repository contains:

- a frozen v0.1 evidence/compatibility line;
- reusable geometry, topology, bridge, reachability and validation operators;
- a prospective finite-world / temporal reconstruction framework;
- frozen earlier manuscript and empirical evidence lines.

These are not separate competing versions of EOG. The active phase is **ecological validation of the combined framework**, not another round of algorithm expansion.

Canonical project state:

- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- implementation / prior-art ledger: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- package boundary: [`docs/eog_v2_package_layout.md`](docs/eog_v2_package_layout.md)
- frozen evidence: [`docs/evidence_ledger.md`](docs/evidence_ledger.md), [`docs/claim_matrix.md`](docs/claim_matrix.md)

## Scientific center

EOG keeps four objects separate:

1. **local possibility** — a state is locally supported by a declared environmental or process representation;
2. **reachability** — a declared transition process can reach that state;
3. **distributional realizability** — an observed configuration is compatible with a declared world;
4. **historical truth** — what actually happened in nature.

Observed occurrences are realized positive states. They constrain admissible distribution-forming processes, but they do **not** identify one true route, colonisation sequence, ancestry, migration rate or movement history.

For a declared world universe, the prospective inverse object is

```text
W(O) = { declared worlds compatible with observations O }
```

and world identity is retained rather than averaged away by default.

## What is not an EOG novelty claim

The prior-art / negative-boundary audit has deliberately removed generic novelty claims for:

- dynamic or time-respecting reachability;
- critical geographic connection thresholds and stepping stones;
- least-cost / minimum cumulative environmental exposure paths;
- multiple-path and circuit-style redundancy;
- suitability + accessibility / functional habitat;
- consensus or ensemble support;
- history-matching / NROY model-space filtering;
- minimum-assumption relaxation, Pareto rescue sets or falsification-frontier mathematics.

These remain useful operators or comparators. They are not presented as new mathematics invented by EOG.

## Remaining contribution hypothesis

The remaining EOG hypothesis is a **biogeographic domain-framework / composition claim**:

> **Occurrence-conditioned ecological and analyst-choice alternatives may be more informative when they are retained as explicit, auditable worlds instead of being silently selected, unioned or averaged, with underidentification preserved and claim strength limited to the declared coverage/certificate.**

That hypothesis is not established by synthetic examples alone. It now requires empirical validation against strong matching comparators.

## Robust, contingent and excluded structure

For an explicitly declared finite world universe, EOG distinguishes states or structures that are:

- supported/reachable in every world;
- contingent on ecological or analytical representation;
- unsupported/unreachable in every enumerated world.

`robust` always means robust under the **declared certified universe**, not universally true in nature.

World-universe expansion must make strong claims more conservative:

- robust sets may stay the same or shrink;
- possible sets may stay the same or expand;
- all-world exclusion may stay the same or shrink.

A 99/100-world consensus can therefore remain contingent if the 100th admissible world disagrees.

## Watershed language

The distributional-watershed vocabulary is retained only as an interpretation layer:

- occurrence = realized anchor;
- basin = reachable set under a declared world;
- channel / tributary = supported transition sequence;
- confluence = reconvergence;
- bottleneck = critical transition or state;
- divide = disconnected reachability boundary;
- water level `lambda` = a **predeclared one-dimensional monotone relaxation coordinate only**;
- basin merge = the first declared relaxation level yielding joint realizability.

Geographic/IBD-like, environmental/IBE-like and barrier relaxation remain separate axes unless a genuinely one-dimensional family was declared before seeing the result.

## Package architecture

### Stable root `eog`

The frozen v0.1 compatibility surface retains:

- environmental-state geometry and shared-reference comparison;
- support topology;
- bridge / bottleneck inference;
- survey / hypothesis-discrimination utilities.

These remain available for frozen reproduction and earlier empirical work.

### Prospective `eog.v2`

`eog.v2` is a thin compatibility namespace. New scientific work stays behind three lazy facades:

- `eog.v2.reachability` — static/temporal flow, compatible-world reconstruction, world-indexed support sets, relaxation diagnostics, survey discrimination and transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental/barrier/pathwise transition constraints;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation.

System-specific A-Islands, Tanzania, Finland, Ryukyu, Zhoushan and similar code belongs to validation/adapters rather than the generic scientific API.

## Current development gate

The next mainline goal is **not another operator**. It is to determine whether preserving a declared world set adds useful ecological information beyond established methods.

Before a confirmatory analysis, freeze:

1. the ecological question;
2. natural versus analyst-choice dimensions of the world universe;
3. strongest established comparator for each estimand;
4. held-out or independent validation endpoint;
5. the result that would count as **no added value**;
6. the coverage/certificate boundary for any robust claim.

PR #181 adds a response-free A-Islands world-set adapter as **exploratory development evidence only**. A-Islands has already been viewed and cannot serve as a new confirmatory test of the integrated framework. If that exploratory representation is useful, confirmation must use an independently frozen system.

## Side-line policy

Side lines are allowed only when they have a distinct scientific or preservation purpose and a clear stop condition.

Allowed examples:

- frozen structural-manuscript release / archive work;
- independent validation required by the mainline;
- recovery of a pre-existing field validation once the required original inputs are actually archived;
- maintenance needed to reproduce frozen evidence.

Do **not** open a side line merely to chase a smaller novelty niche, duplicate an existing operator, obtain a favourable dataset, or create another public EOG identity.

## Frozen evidence is preserved

Cleanup does not erase adverse, null, failed or indeterminate results. Earlier A-Islands, Tanzania, Finland, genetic/reference and synthetic validation lines remain evidence boundaries with their contracts, fingerprints and artifacts intact.

The [`manuscript/`](manuscript/) directory is explicitly the earlier structural-reachability publication/evidence line, not the active package architecture.

## Repository rules

- Preserve evidence before removing implementation.
- Reuse an existing operator/facade before creating a module family.
- Keep benchmark/comparator work in `benchmarks/` and `tests/` unless it exposes a genuinely reusable estimand.
- Keep presentation/system-specific code out of eager scientific imports.
- Do not infer absence from non-detection without an explicit detection model.
- Do not return one history when observations leave several worlds compatible.
- Claim strength must not exceed coverage/certificate strength.
- Physical legacy deletion occurs only after repository search shows no frozen reproduction path depends on it.

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

The strongest active claim is deliberately narrow:

> **Observed distributions can constrain a declared set of distribution-forming worlds while preserving alternative explanations and limiting structural claims to the coverage actually certified.**

## Provenance

The original environmental-state implementation was extracted from ACSP. Support-topology work incorporated defensible frozen-field, occurrence-anchor, component, recovery and audit ideas previously developed in ODSP while avoiding duplicate path implementations. Later structural, empirical and prospective validation lines remain reproducible through their frozen contracts and evidence ledgers.

## License

MIT.
