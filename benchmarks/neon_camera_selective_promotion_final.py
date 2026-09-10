from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'validation/neon_camera_selective_promotion/final_once_only_contract.json'
OUTPUT = ROOT / 'build/neon_camera_selective_promotion/final_result.json'
URLS = {
    'deployments': 'https://zenodo.org/api/records/20826511/files/camera_trap_deployments.csv/content',
    'response': 'https://zenodo.org/api/records/20826511/files/camera_trap_sequences.csv/content',
}


def _get(url: str, ua: str) -> bytes:
    req = Request(url, headers={'User-Agent': ua})
    with urlopen(req, timeout=90) as r:  # noqa: S310 - frozen public files
        return r.read()


def _csv(raw: bytes):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    return list(reader.fieldnames or []), list(reader)


def _haversine_matrix(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    r = 6371.0088
    la = np.radians(lat)
    lo = np.radians(lon)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.minimum(1.0, np.sqrt(a)))


def _split_bin(name: str) -> int:
    return int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:16], 16) % 10


def _baseline(rows):
    years = []
    out = []
    for r in rows:
        start = r['start_date'].strip()
        y, m, d = [int(x) for x in start[:10].split('-')]
        import datetime as dt
        doy = dt.date(y, m, d).timetuple().tm_yday
        duration = (dt.date(*[int(x) for x in r['end_date'][:10].split('-')]) - dt.date(y, m, d)).days
        years.append(y)
        phase = 2 * math.pi * doy / 365.25
        out.append([float(duration), float(r['latitude']), float(r['longitude']), (y - 2015.0) / 7.0, math.sin(phase), math.cos(phase)])
    return np.asarray(out, dtype=float)


def _macro_metric(y, p, groups, kind='logloss'):
    vals = []
    for g in sorted(set(groups)):
        idx = np.array([x == g for x in groups])
        yg, pg = y[idx], p[idx]
        if kind == 'logloss':
            vals.append(log_loss(yg, np.column_stack([1-pg, pg]), labels=[0, 1]))
        else:
            vals.append(float(np.mean((pg - yg) ** 2)))
    return float(np.mean(vals))


def _fit_predict(xtr, ytr, xte, cfg):
    clf = RandomForestClassifier(
        n_estimators=cfg['n_estimators'], min_samples_leaf=cfg['min_samples_leaf'],
        max_features=cfg['max_features'], class_weight=cfg['class_weight'],
        random_state=cfg['random_state'], n_jobs=cfg['n_jobs'],
    )
    clf.fit(xtr, ytr)
    return clf.predict_proba(xte)[:, list(clf.classes_).index(1)]


def _layer_b_for_targets(dist: np.ndarray, source_idx: list[int], target_idx: list[int], thresholds: list[float], ids: list[str]) -> np.ndarray:
    if not source_idx:
        raise RuntimeError('no positive source deployments available for Layer B')
    support = np.zeros((len(source_idx), 5, len(target_idx)), dtype=float)
    for si, s in enumerate(source_idx):
        ds = dist[s, target_idx]
        for wi, th in enumerate(thresholds):
            support[si, wi, :] = (ds <= th).astype(float)
        support[si, 4, :] = 1.0
    res = summarize_source_symmetric_support(
        support,
        source_ids=[ids[i] for i in source_idx],
        world_ids=['q10', 'q25', 'q50', 'q75', 'external_open'],
        node_ids=[ids[i] for i in target_idx],
        declared_world_count=5,
    )
    return res.feature_matrix


def _crossfit_layer_b(dist, y, fit_idx, thresholds, ids):
    positive = [i for i in fit_idx if y[i] == 1]
    rows = []
    for i in fit_idx:
        sources = [s for s in positive if s != i]
        rows.append(_layer_b_for_targets(dist, sources, [i], thresholds, ids)[0])
    return np.asarray(rows, dtype=float)


