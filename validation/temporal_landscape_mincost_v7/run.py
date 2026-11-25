"""Exact integer-cost decisions in frozen finite restoration worlds."""
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import product
import json
import random


@dataclass
class World:
    nodes: tuple
    edges: tuple
    source: object
    target: object
    req: dict

    def __post_init__(self):
        rank = {v: i for i, v in enumerate(self.nodes)}
        if len(rank) != len(self.nodes) or self.source not in rank or self.target not in rank:
            raise ValueError('invalid node registry')
        if self.req.get(self.source, 0) or self.req.get(self.target, 0):
            raise ValueError('source and target must be protected')
        if any(v not in rank or not isinstance(m, int) or m < 0 or m & (m-1)
               for v, m in self.req.items()):
            raise ValueError('each vertex must have at most one restoration requirement')
        self.out = {v: [] for v in self.nodes}
        for a, b in self.edges:
            if a not in rank or b not in rank or rank[a] >= rank[b]:
                raise ValueError('edges must advance in the declared topological order')
            self.out[a].append(b)

    def scan(self, enabled, banned=0):
        reached, boundary = {self.source}, 0
        for a in self.nodes:
            if a not in reached:
                continue
            for b in self.out[a]:
                m = self.req.get(b, 0)
                if m & banned:
                    continue
                if m & enabled == m:
                    reached.add(b)
                else:
                    boundary |= m
        return self.target in reached, boundary

    def necessary_cuts(self, included, banned):
        # Each new cut is disjoint from earlier optimistically enabled cuts.
        x, cuts = included, []
        while True:
            yes, boundary = self.scan(x, banned)
            if yes:
                return cuts
            if not boundary:
                return None
            assert not boundary & (x | banned)
            cuts.append(boundary)
            x |= boundary


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


def solve(worlds, costs, objective, cap=20000):
    if not worlds or objective not in ('possible', 'robust'):
        raise ValueError('nonempty worlds and valid objective required')
    if any(type(c) is not int or c <= 0 for c in costs) or type(cap) is not int or cap < 0:
        raise ValueError('positive integer costs and nonnegative integer cap required')
    full = (1 << len(costs))-1
    if any(m & ~full for w in worlds for m in w.req.values()):
        raise ValueError('world requirement outside action universe')

    def cost(x):
        return sum(costs[i] for i in bits(x))

    def feasible(x):
        values = (w.scan(x)[0] for w in worlds)
        return any(values) if objective == 'possible' else all(values)

    def least(c):
        return min(costs[i] for i in bits(c))

    def pack(cuts):
        used = total = 0
        for c in sorted(set(cuts), key=lambda m: (-least(m), m.bit_count(), m)):
            if not used & c:
                used |= c
                total += least(c)
        return total

    if not feasible(full):
        return {'status': 'infeasible', 'lower': None, 'upper': None,
                'mask': None, 'expanded': 0}
    incumbent = full
    # A deterministic feasible upper bound, not an optimality argument.
    for i in sorted(range(len(costs)), key=lambda i: (-costs[i], i)):
        candidate = incumbent ^ (1 << i)
        if feasible(candidate):
            incumbent = candidate
    upper = cost(incumbent)
    heap, expanded = [], 0

    def push(inc, exc):
        nonlocal incumbent, upper
        base = cost(inc)
        if base >= upper:
            return
        families = [w.necessary_cuts(inc, exc) for w in worlds]
        live = [c for c in families if c is not None]
        if objective == 'robust':
            if len(live) != len(worlds):
                return
            if all(not f for f in live):
                incumbent, upper = inc, base
                return
            pooled = [m for f in live for m in f]
            bound = max(pack(pooled), max(sum(least(m) for m in f) for f in live))
            candidates = pooled
        else:
            if not live:
                return
            if any(not f for f in live):
                incumbent, upper = inc, base
                return
            chosen = min(live, key=lambda f: (sum(least(m) for m in f), tuple(f)))
            bound = sum(least(m) for m in chosen)
            candidates = chosen
        lb = base + bound
        if lb < upper:
            cut = min(candidates, key=lambda m: (m.bit_count(), -least(m), m))
            i = min(bits(cut), key=lambda i: (costs[i], i))
            heappush(heap, (lb, inc, exc, i))

    push(0, 0)
    while heap and heap[0][0] < upper and expanded < cap:
        _, inc, exc, i = heappop(heap)
        bit = 1 << i
        assert not (inc | exc) & bit
        expanded += 1
        push(inc | bit, exc)
        push(inc, exc | bit)
    lower = min(upper, heap[0][0]) if heap else upper
    assert feasible(incumbent) and cost(incumbent) == upper
    return {'status': 'optimal' if lower == upper else 'bounded',
            'lower': lower, 'upper': upper, 'mask': incumbent, 'expanded': expanded}


def oracle(world, mask):
    # Reverse search is independent of the forward cut generator.
    prev = {v: [] for v in world.nodes}
    for a, b in world.edges:
        prev[b].append(a)
    visited, todo = set(), [world.target]
    while todo:
        a = todo.pop()
        if a in visited or world.req.get(a, 0) & mask != world.req.get(a, 0):
            continue
        if a == world.source:
            return True
        visited.add(a)
        todo.extend(prev[a])
    return False


