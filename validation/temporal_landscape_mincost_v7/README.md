# Minimum-cost temporal landscape interventions: exact decisions with bounded claims (v7)

## Provenance

Protocol frozen before scoring at 283a1b596706da8d1b617c904151e1dc5b08310d, stacked on PR #764 head 6e98ac74520aa1001d921c91cae01439fd1b20f4 (both CI workflows passed). Actual Python 3.13.5 execution and targeted pytest replay (1 passed). The Git runner and receipt blobs match local git hash-object: 55d10841ea91d38ad2e6d750d0163e24f5a2517d and de76e2218881e5df4c21f8b37914f0a5470d1720.

## Estimand and certificate

Unlike v6, output ONE feasible intervention and exact integer lower/upper cost bounds; do not claim to enumerate all minimal sets or all optima. A persistent site has a positive integer cost paid once, even if visited at multiple times. A restoration action enables all declared time copies. For a fixed nonempty collection of DAG worlds, possible means at least one world has a complete path; robust means every world has a complete path under the same selected sites (paths may differ). This is conditional reachability, not realized presence, demographics or measured financial costs.

For a search node, some sites are included and some banned. Scan reachability under included sites; if target is unreachable, every feasible completion must enable at least one unavailable, nonbanned site on the outgoing boundary of the reached set. Otherwise any complete path could not first leave this set. Optimistically enable every site in that boundary and repeat. Subsequent boundary sets are disjoint from earlier ones; each is a necessary hitting constraint even for a completion that enables only part of the earlier sets, since adding sites is monotone. If the target is not reached and the boundary is empty, the world cannot be completed. Thus the sum of minimum costs across disjoint boundary sets is a valid lower bound on additional cost. For robust feasibility, any disjoint packing of pooled world cuts also supplies a valid lower bound; take the maximum of that packing and the individual bounds. For possible feasibility, take the minimum lower bound over feasible worlds. The branch-and-bound splits on an undecided site, covering both included and excluded alternatives without omission. Feasible incumbent cost is an upper bound, and the least pending node bound (capped by incumbent) is a global lower bound. When these agree, the returned feasible action is optimal. Full-site infeasibility proves no allowed subset can succeed by monotonicity. The expansion cap can stop with a valid interval rather than a false optimum.

These are standard integer branch-and-bound, reachability cuts and disjoint packing, not new mathematical algorithms. Bounds are exact integer computations, conditional on the specified finite graph and action library; the implementation does not export a formal independently checkable proof trace, nor guarantee polynomial work. Cap limits expanded search nodes only, not all setup computation or time/memory. Input requirements: protected sources/targets, topological order, at most one restoration-site bit per vertex, shared positive integer costs, nonempty world universe. This is an isolated experimental runner, not a released API.

## Executed results

100 synthetic systems × 3 worlds × 256 site subsets = 76,800 independent reverse-search ground-truth masks. All 200 full decision tests matched exhaustive exact cost/infeasibility; 162 feasible optima, 38 infeasible. Another 200 zero-expansion tests had 55 exact, 107 bounded and 38 infeasible; every feasible witness and interval was verified against the oracle. Maximum full-search expansions 33; total 675. These are dependent decisions from a finite generator, not ecological replications.

Structured gateway cases: for 24, 48 and 96 sites, minimum possible cost 2 and minimum robust cost 14, all certified at root (0 expansions). Analytical ground truth: minimum gate plus minimum alternative vs all three gates plus minimum alternative. Binary-layer cases:

| Layers | Sites | Number of inclusion-minimal repairs (not enumerated) | Certified minimum cost | Expansions |
|---:|---:|---:|---:|---:|
| 12 | 24 | 4,096 | 39 | 0 |
| 24 | 48 | 16,777,216 | 81 | 0 |
| 48 | 96 | 281,474,976,710,656 | 166 | 0 |

Root lower/upper bound equality suffices in these deliberately structured examples, not arbitrary large graphs. No timing speedup claim against unrun enumeration. v6's 12-layer full-frontier STOP remains correct; v7 solves a different decision estimand rather than overriding that STOP.

The three-world triangle witness (each world needs one of two distinct site pairs) gives a verified cost interval [1,2] at cap=0; one expansion certifies [2,2]. All-world infeasibility and zero-action possible feasibility witnesses also pass.

## Next empirical gate

No additional synthetic scale panel is required as a default. Before an empirical intervention audit, prospectively freeze the source selection, distinguish observed restoration and modeled hypothetical action, declare coordinate/time/effort semantics, require independent support for directed transition worlds and common action costs or explicitly use hypothetical costs, and separate realized occupancy/detection from reachability. The closed EOG-WF three-endpoint programme must remain closed. No McKee clock/CRS STOP override, 2h response access, new biological source, or new empirical predictive endpoint occurred here. No conservation efficacy or real cost estimate follows from the synthetic results.

Replay from repository root: python validation/temporal_landscape_mincost_v7/run.py . The targeted test compares the complete result to the frozen receipt.
