"""Exact finite restoration/cut duality; synthetic time-expanded graphs only."""
from collections import Counter, defaultdict
from itertools import product
import json
import random

NODES = tuple(product(range(5), range(6)))
SOURCE = (0, 0)
TARGETS = ((4, 0), (4, 5))
SITES = (1, 2, 3, 4)
BITS = {s: 1 << i for i, s in enumerate(SITES)}
FULL = 15
MASKS = tuple(range(FULL + 1))
SUB = {d: tuple(r for r in MASKS if r & d == r) for d in MASKS}


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
    return edges


def prepare(edges):
    out = defaultdict(list)
    for a, b in edges:
        assert 1 <= b[0]-a[0] <= 2 and abs(b[1]-a[1]) <= 2*(b[0]-a[0])
        out[a].append(b)
    return out


def reached(out, damage):
    r = {SOURCE}
    for a in NODES:
        if a in r:
            r.update(b for b in out[a] if not BITS.get(b[1], 0) & damage)
    return r


def signatures(out):
    result = {t: set() for t in TARGETS}

    def visit(a, mask):
        if a in result:
            result[a].add(mask)
        for b in out[a]:
            visit(b, mask | BITS.get(b[1], 0))
    visit(SOURCE, 0)
    return result


def minimal(items):
    s = set(items)
    return {a for a in s if not any(b != a and a & b == b for b in s)}


def combine(families):
    r = {0}
    for f in families:
        r = minimal(a | b for a in r for b in f)
    return r


def repair(truth, d):
    return minimal(r for r in SUB[d] if truth[d ^ r])


def cuts(truth, d):
    return minimal(k for k in SUB[d] if not truth[k])


def blocker(c, d):
    return minimal(r for r in SUB[d] if all(r & k for k in c))


def size(family):
    return min(x.bit_count() for x in family)


def solve(edges, counts):
    outs = [prepare(e) for e in edges]
    rows = [[reached(o, d) for d in MASKS] for o in outs]
    sig = [signatures(o) for o in outs]
    output = {}
    for t in TARGETS:
        local = [[t in row[d] for d in MASKS] for row in rows]
        ps = [any(x) for x in zip(*local)]
        rs = [all(x) for x in zip(*local)]
        truths = local + [ps, rs]
        names = ['local']*len(local) + ['possible', 'robust']
        for truth, s in zip(local, sig, strict=True):
            for d in MASKS:
                assert truth[d] == any(not (m & d) for m in s[t])
                counts['local_reach_checks'] += 1
        for truth, name in zip(truths, names, strict=True):
            for d in MASKS:
                for k in SUB[d]:
                    assert not truth[d] or truth[k]
                    counts['monotonicity_checks'] += 1
                f = repair(truth, d)
                c = cuts(truth, d)
                assert f == blocker(c, d)
                assert c == blocker(f, d)
                counts['duality_checks'] += 2
                assert (not f) == (not truth[0])
                assert (f == {0}) == truth[d]
                counts['boundary_checks'] += 2
                status = 'already' if truth[d] else ('repair_needed' if truth[0] else 'infeasible')
                counts[f'{name}_all_damage_{status}'] += 1
            if name != 'local':
                if truth[0] and not truth[FULL]:
                    a, b = size(cuts(truth, FULL)), size(repair(truth, FULL))
                    counts[f'{name}_eligible'] += 1
                    counts[f'{name}_cut_{a}_repair_{b}'] += 1
                    relation = 'greater' if b > a else ('less' if b < a else 'equal')
                    counts[f'{name}_repair_{relation}'] += 1
                else:
                    status = 'already' if truth[FULL] else 'infeasible'
                    counts[f'{name}_full_damage_{status}'] += 1
        for d in MASKS:
            lr = [repair(truth, d) for truth in local]
            independent = [minimal(m & d for m in s[t]) for s in sig]
            assert lr == independent
            counts['local_repair_oracle_checks'] += len(lr)
            p, r = repair(ps, d), repair(rs, d)
            assert p == minimal(set().union(*independent))
            assert r == combine(independent)
            counts['aggregate_oracle_checks'] += 2
            assert p == minimal(set().union(*lr)) and r == combine(lr)
            counts['aggregate_identity_checks'] += 2
        p, r = repair(ps, FULL), repair(rs, FULL)
        if p and r and p != {0} and r != {0}:
            counts['both_repair_needed'] += 1
            assert size(r) >= size(p)
            counts['robust_larger_than_possible'] += size(r) > size(p)
            lr = [repair(truth, FULL) for truth in local]
            counts['each_world_singleton_but_no_common_singleton'] += (
                all(f and size(f) == 1 for f in lr) and size(r) > 1)
        output[t] = {'possible_repair': sorted(p), 'robust_repair': sorted(r),
                     'possible_cut': sorted(cuts(ps, FULL)), 'robust_cut': sorted(cuts(rs, FULL))}
    return output


def chain(*v):
    return list(zip(v, v[1:]))


def canonical():
    a = chain(SOURCE, (1, 1), (2, 3), (4, 5))
    b = chain(SOURCE, (1, 1), (2, 0), (4, 0))
    c = chain(SOURCE, (1, 2), (2, 0), (4, 0))
    direct = chain(SOURCE, (2, 0), (4, 0))
    results = {
        'serial': solve([a], Counter())[(4, 5)],
        'parallel': solve([b+c], Counter())[(4, 0)],
        'world_disagreement': solve([b, c, b], Counter())[(4, 0)],
        'uncuttable': solve([direct], Counter())[(4, 0)],
        'infeasible': solve([[]], Counter())[(4, 0)],
    }
    assert results['serial']['possible_cut'] == [1, 4]
    assert results['serial']['possible_repair'] == [5]
    assert results['parallel']['possible_cut'] == [3]
    assert results['parallel']['possible_repair'] == [1, 2]
    assert results['world_disagreement'] == {'possible_repair': [1, 2], 'robust_repair': [3], 'possible_cut': [3], 'robust_cut': [1, 2]}
    assert results['uncuttable'] == {'possible_repair': [0], 'robust_repair': [0], 'possible_cut': [], 'robust_cut': []}
    assert results['infeasible'] == {'possible_repair': [], 'robust_repair': [], 'possible_cut': [0], 'robust_cut': [0]}
    return results


def audit():
    cases = canonical()
    rng = random.Random(20261127)
    counts = Counter()
    for _ in range(240):
        solve([generate(rng) for _ in range(3)], counts)
    return {'canonical': cases, 'stress': {'systems': 240, 'worlds': 720,
            'damage_masks': 16, **dict(sorted(counts.items())), 'mismatches': 0},
            'scope': 'synthetic finite graph; EOG-WF 3/31/3 unchanged'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
