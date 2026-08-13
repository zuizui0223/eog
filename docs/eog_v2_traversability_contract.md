# EOG v2 ecological traversability development contract

## Status

This is a prospective development contract for issue #141. It is frozen before any new confirmatory empirical occurrence or genetic outcome is used to tune the quantities below. It does not alter or rescue any frozen v0.1/v2 result.

## Biological distinction

EOG v2 keeps local viability (`V`) distinct from source-conditioned reachability (`R`). This contract adds an intermediate **ecological traversability** layer that asks whether a declared route between viable endpoints requires environmentally discontinuous or poorly viable intermediate states.

The new layer does not turn `V` into `R`. Instead, it makes environmental transition size and transit viability explicit, auditable conditions of a reachability hypothesis.

## Occurrence-derived environmental scale

Observed occurrence states may define a reproducible descriptive scale in environmental feature space. The primary initial scale is a declared quantile of each occurrence state's nearest-other-occurrence Euclidean distance.

This scale is **not** an inferred movement kernel, transition probability, migration estimate, or proof that nearest occurrences are historically connected. It is only a response-free environmental-state scale that can be frozen before a transition hypothesis is evaluated.

If all observed occurrence states are identical in the declared feature space, the scale is non-identifiable and the implementation must fail rather than invent a numerical value.

## Endpoint IBE versus pathwise discontinuity

For a declared route

`p = (x_0, x_1, ..., x_k)`,

EOG reports separately:

- endpoint environmental distance: `d_env(x_0, x_k)`;
- cumulative environmental crossing: `sum d_env(x_i, x_{i+1})`;
- environmental bottleneck: `max d_env(x_i, x_{i+1})`.

Therefore two endpoints may have zero or small endpoint IBE while the only declared route between them contains a large environmental excursion or bottleneck.

## Transit viability

For explicit intermediate nodes in a route, EOG also reports:

- minimum intermediate viability;
- a descriptive niche-desert penalty `sum -log(max(V_i, floor))` over intermediate nodes.

No universal viability threshold is introduced. A binary "niche desert" claim requires a separately declared threshold or process model.

## Continuous propagation versus long jump

Transition edges are typed as either:

- `continuous`: transit viability multiplies the environmental-transition support;
- `long_jump`: transit viability of unrepresented intermediate landscape is not multiplied into the edge, because the hypothesis explicitly permits bypassing it.

Long-jump rarity must be represented independently through geographic, directional, barrier, or other declared support. A long-jump edge is not made cheap merely because it bypasses intermediate viability.

## Integration with existing EOG-R

The new ecological transition object is converted into the existing frozen `DynamicReachabilityEdge` interface. The legacy v2 dynamic operator itself is not modified, so historical operator fingerprints and frozen results remain unchanged.

The traversability bundle fingerprints both the separated ecological assumptions and the dynamic-edge representation generated from them.

## Package boundary

The prospective public API is consolidated under an actual `eog.v2` subpackage with three facades:

- `eog.v2.reachability` — dynamic propagation, state layers, flux and graph outputs;
- `eog.v2.traversability` — environmental continuity and transit-viability primitives;
- `eog.v2.validation` — occurrence and genetic validation interfaces.

The historical `from eog.v2 import ...` surface remains compatible. Root `eog` remains the frozen v0.1 namespace and package version remains `0.1.0`.

## Current non-claims

These primitives do not establish:

- a unique historical route;
- observed migration between occurrence pairs;
- colonisation probability;
- dispersal probability;
- demographic connectivity;
- causal environmental barriers;
- a species-specific transition law learned from occurrences.

The occurrence-derived scale is only the first conservative occurrence-conditioned primitive. Learning or comparing species-specific transition rules is a later prospective stage and must receive its own falsification contract before empirical promotion.

## Next synthetic gate

The next benchmark must freeze known-truth scenarios before result inspection, including at least:

1. same endpoint environment + continuous viable bridge;
2. same endpoint environment + nonviable intermediate state;
3. environmental bottleneck with otherwise viable stepping stones;
4. direct rare long jump across a niche desert;
5. endpoint-IBE-only truth;
6. path-discontinuity truth;
7. irrelevant traversability complexity.

The method must retreat when endpoint environment or an adequate conventional/process reference already contains the generating information.
