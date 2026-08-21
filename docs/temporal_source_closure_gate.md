# Response-blind temporal source/process closure gate

## Purpose

A fresh predictive candidate can pass metadata, registry and static structural gates yet
still be incapable of supporting its own declared source/process explanation through the
full time series.

`src/eog/v2/temporal_source_closure.py` makes that necessary-condition check executable
**before response outcomes are opened**.

It asks:

> Under the already-frozen source eligibility, temporal availability and transition
> relation, does at least one possible source state remain after every declared time
> transition?

This is validation infrastructure, not an ecological movement model.

## Why it belongs before predictive smoke

A response-free synthetic smoke test should verify runner plumbing. It should not need to
invent extra external sources, memory sources, larger jumps or altered availability rules
merely to manufacture a temporally coherent fixture.

If the declared response-blind process/source contract already makes the possible-source
set empty, the candidate should stop before synthetic outcome construction and long before
once-only outcome authorization.

## Inputs

The generic evaluator receives four boolean objects in a frozen node order:

1. `initial_possible_source[n]`
   - every source state allowed at the first time slice;
2. `persistence_eligible[n, T]`
   - whether a currently possible source at node `i` may persist at the same node through
     transition `t -> t+1`;
3. `transition_target_eligible[n, T]`
   - whether node `j` is eligible to become a target in transition `t -> t+1` under the
     response-blind observation/process contract;
4. `transition_adjacency[n, n]`
   - frozen source-row / target-column transition permission.

The evaluator does not infer these from outcome data. Candidate-specific code must derive
them from already-declared geometry, effort/availability and source semantics.

## Optimistic recursion

At each transition, let `C_t` be the current possible-source set.

Same-node persistence is:

```text
P_t = C_t ∩ persistence_eligible[:, t]
```

Reachable declared transition targets are:

```text
A_t = targets reachable from any source in C_t through transition_adjacency
N_t = A_t ∩ transition_target_eligible[:, t]
```

Then:

```text
C_(t+1) = P_t ∪ N_t
```

This is deliberately **set-valued and optimistic**. It preserves every response-blind
possible source and every allowed transition simultaneously. It does not choose one
best parent, one route or one history.

That matters scientifically: arbitrary single-parent compression can destroy future
feasibility even when the union of possible paths remains non-empty.

## Decisions

### Pass

`temporal_source_closure_pass`

At least one possible source remains after every declared transition.

This says only that the declared explanation is temporally admissible as a necessary
condition. It does **not** mean that:

- the species truly occupied those nodes;
- a particular transition occurred;
- the declared source was biologically real;
- the route is historical truth;
- future predictive complementarity will succeed.

### STOP

`stop_temporal_source_closure_gap`

The optimistic possible-source set becomes empty at at least one transition.

Because the gate admits all frozen response-blind possibilities simultaneously, this is a
strong pre-outcome falsification of the **declared explanation**. It is still conditional
on the declared source universe, availability rules and transition relation.

A STOP is not permission to add an external source, memory source, wider threshold or
other rescue rule after seeing the failure and continue the same attempt as prospective.
Such a change defines a new scientific contract.

## North Anatolia failure that motivated the gate

The fresh northwestern Anatolia roe-deer candidate passed:

- closed analysis-registry preflight;
- 171-node response-independent geometry;
- three distinct structural worlds;
- static structural adequacy.

Before opening the roe-deer response, its frozen process/source explanation used:

- current recorded internal sources;
- positive camera effort at the relevant seasons;
- the broadest frozen structural world at 37.290775923813 km.

An optimistic response-free closure audit produced:

```text
14 -> 11 -> 46 -> 45 -> 0
```

and stopped at primary season `4 -> 5` (zero-based transition index `3`).

The response file was never downloaded or opened. Therefore this was neither favourable
nor adverse Layer-B predictive evidence. It was a source/process-closure failure found
before the predictive endpoint.

## Relationship to existing gates

Recommended fresh-validation order is now:

1. metadata candidate preflight;
2. closed analysis-registry check where required;
3. response-independent geometry and structural-scale/adequacy gate;
4. freeze process/source semantics;
5. **temporal source/process closure gate**;
6. response-free paired-runner smoke;
7. bounded physical response-header verification;
8. freeze the complete 16-key once-only outcome-access contract;
9. exact outcome count gate;
10. only then model fitting and heldout scoring.

The temporal closure gate does not replace structural adequacy. Static geometry can be
adequate while time-varying observation availability makes the declared source process
impossible to maintain.

## Audit and fingerprints

The result fingerprints:

- the declaration identity/semantics;
- frozen node order;
- initial-source mask;
- persistence mask;
- target-eligibility mask;
- transition adjacency;
- complete transition counts and final state.

The output records the first empty transition and the possible-source count after every
transition. Strong claims remain limited to the declared finite contract.