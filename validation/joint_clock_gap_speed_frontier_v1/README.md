# Joint clock-gap/speed feasibility: synthetic finite-world audit

Protocol frozen at 57e6996c3aa71fede8914b762e230ac933543ff0 before scoring; runner 5a2f1f07dbadc4b1cbdc07f95b671bae419963df. Base main 39bf420cc83465165678c2f202b11ba8ea250e6d. Python 3.13.5 local replay used exact Git blob identities for both inputs. Archived result SHA-256: e2390b48ae0cd948bb764374b9083dbca57d8cc9fc4e810840e337880b9cedd7.

## Estimand

Given one declared clock/geometry world, ordered fixes have finite timestamp sets T_i and fixed segment distances d_i. A schedule is feasible when all timestamps belong to their respective sets and, jointly, 1 <= dt_i <= G and d_i <= V*dt_i. G is the maximum allowed time gap; V is the maximum required *minimum straight-line average speed* bound in synthetic units. Actual path length, behavior, persistence and instantaneous speed are not inferred. The minimal feasible (G,V) pairs are Pareto points on the frozen 6x6 grid, not a continuous frontier.

Possible means exists a whole world with a whole schedule; robust-feasible means every declared world has at least one whole schedule, not one common schedule shared by all worlds. Forward propagation retains the reachable times of the current fix; induction proves exactness because only consecutive constraints occur. Do not splice edges between clock worlds, or replace nonconvex timestamp domains with their hull.

## Frozen results

All five deliberately constructed existence/boundary hypotheses pass. The 500 single-world stress cases times 36 grid pairs produce 18,000 exact oracle comparisons, zero disagreements and zero relaxation monotonicity violations. Independent local edge tests falsely accept 2,328 grid/world pairs in 176 worlds; hull filling falsely accepts 1,485 in 155 worlds. Counts overlap and are generator-specific, not real GPS error rates.

| Case | Possible grid frontier (G,V) | Robust grid frontier | Key finding |
| --- | --- | --- | --- |
| Tradeoff | (2,3), (3,2) | same | axiswise minimum (2,2) infeasible |
| Nonconvex time | (3,1) | same | hull adds six false grid pairs; local edge test adds twelve |
| World splice | (3,3) | same | 16 extra false grid pairs from mixing worlds |
| Quantifier | (2,1) | (3,2) | a favorable clock is not an all-clock certificate |
| Reversed order | empty | empty | no tested relaxation restores chronology |

The result is a methods-only synthetic extension of the existing McKee source-QC findings and minimum required relaxation line. Neither dynamic programming, path feasibility, Pareto dominance nor these constructed counterexamples establish new mathematics or empirical improvement. No McKee data, dense holdout, movement score, or new candidate endpoint was accessed. Source clock/CRS STOP remains. Frozen EOG-WF 3 scored / 31 scientific STOP / 3 administrative exclusions unchanged.

## Reproduce

From this directory: `python run.py protocol_v1.json`. Compare its JSON with result_v1.json. Random stress counts are archived for the executed Python version; cross-version replay should not silently replace that receipt.
