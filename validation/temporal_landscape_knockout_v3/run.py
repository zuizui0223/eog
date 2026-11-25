"""Synthetic finite time-expanded reachability and site/state knockout audit."""
from collections import defaultdict
import json
import random

NODES = tuple((t, s) for t in range(5) for s in range(4))
SOURCE = (0, 0)
TARGETS = ((4, 0), (4, 3))
STATES = tuple(n for n in NODES if 1 <= n[0] <= 3)
SITES = (1, 2)
CUTS = (frozenset(),) + tuple(frozenset({n}) for n in STATES) + tuple(
    frozenset(n for n in NODES if n[1] == s) for s in SITES
)


def reached(edges, cut=frozenset()):
    """Topological forward propagation in one complete world."""
    r = {SOURCE}
    for a in NODES:
        if a in r:
            r.update(b for u, b in edges if u == a and b not in cut)
    return r


def enumerate_paths(edges):
    """Independent DFS: retain every prefix, not just reachable vertices."""
    outgoing = defaultdict(list)
    for a, b in sorted(edges):
        outgoing[a].append(b)
    paths = defaultdict(list)
    def visit(path):
        paths[path[-1]].append(frozenset(path))
        for b in outgoing[path[-1]]:
            visit(path + (b,))
    visit((SOURCE,))
    return paths


def oracle(paths, cut):
    return {n for n, prefixes in paths.items() if any(not (p & cut) for p in prefixes)}


def projection(sets):
    return set.union(*sets), set.intersection(*sets)


def all_support_lost(before, after, target):
    supporting = [i for i, r in enumerate(before) if target in r]
    return bool(supporting) and all(target not in after[i] for i in supporting)


def generate(rng):
    env = {n: rng.randint(0, 3) for n in NODES}
    edges = set()
    for a in NODES:
        for b in NODES:
            dt = b[0] - a[0]
            if 1 <= dt <= 2 and rng.random() < 0.40:
                barrier = rng.randint(0, 2)
                hard = rng.random() < 0.10
                if not hard and abs(b[1]-a[1]) <= 2*dt and abs(env[b]-env[a]) <= 2 and barrier <= 1:
                    edges.add((a, b))
    return edges


def chain(*nodes):
    return set(zip(nodes, nodes[1:]))


def canonical():
    target = (4, 3)
    a = chain(SOURCE, (1, 1), (3, 2), target)
    b = chain(SOURCE, (2, 1), (3, 3), target)
    site = CUTS[-2]
    for u, v in a | b:
        assert 1 <= v[0]-u[0] <= 2 and abs(v[1]-u[1]) <= 2*(v[0]-u[0])
    assert target in reached(a | b) and target not in reached(a | b, site)
    assert all(target in reached(a | b, frozenset({n})) for n in STATES if n[1] == 1)
    assert target in projection([reached(a), reached(b)])[1]
    assert target not in reached(a & b)
    assert all_support_lost([reached(a), reached(b)], [reached(a, site), reached(b, site)], target)
    c = chain(SOURCE, (2, 1))
    d = chain((2, 1), target)
    assert target not in projection([reached(c), reached(d)])[0]
    assert target in reached(c | d)
    assert not all_support_lost([reached(c), reached(d)], [reached(c, site), reached(d, site)], target)
    return {"time_flexible": True, "across_worlds": True, "splice": True, "no_support": True}


def audit():
    witnesses = canonical()
    counts = dict.fromkeys([
        "world_intervention_checks", "projection_checks", "world_target_site_support",
        "world_target_site_critical", "world_target_site_time_flexible",
        "system_target_site_support", "conditional_all_world_site_critical",
        "robust_initial_target_site_support", "robust_initial_all_world_site_critical",
        "robust_initial_all_world_site_critical_no_common_state",
        "possible_target_losses", "robust_target_losses", "robust_lost_possible_retained",
        "union_false_target_pairs", "intersection_missed_robust_target_pairs",
        "systems_with_union_false", "systems_with_intersection_miss",
        "deletion_monotonicity_violations", "oracle_disagreements"
    ], 0)
    rng = random.Random(20261126)
    for _ in range(160):
        edges = [generate(rng) for _ in range(2)]
        paths = [enumerate_paths(e) for e in edges]
        r = [[reached(e, cut) for cut in CUTS] for e in edges]
        o = [[oracle(p, cut) for cut in CUTS] for p in paths]
        for i in range(2):
            for k in range(len(CUTS)):
                assert r[i][k] == o[i][k]
                assert r[i][k] <= r[i][0]
                counts["world_intervention_checks"] += 1
        proj = [projection([r[0][k], r[1][k]]) for k in range(len(CUTS))]
        for k, (p, q) in enumerate(proj):
            assert p == o[0][k] | o[1][k]
            assert q == o[0][k] & o[1][k]
            assert p <= proj[0][0] and q <= proj[0][1]
            counts["projection_checks"] += 2
        base_p, base_r = proj[0]
        false_union = (reached(edges[0] | edges[1]) - base_p) & set(TARGETS)
        missed_intersection = (base_r - reached(edges[0] & edges[1])) & set(TARGETS)
        counts["union_false_target_pairs"] += len(false_union)
        counts["intersection_missed_robust_target_pairs"] += len(missed_intersection)
        counts["systems_with_union_false"] += bool(false_union)
        counts["systems_with_intersection_miss"] += bool(missed_intersection)
        for j, site in enumerate(SITES):
            k = 1 + len(STATES) + j
            state_indices = [i+1 for i,n in enumerate(STATES) if n[1] == site]
            for target in TARGETS:
                for i in range(2):
                    if target not in r[i][0]:
                        continue
                    counts["world_target_site_support"] += 1
                    critical = target not in r[i][k]
                    assert critical == all(bool(p & CUTS[k]) for p in paths[i][target])
                    counts["world_target_site_critical"] += critical
                    counts["world_target_site_time_flexible"] += critical and all(target in r[i][h] for h in state_indices)
                before = [r[i][0] for i in range(2)]
                after = [r[i][k] for i in range(2)]
                necessary = all_support_lost(before, after, target)
                assert necessary == (target in base_p and target not in proj[k][0])
                counts["system_target_site_support"] += target in base_p
                counts["conditional_all_world_site_critical"] += necessary
                counts["robust_initial_target_site_support"] += target in base_r
                counts["robust_initial_all_world_site_critical"] += target in base_r and necessary
                if target in base_r and necessary:
                    counts["robust_initial_all_world_site_critical_no_common_state"] += all(not all_support_lost(before, [r[i][h] for i in range(2)], target) for h in state_indices)
                counts["possible_target_losses"] += target in base_p and target not in proj[k][0]
                counts["robust_target_losses"] += target in base_r and target not in proj[k][1]
                counts["robust_lost_possible_retained"] += target in base_r and target not in proj[k][1] and target in proj[k][0]
    return {"canonical": witnesses, "stress": {"systems": 160, "worlds": 320, "interventions": len(CUTS), **counts}, "scope": "synthetic finite graph; no empirical scoring; EOG-WF 3/31/3 unchanged"}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