def small():
    rng = random.Random(20261129)
    nodes = tuple(product(range(5), range(10)))
    req = {v: 1 << (v[1]-1) for v in nodes if 1 <= v[1] <= 8}
    stats = {'systems': 100, 'worlds': 300, 'oracle_world_masks': 0,
             'full_checks': 0, 'zero_cap_checks': 0, 'infeasible': 0,
             'zero_cap_bounded': 0, 'zero_cap_exact': 0, 'zero_cap_infeasible': 0,
             'max_expanded': 0, 'total_expanded': 0, 'mismatches': 0}
    for _ in range(100):
        costs = [rng.randint(1, 9) for _ in range(8)]
        worlds = []
        for _ in range(3):
            edges = tuple((a, b) for a in nodes for b in nodes if
                          1 <= b[0]-a[0] <= 2 and abs(b[1]-a[1]) <= 4*(b[0]-a[0]) and rng.random() < .30)
            worlds.append(World(nodes, edges, (0, 0), (4, 9), req))
        masks = range(256)
        truth = [[oracle(w, m) for m in masks] for w in worlds]
        stats['oracle_world_masks'] += 3*256
        price = [sum(costs[i] for i in bits(m)) for m in masks]
        for obj in ('possible', 'robust'):
            combine = any if obj == 'possible' else all
            good = [combine(v) for v in zip(*truth)]
            exact = min((price[m] for m in masks if good[m]), default=None)
            for cap in (20000, 0):
                ans = solve(worlds, costs, obj, cap)
                stats['full_checks' if cap else 'zero_cap_checks'] += 1
                if exact is None:
                    assert ans['status'] == 'infeasible' and ans['mask'] is None
                    stats['infeasible' if cap else 'zero_cap_infeasible'] += 1
                else:
                    assert good[ans['mask']] and price[ans['mask']] == ans['upper']
                    assert ans['lower'] <= exact <= ans['upper']
                    assert (ans['status'] == 'optimal') == (ans['lower'] == ans['upper'])
                    if cap:
                        assert ans['lower'] == ans['upper'] == exact
                    else:
                        stats['zero_cap_exact' if ans['status'] == 'optimal' else 'zero_cap_bounded'] += 1
                if cap:
                    stats['max_expanded'] = max(stats['max_expanded'], ans['expanded'])
                    stats['total_expanded'] += ans['expanded']
    return stats


def gateway(n):
    nodes = ('S', *range(n), 'T')
    req = {i: 1 << i for i in range(n)}
    costs = [1+7*i % 11 for i in range(n)]
    worlds = [World(nodes, tuple([('S', g)] + [(g, i) for i in range(3,n)] + [(i,'T') for i in range(3,n)]), 'S', 'T', req) for g in range(3)]
    p, r = (solve(worlds,costs,obj) for obj in ('possible','robust'))
    alt = min(costs[3:])
    assert p['lower'] == p['upper'] == min(costs[:3])+alt
    assert r['lower'] == r['upper'] == sum(costs[:3])+alt
    return {'sites': n, 'possible_cost': p['upper'], 'robust_cost': r['upper'],
            'possible_expanded': p['expanded'], 'robust_expanded': r['expanded']}


def binary(k):
    nodes = ('S', *range(2*k), 'T')
    req = {i: 1 << i for i in range(2*k)}
    costs = [1+7*i % 11 for i in range(2*k)]
    edges = [('S',0), ('S',1)] + [(a,b) for t in range(k-1) for a in (2*t,2*t+1) for b in (2*t+2,2*t+3)] + [(2*k-2,'T'),(2*k-1,'T')]
    w = World(nodes, tuple(edges), 'S', 'T', req)
    ans = solve([w],costs,'robust')
    assert ans['lower'] == ans['upper'] == sum(min(costs[2*t:2*t+2]) for t in range(k))
    return {'layers': k, 'sites': 2*k, 'full_frontier_size': str(1 << k),
            'minimum_cost': ans['upper'], 'expanded': ans['expanded']}


def witness():
    nodes = ('S',0,1,2,'T')
    req = {i: 1 << i for i in range(3)}
    worlds = [World(nodes, tuple(('S',i) for i in pair)+tuple((i,'T') for i in pair), 'S','T',req) for pair in ((0,1),(1,2),(0,2))]
    bounded = solve(worlds,[1,1,1],'robust',0)
    exact = solve(worlds,[1,1,1],'robust')
    assert bounded['status'] == 'bounded' and bounded['lower'] < 2 == bounded['upper']
    assert exact['status'] == 'optimal' and exact['upper'] == 2
    empty = World(nodes, (), 'S','T',req)
    direct = World(nodes, (('S','T'),), 'S','T',req)
    assert solve(worlds+[empty],[1,1,1],'robust')['status'] == 'infeasible'
    assert solve([direct,empty],[1,1,1],'possible')['upper'] == 0
    return {'bounded': bounded, 'exact': exact, 'infeasible_checked': True, 'already_reachable_checked': True}


def audit():
    return {'small': small(), 'gateway': [gateway(n) for n in (24,48,96)],
            'binary': [binary(k) for k in (12,24,48)], 'witness': witness(),
            'scope': 'synthetic integer-cost decisions only; EOG-WF 3/31/3 unchanged'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
