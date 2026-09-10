from __future__ import annotations
import hashlib, json
from pathlib import Path
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONTRACT=HERE/'source_selection_contract.json'
OUTPUT=ROOT/'build/raccoon_rabies_selective_promotion/gate0_metadata.json'
URL='https://zenodo.org/api/records/5009339'

def main():
    c=json.loads(CONTRACT.read_text())
    base={'schema':'eog.raccoon_rabies_selective_promotion.gate0_metadata.v1','attempt_id':c['attempt_id'],'metadata_requests':0,'file_payload_requests':0,'file_payload_bytes_opened':0,'csv_header_bytes_opened':0,'csv_rows_opened':0,'response_values_opened':False,'model_fits':0,'heldout_scores':0,'counts_as_predictive_evidence':False}
    try:
        req=Request(URL,headers={'User-Agent':'eog-raccoon-rabies-gate0/1.0'})
        with urlopen(req,timeout=30) as r: data=json.loads(r.read().decode())
        base['metadata_requests']=1
        files=data.get('files') or []
        inv=[{'key':x.get('key'),'size':x.get('size'),'checksum':x.get('checksum'),'id':x.get('id'),'content':(x.get('links') or {}).get('content')} for x in files]
        by={x['key']:x for x in inv}
        for name,spec in c['public_file_expectations'].items():
            if name not in by: raise RuntimeError(f'missing frozen file: {name}')
            if str(by[name].get('checksum')) != 'md5:'+spec['md5']: raise RuntimeError(f'checksum drift: {name}')
        result={**base,'status':'gate0_metadata_ready_for_covariate_freeze','inventory':inv,'next_gate':'freeze exact CovariateData identity and authorize it alone; SurveillanceData remains forbidden'}
    except Exception as e:
        result={**base,'status':'stop_pre_response_metadata_identity_or_transport','reason':str(e),'next_gate':'none; no repair within this attempt'}
    result['fingerprint']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
