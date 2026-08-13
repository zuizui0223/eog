# Traversable ecological state space — method contract

Date frozen: 2026-08-13

Status: **synthetic-stage method component. No empirical outcome has been computed with it,
and no promotion claim is attached to it.**

This contract governs `src/eog/traversable_state_space.py`. It is written before any
empirical evaluation so that the transition rules cannot later be tuned to an outcome.

## 1. Position in the pipeline

EOG v2 supplies the downstream propagation machinery: directed sub-stochastic transition,
finite-horizon first passage, edge flux, source attribution, route entropy, bottleneck and
redundancy. Its transition operator is

```text
W_ij = K_geo × K_env × Barrier × Direction × Capture
```

where `K_env` is an **exogenous** per-edge value supplied by the caller. Nothing in v2
derives which environmental transitions are traversable for the species, and the operator
never requires an intermediate node to be habitable.

This module is the upstream layer that supplies that missing information:

```text
occurrence + environment + geography + barriers
  -> local viability V
  -> traversability / transition hypotheses      <- this module
  -> directed transition graph
  -> EOG-R (v2)
  -> first passage / bottleneck / redundancy / flux
  -> history constraints
  -> held-out occurrence / genetic / directional validation
```

Nothing downstream of the transition graph is replaced. V/R/C/P/O separation, sub-stochastic
loss, first passage, edge flux, source attribution, bottleneck, redundancy, route entropy,
the genetic validation infrastructure, frozen manifests, fingerprints, response firewalls
and negative controls are all retained unchanged.

## 2. Estimands, kept separate

Three families of quantity are reported side by side and are never pooled into one score.

| Family | Quantity | Depends on |
|---|---|---|
| Endpoint | `geographic_distance_km` (IBD) | the two populations only |
| Endpoint | `endpoint_environmental_distance` (IBE) | the two populations only |
| Pathwise | `minimax_environmental_step` | what lies between them |
| Pathwise | `cumulative_environmental_cost` | what lies between them |
| Transit viability | `maximin_transit_viability` | habitability of intermediates |
| Transit viability | `cumulative_niche_cost` | habitability of intermediates |

`minimax_environmental_step` is the pathwise counterpart of IBE: the minimum over admissible
routes of the largest single environmental step. Two populations with near-identical
endpoint niches can still be separated by one unavoidable niche jump, and no endpoint
comparison can detect that.

`maximin_transit_viability` is the maximum over routes of the minimum viability among
**intermediate** nodes. Endpoint viability is excluded so the quantity describes the
crossing rather than either population. A low value identifies a niche desert.

Arriving somewhere and establishing there remain different estimands. Transit viability
constrains `R`; it does not stand in for `P`.

## 3. Transition hypotheses

Continuous propagation and rare long-distance jumps are different hypotheses about the
species, not different parameter values of one universal cost. The declared kinds are
`continuous`, `stepping_stone` and `long_jump`.

The distinction is enforced, not merely documented: a `long_jump` hypothesis that also
requires transit viability is rejected at construction, because that combination erases the
property that defines it.

- **continuous / stepping stone**: every intermediate node must satisfy
  `minimum_transit_viability`. A route through an uninhabitable state is not admissible.
- **long jump**: intermediate viability is not required. The hypothesis is limited instead
  by `max_edge_geographic_km`, and optionally by `max_environmental_step`.

Every declared hypothesis is evaluated and retained. No hypothesis is selected by an
outcome, and none is dropped for being unfavourable.

## 4. Node states

Four states are distinguished, and `unsurveyed` is never merged into `surveyed_absent`:

- `current_occurrence`
- `historical_occurrence`
- `surveyed_absent`
- `unsurveyed`

The inference rule is:

> A pair is `unresolved` when it is reachable under the hypothesis, but **every** admissible
> route depends on at least one node that was never surveyed.

Reachability is therefore solved twice per source: once over all nodes, and once over
surveyed nodes only. A sampling gap can neither support nor exclude a route, so it produces
`unresolved` rather than a number that silently treats a blank as an absence.

An extinct intermediate (`historical_occurrence`) is surveyed information and keeps a route
resolvable. This is the difference between "we looked and it is gone" and "we never looked".

## 5. Returned statuses

The module returns hypothesis states, never calibrated probabilities:

| Status | Meaning |
|---|---|
| `supported` | the declared hypothesis admits a route through surveyed nodes |
| `weakly_supported` | admitted, but the best route's intermediate viability falls below a **declared** cutoff |
| `incompatible` | no admissible route exists under this hypothesis |
| `unresolved` | admitted only through unsurveyed nodes |

`weak_support_viability` is supplied by the caller. The module calibrates nothing against
observed occupancy, and `incompatible` is a statement about a declared hypothesis, never
about the species.

## 6. Frozen input rules

- `environmental_values` must already be expressed in a shared frozen reference. The module
  deliberately does not fit a scaling, because a scaling fitted here would silently change
  what one environmental step means between analyses.
- Viability is a per-node value in `[0, 1]` produced upstream and independently of the pairs
  being evaluated.
- Held-out labels never enter graph construction, viability, hypothesis declaration or the
  weak-support cutoff.
- Results carry a SHA-256 fingerprint over inputs, declared hypotheses and rows.

## 7. What this module does not do

It does not estimate colonisation, dispersal or migration probability; propagation here has
no calendar time. It does not reconstruct a historical route, and it does not identify which
route was used. It does not treat an occurrence pair as an edge that was actually traversed.
A `supported` status means the declared hypothesis can generate the observed configuration,
never that it did.

It also does not yet learn transition rules from occurrence configurations. That is the next
item and is deliberately absent here rather than approximated.

## 8. Synthetic discrimination status

Implemented and covered by `tests/test_traversable_state_space.py`:

- same endpoint environment with a continuous viable bridge;
- same endpoint environment with a niche desert;
- geographic barrier;
- environmental bottleneck invisible to endpoint IBE;
- viable versus unsuitable stepping stones;
- rare long-distance jump across an otherwise impassable gap;
- unsurveyed intermediate, on and off the route;
- extinct intermediate;
- endpoint IBD/IBE reported separately from pathwise discontinuity.

Not yet covered, and required before any empirical use:

- IBD-only, IBE-only and path-discontinuity ground truths evaluated as competing generative
  models rather than as separate assertions;
- directional truth, which needs the directed declaration exercised against an endpoint that
  actually carries direction;
- a negative control in which a strong reference already contains the truth and this layer
  must add nothing.

The negative control is mandatory. A layer that never retreats has not been tested.

## 9. Remaining items from the development target

Item 6 (estimating and comparing transition rules from occurrence configurations), the full
item 8 benchmark, item 9 (negative control) and item 10 (independent occurrence validation
as the primary empirical gate) are **not** addressed by this contract. They require their own
pre-outcome contracts.

Item 10 additionally carries a standing constraint: the independent occurrence gate has
already been executed once on this repository's v2 line and returned
`no_empirical_added_information` with `promotion_go=false`
(`docs/eog_v2_finland_strict_source_empirical_result.md`). That frozen result may not be
rerun, reweighted, reinterpreted or rescued by this layer. A new empirical gate for this
layer must use a separately frozen dataset and reference contract, and its result must be
reported alongside the existing NO-GO, not in place of it.
