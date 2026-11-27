"""Conditional ordinal scaffold; not measured river geography or fish observations."""
import json
from itertools import product

NODES = tuple(range(1, 23))
BARRIERS = {"lower": (20, 19), "upper": (14, 13)}
POLICIES = {"mouth_proxy": (22,), "mouth_plus_reach14": (22, 14)}
MASKS = tuple(frozenset(k for k, active in zip(BARRIERS, bits) if active)
              for bits in product((False, True), repeat=2))


def reach(opened, sources):
    blocked = set(BARRIERS.values()) - {BARRIERS[k] for k in opened}
    reached = set(sources)
    todo = list(sources)
    while todo:
        a = todo.pop()
        if a > 1 and (a, a-1) not in blocked and a-1 not in reached:
            reached.add(a-1)
            todo.append(a-1)
    return reached


def oracle(opened, sources):
    return {v for v in NODES if any(v <= s and all(
        k in opened for k, (a,b) in BARRIERS.items() if v <= b < a <= s)
        for s in sources)}


def minimal(family):
    return sorted([sorted(s) for s in family if not any(t < s for t in family)])


def audit():
    scenarios = []
    all_sets = {}
    checks = 0
    for opened in MASKS:
        rows = {}
        for name, sources in POLICIES.items():
            values = reach(opened, sources)
            assert values == oracle(opened, sources)
            checks += len(NODES)
            rows[name] = values
            all_sets[name, opened] = values
        possible = set.union(*rows.values())
        robust = set.intersection(*rows.values())
        scenarios.append({"open_barriers": sorted(opened),
                          "reachable_by_policy": {k: sorted(v) for k,v in rows.items()},
                          "counts_by_policy": {k: len(v) for k,v in rows.items()},
                          "possible": sorted(possible), "robust": sorted(robust),
                          "unresolved": sorted(possible-robust),
                          "excluded": sorted(set(NODES)-possible)})
    targets = []
    for target in NODES:
        local = {k: minimal({m for m in MASKS if target in all_sets[k,m]}) for k in POLICIES}
        possible = minimal({m for m in MASKS if any(target in all_sets[k,m] for k in POLICIES)})
        robust = minimal({m for m in MASKS if all(target in all_sets[k,m] for k in POLICIES)})
        for policy, sources in POLICIES.items():
            interval_requirements = {frozenset(k for k,(a,b) in BARRIERS.items() if target <= b < a <= s)
                                     for s in sources if s >= target}
            assert local[policy] == minimal(interval_requirements)
        targets.append({"target": target, "local": local, "possible": possible, "robust": robust})
    assert [s["counts_by_policy"] for s in scenarios] == [
        {"mouth_proxy":3,"mouth_plus_reach14":4},
        {"mouth_proxy":3,"mouth_plus_reach14":17},
        {"mouth_proxy":9,"mouth_plus_reach14":9},
        {"mouth_proxy":22,"mouth_plus_reach14":22}]
    return {"status": "ORDINAL_CONDITIONAL_ONLY", "nodes": len(NODES),
            "assumed_edges": len(NODES)-1, "oracle_target_checks": checks,
            "scenarios": scenarios, "target_minimal_openings": targets,
            "geometry_verified": False, "survey_crosswalk_verified": False,
            "fish_response_rows_parsed": 0, "ecological_scores": 0}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
