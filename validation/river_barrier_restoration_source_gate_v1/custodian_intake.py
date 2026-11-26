"""Elwha intake helper; run the mixed-table split ONLY on the custodian side."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import tempfile

GEOMETRY = ('reach_break', 'UTM_easting', 'UTM_northing')
RESPONSE = ('Reach_ID', 'Reach_Code', 'Reach_Name', 'Year', 'Reach_Length_km',
            'Upstream_Reach_Boundary_rkm', 'Downstream_Reach_Boundary_rkm',
            'Section', 'Count_Saco', 'Count_Onxx', 'Count_Onts', 'Count_Onmy',
            'Fish_km_Saco', 'Fish_km_Onxx', 'Fish_km_Onts', 'Fish_km_Onmy',
            'JONTS', 'JONKI', 'JONXX')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def verified_bytes(path, expected):
    if not re.fullmatch(r'[0-9a-fA-F]{64}', expected):
        raise ValueError('expected SHA-256 is required')
    raw = path.read_bytes()
    if sha256(raw) != expected.lower():
        raise ValueError('source SHA-256 mismatch')
    return raw


def rows(raw, header):
    reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
    if tuple(next(reader, ())) != header:
        raise ValueError('header differs from pinned FGDC metadata')
    for row in reader:
        if len(row) != len(header):
            raise ValueError('malformed row; contents suppressed')
        yield row


def geometry_receipt(path, expected_sha, provenance):
    if path.name != 'Elwha_Riverscape_reach_breaks.csv' or not provenance.strip():
        raise ValueError('exact geometry filename and provenance required')
    raw = verified_bytes(path, expected_sha)
    ids = set()
    for label, easting, northing in rows(raw, GEOMETRY):
        label = label.strip()
        if not label or label in ids:
            raise ValueError('empty or duplicate boundary identifier')
        try:
            valid = math.isfinite(float(easting)) and math.isfinite(float(northing))
        except ValueError:
            valid = False
        if not valid:
            raise ValueError('nonfinite or invalid coordinate; value suppressed')
        ids.add(label)
    if not ids:
        raise ValueError('empty geometry registry')
    return {'status': 'GEOMETRY_SCHEMA_ONLY_CRS_AND_REACH_JOIN_PENDING',
            'source': path.name, 'sha256': sha256(raw), 'bytes': len(raw),
            'provenance_declared_by_caller': provenance, 'unique_boundary_ids': len(ids),
            'publisher_identity_independently_verified': False,
            'response_payloads_opened': 0, 'graph_built': False, 'scores': 0}


def split_for_custodian(path, expected_sha, output, provenance, confirmed):
    if not confirmed:
        raise ValueError('custodian role confirmation required')
    if path.name != 'Elwha_Riverscape_reach_data.csv' or not provenance.strip():
        raise ValueError('exact mixed-table filename and provenance required')
    if output.exists():
        raise ValueError('output must be new')
    raw = verified_bytes(path, expected_sha)
    # The custodian reads the physical mixed payload; the analyst must not.
    pre, post = [], []
    seen = set()
    for row in rows(raw, RESPONSE):
        year = row[3].strip()
        if year not in {'2007', '2008', '2018', '2019'}:
            raise ValueError('unexpected year; values suppressed')
        seen.add(year)
        (pre if year in {'2007', '2008'} else post).append(row)
    if seen != {'2007', '2008', '2018', '2019'}:
        raise ValueError('four-wave coverage not confirmed')
    # Do not inspect outcome cells or expose per-year post counts in the receipt.
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp) / 'bundle'
        stage.mkdir()
        for name, group in [('pre_2007_2008.csv', pre), ('post_2018_2019_SEALED.csv', post)]:
            with (stage / name).open('w', encoding='utf-8', newline='') as f:
                w = csv.writer(f, lineterminator='\n')
                w.writerow(RESPONSE)
                w.writerows(group)
        receipt = {'status': 'CUSTODIAN_SPLIT_CREATED_NOT_ANALYSIS_AUTHORIZATION',
                   'source_sha256': sha256(raw), 'source_bytes': len(raw),
                   'provenance_declared_by_custodian': provenance,
                   'mixed_payload_physically_read_by_custodian': True,
                   'pre_years': [2007, 2008], 'post_years': [2018, 2019],
                   'pre_sha256': sha256((stage / 'pre_2007_2008.csv').read_bytes()),
                   'sealed_post_sha256': sha256((stage / 'post_2018_2019_SEALED.csv').read_bytes()),
                   'response_values_logged': False,
                   'analyst_post_access_authorized': False, 'scores': 0}
        (stage / 'split_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        # Atomic within the destination parent; no overwrite of an existing bundle.
        if output.exists():
            raise ValueError('output already exists')
        stage.rename(output)
    return receipt


def self_test():
    with tempfile.TemporaryDirectory() as temp:
        d = Path(temp)
        g = d / 'Elwha_Riverscape_reach_breaks.csv'
        g.write_bytes(b'reach_break,UTM_easting,UTM_northing\na,1,2\nb,3,4\n')
        r = geometry_receipt(g, sha256(g.read_bytes()), 'synthetic fixture')
        assert r['unique_boundary_ids'] == 2 and not r['graph_built']
        m = d / 'Elwha_Riverscape_reach_data.csv'
        with m.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(RESPONSE)
            for year in ('2007', '2008', '2018', '2019'):
                w.writerow(['A', 'B', 'C', year] + ['fixture_POST' if year.startswith('201') else 'fixture_PRE'] * 15)
        out = d / 'split'
        try:
            split_for_custodian(m, sha256(m.read_bytes()), out, 'synthetic fixture', False)
        except ValueError:
            pass
        else:
            raise AssertionError('unconfirmed split accepted')
        r = split_for_custodian(m, sha256(m.read_bytes()), out, 'synthetic fixture', True)
        assert 'fixture_POST' not in (out / 'pre_2007_2008.csv').read_text()
        assert 'fixture_PRE' not in (out / 'post_2018_2019_SEALED.csv').read_text()
        assert 'fixture_POST' not in json.dumps(r) and not r['analyst_post_access_authorized']
        try:
            geometry_receipt(g, '0'*64, 'synthetic fixture')
        except ValueError:
            pass
        else:
            raise AssertionError('bad checksum accepted')
    print('Offline custodian/geometry fixtures passed; no real CSV accessed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('self-test')
    for mode in ('geometry', 'custodian-split'):
        s = sub.add_parser(mode)
        s.add_argument('input', type=Path)
        s.add_argument('--expected-sha256', required=True)
        s.add_argument('--provenance', required=True)
        if mode == 'custodian-split':
            s.add_argument('--output', type=Path, required=True)
            s.add_argument('--confirm-custodian', action='store_true')
    args = parser.parse_args()
    if args.mode == 'self-test':
        self_test()
    elif args.mode == 'geometry':
        print(json.dumps(geometry_receipt(args.input, args.expected_sha256, args.provenance), indent=2))
    else:
        receipt = split_for_custodian(args.input, args.expected_sha256, args.output,
                                      args.provenance, args.confirm_custodian)
        print(json.dumps(receipt, indent=2))
