# Time-expanded landscape: persistent-site versus single-time-state knockout

## Provenance and boundaries

Stacked on draft PR #760, head f4907bcaf1c46dea561f4e572db87f251a44326e (both workflows passed). Protocol initially committed at 25d2be07cd4d3c9b1579144f6c4f9c06d25158bf; before any scoring, corrected canonical witness 30->43 (distance 3 per one time unit exceeds V=2) to 33->43, retaining all thresholds and the generator, at 0277208e8fd1b7a37b17154d0ae4855bcd955657. Local Python 3.13.5 execution; runner and result Git blobs match 9247b2d8025f4b5f01923a5608a122ca3165c01c and a3773c78c4802a8a2ebe840ec8d3f11b8a58e5bc. Result SHA256 a122aafdb32a0695f45a25d099c9fd3c0051785b15a999574928238ebc8cb9de.

## Estimands

On a finite common time/site registry, each world has its own directed forward-time edges. Edges obey frozen duration, straight-line speed, environmental transition and barrier bounds; waits require explicit edges. Reachability is exact-time, not demographic persistence or occupancy. A site knockout deletes all its time copies; a state knockout deletes only one copy. The source and scored terminal targets are never deleted. A world-target-site triple is critical when the target was reachable before and is not after site deletion. Time-flexible criticality additionally requires that each individual intermediate copy deletion leaves at least one feasible path in that world. This is not resilience to simultaneous deletion of several time copies.

Across worlds, compute possible (union) and robust (intersection) only AFTER per-world propagation. A conditional all-support-world critical site makes a previously possible target impossible. A robust-initial target can lose robustness yet remain possible if only some supporting worlds lose it. A robust-initial all-support-world critical site has no common critical state if no single intermediate copy deletion removes the target from *all* originally supporting worlds; individual worlds may still have their own critical states.

For edge sets E_w and fixed source, reach(intersection E_w) is a subset of intersection reach(E_w); union reach(E_w) is a subset of reach(union E_w). Both inclusions can be strict. A path in a union graph can splice incompatible worlds; a robust target does not require a shared path in every world. These are standard graph facts, not new mathematics.

## Exact synthetic replay

All four canonical checks passed. 160 two-world systems, 320 worlds, 20 nodes and 15 interventions (none, 12 single-time, two persistent site removals). 4,800 world/intervention reachable-set checks against independent enumeration of all path prefixes and 4,800 projection checks; zero disagreements and deletion monotonicity violations. Necessity in every initially supported world-target-site case also checked against whether every enumerated target path intersects the cut.

| Result | Count and denominator |
|---|---|
| Persistent-site critical | 161/474 initially reachable world-target-site combinations |
| Persistent-site critical without a single critical time copy | 9/161 critical combinations |
| All supporting worlds lose a previously possible target after site removal | 104/374 initially possible system-target-site combinations |
| Initially robust target lost in at least one world | 57/100 initially robust system-target-site combinations |
| Initially robust target remains possible but not robust | 48/100 |
| Initially robust target lost in both worlds | 9/100 |
| Both worlds lose initially robust target, no single time copy suffices to eliminate both | 4/9 |
| Union-edge graph spuriously reaches target | 73/320 system-target pairs (65/160 systems) |
| Intersection-edge graph misses an initially robust target | 43/50 initially robust system-target pairs (36/160 systems have a miss) |

These frequencies are specific to the frozen sparse synthetic random generator. Combinations are dependent, not ecological replicates. The across-world robust count for site interventions is twice the baseline target count because two removal sites share the same unchanged target set. In particular, 43/50 is not an empirical failure rate. No real-data source, sealed 2h GPS or biological outcome opened. McKee clock/CRS STOP and EOG-WF 3 scored / 31 scientific STOP / 3 administrative exclusions unchanged.

## Replay and limits

Run from repository root: python validation/temporal_landscape_knockout_v3/run.py . Compare JSON to result.json. The isolated runner uses frozen constants; the regression checks protocol registry and constraints against those constants and replays the receipt. No production API, uncertain movement parameters, scalable GIS ingestion, multi-site minimum cut, or real conservation impact established. The next question is minimal groups of site removals, with temporal and world-quantifier distinctions preserved, not more synthetic tuning to enlarge a positive count.
