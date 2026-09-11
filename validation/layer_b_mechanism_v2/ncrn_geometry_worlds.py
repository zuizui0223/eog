#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'validation/layer_b_mechanism_v2/ncrn_geometry_world_contract_v1.json'
AMENDMENT = ROOT / 'validation/layer_b_mechanism_v2/ncrn_geometry_missing_coordinate_amendment_v1.json'
OUT = ROOT / 'build/layer_b_mechanism_v2/ncrn_geometry_worlds/geometry_worlds.json'
URL = 'https://irma.nps.gov/DataStore/DownloadFile/757401?Reference=2317363'


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'eog-ncrn-geometry-worlds/2'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float, radius: float) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    return 2.0 * radius * math.asin(math.sqrt(a))


def _quantile_linear(values: list[float], q: float) -> float:
    if not values:
        raise RuntimeError('no values for quantile')
    x = sorted(values)
    i = (len(x) - 1) * q
    lo = math.floor(i)
    hi = math.ceil(i)
    if lo == hi:
        return float(x[lo])
    f = i - lo
    return float(x[lo] * (1.0 - f) + x[hi] * f)


def _finite_float(raw: object) -> float | None:
    text = str(raw or '').strip()
    if not text or text.lower() in {'na', 'n/a', 'nan', 'null', 'none'}:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = json.loads(CONTRACT.read_text())
    a = json.loads(AMENDMENT.read_text())
    result = {
        'schema': 'eog.layer_b_mechanism_v2.ncrn_geometry_worlds.v2',
        'pre_response_amendment': str(AMENDMENT.relative_to(ROOT)),
        'response_payload_requests': 0,
        'response_bytes_opened': 0,
        'response_values_opened': False,
        'model_fits': 0,
        'heldout_scores': 0,
        'response_open_authorized': False,
    }
    try:
        if a['response_payload_requests_so_far'] != 0:
            raise RuntimeError('geometry amendment was not frozen at zero response access')
        data = _get(URL)
        observed_sha = hashlib.sha256(data).hexdigest()
        expected_sha = c['source']['points_sha256']
        if observed_sha != expected_sha:
            raise RuntimeError(f'points SHA256 changed: expected {expected_sha}, got {observed_sha}')
        text = data.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        expected = {c['source']['site_key'], c['source']['latitude'], c['source']['longitude']}
        if reader.fieldnames is None or not expected.issubset(set(reader.fieldnames)):
            raise RuntimeError(f'points header missing frozen fields: {sorted(expected)}')
        coords: dict[str, tuple[float, float]] = {}
        row_count = 0
        excluded_blank_site_rows = 0
        excluded_missing_coordinate_rows = 0
        finite_rows = 0
        for row in reader:
            row_count += 1
            sid = str(row[c['source']['site_key']] or '').strip()
            if not sid:
                excluded_blank_site_rows += 1
                continue
            lat = _finite_float(row[c['source']['latitude']])
            lon = _finite_float(row[c['source']['longitude']])
            if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                excluded_missing_coordinate_rows += 1
                continue
            finite_rows += 1
            pair = (lat, lon)
            if sid in coords and coords[sid] != pair:
                raise RuntimeError(f'coordinate conflict for duplicate site {sid}')
            coords[sid] = pair
        if len(coords) < int(c['registry_rule']['minimum_unique_sites']):
            raise RuntimeError(f'only {len(coords)} unique finite-coordinate sites')
        items = sorted(coords.items())
        radius = float(c['distance_rule']['earth_radius_km'])
        distances: list[float] = []
        zero_distance_distinct_site_pairs = 0
        for i in range(len(items)):
            _, (lat1, lon1) = items[i]
            for j in range(i + 1, len(items)):
                _, (lat2, lon2) = items[j]
                d = _haversine(lat1, lon1, lat2, lon2, radius)
                if not math.isfinite(d):
                    raise RuntimeError('nonfinite haversine distance')
                if d > 0.0:
                    distances.append(d)
                else:
                    zero_distance_distinct_site_pairs += 1
        qs = [float(q) for q in c['distance_rule']['world_threshold_quantiles']]
        thresholds = [_quantile_linear(distances, q) for q in qs]
        if not all(x > 0.0 for x in thresholds):
            raise RuntimeError(f'nonpositive thresholds: {thresholds}')
        if not all(thresholds[i] < thresholds[i + 1] for i in range(len(thresholds) - 1)):
            raise RuntimeError(f'thresholds not strictly increasing: {thresholds}')
        world_ids = c['world_family']['local_world_ids_in_order']
        registry_payload = [[sid, lat, lon] for sid, (lat, lon) in items]
        registry_sha = hashlib.sha256(json.dumps(registry_payload, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        result.update({
            'status': 'geometry_worlds_qualified',
            'points_sha256': observed_sha,
            'points_row_count': row_count,
            'finite_coordinate_rows': finite_rows,
            'excluded_blank_site_rows': excluded_blank_site_rows,
            'excluded_missing_or_invalid_coordinate_rows': excluded_missing_coordinate_rows,
            'unique_sites': len(coords),
            'unique_coordinate_pairs': len(set(coords.values())),
            'registry_sha256': registry_sha,
            'positive_pairwise_distance_count': len(distances),
            'zero_distance_distinct_site_pairs': zero_distance_distinct_site_pairs,
            'pairwise_distance_min_km': min(distances),
            'pairwise_distance_max_km': max(distances),
            'worlds': [
                {'world_id': wid, 'quantile': q, 'threshold_km': t}
                for wid, q, t in zip(world_ids, qs, thresholds)
            ] + [{'world_id': c['world_family']['external_open_world_id'], 'threshold_km': None}],
            'declared_world_count': int(c['world_family']['declared_world_count']),
            'next_gate': 'freeze_exact_threshold_values_and_full_pre_response_execution_contract',
        })
        rc = 0
    except Exception as exc:
        result['status'] = 'terminal_pre_response_geometry_world_stop'
        result['error'] = f'{type(exc).__name__}: {exc}'
        rc = 2
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
