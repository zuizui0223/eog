# World-coherent reachability: a finite-world no-splicing guardrail (2026-11-22)

## Scope

This is an exact, response-free counterexample to a misleading aggregation rule. It does **not** establish mathematical novelty, ecological dispersal mechanisms, or out-of-sample forecasting improvement. It does not change EOG-WF's frozen 3 scored / 31 science STOP / 3 administrative exclusions.

The existing [circuit world-aggregation boundary](../benchmarks/circuit_world_aggregation_boundary.py) demonstrates *artificial redundancy*: two alternative A–C routes, neither simultaneous, become parallel routes if the worlds are unioned. The present case is stricter: world aggregation creates an A–C route that **no declared world contains at all**.

## Static world counterexample

Observed positive evidence is A alone, with declared source A, node universe {A,B,C} and two transition steps. Each edge has raw support 1 and the explicit loss channel is 1, so a single outgoing edge transmits half the support.

| Declared world | Available directed edges | Can A reach C by step 2? |
|---|---|---|
| world_ab | A → B | No |
| world_bc | B → C | No |
| **Invalid pooled graph** | A → B and B → C | **Yes; first-passage support 0.25** |

The correct finite-world union of reachable **nodes** excludes C. Replacing the pair of graphs with their edge union before propagation silently switches from one fixed world to another in the middle of a path.

As a positive control, genuinely adding a third world containing A → B → C makes C **contingent**, not universally supported. The exact universe-expansion audit must report the lost exclusion, preserve the old world fingerprints, and satisfy monotonicity.

## Temporal world counterexample

With snapshots t0,t1,t2:

| Declared world | t0 → t1 edges | t1 → t2 edges | Reaches C at t2? |
|---|---|---|---|
| world_early_ab | A → B | none | No |
| world_late_bc | none | B → C | No |
| **Invalid interval-by-interval union** | A → B | B → C | **Yes; exact-time support 0.25** |

Even a time-labelled, per-interval union is invalid if it permits world identity to switch between intervals. The existing temporal-world flow engine correctly preserves each complete trajectory and keeps C excluded. A robust edge envelope or a possible-edge map alone must never be promoted into a source-conditioned reachability certificate.

## Executable check

Run from the repository root with the package installed:

    python benchmarks/world_coherent_reachability_boundary.py
    python -m pytest tests/test_world_coherent_reachability_boundary.py -q

Outputs distinguish original compatible worlds, their per-world first-passage support, the invalid pooled comparator, an authentic universe expansion, and static/temporal fingerprint-order stability. Tests assert the values and reject any accidental splicing.

## Interpretation limits

- This is a synthetic *logical failure mode of naive aggregation*, not an observed EOG bug in the current world-indexed engines.
- Every exclusion is conditional on exhaustive enumeration of the **declared finite** world set, the source and the finite horizon; unlisted ecological or analytical worlds can rescue it.
- Source support is not a calibrated colonisation probability. A spliced path is not evidence of a historical route.
- The experiment creates no independent ecological replicate, changes no real-data score, and gives no reason to reopen the closed EOG-WF candidate search.
