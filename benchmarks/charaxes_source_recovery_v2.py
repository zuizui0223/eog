"""Versioned same-source repair of the old HTTP406; no ecological scoring.

Only Accept changes, to */*. Original URLs, sizes and MD5 remain fixed.
No retries, mirrors, tokens, or unapproved redirect hosts. Successful bytes
are cached once for reproducible offline analysis; failed bytes are not saved.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

FILES = (
    {'name':'C_jasius_readme.csv','size':1068,'md5':'296db7fac71b138ec6d84f99391388e0'},
    {'name':'C_jasius_reduced_dataset.csv','size':152897,'md5':'6f9f638a1c6966f567c4b7b783a5a47d'},
)
BASE = 'https://zenodo.org/api/records/20525795/files/'

def check_url(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.hostname != 'zenodo.org' or parts.username or parts.password:
        raise ValueError('unapproved source or redirect host')

class SameHostRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch_verified(entry, opener=None):
    url = entry.get('url', BASE + entry['name'] + '/content')
    check_url(url)
    open_ = opener or build_opener(SameHostRedirect()).open
    request = Request(url, headers={
        'Accept':'*/*', 'Accept-Encoding':'identity',
        'User-Agent':'EOG-BAM-CharaxesSchemaGate/1',
    })
    with open_(request, timeout=35) as response:
        check_url(response.geturl())
        if response.status != 200:
            raise ValueError(f'HTTP {response.status}')
        if response.headers.get('Content-Encoding','identity').lower() != 'identity':
            raise ValueError('unexpected content encoding')
        raw = response.read(entry['size']+1)
        content_type = response.headers.get('Content-Type','')
    if len(raw) != entry['size']:
        raise ValueError(f"size mismatch: {len(raw)} != {entry['size']}")
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != entry['md5']:
        raise ValueError('original repository MD5 mismatch')
    return raw, {'name':entry['name'], 'url':url, 'size':len(raw), 'md5':md5,
                 'sha256':hashlib.sha256(raw).hexdigest(), 'content_type':content_type}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'schema':'eog.charaxes.same_source_recovery.v2',
               'prior_v1_run':40862766046,'prior_v1_status':'SOURCE_STOP_HTTP_406',
               'protocol_commit':'37d810d1beb02bc9449f0a7e392bd6080801e609',
               'request_change':'Accept: */*; same endpoints, size and MD5',
               'files':[], 'ecological_rows_scored':0, 'status':'STARTED'}
    exit_status=0
    for entry in FILES:
        try:
            raw, info = fetch_verified(entry)
            (args.output_dir/entry['name']).write_bytes(raw)
            receipt['files'].append(info)
        except Exception as exc:
            receipt['status']='SOURCE_STOP'
            receipt['error_type']=type(exc).__name__
            receipt['error']=str(exc)
            receipt['stopped_at']=entry['name']
            exit_status=1
            break
    else:
        receipt['status']='FILES_VERIFIED_AND_CACHED_NO_ECOLOGICAL_SCORING'
    payload=json.dumps(receipt, sort_keys=True, indent=2)+'\n'
    (args.output_dir/'transport_receipt.json').write_text(payload, encoding='utf-8')
    print(payload)
    return exit_status

if __name__ == '__main__':
    sys.exit(main())
