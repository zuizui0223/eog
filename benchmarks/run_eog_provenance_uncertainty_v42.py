#!/usr/bin/env python3
"""v42: partition synthetic target uncertainty by nested source evidence.

Precision/coverage/source-class components are expected information differences,
not causal variance components. Every latent world and present-state map is v41.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Hashable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PROTOCOL = ROOT / 'validation/eog_provenance_uncertainty_decomposition_v42/protocol_v42.json'
PARENT_DIGEST = '34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d'
TOL = 1e-9
PARTS = ('recovered', 'measurement_loss', 'site_coverage_loss', 'source_type_floor')
CLASSES = ('target_already_determined_by_occupancy', 'selected_noisy_tags_sufficient',
           'perfect_same_site_tags_sufficient', 'additional_perfect_source_sites_needed',
           'different_measurement_class_required')


def deterministic_risk(observation: Mapping[Hashable, Hashable],
                       target: Mapping[Hashable, Hashable]) -> dict[str, float]:
    """Expected target entropy and Bayes error under a uniform history prior."""
    if not observation or set(observation) != set(target):
        raise ValueError('Nonempty matching history domains are required')
    grouped: dict[Hashable, Counter] = defaultdict(Counter)
    for history, signature in observation.items():
        grouped[signature][target[history]] += 1
    n = len(observation)
    entropy = 0.0
    correct = 0.0
    for counts in grouped.values():
        mass = sum(counts.values())
        entropy -= sum(c / n * math.log2(c / mass) for c in counts.values())
        correct += max(counts.values()) / n
    return {'entropy_bits': max(0.0, entropy), 'bayes_error': max(0.0, 1.0 - correct)}


def uncertainty_partition(baseline: dict, noisy: dict, same_site: dict,
                          all_site: dict) -> dict[str, dict[str, float]]:
    """Telescope expected residual risks for the fixed information hierarchy."""
    result = {}
    for label, metric in (('entropy', 'entropy_bits'), ('error', 'bayes_error')):
        b, y, s, a = (float(r[metric]) for r in (baseline, noisy, same_site, all_site))
        if any(not math.isfinite(v) or v < -TOL for v in (b, y, s, a)):
            raise ValueError('Invalid expected risk')
        values = (b - y, y - s, s - a, a)
        if min(values) < -TOL:
            raise ValueError('Invalid nested evidence: expected risk increased')
        parts = {key: max(0.0, value) for key, value in zip(PARTS, values)}
        if abs(sum(parts.values()) - b) > TOL:
            raise ValueError('Nested partition fails to reconstruct baseline')
        result[label] = parts
    return result


def classify_uncertainty(baseline: dict, noisy: dict, same_site: dict,
                         all_site: dict) -> str:
    uncertainty_partition(baseline, noisy, same_site, all_site)
    for risk, category in zip((baseline, noisy, same_site, all_site), CLASSES):
        if risk['entropy_bits'] <= TOL:
            return category
    return CLASSES[-1]


def _signature(occupancy: dict, tags: dict, sites: tuple) -> dict:
    return {h: (occupancy[h], tuple(tags[s][h] for s in sites)) for h in occupancy}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _summary(rows: list[dict], policy: str, target: str, subset: str) -> dict:
    n = len(rows)
    def mean(field: str):
        return sum(r[field] for r in rows) / n if n else None
    out = {'policy': policy, 'target': target, 'subset': subset, 'n_designs': n,
           'mean_selected_site_count': mean('selected_sites')}
    for scale in ('entropy', 'error'):
        components = {p: mean(f'{scale}_{p}') for p in PARTS}
        residual = sum(components[p] for p in PARTS[1:]) if n else None
        out[scale] = {
            'baseline': mean(f'{scale}_baseline'), 'residual_after_noisy': residual,
            **components,
            'residual_shares': {
                p: components[p] / residual if residual is not None and residual > TOL else None
                for p in PARTS[1:]
            },
        }
    counter = Counter(r['resolution_class'] for r in rows)
    out['resolution_counts'] = {c: counter[c] for c in CLASSES}
    residual = out['entropy']['residual_after_noisy']
    out['dominant_residual_component'] = (
        max(PARTS[1:], key=lambda p: out['entropy'][p])
        if residual is not None and residual > TOL else None)
    structural_share = out['entropy']['residual_shares']['source_type_floor']
    out['source_type_floor_majority'] = structural_share > .5 if structural_share is not None else None
    return out


def run() -> tuple[dict, list[dict]]:
    # Load the established simulator only for full execution, not synthetic unit tests.
    from benchmarks import run_eog_provenance_ecological_state_v41 as old
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    if (protocol['schema'] != 'eog.provenance_uncertainty_decomposition.protocol.v42'
        or protocol['parent']['v41_canonical_sha256'] != PARENT_DIGEST
        or protocol['unchanged_design']['noisy_assay']['coverage'] != .6
        or protocol['unchanged_design']['noisy_assay']['miscall'] != .1
        or protocol['reporting']['dominance_rule'] !=
           'source-type-floor majority only when structural residual share > 0.5; otherwise report the largest component and do not relabel thresholds'):
        raise ValueError('Frozen v42 source/design contract changed')
    parent_result = old.run()
    if hashlib.sha256(_canonical(parent_result)).hexdigest() != PARENT_DIGEST:
        raise ValueError('Complete v41 parent rerun does not match original source digest')
    targets_expected = list(old.TARGETS)
    if (protocol['unchanged_design']['targets'] != targets_expected
        or protocol['unchanged_design']['policies'] != list(old.POLICIES)):
        raise ValueError('Target or measurement-site policy changed')
    output = []
    observed_parent = Counter()
    floor_counts = Counter({t: 0 for t in old.TARGETS})
    positive = Counter()
    max_reconstruction = 0.0
    for autocorr in old.AUTOCORR_LEVELS:
        for neighbourhood in old.NEIGHBOURHOODS:
            for replicate in range(old.REPLICATES):
                base = old._generate_base(replicate, autocorr, neighbourhood)
                outlet = old._outlet_corner(replicate, autocorr, neighbourhood)
                anchor = old._truth_source(base, outlet)
                candidates, _ = old._candidate_sources(base, outlet, anchor)
                source_sets = old._source_sets(candidates, anchor)
                if not source_sets:
                    raise ValueError('An original v41 world is missing')
                for barrier in old.BARRIER_LEVELS:
                    _, graph = old._graphs(base, barrier, old.RULE, outlet)
                    for geometry in old.DESIGNS:
                        sources = source_sets[geometry][3]
                        key = f'{replicate}|{autocorr}|{neighbourhood}|{barrier}|{geometry}'
                        design = old.prepare_design(graph, sources, key)
                        targets = old._synthetic_present_targets(graph, sources)
                        occ, tags = design['occupancy'], design['provenance_tags']
                        full_sig = _signature(occ, tags, tuple(sorted(tags)))
                        aliased = not design['occupancy_exact_history_identifiable']
                        fair = aliased and design['equal_budget_eligible']
                        source_alias = len(set(full_sig.values())) < 3
                        observed_parent['design_rows'] += 1
                        observed_parent['occupancy_alias'] += int(aliased)
                        observed_parent['equal_budget_alias'] += int(fair)
                        observed_parent['perfect_combined_alias'] += int(source_alias)
                        base_risks = {t: deterministic_risk(occ, values) for t, values in targets.items()}
                        full_risks = {t: deterministic_risk(full_sig, values) for t, values in targets.items()}
                        for t in old.TARGETS:
                            floor_counts[t] += int(full_risks[t]['entropy_bits'] > TOL)
                        for policy in old.POLICIES:
                            selected = tuple(design['selected'][policy])
                            selected_sig = _signature(occ, tags, selected)
                            for t in old.TARGETS:
                                measured = old.target_bayes_information(occ, targets[t], tags, selected, .6, .1)
                                baseline = base_risks[t]
                                if (abs(measured['base_conditional_entropy_bits'] - baseline['entropy_bits']) > TOL
                                    or abs(1 - measured['base_bayes_correct_target_probability'] - baseline['bayes_error']) > TOL):
                                    raise ValueError('Independent deterministic target-risk baseline mismatches v41')
                                noisy = {
                                    'entropy_bits': max(0.0, baseline['entropy_bits'] - measured['information_bits']),
                                    'bayes_error': max(0.0, baseline['bayes_error'] - measured['bayes_correct_target_gain'])}
                                same = deterministic_risk(selected_sig, targets[t])
                                full = full_risks[t]
                                parts = uncertainty_partition(baseline, noisy, same, full)
                                row = {'design_key': key, 'geometry': geometry, 'policy': policy, 'target': t,
                                       'occupancy_aliased': aliased, 'equal_budget_aliased': fair,
                                       'full_source_history_aliased': source_alias,
                                       'selected_sites': len(selected),
                                       'resolution_class': classify_uncertainty(baseline, noisy, same, full)}
                                for scale, metric in (('entropy', 'entropy_bits'), ('error', 'bayes_error')):
                                    row[f'{scale}_baseline'] = baseline[metric]
                                    row.update({f'{scale}_{p}': v for p, v in parts[scale].items()})
                                    max_reconstruction = max(max_reconstruction, abs(sum(parts[scale].values()) - baseline[metric]))
                                if aliased and policy == 'confluence_targeted' and measured['information_bits'] > TOL:
                                    positive[t] += 1
                                output.append(row)
    if dict(observed_parent) != {'design_rows': 768, 'occupancy_alias': 189, 'equal_budget_alias': 88, 'perfect_combined_alias': 81}:
        raise ValueError(f'Original world counts changed: {observed_parent}')
    if dict(floor_counts) != {'exact_activation_history':81, 'history_blind_occupancy':0,
                             'persistent_threshold_lag2':12, 'transient_window_age1_2':45, 'saturating_age_class_cap3':45}:
        raise ValueError('Source-class target-equivalence counts changed')
    if positive['exact_activation_history'] != 120 or positive['persistent_threshold_lag2'] != 48:
        raise ValueError('v41 informative-history/maturity population changed')
    summaries = []
    for policy in old.POLICIES:
        for target in old.TARGETS:
            same_target = [r for r in output if r['policy'] == policy and r['target'] == target]
            strata = {
                'all': same_target,
                'occupancy_aliased': [r for r in same_target if r['occupancy_aliased']],
                'equal_budget_aliased': [r for r in same_target if r['equal_budget_aliased']],
                'full_source_history_aliased': [r for r in same_target if r['full_source_history_aliased']],
            }
            for geometry in old.DESIGNS:
                strata[f'occupancy_aliased_{geometry}'] = [r for r in same_target if r['occupancy_aliased'] and r['geometry'] == geometry]
            summaries.extend(_summary(rows, policy, target, subset) for subset, rows in strata.items())
    primary = next(s for s in summaries if s['policy'] == 'confluence_targeted'
                   and s['target'] == 'persistent_threshold_lag2' and s['subset'] == 'occupancy_aliased')
    return {
        'schema': 'eog.provenance_uncertainty_decomposition.result.v42',
        'status': 'COMPLETED_SYNTHETIC_NESTED_EVIDENCE_DECOMPOSITION',
        'protocol': str(PROTOCOL.relative_to(ROOT)),
        'parent_complete_v41_canonical_sha256': PARENT_DIGEST,
        'parent_counts': dict(observed_parent), 'full_source_target_floor_counts': dict(floor_counts),
        'recomputed_positive_information_counts': dict(positive),
        'scenario_metric_rows': len(output), 'max_partition_reconstruction_error': max_reconstruction,
        'primary': primary, 'summary_by_policy_target_stratum': summaries,
        'scope': protocol['scope'],
    }, output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError('Refuse to overwrite an existing result directory')
    result, rows = run()
    args.output_dir.mkdir(parents=True)
    with (args.output_dir / 'scenario_metrics.csv').open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    csv_hash = hashlib.sha256((args.output_dir / 'scenario_metrics.csv').read_bytes()).hexdigest()
    result['scenario_csv_sha256'] = csv_hash
    (args.output_dir / 'result_v42.json').write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'primary': result['primary'], 'csv_sha256': csv_hash}, indent=2))


if __name__ == '__main__':
    main()
