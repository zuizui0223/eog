# A-Islands reachability contract

The A-Islands benchmark is designed to separate **pointwise environmental support** from **occurrence-anchored spatial structure**. It is not designed to prove that EOG is a superior species distribution model.

## What changes relative to the SDM

The upstream model has already been frozen independently. For every species and fold it returns one fitted support value for each climate-evaluable island. EOG does not replace or retune that model.

The reachability layer asks a different question: given the locations of training occurrences, the geography of all surveyed islands, and the same frozen climate variables, is a held-out island embedded in a plausible island-chain structure under a predeclared family of geographic and environmental edge rules?

The answer is a **structural diagnostic**, not a dispersal probability. Unlabelled islands may be used as potential stepping-stone nodes. This means a connecting path says that the island configuration could support a chain under the declared assumptions; it does not say that intermediate islands were occupied or that the species actually dispersed along that path.

## Frozen scenario family

The unlabeled 842-island geometry was audited before species outcomes. Nearest-neighbour distances were approximately:

- q90: 19.67 km;
- q97.5: 50.55 km;
- q99: 120.83 km;
- maximum: 234.74 km.

The geographic edge ensemble is therefore frozen at rounded scales of **25, 50, 125 and 250 km**. These are sensitivity assumptions, not estimated species-specific dispersal kernels.

Each geographic radius is crossed with three environmental rules:

1. no environmental edge filter;
2. edge climate distance no greater than the 90th percentile among eligible training-training edges;
3. edge climate distance no greater than the 75th percentile among eligible training-training edges.

Climate distances use the same five frozen CHELSA variables as the support model, but are expressed in a median/MAD reference fitted to training islands only. Environmental cutoffs are recalculated by fold from training-island covariates and do not use species labels.

The 4 × 3 design yields **12 scenarios**. All scenarios receive equal weight. There is no post-hoc selection of the best radius or environmental cutoff.

## Reachability quantity

For each target island and scenario, the graph is searched from all training-presence anchors. The primary quantity is:

`connected_frequency = number of scenarios connected to >=1 training anchor / 12`.

A value of 0.75 means that the target is connected under 9 of the 12 declared structural assumptions. It is a robustness frequency across assumptions, not a 75% probability of dispersal, occupancy or colonisation.

Secondary diagnostics retain geography-only connectivity, environmentally constrained connectivity and the median normalized geographic bottleneck of connected paths.

## Why nearest-occurrence distance is a mandatory baseline

Graph connectivity can appear informative simply because nearby targets are more likely to connect. The benchmark therefore treats great-circle distance to the nearest training presence as a mandatory baseline rather than calling every graph effect “connectivity”.

The primary held-out statistic first groups islands by **pointwise support quintile × nearest-anchor-distance quintile**, using covariate values only. Within each resulting stratum, every presence-absence pair receives a reachability concordance score:

- 1 if the presence has higher `connected_frequency`;
- 0 if the absence has higher `connected_frequency`;
- 0.5 if tied.

The null is 0.5. Fold scores are averaged equally within species, and species summaries are averaged equally across estimable species. Taxa or folds with no mathematically comparable presence-absence pair remain explicit applicability failures and are not replaced.

This design makes the central claim conditional. If the statistic is above 0.5, the defensible interpretation is that structural reachability adds held-out incidence discrimination **among islands already similar in fitted support and proximity to known occurrences**.

## What this benchmark cannot establish

Even a positive result cannot establish:

- that EOG is generally a better SDM;
- a species-specific dispersal kernel;
- the true historical colonisation route;
- realized occupancy of intermediate stepping-stone islands;
- demographic or genetic connectivity along graph edges;
- a causal sea or landscape barrier;
- that spatial block cross-validation itself models dispersal limitation.

The framework intentionally keeps these quantities separate. Pointwise support is one estimand, structural reachability is another, and finite survey allocation remains a downstream decision problem that can be delegated to ACSP.
