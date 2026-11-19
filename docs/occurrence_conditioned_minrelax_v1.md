# Occurrence-conditioned minimum required relaxation — finite-graph v1

## Status and scientific role

**Research-only, predeclared known-truth synthetic benchmark.** The canonical
pre-score contract is
[`validation/occurrence_conditioned_minrelax_v1/protocol_v1.json`](../validation/occurrence_conditioned_minrelax_v1/protocol_v1.json).
This work **does not alter EOG-WF's closed 3 scored / 31 scientific STOP / 3
administrative exclusion denominator** or expose a new public API.

Existing EOG already implements `minimum_relaxation_frontier` and
`minimum_temporal_relaxation_frontier` for *declared finite worlds*. This
benchmark fills a narrower missing input-to-estimand link: it derives a
complete finite family of threshold worlds from a **fixed, directed graph of
explicit geographic, environmental and barrier requirements**, then calls
the existing EOG reconstruction and Pareto operators. No duplicate
connectivity/Pareto implementation is introduced.

## Target and formal definition

Freeze a finite directed candidate network `G`, fixed nonempty observed
source set `S`, observed-positive node set `O`, horizon `H`, and a baseline
per-edge crossing rule `theta0=(r0, delta0, b0)`.

For edge `i->j`, declare:

- `d_geo(i,j)`: maximum geographic single-step distance in km;
- `d_env(i,j)`: nonnegative distance in a frozen environmental feature scale;
- `b(i,j)`: categorical **barrier permission required** (0 or 1);
- `hard_unavailable(i,j)`: physically excluded edge, *not* reopened by relaxing `b`.

For `theta=(r,delta,b)>=theta0`, an edge is admitted only if it is
not hard unavailable and all three component requirements are met.

Define `Compatible(theta | G,S,O,H)` as true only if every observed
positive node is reachable from the **same fixed source declaration** in
at most `H` directed steps. It does **not** assert that the source really
founded the other sites, that every site is occupied simultaneously,
or that the witness routes occurred historically.

The estimand is the *coordinatewise non-dominated* feasible increment set:

```text
F*(G,S,O,H; theta0) = ParetoMin {
    (r-r0, delta-delta0, b-b0) :
    r>=r0, delta>=delta0, b>=b0,
    Compatible((r,delta,b) | G,S,O,H)
}
```

No arbitrary alpha*d_geo + beta*d_env + gamma*b weights are used.
The three axes have different units and meanings. The componentwise
minimum of each axis over `F*` **need not itself be jointly feasible**.

## Exact finite breakpoint algorithm

With the candidate graph fixed, an edge's admitted state changes only
when a threshold passes its declared requirement. Therefore the complete
set of thresholds at or above the baseline is the Cartesian product of
the baseline and **all unique, higher, non-hard edge requirements**
on each axis. Exhaustive enumeration on that finite grid is exact
**conditional on the input candidate graph and step horizon**; it does
not claim coverage of undiscovered intermediate patches, alternative
source histories, uncertainty in input environmental measurements, or
continuous ecological dispersal biology.

The benchmark:

1. Strictly validates positive sources, edges, axis units, horizon and the
   finite candidate-world budget (512); otherwise stops.
2. Creates all breakpoint-specific `DynamicTransitionOperator` and
   `FiniteWorld` objects with original EOG code and auditable fingerprints.
3. Applies original `reconstruct_compatible_worlds` under *fixed* sources,
   then original `minimum_relaxation_frontier`.
4. Independently checks **every single compatibility decision** by bounded
   directed BFS, and records deterministic possible-route witnesses for
   surviving Pareto points.
5. Returns `no_feasible_world_within_declared_graph_and_step_limit` when
   no candidate is compatible, **not** a claim of absolute impossibility.

The EOG operator's edge support is fixed at 1.0 for graph-positive
transitions and the first-passage **positive-support criterion** is used;
it is not fit to animal movements or calibrated as a colonization
probability. Maximum steps are graph hops, not elapsed years.

## Predeclared examples and expected checkable results

