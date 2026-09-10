from __future__ import annotations
import csv, hashlib, io, json
from pathlib import Path
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONTRACT=HERE/'stage1_covariate_contract.json'
OUTPUT=ROOT/'build/raccoon_rabies_selective_promotion/stage1_covariates.json'
URL='https://zenodo.org/api/records/5009339/files/CovariateData.csv/content'

def main():
    c=json.loads(CONTRACT.read_text())
    base={'schema':'eog.raccoon_rabies_selective_promotion.stage1_covariates.v1','attempt_id':c['attempt_id'],'response_requests':0,'response_header_bytes_opened':0,'response_rows_opened':0,'response_values_opened':False,'model_fits':0,'heldout_scores':0,'counts_as_predictive_evidence':False}
    try:
        req=Request(URL,headers={'User-Agent':'eog-raccoon-rabies-stage1/1.0'})
        with urlopen(req,timeout=60) as r: raw=r.read()
        spec=c['authorized_payload']
        if len(raw)!=spec['exact_size']: raise RuntimeError(f"size drift: {len(raw)}")
        md5=hashlib.md5(raw).hexdigest()
        if md5!=spec['md5']: raise RuntimeError(f'checksum drift: {md5}')
        rd=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))); cols=list(rd.fieldnames or []); rows=list(rd)
        low={x.lower():x for x in cols}
        def pick(names):
            for n in names:
                if n.lower() in low:return low[n.lower()]
            return next((x for x in cols if any(n.lower() in x.lower() for n in names)),None)
        site=pick(['site','grid','gridid','grid_id']); lat=pick(['latitude','lat']); lon=pick(['longitude','long','lon'])
        if not site or not lat or not lon: raise RuntimeError(f'required geometry schema missing; columns={cols}')
        coords=[]
        for r in rows:
            try: coords.append((r[site],float(r[lat]),float(r[lon])))
            except Exception: pass
        if len(coords)<50: raise RuntimeError(f'too few complete geometry rows: {len(coords)}')
        result={**base,'status':'stage1_covariates_ready_for_final_freeze','opened_file':{'size':len(raw),'md5':md5,'columns':cols,'rows':len(rows)},'identified_columns':{'site':site,'latitude':lat,'longitude':lon},'geometry':{'complete_rows':len(coords),'unique_sites':len({x[0] for x in coords}),'unique_coordinates':len({(round(x[1],6),round(x[2],6)) for x in coords})},'next_gate':'freeze SurveillanceData schema assumptions, deterministic site partition, baseline, Layer B and selector before one response access'}
    except Exception as e:
        result={**base,'status':'stop_pre_response_covariate_schema_or_transport','reason':str(e),'next_gate':'none; no repair within attempt'}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
