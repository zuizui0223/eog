from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'validation/raccoon_rabies_selective_promotion/final_once_only_contract.json'
OUTPUT = ROOT / 'build/raccoon_rabies_selective_promotion/final_result.json'
COV_URL = 'https://zenodo.org/api/records/5009339/files/CovariateData.csv/content'
RESP_URL = 'https://zenodo.org/api/records/5009339/files/SurveillanceData.csv/content'


def get_bytes(url: str, ua: str) -> bytes:
    req = Request(url, headers={'User-Agent': ua})
    with urlopen(req, timeout=120) as r:  # noqa: S310 frozen public source
        return r.read()


def read_csv(raw: bytes):
    rd = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    return list(rd.fieldnames or []), list(rd)


def choose(cols, names):
    for n in names:
        if n in cols:
            return n
    low = {c.lower(): c for c in cols}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None


def num(x):
    if x is None or str(x).strip() == '':
        return 0.0
    return float(str(x).strip())


def site_bin(site: str) -> int:
    return int(hashlib.sha256(str(site).encode()).hexdigest()[:16], 16) % 10


def norm_season(x: str):
    s = str(x).strip().lower().replace('_', '-').replace(' ', '-')
    while '--' in s:
        s = s.replace('--', '-')
    aliases = {
        'spring-summer': 0, 'spring/summer': 0, 'spring': 0, 'summer': 0,
        'fall-winter': 1, 'fall/winter': 1, 'fall': 1, 'autumn': 1, 'winter': 1,
    }
    if s in aliases:
        return aliases[s], s
    return 2, s


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1); dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1.0, math.sqrt(a)))


def macro(y, p, groups, kind='logloss'):
    vals=[]
    for g in sorted(set(groups)):
        ii=np.array([x==g for x in groups])
        yg=y[ii]; pg=p[ii]
        if kind=='logloss':
            vals.append(log_loss(yg, np.column_stack([1-pg,pg]), labels=[0,1]))
        else:
            vals.append(float(np.mean((pg-yg)**2)))
    return float(np.mean(vals))


def fit_predict(xtr,ytr,xte,cfg):
    clf=RandomForestClassifier(n_estimators=cfg['n_estimators'],min_samples_leaf=cfg['min_samples_leaf'],max_features=cfg['max_features'],class_weight=cfg['class_weight'],random_state=cfg['random_state'],n_jobs=cfg['n_jobs'])
    clf.fit(xtr,ytr)
    return clf.predict_proba(xte)[:,list(clf.classes_).index(1)]


