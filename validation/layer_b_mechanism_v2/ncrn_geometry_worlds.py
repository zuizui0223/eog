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
OUT = ROOT / 'build/layer_b_mechanism_v2/ncrn_geometry_worlds/geometry_worlds.json'
URL = 'https://irma.nps.gov/DataStore/DownloadFile/757401?Reference=2317363'


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'eog-ncrn-geometry-worlds/1'})
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


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = json.loads(CONTRACT.read_text())
    result = {
        'schema': 'eog.layer_b_mechanism_v2.ncrn_geometry_worlds.v1',
        'response_payload_requests': 0,
        'response_bytes_opened': 0,
        'response_values_opened': False,
        'model_fits': 0,
        'heldout_scores': 0,
        'response_open_authorized': False,
    }
    try:
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
        for row in reader:
            row_count += 1
            sid = str(row[c['source']['site_key']]).strip()
            if not sid:
                raise RuntimeError('blank Point_Name')
            lat = float(row[c['source']['latitude']])
            lon = float(row[c['source']['longitude']])
            if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise RuntimeError(f'invalid coordinates for {sid}')
            pair = (lat, lon)
            if sid in coords and coords[sid] != pair:
                raise RuntimeError(f'coordinate conflict for duplicate site {sid}')
            coords[sid] = pair
        if len(coords) < int(c['registry_rule']['minimum_unique_sites']):
            raise RuntimeError(f'only {len(coords)} unique sites')
        items = sorted(coords.items())
        radius = float(c['distance_rule']['earth_radius_km'])
        distances: list[float] = []
        for i in range(len(items)):
            _, (lat1, lon1) = items[i]
            for j in range(i + 1, len(items)):
                _, (lat2, lon2) = items[j]
                d = _haversine(lat1, lon1, lat2, lon2, radius)
                if math.isfinite(d) and d > 0.0:
                    distances.append(d)
        qs = [float(q) for q in c['distance_rule']['world_threshold_quantiles']]
        thresholds = [_quantile_linear(distances, q) for q in qs]
        if not all(x > 0.0 for x in thresholds):
            raise RuntimeError(f'nonpositive thresholds: {thresholds}')
        if not all(thresholds[i] < thresholds[i + 1] for i in range(len(thresholds) - 1)):
            raise RuntimeError(f'thresholds not strictly increasing: {thresholds}')
        world_ids = c['world_family']['local_world_ids_in_order']
        result.update({
            'status': 'geometry_worlds_qualified',
            'points_sha256': observed_sha,
            'points_row_count': row_count,
            'unique_sites': len(coords),
            'unique_coordinate_pairs': len(set(coords.values())),
            'positive_pairwise_distance_count': len(distances),
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
