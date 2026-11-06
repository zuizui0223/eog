"""Exploratory, fixed-source capture-resource geometry; not full BAM causality.

Contract: validation/charaxes_empirical_geometry_v1/analysis_contract.json,
committed at 3ff68b0a6418917922926b63e118d53d9981d9e0 before scoring.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

SOURCE_SHA='9338e8f064079c7f9694a55d9b948afedd93b9ac74c771befcbff48218376cd8'
SEED=20261106
METRICS=('span','centroid_mean','mst_compactness','gap_strength')
PANELS={'primary':['HPC_5','dist_min'], 'add_connectivity':['HPC_5','dist_min','Ci'],
        'add_local_cover':['HPC_05','HPC_5','dist_min']}

def transform(x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or len(x)<2 or not np.isfinite(x).all():
        raise ValueError('finite n x p matrix with n>=2 required')
    center=np.median(x,axis=0)
    constant=np.ptp(x,axis=0)==0
    scale=x.std(axis=0,ddof=0)
    scale[constant]=1.
    z=(x-center)/scale
    z[:,constant]=0.
    return z,{'center':center.tolist(),'scale':scale.tolist(),'constant':constant.tolist(),
              'definition':'pooled full-survey median center / population SD; log1p inputs'}

def geometry(x,full=True):
    x=np.asarray(x,float)
    if len(x)<2 or not np.isfinite(x).all():
        raise ValueError('geometry requires >=2 finite observations')
    distances=np.sqrt(np.sum((x[:,None,:]-x[None,:,:])**2,axis=2))
    upper=distances[np.triu_indices(len(x),1)]
    positive=upper[upper>0]
    result={'span':float(np.quantile(positive,.9)) if len(positive) else 0.,
            'centroid_mean':float(np.linalg.norm(x-x.mean(0),axis=1).mean())}
    if full:
        # Same deterministic Prim algorithm and zero-edge semantics as eog.geometry.
        visited=np.zeros(len(x),bool);visited[0]=True
        best=distances[0].copy();lengths=[]
        for _ in range(1,len(x)):
            target=int(np.argmin(np.where(visited,np.inf,best)))
            lengths.append(float(best[target]));visited[target]=True
            best=np.minimum(best,distances[target])
        lengths=np.asarray(lengths)
        total=float(lengths.sum());pos=lengths[lengths>0]
        result['mst_compactness']=float(upper.max()/total) if total else 1.
        result['gap_strength']=float(pos.max()/np.median(pos)) if len(pos) else 1.
    return result

def make_strata(d,positive):
    groups=[]
    for _,indexes in d.groupby(['district_ID','year','oak_species'],sort=True).indices.items():
        indexes=np.asarray(indexes,int)
        n=int(positive[indexes].sum())
        if n: groups.append((indexes,n))
    return groups

def draw_indices(strata,rng):
    return np.sort(np.concatenate([rng.choice(indexes,size=n,replace=False) for indexes,n in strata]))

def read_source(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError('original source SHA mismatch')
    d=pd.read_csv(path,sep=';',decimal=',')
    if len(d)!=1544 or not d.trap_ID.is_unique or d.isna().any().any():
        raise ValueError('source rows, IDs or missingness changed')
    if not np.array_equal(d.occupancy_jasius,np.asarray(d.n_jasius>0,dtype=int)):
        raise ValueError('detection count disagreement')
    if not set(d.year)=={2018,2019,2020,2021}:
        raise ValueError('year scope changed')
    if not d.filter(regex='^HPC_').apply(lambda x:x.between(0,100).all()).all():
        raise ValueError('host percent range error')
    if (d[['Ci','dist_min']]<0).any().any(): raise ValueError('negative index/distance')
    return d

def run(path,output,draws=999,lodo_draws=199):
    d=read_source(path);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    p=d.occupancy_jasius.to_numpy(bool);n=int(p.sum())
    strata=make_strata(d,p)
    rng=np.random.default_rng(SEED)
    # Identical sampled record IDs across feature panels, never outcome-tuned draws.
    null_ids={
      'unconditional':[np.sort(rng.choice(len(d),n,replace=False)) for _ in range(draws)],
      'district_year_oak':[draw_indices(strata,rng) for _ in range(draws)]}
    records=[];draw_records=[];references={};zs={}
    for panel,features in PANELS.items():
        x=d[features].to_numpy(float).copy()
        if 'dist_min' in features:x[:,features.index('dist_min')]/=1000.
        z,reference=transform(np.log1p(x));references[panel]=reference;zs[panel]=z
        observed=geometry(z[p])
        for scheme,ids in null_ids.items():
            sim=[geometry(z[index]) for index in ids]
            for j,row in enumerate(sim): draw_records.append({'panel':panel,'scheme':scheme,'draw':j,**row})
            for metric in METRICS:
                a=np.array([r[metric] for r in sim]);v=observed[metric]
                low=(1+int(np.sum(a<=v)))/(draws+1)
                high=(1+int(np.sum(a>=v)))/(draws+1)
                records.append({'panel':panel,'scheme':scheme,'metric':metric,'observed':v,
                   'null_median':float(np.median(a)),'observed_over_null_median':float(v/np.median(a)),
                   'null_q05':float(np.quantile(a,.05)),'null_q95':float(np.quantile(a,.95)),
                   'exploratory_two_sided_mc_p':min(1.,2*min(low,high)),'draws':draws})
    lodo=[];z=zs['primary']
    for district in sorted(d.district_ID.unique()):
        keep=d.district_ID.to_numpy()!=district
        sub=d.loc[keep].reset_index(drop=True);pp=p[keep];zz=z[keep]
        observed=geometry(zz[pp],full=False)['span']
        ss=make_strata(sub,pp);rr=np.random.default_rng(SEED+int(district))
        sim=np.array([geometry(zz[draw_indices(ss,rr)],full=False)['span'] for _ in range(lodo_draws)])
        lodo.append({'excluded_district':int(district),'remaining_records':int(keep.sum()),
                    'positive_records':int(pp.sum()),'observed_span':observed,'null_median_span':float(np.median(sim)),
                    'ratio':float(observed/np.median(sim)),'draws':lodo_draws})
    qc={'records':len(d),'positive_records':n,'non_detections':int((~p).sum()),'captured_individuals':int(d.n_jasius.sum()),
        'districts':int(d.district_ID.nunique()),'years':{str(y):int(c) for y,c in d.year.value_counts().sort_index().items()},
        'strata_with_positive_records':len(strata),'all_strata':int(d.groupby(['district_ID','year','oak_species']).ngroups),
        'original_source_sha256':SOURCE_SHA,'unique_trap_ids':int(d.trap_ID.nunique()),'missing_cells':0,
        'inference_unit':'trap record; repeated spatial dependence not ruled out by unique ID',
        'scope_discrepancy':'Reduced CSV1544/2018-2021, not public description1666/seven years'}
    result={'schema':'eog.charaxes.capture_resource_geometry.v1','status':'RETROSPECTIVE_EXPLORATORY',
            'contract_commit':'3ff68b0a6418917922926b63e118d53d9981d9e0','seed':SEED,'data_quality':qc,
            'features':PANELS,'references':references,'contrasts':records,'leave_one_district_out':lodo,
            'limits':['Not full independently measured BAM: no climate or coordinates; host-derived B/M proxies overlap.',
            'Nondetections are not certified absences; no trap effort/detection-replicate information.',
            'Conditional draws assume exchangeability within district/year/oak; residual spatial dependence remains.',
            'Null quantiles are resampling reference ranges, not confidence intervals on a natural population effect.',
            'Environmental MST gap and compactness are descriptive, not geographic fragmentation or routes.']}
    payload=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n'
    (output/'result.json').write_text(payload,encoding='utf-8')
    pd.DataFrame(records).to_csv(output/'geometry_contrasts.csv',index=False)
    pd.DataFrame(draw_records).to_csv(output/'null_draws.csv',index=False)
    pd.DataFrame(lodo).to_csv(output/'leave_one_district_out.csv',index=False)
    (output/'result_sha256.txt').write_text(hashlib.sha256(payload.encode()).hexdigest()+'\n')
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--output-dir',required=True)
    a.add_argument('--draws',type=int,default=999);a.add_argument('--lodo-draws',type=int,default=199)
    args=a.parse_args();r=run(args.source,args.output_dir,args.draws,args.lodo_draws)
    print(json.dumps({'data_quality':r['data_quality'],'contrasts':r['contrasts'],
         'lodo_span_increase':sum(x['ratio']>1 for x in r['leave_one_district_out'])},indent=2))
