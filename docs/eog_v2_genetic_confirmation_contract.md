# EOG v2 frozen synthetic genetic-confirmation contract

## Status

This contract is frozen before the confirmation outcomes are inspected. It applies only to the FST-oriented, hyperparameter-free exact-eventual EOG-R candidate implemented in `src/eog/eventual_genetic_connectivity.py`.

The confirmation must be retained if it fails. Seeds, gates, truth regimes, references and the candidate method must not be changed to rescue the outcome.

Contract fingerprint:

`9781b171f703010fe16efdd5adc7f12daaa5a3b0be72986438c2bd63e78db1d7`

## Candidate method

The symmetric FST-oriented EOG predictors are fixed as:

1. exact eventual first-passage support under the frozen sub-stochastic EOG-R operator;
2. reciprocal exchange support = arithmetic mean of `i -> j` and `j -> i` eventual supports;
3. connected-pair continuous distance = negative log reciprocal exchange support;
4. bidirectionally zero-support pairs receive a separate symmetric `disconnected` indicator;
5. the continuous distance for disconnected pairs is capped at the maximum finite connected-pair distance so disconnection remains a separate estimand.

The candidate has **no propagation horizon, no numerical support-floor hyperparameter and no fitted symmetrisation parameter**.

Directional support is retained separately. Symmetric pairwise FST is not used to confirm migration direction.

## Confirmation seeds and simulator

Unused confirmation seeds:

`2503, 2609, 2707, 2801, 2903, 3001, 3109, 3203`

For every regime:

- 2,048 neutral biallelic loci;
- 120 generations;
- effective population size 80 for every population;
- ancestral beta distribution `(0.8, 0.8)`;
- exact latent-frequency pairwise FST as the simulation response.

Primary predictive metric: leave-one-population-out pairwise FST prediction MSE.

Primary contrast:

`reference + EOG continuous distance + EOG disconnected indicator - reference`.

## Fixed archipelago geometry

Eight populations are arranged as two four-node rows at coordinates:

`(0,0), (1,0), (2,0), (3,0), (0,1), (1,1), (2,1), (3,1)`.

Environmental values are:

`0.0, 0.2, 0.4, 0.6, 1.5, 1.7, 1.9, 2.1`.

Geographic support uses `exp(-distance / 1.0)`. Environmental support uses `exp(-environmental_distance / 0.5)`. The EOG-R operator uses loss support `0.5`.

## Frozen regimes

### Geography-only null

Truth: smooth geography-only migration support.

Migration scale: `0.03`.

Reference: geography-only effective resistance/current flow.

Gate: mean EOG increment must be `>= -1e-5` MSE. A material gain is not expected because the strong reference contains the truth.

### IBD + IBE reference-complete null

Truth: product of smooth geographic and environmental migration support.

Migration scale: `0.03`.

Reference: effective resistance/current flow on the same geography-times-environment conductance.

Gate: mean EOG increment must be `>= -1e-5` MSE.

### Intermediate-structure truth

Truth: two four-node chains with no cross-chain migration. One chain has support `0.9` on all three edges; the other has `0.9`, `0.03`, `0.9`, creating a severe middle bottleneck/disconnection structure absent from the geography-only reference.

Migration scale: `0.06`.

Reference: geography-only effective resistance/current flow.

Gates:

- mean EOG increment must be `<= -5e-4` MSE; and
- EOG must improve the reference in at least `6/8` confirmation seeds.

### Directional-structure FST boundary

Truth: connected two-row topology with one middle edge `0.8` forward and `0.05` reverse, while the undirected reference topology is matched.

Migration scale: `0.05`.

Reference: effective resistance on the matched undirected topology.

**Record only. No pass/fail gate.** Development showed that symmetric pairwise FST should not be treated as a validator of migration direction. Directional EOG hypotheses require a directional movement or genetic endpoint when available.

## Decision rule

The synthetic genetic confirmation passes only if all three symmetric-isolation gates pass:

1. geography-only null does not show material EOG added information;
2. IBD+IBE strong-reference null does not show material EOG added information;
3. intermediate structure shows the predeclared EOG improvement and seed consistency.

The directional FST result is retained as a boundary result but does not enter the decision.

## After this confirmation

A pass permits freezing this predictor construction for the first independent empirical genetic validation. It does not establish empirical validity, exact FST prediction, migration rates, historical routes, or directional gene flow.
