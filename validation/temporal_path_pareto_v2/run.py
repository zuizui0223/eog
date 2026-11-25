"""Exact finite time-expanded path frontiers; no biological payloads."""
from fractions import Fraction
from itertools import product
import json
import random

ZERO = (0, Fraction(0), 0, 0)


def join(a, b):
    return tuple(max(x, y) for x, y in zip(a, b, strict=True))


def pareto(points):
    points = set(points)
    return {p for p in points if not any(q != p and all(x <= y for x, y in zip(q, p, strict=True)) for q in points)}


def dp(edges, source, target, checks=()):
    """Node IDs are ordered integer times. No implicit waiting."""
    labels = {(source, int(bool(checks) and source == checks[0])): {ZERO}}
    for i in range(source, target):
        for a, b, d, e, barrier, hard in edges:
            if a != i or hard or b > target:
                continue
            cost = (b-a, Fraction(d, b-a), e, barrier)
            for k in range(len(checks)+1):
                state = (b, k + int(k < len(checks) and b == checks[k]))
                candidates = {join(p, cost) for p in labels.get((i, k), ())}
                if candidates:
                    labels[state] = pareto(labels.get(state, set()) | candidates)
    return labels.get((target, len(checks)), set())


def oracle(edges, source, target, checks=()):
    """Independent exhaustive DFS over complete paths, then direct path maxima."""
    paths = []
    def visit(node, route, trace):
        if node == target:
            if tuple(v for v in route if v in checks) == checks:
                paths.append((max((b-a for a,b,*_ in trace), default=0),
                              max((Fraction(d,b-a) for a,b,d,*_ in trace), default=Fraction(0)),
                              max((e for _,_,_,e,*_ in trace), default=0),
                              max((h for _,_,_,_,h,_ in trace), default=0)))
            return
        for edge in edges:
            a,b,*_,hard = edge
            if a == node and not hard and b <= target:
                visit(b, route+[b], trace+[edge])
    visit(source,[source],[])
    return {p for p in paths if not any(q != p and q[0]<=p[0] and q[1]<=p[1] and q[2]<=p[2] and q[3]<=p[3] for q in paths)}


def aggregate(worlds):
    possible = pareto(set().union(*worlds))
    robust = {ZERO}
    for w in worlds:
        robust = pareto(join(a,b) for a in robust for b in w)
    return possible, robust


def oracle_aggregate(worlds):
    ps = set().union(*worlds)
    rs = {tuple(max(v[i] for v in combo) for i in range(4)) for combo in product(*worlds)}
    def minimal(s):
        return {p for p in s if not any(q!=p and q[0]<=p[0] and q[1]<=p[1] and q[2]<=p[2] and q[3]<=p[3] for q in s)}
    return minimal(ps), minimal(rs)


def encode(points):
    return [[g,str(v),e,b] for g,v,e,b in sorted(points)]


def audit():
    a = [(0,1,1,2,0,False),(1,4,6,0,0,False)]
    b = [(0,2,1,0,1,False),(2,4,6,1,0,False)]
    alias = [(0,2,1,0,0,False),(0,4,1,0,0,False)]
    hard = [(0,4,1,0,0,True)]
    trade = dp(a+b,0,4)
    assert trade == {(3,Fraction(2),2,0),(2,Fraction(3),1,1)} == oracle(a+b,0,4)
    assert dp(alias,0,2) and dp(alias,0,4) and not dp(alias,0,4,(2,))
    assert not oracle(alias,0,4,(2,))
    quant = aggregate([dp(a,0,4),dp(b,0,4)])
    assert quant == (trade,{(3,Fraction(3),2,1)}) == oracle_aggregate([oracle(a,0,4),oracle(b,0,4)])
    assert not aggregate([dp(a,0,4),dp(hard,0,4)])[1]
    assert not dp(hard,0,4) and not oracle(hard,0,4)
    counts = dict(systems=240, worlds=480, world_oracle_comparisons=0, aggregate_oracle_comparisons=0,
                  unreachable_worlds=0, possible_but_not_robust_systems=0, independent_checkpoint_false_worlds=0,
                  robust_differs_from_possible_systems=0, multiobjective_worlds=0, both_feasible_robust_differs_systems=0)
    rng = random.Random(20261125)
    for _ in range(240):
        fs, os = [], []
        for _ in range(2):
            edges = []
            for i in range(7):
                for j in range(i+1,7):
                    if rng.random() < .45:
                        edges.append((i,j,rng.randint(0,12),rng.randint(0,4),rng.randint(0,2),rng.random()<.15))
            f,o = dp(edges,0,6,(3,)),oracle(edges,0,6,(3,))
            assert f == o
            counts['world_oracle_comparisons'] += 1
            counts['unreachable_worlds'] += not f
            counts['independent_checkpoint_false_worlds'] += bool(dp(edges,0,3) and dp(edges,0,6) and not f)
            counts['multiobjective_worlds'] += len(f)>1
            fs.append(f); os.append(o)
        p,r = aggregate(fs)
        assert (p,r) == oracle_aggregate(os)
        counts['aggregate_oracle_comparisons'] += 2
        counts['possible_but_not_robust_systems'] += bool(p and not r)
        counts['robust_differs_from_possible_systems'] += p != r
        counts['both_feasible_robust_differs_systems'] += bool(r and p != r)
    return {'canonical':{'tradeoff':encode(trade),'checkpoint_alias':True,'world_quantifier_possible':encode(quant[0]),'world_quantifier_robust':encode(quant[1]),'hard_block':True},'stress':counts,'oracle_disagreements':0,'scope':'finite graph/time states; synthetic only; EOG-WF 3/31/3 unchanged'}


if __name__ == '__main__':
    print(json.dumps(audit(),indent=2))
