# Joint gap–speed frontier under uncertain observation clocks (synthetic v1)

Protocol committed before execution: [57e6996](https://github.com/zuizui0223/eog/commit/57e6996c3aa71fede8914b762e230ac933543ff0). Base main: 39bf420cc83465165678c2f202b11ba8ea250e6d.

## Estimand

For a single declared world w with ordered nonempty finite timestamp sets T_i and fixed nonnegative inter-record distances d_i, require one shared schedule t_i in T_i such that every consecutive pair satisfies 1 <= t_(i+1)-t_i <= G and d_i <= V*(t_(i+1)-t_i). G is the permitted upper gap; V is the permitted upper average speed, not a fitted movement speed. The possible grid frontier requires some entire world to have a schedule; the robust feasible grid frontier requires every world to have a schedule (schedules may differ between worlds). Neither is an actual observed trajectory. No world- or edge-wise splicing is allowed.

For each fixed G,V, forward reachable-time propagation is exact by induction: its set after record i contains precisely the final timestamps of feasible prefixes through i. The union over worlds of *whole-schedule* existence need not equal the conjunction over edges of local existence across worlds. This is standard finite constraint propagation and Pareto filtering, not a new mathematical algorithm.

## Local execution results

Run with Python standard library, seed 20261125, the five frozen canonical cases and 500 frozen-generator worlds. The local replay used the same protocol case/grid/seed fields; no source GPS or heldout data were accessed. The branch's complete protocol is available alongside the runner.

| Case | Possible frontier (G,V) | Robust feasible frontier (G,V) |
|---|---|---|
| tradeoff | (2,3), (3,2) | (2,3), (3,2) |
| nonconvex | (3,1) | (3,1) |
| world_splice | (3,3) | (3,3) |
| quantifier | (2,1) | (3,2) |
| order_impossible | empty | empty |

All five predeclared synthetic witness checks passed. Tradeoff marginal minima (2,2) are jointly infeasible. Nonconvex case adds six false grid pairs when holes in the clock domain are filled. World-splice case adds 16 false grid pairs relative to within-world local feasibility; neither declared whole world can satisfy (3,1).

| Stress result | Count |
|---|---:|
| Generated single worlds | 500 |
| Forward vs complete timestamp assignment oracle comparisons | 18,000 |
| Disagreements | 0 |
| Increasing-budget monotonicity violations | 0 |
| Worlds with at least one false pairwise-feasible grid point | 176 |
| False pairwise-feasible grid points | 2,328 |
| Worlds with at least one false hull-feasible grid point | 155 |
| False hull-feasible grid points | 1,485 |

The two error sets may overlap. Counts are generator-specific, and grid pairs within each world are dependent. They are not natural movement-error rates. These are arithmetic integrity and synthetic counterexample checks; they do not establish field predictive improvement. The scope is a fixed ordered consecutive-record chain with integer time domains and supplied distances, not arbitrary graph routes, time-zone inference, partition selection, a continuous-parameter certificate, or actual movement speed.

## Replay

From repository root:

```sh
python validation/joint_clock_gap_speed_frontier_v1/run.py validation/joint_clock_gap_speed_frontier_v1/protocol_v1.json
```

The branch contains an isolated benchmark, not a production EOG API change. Repository-wide tests/CI not claimed. No McKee data accessed; source clock and CRS STOP remain. No dense 2h holdout opened. Frozen EOG-WF denominator remains 3 scored / 31 scientific STOPs / 3 administrative exclusions. A finite grid frontier must not be marketed as a continuous minimum speed. Any real application requires separately authenticated clock, CRS, distance and observation model.
