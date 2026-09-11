#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/layer_b_mechanism_v2/ncrn_r1_head_preflight/head_preflight.json'
URL = 'https://irma.nps.gov/DataStore/DownloadFile/757402?Reference=2317363'


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        'schema': 'eog.layer_b_mechanism_v2.ncrn_r1_head_preflight.v1',
        'url': URL,
        'method': 'HEAD',
        'response_payload_requests': 0,
        'response_body_bytes_opened': 0,
        'response_header_bytes_opened': 0,
        'response_values_opened': False,
        'model_fits': 0,
        'heldout_scores': 0,
        'response_open_authorized': False,
    }
    try:
        req = urllib.request.Request(URL, method='HEAD', headers={'User-Agent': 'eog-ncrn-r1-head-preflight/1'})
        with urllib.request.urlopen(req, timeout=60) as r:
            result['http_status'] = int(r.status)
            result['final_url'] = r.geturl()
            result['content_length'] = r.headers.get('Content-Length')
            result['content_type'] = r.headers.get('Content-Type')
            result['content_disposition'] = r.headers.get('Content-Disposition')
            result['etag'] = r.headers.get('ETag')
            result['last_modified'] = r.headers.get('Last-Modified')
        if result['http_status'] < 200 or result['http_status'] >= 400:
            raise RuntimeError(f"unexpected HEAD status {result['http_status']}")
        if result['content_length'] is not None and int(result['content_length']) <= 0:
            raise RuntimeError('nonpositive Content-Length')
        result['status'] = 'head_only_response_transport_qualified'
        result['live_route_qualified_without_payload'] = True
        rc = 0
    except Exception as exc:
        result['status'] = 'terminal_pre_response_r1_head_transport_stop'
        result['live_route_qualified_without_payload'] = False
        result['error'] = f'{type(exc).__name__}: {exc}'
        rc = 2
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
