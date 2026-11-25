# Minimal persistent site-removal sets across temporal worlds (v4)

Protocol frozen before scoring at a4cb440088462e95eeddde75b1c7590277382080. Stacked on PR #761 head 0cfe24aa963b5cb645a6d78ebdfa57947970f003. Local Python 3.13.5 actual execution; runner and receipt Git blobs independently matched local git hash-object (c41e7e88c16d33adc33c392f3b54110f4e6f95cb, 0201822d0dc9bd801179d83c060069b96afc1ea0). Targeted regression: 1 passed locally. No new ecological data or EOG-WF endpoints.

## Exact finite estimands

Use a common 5-time by 6-site registry, fixed source, two protected terminal targets, four removable sites. Each world independently supplies a time-directed graph, with explicit same-site waiting and frozen distance/time, environmental and barrier limits. A persistent deletion removes every time copy of each selected removable site. It cannot delete the source or evaluated targets. Reachability is not realized occupancy or a demographic persistence model.

For each target initially reachable in world w, let C_w be the family of inclusion-minimal site deletion sets that eliminate reachability in that world. For a nonempty set of supporting worlds, the minimal deletions making the target no longer possible are minimal unions of one member of C_w from every supporting world. If any supporting world has no allowable cut, no such aggregate cut exists. For a target initially reached in *every* world, the minimal deletions destroying robustness are the inclusion-minimal elements of the union of C_w over all worlds. Do not report a vacuous empty cut for an initially unsupported target, nor loss of robustness for an initially nonrobust target.

Proof: in a finite deletion lattice, every deletion that destroys a world's reachability contains at least one minimal cut in that world. Deleting extra sites cannot restore reachability. To eliminate all support, a deletion must therefore contain one cut from each supporting world, hence their union; to eliminate at least one world's support, it must contain a cut from some world. Removing dominated supersets gives the exact respective frontiers. These are standard monotone Boolean/hitting-set facts, not new graph theory. Persistent-site cuts are grouped removals of time copies rather than single-state minimum cuts. Inclusion-minimal does not imply minimum cardinality or minimum financial cost.

## Actual frozen results

180 systems x 3 worlds = 540 worlds; all 16 deletion subsets, 2 targets. All four constructed witnesses passed. Exact direct propagation versus independent DFS path signatures: 17,280 target reachability decisions, 43,740 subset monotonicity checks, 1,080 local minimal-frontier checks, 720 possible-loss frontier checks, 30 robust-loss frontier checks. No disagreement or monotonicity violation.

| Outcome | Count |
|---|---:|
| Initially supported world-target pairs | 363/1080 |
| Of those, some cut but no singleton cut | 37/363 |
| Initially possible system-target pairs | 256/360 |
| Minimum all-support cut size 1 | 152/256 |
| Minimum all-support cut size 2 | 62/256 |
| Minimum all-support cut size 3 | 10/256 |
| No all-support cut within declared library | 32/256 |
| Multiple inclusion-minimal all-support cuts | 61/256 |
| Initially robust system-target pairs | 15/360 |
| Possible-loss and robust-loss frontiers differ | 15/15 |
| All-support cut requires multiple sites although each world has a singleton cut | 8/15 |
| Can destroy robustness but cannot destroy possibility with any allowed deletion | 3/15 |

The latter 15 initially robust pairs are a small subset, not independent empirical observations. All counts are generator-specific, and within-system pairs are dependent. In the canonical split-world witness, each world has one of two disjoint routes. Any-world loss minimal sets are four singletons; all-world loss minimal sets are four cross-route pairs. Thus distributed redundancy arises both within worlds and from unresolved world identity; the corresponding intervention objectives must not be conflated.

## Replay and limitations

Run from repository root: python validation/temporal_landscape_minimal_cuts_v4/run.py . Compare with result.json; targeted test replays the full receipt. The runner uses constants matching the frozen protocol, not a generic production interface. Exhaustive subset and path enumeration is suitable for this small library only; large landscapes may require bounded or certified hitting-set search. Interventions mean hypothetical edge/node availability removal under frozen world assumptions, not a measured conservation effect. No empirical movement or conservation efficacy claim. No McKee data, 2h holdout, or new source was opened; source clock/CRS STOP and frozen EOG-WF 3/31/3 unchanged.
