# EOG finite-world path quantifier certificate (2026-11-22)

## Scientific question

The existing EOG finite-world engines preserve world-indexed reachability. They correctly ask whether a target is reached by every compatible world. That does **not** imply one geographic route is available in every world.

Two different quantifiers must be kept separate:

\[
\forall w\in W(O)\;\exists p_w: A\leadsto C
\quad \text{(each world has some route)}
\]

\[
\exists p\;\forall w\in W(O): p\subseteq E_w
\quad \text{(one shared route works in every world)}
\]

The second condition implies the first. The reverse need not hold. This is ordinary logic on graphs, **not a newly invented graph theorem**. EOG adds a narrowly scoped audit of these distinct claims against exact finite-world identities.

## Implemented API

Import audit_world_path_quantifiers from eog.v2.reachability.

Call with the frozen FiniteWorldReconstruction, its unchanged FiniteWorld objects, selected source/target, and optional edge_support_floor.

WorldPathCertificate reports:

- shortest_path_by_world: deterministic path witnesses, or None if no path exists;
- every_world_reachable: all compatible worlds admit at least one path;
- common_path_exists and common_path: one identical directed-edge sequence works across all worlds;
- mandatory_intermediates_by_world: nodes whose removal blocks all source-target paths in that world;
- necessary_in_every_world: nodes unavoidable in every compatible world, withheld if any world cannot reach the target;
- necessary_in_some_reachable_worlds: world-dependent vulnerability candidates;
- shared_active_edges, world fingerprints, finite step horizon, edge floor and coverage certificate.

The API rejects mismatched world identities/fingerprints, an empty compatible set, inconsistent node definitions, zero source weight, and invalid gates. World input ordering is irrelevant.

## Exact synthetic counterexamples

| Finite scenario | Every world reaches C? | One shared complete route? | Unavoidable intermediate in every world? |
|---|---|---|---|
| World 1: A-B-C; world 2: A-D-C | Yes | No | None |
| World 1: A-B-C; world 2: A-B-C plus A-D-C | Yes | Yes (A-B-C) | None (B replaceable in world 2) |
| World 1: A-B-X-C; world 2: A-D-X-C | Yes | No | X |
| Both worlds A-B-C only | Yes | Yes | B |
| Only one world reaches C | No | No | Withheld |

The third row is important: a universally unavoidable stepping stone can exist even with no common full route. Conversely a shared complete route can exist without a universally unavoidable stepping stone.

For each edge set E_w, the common-path check builds the intersection of all E_w and searches a directed path within the frozen step limit. It never uses edge union as a surrogate world. Necessity is tested separately by removing each intermediate within each world.

## Boundary and semantic cautions

1. The API gates **raw edge support**, strictly greater than edge_support_floor. This is a structural graph test, NOT EOG's mass-based first-passage threshold. A structurally possible path can have negligible numerical support. Do not equate these results.
2. The hop limit is not calibrated physical time.
3. The selected source must be a positive-weight declared source in every compatible world.
4. Finite completeness is conditional on exactly the enumerated world set. No unique history, actual corridor use, ecological movement probability, or validated conservation importance follows.
5. This module handles static directed transition operators with a finite hop limit. A time-changing world family requires a separate temporally coherent audit.
6. The frozen EOG-WF denominator remains 3 scored (2 favorable, 1 adverse) / 31 scientific STOP / 3 administrative exclusions. No field endpoint is added.

## Verification

From an installed development environment at repository root:

    python -m pytest tests/test_world_path_certificates.py -q
    python -m pytest tests/test_world_coherent_reachability_boundary.py -q

The tests cover alternative corridors, shared paths with optional intermediates, common necessary node without a shared route, world expansion, missing target access, edge floors, world-order invariance, and fail-closed source/fingerprint validation.

Implementation: [world path certificates](../src/eog/v2/world_path_certificates.py). Previous guardrail: [world-coherent reachability boundary](world_coherent_reachability_boundary_20261122.md).

## Time-indexed extension

The previously deferred temporal-world case now has its own [time-coherent path quantifier certificate](temporal_path_quantifier_certificate_20261122.md). The new API retains ordered interval identity and distinguishes common routes, universally necessary spatial waypoints and universally necessary timed states, without pooling alternative temporal worlds. No static API, mass forecast, or frozen empirical result is changed.
