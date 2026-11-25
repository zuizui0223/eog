"""Finite temporal reachability antichains, with a fail-closed label cap."""
from collections import defaultdict
from itertools import product
import json
import random

CAP = 2048


class LabelLimit(RuntimeError):
    """No complete frontier is certified when a live-label cap is exceeded."""


class Solver:
    def __init__(self, cap=CAP):
        self.cap = cap
        self.peak = 0

    def insert(self, family, x):
        if any(y & x == y for y in family):
            return
        family.difference_update({y for y in family if x & y == x})
        if len(family) == self.cap:
            raise LabelLimit("live antichain limit exceeded")
        family.add(x)
        self.peak = max(self.peak, len(family))

    def reduce(self, masks):
        f = set()
        for x in masks:
            self.insert(f, x)
        return f

    def path(self, nodes, edges, source, target, requirements):
        out = defaultdict(list)
        rank = {n: i for i, n in enumerate(nodes)}
        for a, b in edges:
            if rank[a] >= rank[b]:
                raise ValueError("graph must be topologically ordered")
            out[a].append(b)
        labels = defaultdict(set)
        self.insert(labels[source], requirements.get(source, 0))
        for a in nodes:
            for b in out[a]:
                for mask in sorted(labels[a]):
                    self.insert(labels[b], mask | requirements.get(b, 0))
        return labels[target]

    def possible(self, families):
        return self.reduce(x for f in families for x in sorted(f))

    def robust(self, families):
        result = {0}
        for f in families:
            result = self.reduce(a | b for a in sorted(result) for b in sorted(f))
        return result

    def cuts(self, repairs):
        result = {0}
        for p in sorted(repairs):
            result = self.reduce(
                b for a in sorted(result)
                for b in ([a] if a & p else [a | (1 << i) for i in range(p.bit_length()) if p & (1 << i)])
            )
        return result


def oracle_truth(nodes, edges, source, target, req, n):
    out = defaultdict(list)
    for a, b in edges:
        out[a].append(b)
    truth = []
    for enabled in range(1 << n):
        reached = {source}
        for a in nodes:
            if a in reached:
                reached.update(b for b in out[a] if req.get(b, 0) & enabled == req.get(b, 0))
        truth.append(target in reached)
    return truth


def oracle_families(truth):
    full = len(truth) - 1
    def minimal_true(values):
        return {m for m, yes in enumerate(values) if yes and all(
            not values[m ^ (1 << i)] for i in range(m.bit_length()) if m & (1 << i))}
    return minimal_true(truth), minimal_true([not truth[full ^ d] for d in range(full + 1)])


def small():
    rng = random.Random(20261128)
    nodes = tuple(product(range(5), range(10)))
    source, target = (0, 0), (4, 9)
    req = {v: 1 << (v[1]-1) for v in nodes if 1 <= v[1] <= 8}
    solver = Solver()
    checks = 0
    for _ in range(80):
        families, truths = [], []
        for _ in range(3):
            edges = [(a,b) for a in nodes for b in nodes if
                     1 <= b[0]-a[0] <= 2 and abs(b[1]-a[1]) <= 4*(b[0]-a[0]) and rng.random() < .3]
            f = solver.path(nodes, edges, source, target, req)
            truth = oracle_truth(nodes, edges, source, target, req, 8)
            assert (f, solver.cuts(f)) == oracle_families(truth)
            checks += 2
            families.append(f)
            truths.append(truth)
        for agg, truth in [(solver.possible(families), [any(v) for v in zip(*truths)]),
                           (solver.robust(families), [all(v) for v in zip(*truths)])]:
            assert (agg, solver.cuts(agg)) == oracle_families(truth)
            checks += 2
    return {"systems": 80, "worlds": 240, "oracle_world_masks": 240*256,
            "frontier_checks": checks, "peak_labels": solver.peak, "mismatches": 0}


def large(n):
    nodes = ('S', *range(n), 'T')
    req = {i: 1 << i for i in range(n)}
    alt = list(range(3, n))
    solver = Solver()
    families = []
    all_alt = sum(req[i] for i in alt)
    for gate in range(3):
        edges = [('S', gate)] + [(gate, i) for i in alt] + [(i, 'T') for i in alt]
        f = solver.path(nodes, edges, 'S', 'T', req)
        assert f == {req[gate] | req[i] for i in alt}
        assert solver.cuts(f) == {req[gate], all_alt}
        families.append(f)
    p, r = solver.possible(families), solver.robust(families)
    assert p == {req[g] | req[i] for g in range(3) for i in alt}
    assert r == {7 | req[i] for i in alt}
    pc, rc = solver.cuts(p), solver.cuts(r)
    assert pc == {7, all_alt} and rc == {1, 2, 4, all_alt}
    return {"sites": n, "all_subset_count": str(1 << n), "possible_repairs": len(p),
            "robust_repairs": len(r), "possible_cuts": len(pc), "robust_cuts": len(rc),
            "peak_labels": solver.peak, "complete": True}


def adversarial(k):
    nodes = ('S', *range(2*k), 'T')
    req = {i: 1 << i for i in range(2*k)}
    edges = [('S',0), ('S',1)] + [(a,b) for t in range(k-1) for a in (2*t,2*t+1)
            for b in (2*t+2,2*t+3)] + [(2*k-2,'T'),(2*k-1,'T')]
    solver = Solver()
    try:
        f = solver.path(nodes, edges, 'S', 'T', req)
        assert k < 12
        assert f == {sum(1 << i for i in x) for x in product(*[(2*t,2*t+1) for t in range(k)])}
        c = solver.cuts(f)
        assert c == {3 << (2*t) for t in range(k)}
        return {"layers": k, "complete": True, "repairs": len(f), "cuts": len(c), "peak_labels": solver.peak}
    except LabelLimit:
        assert k == 12
        return {"layers": k, "complete": False, "status": "label_cap_exceeded_no_certificate", "peak_labels": solver.peak}


def audit():
    return {"small": small(), "large": [large(n) for n in (24,48,96)],
            "adversarial": [adversarial(k) for k in (8,10,12)],
            "scope": "finite synthetic graphs only; EOG-WF 3/31/3 unchanged"}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
