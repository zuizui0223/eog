# Consolidated temporal EOG methods line: v1–v6

Status: draft experimental methods only; not main/release or a new ecological discovery. Source receipts are fixed in the stacked PRs, not pooled across panels. PR #759–#763 are the parent sequence. The frozen EOG-WF prediction programme stays closed at 3/31/3.

| Stage | Estimand and evidence | Boundary |
|---|---|---|
| [v1](../joint_clock_gap_speed_frontier_v1/result_v1.json) (#759) | Shared timestamp schedule for gap/speed bounds; 18,000 oracle checks, 176/500 worlds have pairwise-only false positives | Fixed ordered chain; finite grid; no physical speed |
| [v2](../temporal_path_pareto_v2/result.json) (#760) | Exact rational path bound frontier; 960 world/aggregate oracle checks; 96/480 have independently reachable checkpoint and endpoint but no coherent checkpoint path | Single trajectory constraint, not separate population establishment |
| [v3](../temporal_landscape_knockout_v3/result.json) (#761) | Persistent site vs single time-copy knockout; 161/474 supported triples critical, 9/161 lack a single critical time copy; union-edge graph falsely supports 73/320 targets | Fixed finite worlds, no true habitat removal effect |
| [v4](../temporal_landscape_minimal_cuts_v4/result.json) (#762) | Minimal persistent cut families; 72/256 possible targets require at least two sites, 32/256 uncuttable; 15 initially robust targets have distinct loss frontiers | Four-action library; inclusion-minimal not necessarily cheapest |
| [v5](../temporal_landscape_restoration_v5/result.json) (#763) | Exact blocker duality; 76,800 checks; 18/20 all-world repair eligible targets need more sites than a minimum destructive cut | 460/480 intact all-world infeasible; exact reversal of declared graph, not real regeneration |
| [v6](result.json) | Exact antichain pruning and transversals; 800 frontier checks, 96-site structured success, 24-site exponential STOP | Not general scalable full enumeration; no new biological endpoint |

The unifying estimand is a family of reachable states and action requirements conditional on a frozen set of whole ecological worlds. Distinct pathwise constraints (v1/v2), temporal geometry (v3), loss predicates (v4) and restoration predicates (v5) must not be collapsed into a scalar score or one consensus graph. v6 computes the same finite restoration/cut objects without full action-subset enumeration. The stages are distinct demonstrations, not independent ecological replications, and their denominators must not be added to claim empirical accuracy.

Publication boundary: this experimental extension is not needed to change the closed EOG-WF submission claim. It can inform a separately scoped methods development only. No production integration or main merge is implied. Independent real-data use requires a new frozen observation/transition/action contract and evidence that the candidate-world family is biologically meaningful; synthetic correctness alone cannot establish that. Prioritize a decision-specific computational certificate and an empirical source-qualification gate over further broad synthetic searches.
