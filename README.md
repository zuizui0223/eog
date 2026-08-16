# Environmental Occupancy Geometry (EOG)

EOG is an auditable biogeographic framework for asking a broader question than local suitability alone:

> **Given an observed distribution and a declared set of ecological and analytical worlds, which distribution-forming explanations remain compatible, and which structural conclusions survive disagreement among those worlds?**

## Current status

There is **one EOG scientific mainline**. Generic operator growth is stopped by default.

Current evidence status:

> **exploratory-supported but independently unconfirmed**

Methodological audit status:

> **The finite world-set inference is coherent as a conditional, set-valued framework. Predictive superiority is a separate estimand and is not established.**

- **A-Islands**: response-free exploratory work showed that retaining exact world identity can preserve structure erased by scalar `connected_frequency`; this is not independent confirmation because the system had already been viewed.
- **A-Islands strong-reference predictive extension**: a separate prospectively frozen candidate-vs-R3 test was adverse; it did not establish predictive superiority.
- **SIVFLORA**: independent attempt stopped pre-outcome because the frozen WorldClim representation had nodata at four frozen nodes. It was not rescued.
- **Azores**: independent attempt passed source, node, climate, world-universe and outcome-contract gates, then stopped pre-model because the frozen literal `Tracheophyta` taxon rule yielded zero eligible species. Distribution rows were not read and no predictive model or confirmation metric was computed.

The repository therefore does **not** currently claim independent evidence that exact world identity improves held-out ecological prediction or has independent identity-preserving inferential value.

Canonical project state:

- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- method-validation protocol: [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md)
- implementation / prior-art ledger: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- package boundary: [`docs/eog_v2_package_layout.md`](docs/eog_v2_package_layout.md)
- frozen evidence: [`docs/evidence_ledger.md`](docs/evidence_ledger.md), [`docs/claim_matrix.md`](docs/claim_matrix.md)
- Azores independent-attempt evidence: [`validation/azores_confirmation/README.md`](validation/azores_confirmation/README.md)

## Scientific center

EOG keeps four objects separate:

1. **local possibility** — a state is locally supported by a declared representation;
2. **reachability** — a declared transition process can reach that state from a declared anchor/source set;
3. **distributional realizability** — an observed configuration is compatible with a declared world;
4. **historical truth** — what actually happened in nature.

Occurrences are realized positive states. They constrain admissible worlds but do not identify one true route, colonisation history, ancestry, migration rate or movement process.

For a declared world universe,

```text
W(O) = { declared worlds compatible with observations O }
```

World identity is retained rather than averaged away by default.

## What EOG does not claim as new

The prior-art audit removed generic novelty claims for:

- dynamic / time-respecting reachability;
- critical geographic thresholds and stepping stones;
- least-cost / minimum cumulative environmental exposure;
- circuit-style multiple-path redundancy;
- suitability + accessibility / functional habitat;
- consensus ensembles;
- history matching / NROY filtering;
- minimum-relaxation / Pareto falsification-frontier mathematics.

These are established operators or comparators, not separate EOG inventions.

## Remaining contribution hypothesis

The only active integrated-method hypothesis is:

> **Biogeographic inference may gain useful information when ecological and analyst-choice alternatives are retained as explicit auditable worlds, mutually exclusive worlds are not silently averaged or unioned, underidentification is preserved, and robust claims are restricted to certified coverage.**

That hypothesis remains **unconfirmed independently**.

The method audit separates two empirical questions:

1. **identity-preserving inferential value** — does exact world identity retain an independently testable distinction that a predeclared compression of the same worlds erases?;
2. **predictive increment** — does world identity improve held-out predictive loss over a stated comparator?

The first is the primary validation target for the current framework claim. The second is a separate, narrower claim. Predictive failure does not automatically invalidate a useful set-valued uncertainty representation, and predictive success would not identify historical truth.

## Robust, contingent and excluded structure

Within an explicitly declared finite universe, EOG distinguishes structure that is:

- supported/reachable in every compatible world;
- contingent on ecological or analytical representation;
- unsupported/unreachable in every compatible world.

`Robust` means robust over the **declared certified universe**, not universally true in nature.

World-universe adequacy is therefore part of the method. Future empirical worlds must distinguish biologically intended process uncertainty from analyst-choice sensitivity worlds and state which plausible alternatives lie outside the certificate.

## Watershed language

The watershed vocabulary is interpretation only:

- occurrence = realized anchor;
- basin = reachable set under a declared world;
- channel / tributary = supported transition sequence;
- confluence = reconvergence;
- bottleneck = critical transition/state;
- divide = disconnected reachability boundary;
- `lambda` = a predeclared one-dimensional monotone relaxation coordinate only.

Geographic/IBD-like, environmental/IBE-like and barrier axes remain separate unless a one-dimensional family was declared in advance.

## Package architecture

Root `eog` preserves the frozen v0.1 compatibility surface. `eog.v2` remains a thin lazy namespace over:

- `eog.v2.reachability`
- `eog.v2.traversability`
- `eog.v2.validation`

System-specific validation code belongs in `benchmarks/`, `validation/` and tests, not in a new public API family.

## Development rule now

The next default task is **method/evidence consolidation and simplification**, not another ecological operator and not another bespoke dataset search.

A future independent confirmation is admissible only through the protocol in [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md). In particular, a generic pre-outcome eligibility screen must establish source identity, node mapping, input coverage, taxonomic/response vocabulary, response semantics and enough genuinely independent holdout units before EOG-specific outcomes are opened.

A future confirmation must predeclare which claim it tests:

- structural/identity-preserving inferential value;
- predictive added value;
- or both, with separate decision rules.

## Side lines

Meaningful side lines remain allowed when they have a distinct purpose and stop condition, especially:

- frozen manuscript archive/release work;
- reproduction maintenance;
- pre-existing field validation once its original inputs are archived.

Do not create another EOG identity, duplicate established connectivity machinery, retune blocked systems, or search for a favourable dataset.

## Repository rules

- Preserve adverse, null, blocked and indeterminate evidence.
- Reuse existing operators/facades before adding modules.
- Keep system-specific validation outside eager package imports.
- Do not infer biological absence without an explicit response/detection interpretation.
- Do not return one history when several worlds remain compatible.
- Do not call analyst-choice thresholds biological dispersal/tolerance constants without external calibration.
- Do not use a large number of bootstrap draws to disguise a small number of genuinely independent holdout units.
- Claim strength must not exceed coverage/certificate strength.

## Installation

```bash
python -m pip install .
```

For raster benchmark work:

```bash
python -m pip install ".[raster]"
```

## Scientific boundary

EOG does not justify calling uncalibrated reachability support an occupancy probability, colonisation probability, dispersal probability, migration rate, demographic connectivity or ancestry estimate.

The strongest current claim is:

> **Observed distributions can constrain a declared set of distribution-forming worlds while preserving alternative explanations and limiting structural claims to the coverage actually certified.**

## License

MIT.
