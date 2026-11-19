"""Frozen target-scoped EOG experimental-analogue analysis.

Source and target rules are locked before row-level experimental response access at
validation/nutnet_hodapp_y3_target_v1/protocol_v1.json (EOG commit b5ae8afd).
This is NOT the original BAM mask-release or a fourth EOG-WF endpoint.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

EXPECTED = {
    "composition-data.csv": ("5d9455e9ec281ca351db250340f3a1e5", 1510812),
    "env-param-Y0.csv": ("663fe1ce5ce18ffb27462e99c0e3d2a6", 47604),
}
SALT = 'EOG_NUTNET_Y3_20261119_V1|'
TOL = 0.02
ALPHA = 10.
FAMILIES = ('mean', 'abiotic', 'biotic', 'joint')
ID = ['site_code', 'block', 'plot']


def read_verified(root):
    for file,(md5,nbytes) in EXPECTED.items():
        raw=(root/file).read_bytes()
        if len(raw)!=nbytes or hashlib.md5(raw, usedforsecurity=False).hexdigest()!=md5:
            raise ValueError('SOURCE_BYTE_STOP ' + file)
    comp=pd.read_csv(root/'composition-data.csv',dtype={'site_code':str,'block':str,'plot':str,'year_trt':int,'trt':str,'Taxon':str})
    env=pd.read_csv(root/'env-param-Y0.csv',dtype={'site_code':str,'block':str,'plot':str,'trt':str})
    assert list(comp.columns)==['site_code','block','plot','year_trt','trt','Taxon','cov']
    assert list(env.columns[:4])==['site_code','block','plot','trt']
    if comp.duplicated(ID+['year_trt','Taxon']).any():
        raise ValueError('SCIENCE_STOP duplicate plot-year-taxon')
    if env.duplicated(ID).any():
        raise ValueError('SCIENCE_STOP duplicate baseline env plot')
    if comp['cov'].isna().any() or (comp['cov']<0).any() or (comp['cov']>100).any() or not np.isfinite(comp['cov'].to_numpy()).all():
        raise ValueError('SCIENCE_STOP invalid cover')
    if comp[ID+['year_trt','trt']].isna().any().any():
        raise ValueError('SCIENCE_STOP invalid keys')
    if comp.groupby(ID).trt.nunique().gt(1).any():
        raise ValueError('SCIENCE_STOP treatment changes within plot')
    if comp.groupby(ID+['year_trt']).trt.nunique().gt(1).any():
        raise ValueError('SCIENCE_STOP treatment inconsistent per plot-year')
    return comp,env


def eligible_match(comp):
    plot_year=comp[ID+['year_trt','trt']].drop_duplicates()
    y0=plot_year[plot_year.year_trt.eq(0)][ID+['trt']].rename(columns={'trt':'t0'})
    y3=plot_year[plot_year.year_trt.eq(3)][ID+['trt']].rename(columns={'trt':'t3'})
    pair=y0.merge(y3,on=ID,how='inner')
    pair=pair[pair.t0.eq(pair.t3)&pair.t0.isin(['Control','Fence'])]
    counts=pair.groupby(['site_code','block','t0']).size().unstack(fill_value=0)
    if 'Control' not in counts: counts['Control']=0
    if 'Fence' not in counts: counts['Fence']=0
    good=counts[(counts['Control']==1)&(counts['Fence']==1)]
    blocks=defaultdict(list)
    for site,block in good.index:
        blocks[site].append(block)
    valid={site:sorted(blk) for site,blk in blocks.items() if len(blk)>=3}
    return valid, {'all_site_codes':comp.site_code.nunique(),'all_blocks':comp.groupby(['site_code','block']).ngroups,
                   'Y0_Y3_paired_plots':len(y0.merge(y3,on=ID,how='inner')),
                   'one_control_one_fence_blocks':len(good),
                   'minimum_3_matched_site_count':len(valid),
                   'excluded_site_codes':sorted(set(comp.site_code)-set(valid))}


def positive_span(x):
    x=np.asarray(x,float)
    if x.ndim!=2 or len(x)<2: raise ValueError('not enough plot community points')
    delta=x[:,None,:]-x[None,:,:]
    d=np.sqrt(np.sum(delta**2,axis=2))
    pairs=d[np.triu_indices(len(x),1)]
    positives=pairs[pairs>0]
    return float(np.quantile(positives,0.90)) if len(positives) else 0.


def jaccard(x,y):
    a=set(x); b=set(y)
    if not a and not b:return 0.
    return 1.-len(a&b)/len(a|b)


def site_metrics(comp, env, site, blocks):
    t=comp[(comp.site_code==site)&(comp.block.isin(blocks))&(comp.year_trt.isin((0,3)))&(comp.trt.isin(('Control','Fence')))].copy()
    key=['site_code','block','plot','year_trt','trt']
    plot_year=t[key].drop_duplicates()
    if len(plot_year)!=4*len(blocks):
        raise ValueError(f'SCIENCE_STOP unexpected matched plot count at {site}: {len(plot_year)} vs {4*len(blocks)}')
    pivot=t.pivot_table(index=key,columns='Taxon',values='cov',aggfunc='first',fill_value=0.,sort=True)
    if len(pivot)!=4*len(blocks): raise ValueError('plot-year count changed during pivot')
    arr=pivot.to_numpy(float)
    den=arr.sum(axis=1)
    hellinger=np.sqrt(np.divide(arr,den[:,None],out=np.zeros_like(arr),where=den[:,None]>0))
    baseline_sets={}
    group_vectors={}
    for i,(site_code,block,plot,year,trt) in enumerate(pivot.index):
        if year==0:
            baseline_sets[(str(block),str(plot),trt)] = set(pivot.columns[arr[i,:]>0])
        group_vectors.setdefault((trt,int(year)),[]).append(hellinger[i])
    spans={trt:{int(year):positive_span(group_vectors[(trt,year)]) for year in (0,3)} for trt in ('Control','Fence')}
    effect=(spans['Fence'][3]-spans['Fence'][0])-(spans['Control'][3]-spans['Control'][0])
    # block-wise Jaccard turnover contrast, separately from primary outcome
    d_jacc=[]
    for block in blocks:
        values={}
        for trt in ('Control','Fence'):
            pr=plot_year[(plot_year.block==block)&(plot_year.year_trt==0)&(plot_year.trt==trt)]
            assert len(pr)==1
            plot=str(pr.iloc[0]['plot'])
            def seen(year):
                k=(site,str(block),plot,year,trt)
                return set(pivot.columns[pivot.loc[k].to_numpy()>0])
            values[trt]=jaccard(seen(0),seen(3))
        d_jacc.append(values['Fence']-values['Control'])
    y0=plot_year[plot_year.year_trt==0]
    y0arr=t[t.year_trt.eq(0)]
    sampled=y0arr.groupby(['block','plot','trt']).Taxon.nunique().to_numpy()
    richness=float(sampled.mean())
    y0hl=np.array(group_vectors[('Control',0)] +group_vectors[('Fence',0)])
    # robust global Y0 within-site pairwise Hellinger span and Jaccard heterogeneity
    y0span=positive_span(y0hl)
    y0sets=list(baseline_sets.values())
    dissim=[jaccard(y0sets[i],y0sets[j]) for i in range(len(y0sets)) for j in range(i+1,len(y0sets))]
    predictors={'y0_richness':richness,'y0_span':y0span,'y0_mean_jaccard':float(np.mean(dissim))}
    e=env[env.site_code==site]
    if e.empty:raise ValueError('SCIENCE_STOP baseline environment site absent '+site)
    for column in env.columns:
        if column in ID or column=='trt':continue
        if not pd.api.types.is_numeric_dtype(env[column]):
            raise ValueError('SCIENCE_STOP nonnumeric baseline environmental predictor '+column)
        predictors['E_'+column]=float(e[column].median()) if e[column].notna().any() else float('nan')
    return {'site':site, 'n_matched_blocks':len(blocks), 'D_site':float(effect),
            'Y_site_sign':1 if effect>TOL else -1 if effect< -TOL else 0,
            'secondary_jaccard_median_block_effect':float(np.median(d_jacc)),
            'spans':spans,'predictors':predictors}


def matrices(rows,train,test,family):
    if family=='mean':return None,None
    if family=='biotic': keys=['y0_richness','y0_span','y0_mean_jaccard']
    elif family=='abiotic':keys=sorted(k for k in rows[0]['predictors'] if k.startswith('E_'))
    elif family=='joint':keys=sorted(rows[0]['predictors'])
    else:raise ValueError(family)
    def col(indices):
        return np.asarray([[rows[i]['predictors'].get(k,np.nan) for k in keys] for i in indices],float)
    xtrain=col(train);xtest=col(test)
    miss=np.isnan(xtrain);missing_test=np.isnan(xtest)
    med=np.asarray([np.nanmedian(xtrain[:,j]) if np.any(np.isfinite(xtrain[:,j])) else 0 for j in range(len(keys))])
    xtrain=np.where(miss,med,xtrain);xtest=np.where(missing_test,med,xtest)
    # no leakage; missingness indicators always present even if constant
    xtrain=np.column_stack([xtrain,miss.astype(float)]);xtest=np.column_stack([xtest,missing_test.astype(float)])
    mu=xtrain.mean(axis=0); sd=xtrain.std(axis=0);sd[sd<=1e-12]=1
    return (xtrain-mu)/sd,(xtest-mu)/sd


def predict_family(rows,train,test,family):
    y=np.asarray([rows[i]['D_site'] for i in train])
    if family=='mean':return np.repeat(y.mean(),len(test))
    a,b=matrices(rows,train,test,family)
    return Ridge(alpha=ALPHA,fit_intercept=True).fit(a,y).predict(b)


def sign(x):return 1 if x>TOL else -1 if x< -TOL else 0


def score(comp,env,bootstrap=True):
    matches,flow=eligible_match(comp)
    if len(matches)<20:raise ValueError('SCIENTIFIC_STOP fewer than 20 structurally eligible independent sites')
    rows=[site_metrics(comp,env,site,blocks) for site,blocks in sorted(matches.items())]
    order=sorted(range(len(rows)),key=lambda i:hashlib.sha256((SALT+rows[i]['site']).encode()).hexdigest())
    hold_n=math.ceil(0.25*len(rows));test=order[:hold_n];train=order[hold_n:]
    if hold_n<5:raise ValueError('SCIENTIFIC_STOP fewer than 5 heldout sites')
    preds={name:predict_family(rows,train,test,name) for name in FAMILIES}
    baseline_sign=sign(float(np.mean([rows[i]['D_site'] for i in train])))
    train_signs=[rows[i]['Y_site_sign'] for i in train if rows[i]['Y_site_sign']!=0]
    count_sign={-1:train_signs.count(-1),1:train_signs.count(1)}
    majority_sign=(1 if count_sign[1]>count_sign[-1] else -1 if count_sign[-1]>count_sign[1] else 0)
    details=[]
    for j,i in enumerate(test):
        x={family:float(preds[family][j]) for family in FAMILIES}
        m=[sign(x[name]) for name in FAMILIES]
        dec=m[0] if m[0]!=0 and len(set(m))==1 else None
        details.append({'site':rows[i]['site'],'truth_sign':int(rows[i]['Y_site_sign']),'true_D':rows[i]['D_site'],
                        'all_model_predictions':x,'model_signs':dict(zip(FAMILIES,m)),
                        'issued_sign':dec,'status':'abstain' if dec is None else 'signed',
                        'correct_if_issued':None if dec is None else bool(dec==rows[i]['Y_site_sign']),
                        'baseline_mean_sign':baseline_sign,'baseline_majority_nonzero_sign':majority_sign})
    issued=[r for r in details if r['issued_sign'] is not None]
    correct=sum(r['correct_if_issued'] for r in issued)
    outcomes={
        'n_train_sites':len(train),'n_holdout_sites':len(test),
        'signed':len(issued),'abstain':len(details)-len(issued),
        'coverage':len(issued)/len(test),'correct_issued':correct,
        'wrong_issued':len(issued)-correct,
        'accuracy_conditional_on_issued':correct/len(issued) if issued else None,
        'mean_only_correct':sum(r['truth_sign']==baseline_sign for r in details),
        'majority_sign_correct':sum(r['truth_sign']==majority_sign for r in details),
        'holdout_actual_sign_counts':{str(k):sum(r['truth_sign']==k for r in details) for k in (-1,0,1)},
        'training_actual_sign_counts':{str(k):sum(rows[i]['Y_site_sign']==k for i in train) for k in (-1,0,1)},
    }
    summary={'schema':'eog.nutnet_hodapp_frozen_y3_target.result.v1','evidence_status':'RETROSPECTIVE_HELDOUT_EXPERIMENTAL_ANALOGUE',
             'source':{'doi':'10.5061/dryad.8vs569h','md5':{k:v[0] for k,v in EXPECTED.items()}},
             'frozen_protocol_commit':'b5ae8afd45de101504539b87482114a731ff247d',
             'frozen_target_tolerance':TOL,'model_families':list(FAMILIES),
             'eligibility_flow':flow,'holdout_sites_sha256_rule':SALT,
             'training_sites':[rows[i]['site'] for i in train],
             'holdout_sites':[rows[i]['site'] for i in test],
             'site_response_signs_all_eligible':{str(k):sum(r['Y_site_sign']==k for r in rows) for k in (-1,0,1)},
             'heldout_evaluation':outcomes,'holdout_details':details,
             'all_eligible_sites':rows,
             'limits':['Known 2018 paper includes aggregate treatment findings; this is not independent discovery of aggregate sign.',
                       'Plot community-state span is not original EOG environmental niche span.',
                       'Predictive-model unanimity does not identify ecological BAM mechanisms.',
                       'Static Y0/Y3 treatment contrast is an experimental analogue, not exact A or B constraint deletion.',
                       'Model universe is finite and manually declared; site count rather than plot count is the unit.']}
    if bootstrap:
        rng=np.random.default_rng(20261119)
        boot={k:[] for k in FAMILIES}
        for _ in range(200):
            train_rep=[int(train[j]) for j in rng.integers(0,len(train),len(train))]
            for family in FAMILIES:
                boot[family].append(predict_family(rows,train_rep,test,family))
        summary['bootstrap_site_resample_predictor_sensitivity']={
            family:{rows[i]['site']:{'q05':float(np.quantile(np.asarray(boot[family])[:,j],.05)),
                                      'q95':float(np.quantile(np.asarray(boot[family])[:,j],.95))} for j,i in enumerate(test)}
            for family in FAMILIES}
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); c,e=read_verified(args.source_dir)
    r=score(c,e,bootstrap=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def output_safe(v):
        if isinstance(v,dict):return {k:output_safe(z) for k,z in v.items()}
        if isinstance(v,list):return [output_safe(z) for z in v]
        if isinstance(v,(float,np.floating)) and not np.isfinite(v):return None
        return v
    args.output.write_text(json.dumps(output_safe(r),sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'flow':r['eligibility_flow'],'heldout':r['heldout_evaluation']},indent=2))

if __name__=='__main__': main()