Baseline geographic single-step limit = **10 km**, environmental tolerance
= **1 feature unit**, and permission to cross the declared relaxable barrier
= **0**. Source is A and positive observations are A and B.

The frozen directed candidate routes are:

| Candidate route | Largest step (km) | Environmental step (units) | Barrier permission |
| --- | ---: | ---: | ---: |
| A -> X -> B | 8 | 2 | 0 |
| A -> B | 30 | 0 | 0 |
| A -> Y -> B | 7 | 0 | 1 |

At the baseline none is feasible. The expected *non-dominated
extra assumptions* are:

| Rescue | Geographic increment | Environmental increment | Barrier permission increment |
| --- | ---: | ---: | ---: |
| Environmental crossing | 0 km | +1 unit | 0 |
| Long single jump | +20 km | 0 | 0 |
| Barrier reinterpretation | 0 km | 0 | +1 |

Each of these is only a **constructed path witness** in the frozen graph,
not an estimate of real dispersal or three independent ecological effects.
All three coordinatewise *individual* minima equal zero, while the
(0,0,0) joint point is infeasible. This is why a scalar or separate
axis-by-axis answer can be dangerously misleading.

A second declared synthetic positive C has a candidate A->C edge
requiring 15 km, one environmental unit, no barrier permission. All
feasible explanations now require at least +5 km geography. The
expected frontier is (20,0,0), (5,1,0), and (5,0,1). A valid **world
contraction** comparison must hold C and its edge present in the
candidate graph *both before and after* observing C; merely adding C
as a new node and changing the candidate universe is NOT evidence
contraction.

A completely `hard_unavailable=True` crossing stays closed even at
permission = 1. No feasible world returns an explicit declared-network
STOP and invites revised *candidate graph or externally verified
hypothesis*, not fabricated ecological impossibility.

## What must not be claimed

- Generic new Pareto mathematics, critical thresholds or connectivity:
  all have prior art (e.g., landscape graph critical dispersal scales,
  falsification-adaptive and breakdown-frontier frameworks).
- Historical A-to-B origin, realized route, colonization probability,
  or unmeasured barriers. Observed A/B do not establish their ancestry.
- `hard_unavailable` from an amphibian nondetection or unsurveyed edge.
- Robustness to analyst choices. This v1 has **one** frozen feature scale
  and candidate graph; an alternative raster, graph, source or H is a
  *different hypothesis family* and needs an explicitly declared universe.
- General improvement over dynamic SDM or landscape connectivity.
- Independent biological replication: this benchmark is synthetic.

## Required extension before a biological result

Choose one independent real study with a pre-observation candidate
source prior or source-class alternatives; explicitly measured or
externally calibrated candidate transitions and barrier evidence; a
recorded time horizon; positive observations not used to construct/tune
the edge constraints; and **held-out movement, genetic or re-colonization
observations**. Freeze at least two analytic representations and propagate
their alternative frontiers without treating source IDs as interchangeable.

The wetland-amphibian source qualified in
[`wetland_amphibian_source_qualification_v1.md`](wetland_amphibian_source_qualification_v1.md)
has real repeated visits and habitat covariates, but does **not** yet
contain a verified dispersal network or founding-source identity.
Its nondetections cannot be promoted to structurally forbidden edges.

### Reproduce

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_occurrence_conditioned_minrelax_v1.py
python benchmarks/occurrence_conditioned_minrelax_v1.py \
  --output results/occurrence_conditioned_minrelax_v1.json
```

### Methodological prior art to cite before manuscript promotion

- Keitt et al. (1997), landscape critical dispersal thresholds /
  stepping-stone network percolation:
  https://www.ecologyandsociety.org/vol1/iss1/art4/
- Masten & Poirier (2021), falsification-adaptive sets:
  https://doi.org/10.3982/ECTA17969
- Masten & Poirier (2020), inference on multidimensional breakdown frontiers:
  https://doi.org/10.3982/QE1288

The candidate contribution is ecological *interpretation and audited
conditional inversion*, not the underlying Pareto algorithm.
