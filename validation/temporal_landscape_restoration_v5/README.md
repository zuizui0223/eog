# Restoration and destruction duality on finite temporal landscapes (v5)

## Provenance

Protocol committed before scoring at b295f45ec52027acef6736951815920a3a444fbc; clarified the parallel witness text before scoring at 64ae21ac00902803ada9557ee11468fe3cbbf5a9 without changing the final declared paths, generator or estimands. Stacked on PR #762 head 31e4cc26a2c1aa76b27aecd201222f74b96c00f9 (both workflows passed). Actual local Python 3.13.5 run. Git blobs match local git hash-object: runner 919a121eb178cd34a0e32ee9592f548246ac7983, receipt 179013e14ad969c7a0123289e9d17027fe137ad6.

## Estimand and proof

Fix an intact finite temporal graph per world and a declared subset D of initially unavailable sites. Restore R subset D by returning exactly the original edges incident to available states; no change to any other edge, environmental state, time or barrier. F(K) denotes reachability after removing all time copies of K, for one world, at least one world, or every world. F is decreasing under set inclusion of K. Define the inclusion-minimal cut family C_D = min{K subset D: not F(K)} and restoration family A_D = min{R subset D: F(D minus R)}. Since a deletion destroys reachability iff it contains some minimal cut, F(D minus R) holds iff R intersects every member of C_D. Thus A_D is the blocker (minimal hitting sets) of C_D. Conversely C_D is the blocker of A_D. This is standard finite monotone Boolean duality, not new graph theory. It does not imply equal minimum cardinalities, nor symmetric restoration and degradation in nature.

Boundary conventions: empty cut family means no allowed cut; its blocker contains the empty restoration (no intervention). The cut family containing the empty set is an algebraic marker of intact infeasibility, not a physical destructive intervention; its blocker is empty. Never count an already-reachable target as needing restoration. The all-world repair objective permits a different complete path in each world, but requires the *same action set* to suffice in every world. It is a minimal union of one local restoration per world; the possible restoration family is the minimal union of local families without combining actions. If one world is intact-infeasible, all-world repair cannot succeed within this library. World sets and transitions remain frozen; no cross-world edge splicing. Reachability is not realized occupancy or demographic recovery.

## Synthetic results

240 systems x 3 worlds x 2 targets x 16 damage masks, new random seed 20261127 but same generator family as v4. Five boundary witnesses passed. 23,040 local reachability decisions versus DFS path signatures; 23,040 local restoration-family checks, 15,360 aggregate oracle and 15,360 aggregate identity checks, 76,800 bidirectional blocker checks, 76,800 boundary checks and 194,400 monotonicity checks; all assertions passed. These checks are dependent, not independent empirical replications.

Primary panel: all four intervention sites initially absent, compared with intact. Of 480 system-target pairs:

| Predicate | Already true even with all four absent | Intact-infeasible | Repair needed and feasible |
|---|---:|---:|---:|
| At least one world | 60 | 130 | 290 |
| Every world | 0 | 460 | 20 |

Among eligible pairs, minimum repair cardinality less/equal/greater than minimum destructive cut cardinality: possible 96/160/34 of 290; robust 0/2/18 of 20. Robust destruction means breaking all-world feasibility (at least one world fails), not destroying possibility everywhere. Possible destruction means eliminating all-world support (every world fails). Minimum costs here count sites, not money or actual effort.

Of 16 system-target pairs requiring both kinds of repair and feasible intact for both, robust minimum exceeds possible minimum in 15, and 10 have a singleton repair in each individual world but no common singleton across worlds. The other four of 20 robust-repair eligible pairs were already possible under full damage. This is a distinction between uncertainty about route identity and within-world serial dependence; the small 20 and 16 subsets are generator-specific, not estimates of nature. Unconditional robust feasibility was rare (20/480), a limitation of this sparse generator.

All damage states were preserved, including infeasible and no-action states. No empirical source, McKee GPS, sealed 2h outcome or new EOG-WF endpoint opened. Clock/CRS STOP and frozen 3 scored / 31 scientific STOP / 3 administrative exclusions unchanged.

## Replay and next gate

From repository root: python validation/temporal_landscape_restoration_v5/run.py . Compare with result.json. The runner uses fixed small-case constants and no production API. Full repository CI not yet verified. Real restoration can create novel edges, change persistence, or be irreversible, none of which is represented by this duality. Before more synthetic panels, consolidate v1-v5 and evaluate whether a scalable certificate and an independent real-data restoration design are warranted. Do not reopen the frozen EOG-WF candidate funnel.
