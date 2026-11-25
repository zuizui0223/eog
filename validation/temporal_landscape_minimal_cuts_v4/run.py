"""Exact finite temporal landscape site-cut audit (synthetic only)."""
from collections import Counter, defaultdict
from itertools import product
import json
import random

NODES = tuple(product(range(5), range(6)))
SOURCE = (0, 0)
TARGETS = ((4, 0), (4, 5))
SITES = (1, 2, 3, 4)
MASKS = tuple(range(1 << len(SITES)))
BITS = {s: 1 << i for i, s in enumerate(SITES)}


def generate(rng):
    env = {n: rng.randint(0, 3) for n in NODES}
    edges = []
    for a in NODES:
        for b in NODES:
            dt = b[0] - a[0]
            if 1 <= dt <= 2 and rng.random() < 0.40:
                barrier = rng.randint(0, 2)
                hard = rng.random() < 0.10
                if (not hard and abs(b[1]-a[1]) <= 2*dt
                        and abs(env[b]-env[a]) <= 2 and barrier <= 1):
                    edges.append((a, b))
    return tuple(edges)


def adjacency(edges):
    out = defaultdict(list)
    for a, b in edges:
        assert 1 <= b[0]-a[0] <= 2
        assert abs(b[1]-a[1]) <= 2*(b[0]-a[0])
        out[a].append(b)
    return out


def reach(out, mask):
    r = {SOURCE}
    for a in NODES:
        if a in r:
            r.update(b for b in out[a] if not mask & BITS.get(b[1], 0))
    return r


def path_signatures(out):
    """Independent DFS of every full source-target path, without label pruning."""
    sig = {t: set() for t in TARGETS}

    def walk(a, visited):
        if a in sig:
            sig[a].add(visited)
        for b in out[a]:
            walk(b, visited | BITS.get(b[1], 0))
    walk(SOURCE, 0)
    return sig


def minimal(masks):
    m = set(masks)
    return {a for a in m if not any(b != a and (b & a) == b for b in m)}


def oracle_cuts(signatures):
    if not signatures:
        return set()
    return minimal(m for m in MASKS if all(m & s for s in signatures))


def from_reached(rows, target):
    return minimal(m for m in MASKS if target not in rows[m]) if target in rows[0] else set()


def combine_all(families):
    if not families:
        return set()
    result = {0}
    for f in families:
        result = minimal(a | b for a in result for b in f)
    return result


def solve(edges, counts):
    outs = [adjacency(e) for e in edges]
    rows = [[reach(out, m) for m in MASKS] for out in outs]
    sigs = [path_signatures(out) for out in outs]
    for row, sig in zip(rows, sigs, strict=True):
        for m in MASKS:
            for target in TARGETS:
                expected = any(not m & s for s in sig[target])
                assert (target in row[m]) == expected
                counts['reachability_oracle_checks'] += 1
            for j in MASKS:
                if m & j == m:
                    assert row[j] <= row[m]
                    counts['subset_monotonicity_checks'] += 1
    results = {}
    for t in TARGETS:
        support = [i for i, row in enumerate(rows) if t in row[0]]
        local = [from_reached(row, t) for row in rows]
        for f, sig in zip(local, sigs, strict=True):
            assert f == oracle_cuts(sig[t])
            counts['local_frontier_checks'] += 1
        possible = (minimal(m for m in MASKS if all(t not in rows[i][m] for i in support))
                    if support else set())
        robust = (minimal(m for m in MASKS if any(t not in row[m] for row in rows))
                  if len(support) == len(rows) else None)
        union_sig = set().union(*(sigs[i][t] for i in support))
        assert possible == oracle_cuts(union_sig)
        assert possible == combine_all([local[i] for i in support])
        counts['possible_frontier_checks'] += 2
        if robust is not None:
            assert robust == minimal(set().union(*(oracle_cuts(s[t]) for s in sigs)))
            assert robust == minimal(set().union(*local))
            counts['robust_frontier_checks'] += 2
        for i in support:
            f = local[i]
            counts['world_target_supported'] += 1
            counts['world_target_uncuttable'] += not f
            counts['world_target_any_higher_order'] += any(m.bit_count() > 1 for m in f)
            counts['world_target_only_higher_order'] += bool(f) and all(m.bit_count() > 1 for m in f)
        counts['system_target_total'] += 1
        counts['system_target_possible'] += bool(support)
        counts['system_target_robust'] += robust is not None
        if support:
            counts['possible_loss_uncuttable'] += not possible
            counts['possible_loss_any_higher_order'] += any(m.bit_count() > 1 for m in possible)
            counts['possible_loss_only_higher_order'] += bool(possible) and all(m.bit_count() > 1 for m in possible)
            counts['possible_loss_multiple_minimal_cuts'] += len(possible) > 1
            if possible:
                counts[f'possible_min_size_{min(m.bit_count() for m in possible)}'] += 1
        if robust is not None:
            counts['robust_loss_uncuttable'] += not robust
            counts['robust_loss_any_higher_order'] += any(m.bit_count() > 1 for m in robust)
            counts['robust_loss_only_higher_order'] += bool(robust) and all(m.bit_count() > 1 for m in robust)
            counts['robust_loss_but_not_possible_loss'] += bool(robust) and not possible
            counts['different_loss_frontiers'] += robust != possible
            counts['cross_world_only_higher_order'] += (bool(possible) and all(m.bit_count() > 1 for m in possible)
                and all(any(m.bit_count() == 1 for m in local[i]) for i in support))
        results[t] = (local, possible, robust)
    return results


def chain(*v):
    return tuple(zip(v, v[1:]))


def canonical():
    target = (4, 5)
    a = chain(SOURCE, (1, 1), (2, 3), target)
    b = chain(SOURCE, (1, 2), (3, 4), target)
    cross = {BITS[i] | BITS[j] for i in (1, 3) for j in (2, 4)}
    cases = {}
    l, p, r = solve([a+b], Counter())[target]
    assert l == [cross] and p == r == cross
    cases['redundant_paths'] = sorted(p)
    l, p, r = solve([a, b, a], Counter())[target]
    assert p == cross and r == set(BITS.values())
    cases['world_difference'] = {'possible_loss': sorted(p), 'robust_loss': sorted(r)}
    direct = chain(SOURCE, (2, 0), (4, 0))
    detour = chain(SOURCE, (1, 1), (2, 0), (4, 0))
    l, p, r = solve([direct, detour, detour], Counter())[(4, 0)]
    assert not p and r == {BITS[1]}
    cases['uncuttable'] = {'possible_loss': sorted(p), 'robust_loss': sorted(r)}
    l, p, r = solve([(), (), ()], Counter())[target]
    assert not any(l) and not p and r is None
    cases['unsupported'] = True
    return cases


def audit():
    cases = canonical()
    rng = random.Random(20261126)
    counts = Counter()
    for _ in range(180):
        solve([generate(rng) for _ in range(3)], counts)
    return {'canonical': cases, 'stress': {'systems': 180, 'worlds': 540,
            'site_subsets': 16, **dict(sorted(counts.items())), 'oracle_disagreements': 0,
            'monotonicity_violations': 0}, 'scope': 'synthetic finite graph; EOG-WF 3/31/3 unchanged'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
