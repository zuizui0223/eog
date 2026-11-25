"""Independent synthetic audit of joint time-gap/speed feasibility; stdlib only."""
import argparse
import itertools
import json
import random
from pathlib import Path


def edge(a, b, d, g, v):
    return 1 <= b - a <= g and d <= v * (b - a)


def forward(w, g, v):
    r = set(w['times'][0])
    for target, d in zip(w['times'][1:], w['distances']):
        r = {b for b in target if any(edge(a, b, d, g, v) for a in r)}
    return bool(r)


def oracle(w, g, v):
    for t in itertools.product(*w['times']):
        if all(1 <= t[i+1]-t[i] <= g and w['distances'][i] <= v*(t[i+1]-t[i])
               for i in range(len(t)-1)):
            return True
    return False


def local_edges(w, g, v):
    return [any(edge(a, b, d, g, v) for a in left for b in right)
            for left, right, d in zip(w['times'], w['times'][1:], w['distances'])]


def hull(w):
    return {**w, 'times': [list(range(min(t), max(t)+1)) for t in w['times']]}


def frontier(points):
    return [p for p in points if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in points)]


def audit(p):
    grid = list(itertools.product(p['grid']['G'], p['grid']['V']))
    cases = {}
    for c in p['cases']:
        ws = c['worlds']
        possible, robust, pairwise, splice, convex = [], [], [], [], []
        for g, v in grid:
            point = (g, v)
            fs = [forward(w,g,v) for w in ws]
            assert fs == [oracle(w,g,v) for w in ws]
            if any(fs): possible.append(point)
            if all(fs): robust.append(point)
            es = [local_edges(w,g,v) for w in ws]
            if any(all(e) for e in es): pairwise.append(point)
            if all(any(e[i] for e in es) for i in range(len(es[0]))): splice.append(point)
            if any(forward(hull(w),g,v) for w in ws): convex.append(point)
        cases[c['id']] = {'possible_frontier':frontier(possible), 'robust_frontier':frontier(robust),
                          'pairwise_false':sorted(set(pairwise)-set(possible)),
                          'world_splice_false':sorted(set(splice)-set(pairwise)),
                          'convex_hull_false':sorted(set(convex)-set(possible)),
                          'coordinate_minimum_feasible': None if not possible else (min(x[0] for x in possible),min(x[1] for x in possible)) in possible}
    rng = random.Random(p['stress']['seed'])
    checks = violations = false_pairs = false_hulls = worlds_pair = worlds_hull = 0
    for _ in range(500):
        n = rng.randint(2,5)
        w = {'times':[sorted(rng.sample(range(9),rng.randint(1,4))) for _ in range(n)], 'distances':[rng.randint(0,9) for _ in range(n-1)]}
        valid = {pt:forward(w,*pt) for pt in grid}
        fp = fh = 0
        for pt, yes in valid.items():
            checks += 1
            assert yes == oracle(w,*pt)
            if yes:
                violations += sum(not z for q,z in valid.items() if q[0]>=pt[0] and q[1]>=pt[1])
            else:
                fp += all(local_edges(w,*pt))
                fh += forward(hull(w),*pt)
        false_pairs += fp
        false_hulls += fh
        worlds_pair += bool(fp)
        worlds_hull += bool(fh)
    assert violations == 0
    a,b,c,d,e = (cases[k] for k in ('tradeoff','nonconvex','world_splice','quantifier','order_impossible'))
    hypotheses = {'H1':len(a['possible_frontier'])>=2 and not a['coordinate_minimum_feasible'],
                  'H2':bool(b['convex_hull_false']), 'H3':bool(c['world_splice_false']),
                  'H4':d['possible_frontier']!=d['robust_frontier'], 'H5':not e['possible_frontier']}
    return {'cases':cases,'hypotheses':hypotheses,'stress':{'worlds':500,'oracle_comparisons':checks,'oracle_disagreements':0,'monotonicity_violations':violations,'pairwise_false_grid_pairs':false_pairs,'worlds_with_pairwise_false':worlds_pair,'hull_false_grid_pairs':false_hulls,'worlds_with_hull_false':worlds_hull},'scope':'synthetic finite grid only; no empirical data; EOG-WF 3/31/3 unchanged'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('protocol',type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.protocol.read_text())),indent=2))