def main():
    c=json.loads(CONTRACT.read_text())
    base={'schema':'eog.raccoon_rabies_selective_promotion.final_result.v1','attempt_id':c['attempt_id'],'response_payload_requests':0,'response_payload_bytes_opened':0,'response_values_opened':False,'counts_as_predictive_evidence':False,'closed_eog_wf_unchanged':True}
    try:
        cov_raw=get_bytes(COV_URL,'eog-raccoon-rabies-final-covariates/1.0')
        if hashlib.md5(cov_raw).hexdigest()!='386c0498ace1dd9929c69119354dd7ae':  # noqa: S324
            raise RuntimeError('CovariateData checksum drift')
        cov_cols,cov_rows=read_csv(cov_raw)
        cov={str(r['Site']).strip():r for r in cov_rows}
        sites=sorted(cov)
        coords={s:(float(cov[s]['Latitude']),float(cov[s]['Longitude'])) for s in sites}
        ds=[]
        for i,s in enumerate(sites):
            for t in sites[i+1:]: ds.append(haversine(*coords[s],*coords[t]))
        thresholds=[float(np.quantile(np.asarray(ds),q)) for q in (.10,.25,.50,.75)]

        # Single authorized response access starts here.
        raw=get_bytes(RESP_URL,'eog-raccoon-rabies-final-response-once/1.0')
        base['response_payload_requests']=1; base['response_payload_bytes_opened']=len(raw); base['response_values_opened']=True
        if len(raw)!=c['response']['exact_size']: raise RuntimeError(f"response size drift: {len(raw)}")
        md5=hashlib.md5(raw).hexdigest()  # noqa: S324 provenance only
        if md5!=c['response']['md5']: raise RuntimeError(f'response checksum drift: {md5}')
        cols,rows=read_csv(raw)
        names=c['response']['required_fields_and_accepted_names']
        f={k:choose(cols,v) for k,v in names.items()}
        if any(v is None for v in f.values()): raise RuntimeError(f'response schema mismatch: identified={f}; columns={cols}')

        agg=defaultdict(lambda:{'pos':0.0,'neg':0.0,'methods':defaultdict(float)})
        method_values=set()
        for r in rows:
            site=str(r[f['site']]).strip()
            if site not in cov: continue
            yr=int(float(r[f['year']]))
            ss=str(r[f['season']]).strip()
            meth=str(r[f['method']]).strip()
            p=num(r[f['positive_count']]); n=num(r[f['negative_count']])
            key=(site,yr,ss); agg[key]['pos']+=p; agg[key]['neg']+=n; agg[key]['methods'][meth]+=p+n; method_values.add(meth)
        methods=sorted(method_values)
        units=[]
        for (site,yr,ss),a in agg.items():
            effort=a['pos']+a['neg']
            if effort<=0: continue
            srank,snorm=norm_season(ss)
            units.append({'site':site,'year':yr,'season':ss,'season_rank':srank,'season_norm':snorm,'y':1 if a['pos']>0 else 0,'effort':effort,'methods':a['methods']})
        units.sort(key=lambda u:(u['year'],u['season_rank'],u['season_norm'],u['site']))
        if not units: raise RuntimeError('no eligible site-season units')
        years=sorted({u['year'] for u in units}); y0=min(years); yspan=max(1,max(years)-y0)

        site_cov_names=['Longitude','Latitude','ORV','Cult','DFMF','EVF','Hay','MedHi','OpenLow','WT']
        Xb=[]; y=[]; groups=[]; bins=[]; contexts=[]
        for u in units:
            season_angle=math.pi*u['season_rank'] if u['season_rank']<2 else 0.0
            row=[float(cov[u['site']][k]) for k in site_cov_names]
            row += [(u['year']-y0)/yspan,math.sin(season_angle),math.cos(season_angle),math.log1p(u['effort'])]
            row += [u['methods'].get(m,0.0)/u['effort'] for m in methods]
            Xb.append(row); y.append(u['y']); groups.append(u['site']); bins.append(site_bin(u['site'])); contexts.append((u['year'],u['season_rank'],u['season_norm']))
        Xb=np.asarray(Xb,float); y=np.asarray(y,int)
        tr=[i for i,b in enumerate(bins) if b in c['partition']['inner_train_bins']]
        va=[i for i,b in enumerate(bins) if b in c['partition']['inner_validation_bins']]
        out=[i for i,b in enumerate(bins) if b in c['partition']['outer_heldout_bins']]

        def counts(idx):
            yy=y[idx]; gs=[groups[i] for i in idx]
            both=sum(1 for g in set(gs) if len(set(y[[j for j in idx if groups[j]==g]].tolist()))==2)
            return {'n':len(idx),'positive':int(yy.sum()),'negative':int(len(yy)-yy.sum()),'sites':len(set(gs)),'sites_with_both_classes':both}
        cc={'inner_train':counts(tr),'inner_validation':counts(va),'outer':counts(out)}
        mn=c['estimability_minima']
        checks=[cc['inner_train']['positive']>=mn['inner_train_positive_units'],cc['inner_train']['negative']>=mn['inner_train_negative_units'],cc['inner_validation']['positive']>=mn['inner_validation_positive_units'],cc['inner_validation']['negative']>=mn['inner_validation_negative_units'],cc['outer']['positive']>=mn['outer_positive_units'],cc['outer']['negative']>=mn['outer_negative_units'],cc['inner_validation']['sites_with_both_classes']>=mn['inner_validation_sites_with_both_classes'],cc['outer']['sites_with_both_classes']>=mn['outer_sites_with_both_classes']]
        if not all(checks): raise RuntimeError(f'estimability failure: {cc}')

        site_index={s:i for i,s in enumerate(sites)}
        D=np.zeros((len(sites),len(sites)))
        for i,s in enumerate(sites):
            for j,t in enumerate(sites): D[i,j]=haversine(*coords[s],*coords[t])

        def make_lb(target_idx, source_pool_idx):
            mat=[]
            for ti in target_idx:
                ctx=contexts[ti]; target_site=groups[ti]
                source_sites=sorted({groups[j] for j in source_pool_idx if y[j]==1 and contexts[j]<ctx and groups[j]!=target_site})
                if not source_sites:
                    mat.append(np.zeros(10)); continue
                support=np.zeros((len(source_sites),5,1))
                tgt=site_index[target_site]
                for si,s in enumerate(source_sites):
                    d=D[site_index[s],tgt]
                    for wi,th in enumerate(thresholds): support[si,wi,0]=float(d<=th)
                    support[si,4,0]=1.0
                res=summarize_source_symmetric_support(support,source_ids=source_sites,world_ids=['q10','q25','q50','q75','external_open'],node_ids=[target_site],declared_world_count=5)
                mat.append(res.feature_matrix[0])
            return np.asarray(mat,float)

        lb_tr=make_lb(tr,tr); lb_va=make_lb(va,tr)
        cfg=c['learner']
        pbv=fit_predict(Xb[tr],y[tr],Xb[va],cfg)
        pav=fit_predict(np.column_stack([Xb[tr],lb_tr]),y[tr],np.column_stack([Xb[va],lb_va]),cfg)
        vgroups=[groups[i] for i in va]
        vbase=macro(y[va],pbv,vgroups); vaug=macro(y[va],pav,vgroups); promote=bool(vaug<vbase)

        cal=tr+va; lb_cal=make_lb(cal,cal); lb_out=make_lb(out,cal)
        pbo=fit_predict(Xb[cal],y[cal],Xb[out],cfg)
        pao=fit_predict(np.column_stack([Xb[cal],lb_cal]),y[cal],np.column_stack([Xb[out],lb_out]),cfg)
        psel=pao if promote else pbo; og=[groups[i] for i in out]
        bll=macro(y[out],pbo,og); all_=macro(y[out],pao,og); sll=macro(y[out],psel,og)
        bbr=macro(y[out],pbo,og,'brier'); abr=macro(y[out],pao,og,'brier'); sbr=macro(y[out],psel,og,'brier')
        delta=sll-bll
        if promote and delta<0: term='favorable_predictive_improvement'
        elif not promote and delta==0 and all_<bll: term='conservative_miss'
        elif not promote and delta==0: term='protective_null'
        elif delta>0: term='adverse_selective_promotion'
        else: term='tie_or_unclassified'
        result={**base,'status':'terminal_predictive_result','terminal_class':term,'counts_as_predictive_evidence':True,'response_md5':md5,'response_columns':cols,'identified_response_fields':f,'response_row_count':len(rows),'method_categories':methods,'partition_counts':cc,'local_threshold_km':thresholds,'inner_validation':{'baseline_macro_log_loss':vbase,'augmented_macro_log_loss':vaug,'augmented_minus_baseline':vaug-vbase,'promote_layer_b':promote},'outer':{'baseline_macro_log_loss':bll,'always_augmented_macro_log_loss':all_,'selected_macro_log_loss':sll,'selected_minus_baseline':delta,'always_augmented_minus_baseline':all_-bll,'selected_minus_always_augmented':sll-all_,'baseline_macro_brier':bbr,'always_augmented_macro_brier':abr,'selected_macro_brier':sbr},'known_truth_translation_to_real_improvement_supported':bool(delta<0),'selector_protective_behavior_observed':bool((not promote) and all_>=bll)}
    except Exception as e:
        result={**base,'status':'terminal_stop_after_or_before_response','reason':str(e)}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