def main() -> int:
    c = json.loads(CONTRACT.read_text())
    base = {
        'schema': 'eog.neon_camera_selective_promotion.final_result.v1',
        'attempt_id': c['attempt_id'],
        'response_payload_requests': 0,
        'response_payload_bytes_opened': 0,
        'response_values_opened': False,
        'counts_as_predictive_evidence': False,
    }
    try:
        dep_raw = _get(URLS['deployments'], 'eog-neon-final-nonresponse/1.0')
        dep_cols, dep_rows = _csv(dep_raw)
        required_dep = {'deployment_id','latitude','longitude','start_date','end_date','subproject_name'}
        if not required_dep.issubset(dep_cols):
            raise RuntimeError(f'deployment schema mismatch: missing {sorted(required_dep-set(dep_cols))}')
        if len(dep_rows) != 820:
            raise RuntimeError(f'deployment row drift: {len(dep_rows)}')

        lat = np.array([float(r['latitude']) for r in dep_rows])
        lon = np.array([float(r['longitude']) for r in dep_rows])
        dist = _haversine_matrix(lat, lon)
        upper = dist[np.triu_indices(len(dep_rows), k=1)]
        thresholds = [float(np.quantile(upper, q)) for q in (0.10, 0.25, 0.50, 0.75)]

        # The single authorized biological-response access begins here.
        resp_raw = _get(URLS['response'], 'eog-neon-final-response-once/1.0')
        base['response_payload_requests'] = 1
        base['response_payload_bytes_opened'] = len(resp_raw)
        base['response_values_opened'] = True
        if len(resp_raw) != c['authoritative_response']['exact_size']:
            raise RuntimeError(f"response size drift: {len(resp_raw)}")
        md5 = hashlib.md5(resp_raw).hexdigest()  # noqa: S324 provenance only
        if md5 != c['authoritative_response']['md5']:
            raise RuntimeError(f'response checksum drift: {md5}')
        resp_cols, resp_rows = _csv(resp_raw)
        dep_alias = next((x for x in c['authoritative_response']['accepted_deployment_id_columns'] if x in resp_cols), None)
        sci_alias = next((x for x in c['authoritative_response']['accepted_scientific_name_columns'] if x in resp_cols), None)
        if dep_alias is None or sci_alias is None:
            raise RuntimeError(f'response schema mismatch; columns={resp_cols}')

        focal = c['focal_response']['scientific_name']
        positive_ids = {r[dep_alias].strip() for r in resp_rows if r.get(dep_alias) and r.get(sci_alias, '').strip() == focal}
        ids = [r['deployment_id'].strip() for r in dep_rows]
        y = np.array([1 if x in positive_ids else 0 for x in ids], dtype=int)
        groups = [r['subproject_name'].strip() for r in dep_rows]
        bins = [_split_bin(g) for g in groups]
        train_idx = [i for i,b in enumerate(bins) if b in c['partition']['inner_train_bins']]
        val_idx = [i for i,b in enumerate(bins) if b in c['partition']['inner_validation_bins']]
        outer_idx = [i for i,b in enumerate(bins) if b in c['partition']['outer_heldout_bins']]

        def counts(idx):
            yy = y[idx]
            gs = [groups[i] for i in idx]
            both = sum(1 for g in set(gs) if len(set(y[[j for j in idx if groups[j] == g]].tolist())) == 2)
            return {'n': len(idx), 'positive': int(yy.sum()), 'negative': int(len(yy)-yy.sum()), 'subprojects': len(set(gs)), 'subprojects_with_both_classes': both}
        cc = {'inner_train': counts(train_idx), 'inner_validation': counts(val_idx), 'outer': counts(outer_idx)}
        mins = c['estimability_minima']
        checks = [
            cc['inner_train']['positive'] >= mins['inner_train_positive_deployments'], cc['inner_train']['negative'] >= mins['inner_train_negative_deployments'],
            cc['inner_validation']['positive'] >= mins['inner_validation_positive_deployments'], cc['inner_validation']['negative'] >= mins['inner_validation_negative_deployments'],
            cc['outer']['positive'] >= mins['outer_positive_deployments'], cc['outer']['negative'] >= mins['outer_negative_deployments'],
            cc['inner_validation']['subprojects_with_both_classes'] >= mins['inner_validation_subprojects_with_both_classes'],
            cc['outer']['subprojects_with_both_classes'] >= mins['outer_subprojects_with_both_classes'],
        ]
        if not all(checks):
            raise RuntimeError(f'estimability failure: {cc}')

        xb = _baseline(dep_rows)
        cfg = c['learner']
        lb_train = _crossfit_layer_b(dist, y, train_idx, thresholds, ids)
        train_pos = [i for i in train_idx if y[i] == 1]
        lb_val = _layer_b_for_targets(dist, train_pos, val_idx, thresholds, ids)
        p_b_val = _fit_predict(xb[train_idx], y[train_idx], xb[val_idx], cfg)
        p_a_val = _fit_predict(np.column_stack([xb[train_idx], lb_train]), y[train_idx], np.column_stack([xb[val_idx], lb_val]), cfg)
        val_groups = [groups[i] for i in val_idx]
        val_base = _macro_metric(y[val_idx], p_b_val, val_groups)
        val_aug = _macro_metric(y[val_idx], p_a_val, val_groups)
        promote = bool(val_aug < val_base)

        cal_idx = train_idx + val_idx
        lb_cal = _crossfit_layer_b(dist, y, cal_idx, thresholds, ids)
        cal_pos = [i for i in cal_idx if y[i] == 1]
        lb_outer = _layer_b_for_targets(dist, cal_pos, outer_idx, thresholds, ids)
        p_b_outer = _fit_predict(xb[cal_idx], y[cal_idx], xb[outer_idx], cfg)
        p_a_outer = _fit_predict(np.column_stack([xb[cal_idx], lb_cal]), y[cal_idx], np.column_stack([xb[outer_idx], lb_outer]), cfg)
        p_sel = p_a_outer if promote else p_b_outer
        outer_groups = [groups[i] for i in outer_idx]
        base_ll = _macro_metric(y[outer_idx], p_b_outer, outer_groups)
        aug_ll = _macro_metric(y[outer_idx], p_a_outer, outer_groups)
        sel_ll = _macro_metric(y[outer_idx], p_sel, outer_groups)
        base_br = _macro_metric(y[outer_idx], p_b_outer, outer_groups, 'brier')
        aug_br = _macro_metric(y[outer_idx], p_a_outer, outer_groups, 'brier')
        sel_br = _macro_metric(y[outer_idx], p_sel, outer_groups, 'brier')
        delta = sel_ll - base_ll
        always_delta = aug_ll - base_ll
        if promote and delta < 0:
            terminal = 'favorable_predictive_improvement'
        elif not promote and delta == 0 and aug_ll < base_ll:
            terminal = 'conservative_miss'
        elif not promote and delta == 0:
            terminal = 'protective_null'
        elif delta > 0:
            terminal = 'adverse_selective_promotion'
        else:
            terminal = 'tie_or_unclassified'

        result = {
            **base,
            'status': 'terminal_predictive_result',
            'terminal_class': terminal,
            'counts_as_predictive_evidence': True,
            'response_file_md5': md5,
            'response_row_count': len(resp_rows),
            'response_columns': resp_cols,
            'deployment_id_column_used': dep_alias,
            'scientific_name_column_used': sci_alias,
            'focal_scientific_name': focal,
            'partition_counts': cc,
            'local_threshold_km': thresholds,
            'inner_validation': {'baseline_macro_log_loss': val_base, 'augmented_macro_log_loss': val_aug, 'augmented_minus_baseline': val_aug-val_base, 'promote_layer_b': promote},
            'outer': {
                'baseline_macro_log_loss': base_ll, 'always_augmented_macro_log_loss': aug_ll, 'selected_macro_log_loss': sel_ll,
                'selected_minus_baseline': delta, 'always_augmented_minus_baseline': always_delta, 'selected_minus_always_augmented': sel_ll-aug_ll,
                'baseline_macro_brier': base_br, 'always_augmented_macro_brier': aug_br, 'selected_macro_brier': sel_br,
            },
            'known_truth_translation_to_real_improvement_supported': bool(delta < 0),
            'selector_protective_behavior_observed': bool((not promote) and aug_ll >= base_ll),
            'closed_eog_wf_unchanged': True,
        }
    except Exception as exc:
        result = {
            **base,
            'status': 'terminal_stop_after_or_before_response',
            'reason': str(exc),
            'counts_as_predictive_evidence': False,
            'closed_eog_wf_unchanged': True,
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
