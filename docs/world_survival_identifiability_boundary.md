# World-survival identifiability boundary

## Status

The prospective NEON world-survival programme is closed.

The empirical result does not support the hypothesis that a response-blind,
whole-network structural summary can forecast whether a finite EOG world universe will
later be falsified, partially contract, or saturate after positive occurrence evidence.

The deeper conclusion is an identifiability boundary rather than a request for another
cutoff search.

## Prospective empirical result

The v2 rule was frozen before biological response access:

- sixteen NEON small-mammal sites;
- one-step structural horizon;
- exact duplicate adjacency operators counted once;
- horizon-realization cutoff fixed at 0.5;
- all sixteen sites prospectively forecast as contracting;
- no model fitting or predictive loss endpoint.

The once-only response programme consumed one frozen NEON query and closed with:

- fixed sites: 16;
- scored sites: 9;
- response-consumed registry STOPs: 7;
- exact regime matches: 2/9 = 0.2222;
- fixed simple three-label reference: 1/3;
- one-sided binomial upper tail versus that reference: 0.8569;
- mean absolute survival-fraction error: 0.4167;
- observed regimes among scored sites:
  - saturated: 7;
  - contracting: 2;
  - falsified_universe: 0.

Every scored site's observed surviving-world fraction exceeded its frozen forecast.

The two matching systems were DELA and DSNY. The seven saturated mismatches were ABBY,
BARR, BLAN, CPER, DCFS, GRSM and GUAN.

The seven unscored sites stopped because target-positive response rows contained trap
coordinates outside the response-blind frozen location registry. Those sites are not
assigned a biological regime and cannot be repaired or reclassified inside the consumed
programme.

## What this resolves

### The finite-world framework is not intrinsically endpoint-only

Before this programme, the major empirical examples appeared to collapse to endpoints:
complete falsification or complete saturation.

The NEON programme produced two genuine intermediate contractions:

- DELA: 3/4 distinct falsifiable worlds survived;
- DSNY: 2/3 distinct falsifiable worlds survived.

Therefore the finite-world formulation itself does not mathematically force only 0 or 1
survival fractions.

### The frozen structure-only regime forecast failed

The prospective v2 rule predicted contracting for all sixteen fixed sites, but seven of
nine scored sites saturated.

This is not evidence for retuning the cutoff. The frozen hypothesis was that response-blind
whole-network structure was sufficient to anticipate the later epistemic regime. That
hypothesis failed in this programme.

## Why a deeper limitation exists

Under the one-step, self-excluded peer-positive rule, a world survives a positive-node set
P if and only if every positive node has at least one positive neighbour:

    minimum degree of G[P] >= 1

where G[P] is the subgraph induced by the observed positive nodes.

The decisive object is therefore not only the whole graph G. It is the placement of the
positive set P inside G.

### Two-positive witness theorem

Consider any undirected world graph containing:

- at least one edge; and
- at least one non-edge.

Freeze the graph and freeze the positive-set cardinality at exactly two.

If the two positive nodes are the endpoints of an edge, the world survives.

If the two positive nodes are a non-adjacent pair, the world fails.

Nothing about the response-blind graph changed. Node count, edge count, component
structure, LCC fraction, isolated-node fraction, degree distribution and all other
graph-only summaries are identical. Even the number of positives is identical.

Therefore:

> For any nonempty, noncomplete undirected world graph, later one-step positive-evidence
> survival is not identifiable from response-blind graph structure alone.

The implementation and proof witnesses are in:

- src/eog/v2/world_survival_identifiability.py
- tests/test_world_survival_identifiability.py

The exhaustive helper also demonstrates the same non-identifiability for larger fixed
positive-set cardinalities on synthetic graphs.

## Consequence for EOG

This separates two questions that had previously been conflated.

### Structural adequacy can be response-blind

Before the response is opened, EOG can legitimately ask whether the declared world family
contains the structural scales required to make the intended claim testable.

Examples include:

- largest weak-component coverage;
- isolated-node fraction;
- declared horizon structure;
- finite-n completeness of the ladder;
- duplicate-world detection.

These are properties of the declared world universe.

### Later world survival is response-conditioned

Whether a structurally adequate world survives occurrence evidence depends on where the
positive observations occur inside that structure.

A response-blind whole-network summary cannot generally determine that placement.

Thus the strong version of the proposed claim is rejected:

> structural adequacy does not imply predictable epistemic contraction.

## What would be required to predict survival probabilistically

A probabilistic forecast of later world survival would require extra assumptions about
the future or hidden positive-node configuration, for example:

- a spatial occupancy distribution;
- a source-location prior;
- an environmental occurrence model;
- a mechanistic colonisation model;
- an externally justified sampling distribution.

But those assumptions are no longer pure graph-adequacy information. They reintroduce a
model of where occurrences are expected to appear.

That is not forbidden, but it is a different scientific product and must not be presented
as a response-blind structural certificate.

## Final EOG boundary after this programme

The strongest supported Layer-A statement is now narrower and clearer:

> EOG can prospectively certify whether a declared finite world universe is structurally
> capable of being tested, and positive evidence can subsequently contract or falsify
> that universe. The amount of later contraction is not, in general, identifiable from
> response-blind global structure alone because compatibility depends on the placement of
> the observed positives.

This preserves the main EOG distinction:

- suitability is not reachability;
- reachability is not realized distribution;
- realized positive evidence constrains worlds;
- surviving worlds are not historical truth.

It adds a new boundary:

- structural testability is not the same thing as predictable future contraction.

## What not to do next

Do not:

- retune the 0.5 cutoff on the consumed NEON result;
- search for a structural summary that recovers these nine labels and call it prospective;
- repair the seven registry-mismatch sites and add their regimes;
- add candidate systems until accuracy improves;
- reinterpret the NEON guild endpoint as a taxon-level validation;
- weaken the identifiability result by calling this merely an RF or Layer-B failure.

A future response-location model, if scientifically desired, must begin as a new
prospectively declared question with new independent validation.
