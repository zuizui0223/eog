#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from eog import infer_occupancy_geometry,pairwise_distances,minimum_spanning_tree
SIZES=(60,120,240); CONN=("gaussian","heavy_tail","skewed","banana"); FRAG=("two_modes","missing_bridge")
def cloud(k,n,r):
    if k=="gaussian":
        x=r.normal(size=(n,2));x[:,1]*=.45;return x
    if k=="heavy_tail":
        z=r.normal(size=(n,2));s=np.sqrt(r.chisquare(4,size=n)/4)[:,None];x=z/s;x[:,1]*=.45;return x
    if k=="skewed":
        z=r.normal(size=(n,2));return np.c_[np.exp(.65*z[:,0]),.45*z[:,1]]
    if k=="banana":
        x=r.normal(size=n);return np.c_[x,.3*r.normal(size=n)+.55*(x*x-1)]
    if k=="two_modes":
        h=n//2;return np.vstack([r.normal((-1.8,0),(.3,.25),(h,2)),r.normal((1.8,0),(.3,.25),(n-h,2))])
    a=np.r_[r.uniform(-2.5,-.65,n//2),r.uniform(.65,2.5,n-n//2)];return np.c_[a,r.normal(0,.2,n)]
def split_balance(n,e,cut):
    adj=[[] for _ in range(n)]
    for i,(a,b,_) in enumerate(e):
        if i==cut: continue
        a=int(a);b=int(b);adj[a].append(b);adj[b].append(a)
    lab=np.ones(n,int);st=[int(e[cut,0])];lab[st[0]]=0
    while st:
        a=st.pop()
        for b in adj[a]:
            if lab[b]:lab[b]=0;st.append(b)
    return float(min((lab==0).mean(),(lab==1).mean()))
def metrics(x,k=5,retain=.9):
    raw=infer_occupancy_geometry(x).gap_strength;d=pairwise_distances(x);sc=[]
    for i in range(len(x)):
        a=np.delete(d[i],i);kk=min(k,len(a));sc.append(np.median(np.partition(a,kk-1)[:kk]))
    keep=np.argsort(sc)[:max(2,int(round(len(x)*retain)))];xc=x[keep];dc=pairwise_distances(xc);e=minimum_spanning_tree(dc);lens=e[:,2];cut=int(np.argmax(lens));u,v=int(e[cut,0]),int(e[cut,1]);L=float(lens[cut]);pos=lens[lens>0];core_gap=L/float(np.median(pos))
    local=[]
    for node,other in ((u,v),(v,u)):
        a=np.delete(dc[node],[node,other]);kk=min(k,len(a));local.append(float(np.median(np.partition(a,kk-1)[:kk])))
    contrast=L/max(local);bal=split_balance(len(xc),e,cut);score=contrast*(bal/.5)
    return raw,core_gap,contrast,bal,score
def auc(a,b):
    a=np.asarray(a);b=np.asarray(b);return float((b[:,None]>a).mean()+.5*(b[:,None]==a).mean())
def run(repeats,seed,out):
    r=np.random.default_rng(seed);rows=[]
    for n in SIZES:
      for s in CONN+FRAG:
       for q in range(repeats):
        vals=metrics(cloud(s,n,r));rows.append(dict(n=n,structure=s,kind="connected" if s in CONN else "fragmented",repeat=q+1,raw_gap=vals[0],core_gap=vals[1],core_local_bridge=vals[2],core_balance=vals[3],core_local_bridge_score=vals[4]))
    out.mkdir(parents=True,exist_ok=True)
    with (out/'core_local_bridge_results.csv').open('w',newline='',encoding='utf-8') as h:
      w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    comp=[]
    for n in SIZES:
      neg=[x for x in rows if x['n']==n and x['kind']=='connected']
      for s in FRAG:
        pos=[x for x in rows if x['n']==n and x['structure']==s];rec={'n':n,'structure':s}
        for m in ('raw_gap','core_gap','core_local_bridge','core_local_bridge_score'):rec[m+'_auc']=auc([float(x[m]) for x in neg],[float(x[m]) for x in pos])
        comp.append(rec)
    with (out/'core_local_bridge_auc.csv').open('w',newline='',encoding='utf-8') as h:
      w=csv.DictWriter(h,fieldnames=list(comp[0]));w.writeheader();w.writerows(comp)
    mr=min(x['raw_gap_auc'] for x in comp);ms=min(x['core_local_bridge_score_auc'] for x in comp);mt=min(x['core_local_bridge_score_auc'] for x in comp if x['structure']=='two_modes')
    d={'minimum_raw_auc':mr,'minimum_score_auc':ms,'minimum_two_mode_auc':mt,'minimum_auc_improvement':ms-mr};d['passes_development_gate']=bool(ms>=.8 and ms-mr>=.3 and mt>=.9)
    (out/'core_local_bridge_decision.json').write_text(json.dumps(d,indent=2)+'\n');return d
def main():
    p=argparse.ArgumentParser();p.add_argument('--repeats',type=int,default=30);p.add_argument('--seed',type=int,default=20260830);p.add_argument('--output',type=Path,default=Path('benchmark_results/core_local_bridge'));a=p.parse_args();print(json.dumps(run(a.repeats,a.seed,a.output),indent=2))
if __name__=='__main__':main()
