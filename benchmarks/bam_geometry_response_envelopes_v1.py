"""Geometric target identification on the unchanged finite BAM universe.

Exploratory re-use, not field validation. Complete-current-G fibres, idealised
single-mask releases, full-census geometry. No probabilities assigned to worlds.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

AXES=('A','B','M')
METRICS=('span','centroid_mean','hull_area','components')
EPS=1e-10
CONTRACT_COMMIT='a24b73faa98888ffae5e165c3cf5d6d614e2a501'


def hull_area(x):
    """Exact planar convex polygon area; zero for fewer than 3 distinct points."""
    pts=sorted(set(map(tuple,np.asarray(x,float))))
    if len(pts)<3: return 0.
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    h=lo[:-1]+hi[:-1]
    return float(abs(sum(h[i][0]*h[(i+1)%len(h)][1]-h[(i+1)%len(h)][0]*h[i][1] for i in range(len(h))))/2)


def measure(z,bits,width,height):
    z=np.asarray(z,float);n=width*height
    if z.shape!=(n,2) or not np.isfinite(z).all() or bits<0 or bits>>n:
        raise ValueError('finite 2D feature grid and valid node mask required')
    ids=[i for i in range(n) if bits&(1<<i)]
    if len(ids)<2:raise ValueError('geometry unestimable with fewer than 2 nodes')
    x=z[ids]
    d=np.sqrt(np.sum((x[:,None,:]-x[None,:,:])**2,axis=2))
    pairs=d[np.triu_indices(len(x),1)];positive=pairs[pairs>0]
    remaining=set(ids);count=0
    while remaining:
        stack=[remaining.pop()];count+=1
        while stack:
            i=stack.pop();r,c=divmod(i,width)
            neighbours=[]
            if c:neighbours.append(i-1)
            if c+1<width:neighbours.append(i+1)
            if r:neighbours.append(i-width)
            if r+1<height:neighbours.append(i+width)
            for j in neighbours:
                if j in remaining:remaining.remove(j);stack.append(j)
    return {'span':float(np.quantile(positive,.9)) if len(positive) else 0.,
            'centroid_mean':float(np.linalg.norm(x-x.mean(0),axis=1).mean()),
            'hull_area':hull_area(x),'components':count}


def release(row,axis):
    a,b,m=(int(row[f'{k}_bits']) for k in AXES)
    if int(row['G_bits'])!=a&b&m:raise ValueError('G is not A&B&M')
    if axis=='A':return b&m
    if axis=='B':return a&m
    if axis=='M':return a&b
    raise ValueError('axis must be A, B or M')


def refine_fibre(rows,evidence_axis):
    groups=defaultdict(list)
    for r in rows:groups[int(r[evidence_axis+'_bits'])].append(r)
    return [groups[k] for k in sorted(groups)]


def fibre_summary(sid,rows,z,width,height,axis,cache=None):
    if not rows:raise ValueError('empty evidence fibre')
    gs={int(r['G_bits']) for r in rows}
    if len(gs)!=1:raise ValueError('all candidates must share current G')
    g=next(iter(gs));cache={} if cache is None else cache
    def metric(bits):
        if bits not in cache:cache[bits]=measure(z,bits,width,height)
        return cache[bits]
    present=metric(g);outcomes=[];maps=set()
    for row in rows:
        cf=release(row,axis)
        if g&~cf:raise AssertionError('release lost current occupied cells')
        maps.add(cf);after=metric(cf)
        if after['hull_area']+EPS*max(1.,present['hull_area'])<present['hull_area']:
            raise AssertionError('convex hull shrank under set inclusion')
        outcomes.append({'world_id':row['world_id'],'map':cf,'after':after,
                         'changes':{k:float(after[k]-present[k]) for k in METRICS}})
    targets={}
    for k in METRICS:
        values=[o['changes'][k] for o in outcomes]
        tolerance=EPS*max(1.,abs(present[k]),*(abs(o['after'][k]) for o in outcomes))
        dirs=sorted({-1 if v < -tolerance else 1 if v > tolerance else 0 for v in values})
        targets[k]={'current':present[k],'minimum_change':min(values),'maximum_change':max(values),
                    'directions':dirs,'direction_identified':len(dirs)==1,
                    'magnitude_identified':max(values)-min(values)<=tolerance,
                    'opposite_signs':-1 in dirs and 1 in dirs}
        if len(maps)==1 and not (targets[k]['direction_identified'] and targets[k]['magnitude_identified']):
            raise AssertionError('identified map did not identify geometry')
    return {'system_id':sid,'G_bits':g,'release_axis':axis,'n_worlds':len(rows),
            'n_mask_triples':len({tuple(r[k+'_bits'] for k in AXES) for r in rows}),
            'n_release_maps':len(maps),'map_identified':len(maps)==1,
            'targets':targets,'world_outcomes':outcomes}


def analyse(systems):
    fibres=[];evidence=[];worlds=[];audit=defaultdict(int)
    for system in systems:
        sid=system['system_id'];x=np.asarray(system['environment'],float)
        med=np.median(x,axis=0);scale=np.median(abs(x-med),axis=0)*1.4826
        if np.any(scale<=0):raise ValueError('zero MAD in frozen landscape; no silent refit')
        z=(x-med)/scale;w=system['width'];h=system['height'];cache={}
        groups=defaultdict(list)
        for r in system['worlds']:groups[int(r['G_bits'])].append(r)
        for g,rows in sorted(groups.items()):
            audit['current_G_fibres']+=1;audit['worlds']+=len(rows)
            alias=len({tuple(r[k+'_bits'] for k in AXES) for r in rows})>1
            audit['mask_ambiguous_fibres']+=alias
            audit['worlds_in_mask_ambiguous_fibres']+=len(rows) if alias else 0
            for axis in AXES:
                f=fibre_summary(sid,rows,z,w,h,axis,cache)
                for out in f.pop('world_outcomes'):
                    worlds.append({'system_id':sid,'G_bits':g,'release_axis':axis,
                                   'world_id':out['world_id'],'release_mask':out['map'],
                                   **{f'change_{k}':v for k,v in out['changes'].items()}})
                fibres.append(f)
                for obs_axis in AXES:
                    sub=[]
                    for subset in refine_fibre(rows,obs_axis):
                        s=fibre_summary(sid,subset,z,w,h,axis,cache)
                        for k in METRICS:
                            t=s['targets'][k];parent=f['targets'][k]
                            tol=EPS*max(1.,abs(parent['current']),abs(parent['maximum_change']))
                            if t['minimum_change']<parent['minimum_change']-tol or t['maximum_change']>parent['maximum_change']+tol:
                                raise AssertionError('extra true evidence broadened target set')
                            audit['evidence_envelope_checks']+=1
                        sub.append(s)
                    for k in METRICS:
                        evidence.append({'system_id':sid,'G_bits':g,'release_axis':axis,'extra_observed_axis':obs_axis,'metric':k,
                            'prior_direction_identified':f['targets'][k]['direction_identified'],
                            'all_refinements_direction_identified':all(s['targets'][k]['direction_identified'] for s in sub),
                            'identified_worlds':sum(s['n_worlds'] for s in sub if s['targets'][k]['direction_identified']),
                            'total_worlds':len(rows),'refinements':len(sub)})
    summary=[]
    for axis in AXES:
        fs=[f for f in fibres if f['release_axis']==axis]
        for metric in METRICS:
            identified=[f for f in fs if f['targets'][metric]['direction_identified']]
            summary.append({'release_axis':axis,'metric':metric,'fibres':len(fs),
                'map_identified_fibres':sum(f['map_identified'] for f in fs),
                'magnitude_identified_fibres':sum(f['targets'][metric]['magnitude_identified'] for f in fs),
                'direction_identified_fibres':len(identified),
                'direction_identified_worlds':sum(f['n_worlds'] for f in identified),
                'direction_identified_map_unidentified':sum(not f['map_identified'] for f in identified),
                'opposite_sign_fibres':sum(f['targets'][metric]['opposite_signs'] for f in fs),
                'identified_increase':sum(f['targets'][metric]['directions']==[1] for f in fs),
                'identified_no_change':sum(f['targets'][metric]['directions']==[0] for f in fs),
                'identified_decrease':sum(f['targets'][metric]['directions']==[-1] for f in fs)})
    joint=[]
    for k in METRICS:
        by_g=defaultdict(list)
        for f in fibres:by_g[(f['system_id'],f['G_bits'])].append(f)
        id_groups=[fs for fs in by_g.values() if all(f['targets'][k]['direction_identified'] for f in fs)]
        joint.append({'metric':k,'fibres_all_three_directions_identified':len(id_groups),
                      'worlds_all_three_directions_identified':sum(fs[0]['n_worlds'] for fs in id_groups)})
    e_summary=[]
    for axis in AXES:
        for obs_axis in AXES:
            for k in METRICS:
                es=[e for e in evidence if e['release_axis']==axis and e['extra_observed_axis']==obs_axis and e['metric']==k]
                e_summary.append({'release_axis':axis,'extra_observed_axis':obs_axis,'metric':k,
                    'parent_fibres':len(es),'uniformly_direction_identified_fibres':sum(e['all_refinements_direction_identified'] for e in es),
                    'newly_uniformly_identified_fibres':sum(e['all_refinements_direction_identified'] and not e['prior_direction_identified'] for e in es),
                    'direction_identified_worlds':sum(e['identified_worlds'] for e in es)})
    ordered=sorted(fibres,key=lambda f:(f['system_id'],f['G_bits'],f['release_axis']))
    examples={}
    filters={'map_ambiguous_direction_identified':lambda f:not f['map_identified'] and f['targets']['span']['direction_identified'],
             'opposite_span_signs':lambda f:f['targets']['span']['opposite_signs']}
    for name,fn in filters.items():
        chosen=next((f for f in ordered if fn(f)),None)
        if chosen:
            example=dict(chosen)
            example['worlds']=[r for r in worlds if (r['system_id'],r['G_bits'],r['release_axis'])==(chosen['system_id'],chosen['G_bits'],chosen['release_axis'])]
            examples[name]=example
        else:examples[name]=None
    report={'schema':'eog.bam_geometry_response_envelopes.result.v1','status':'EXPLORATORY_KNOWN_TRUTH',
        'contract_commit':CONTRACT_COMMIT,'systems':len(systems),'audit':dict(audit),'axis_targets':summary,
        'joint_targets':joint,'direct_evidence':e_summary,'examples':examples,
        'limits':['Complete ideal presence/absence, not real presence-only data.',
                  'Static mask release, not literal biological intervention or dynamic range forecast.',
                  'Full-census geometry includes true number/placement of occupied cells; not a matched-size sampling contrast.',
                  'Finite candidate support, no probabilities and no confidence intervals; all conclusions conditional on declared world family.',
                  '12 constructed landscapes, not768 independent ecological replicates.']}
    report['fingerprint']=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return report,fibres,evidence,worlds


def canonical_systems():
    from eog.v2.known_truth_bam_generality import SYSTEM_SPECS,build_generality_system,audit_system_activation
    from eog.v2.bam_counterfactual_identifiability import axis_release_outcome
    from eog.comparative import fit_robust_reference,infer_comparative_geometry
    out=[]
    for spec in SYSTEM_SPECS:
        system=build_generality_system(spec)
        if audit_system_activation(system).status!='PASS':raise ValueError('parent DESIGN_STOP')
        env=np.asarray(system.landscape.environment,float)
        ref=fit_robust_reference(env,provenance='unchanged finite-world landscape reference')
        z=(env-ref.median)/ref.scale;rows=[]
        for world in system.worlds:
            r={'world_id':world.world_id,'A_bits':world.abiotic_mask,'B_bits':world.biotic_mask,'M_bits':world.movement_mask,'G_bits':world.occupied_mask}
            for axis in AXES:
                if release(r,axis)!=axis_release_outcome(world,axis):raise AssertionError('original operator parity failed')
            ids=[i for i in range(len(env)) if world.occupied_mask&(1<<i)]
            base=infer_comparative_geometry(env[ids],ref).span
            if not np.isclose(base,measure(z,world.occupied_mask,spec.width,spec.height)['span'],rtol=1e-12,atol=1e-12):raise AssertionError('original EOG scalar parity failed')
            rows.append(r)
        out.append({'system_id':spec.system_id,'environment':env.tolist(),'width':spec.width,'height':spec.height,'worlds':rows})
    return out


def save_outputs(result,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report,fibres,evidence,worlds=result
    (output/'result.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    flat=[]
    for f in fibres:
        for metric,t in f['targets'].items():
            flat.append({**{k:v for k,v in f.items() if k!='targets'},'metric':metric,
                         **{k:v for k,v in t.items() if k!='directions'},'directions':'|'.join(map(str,t['directions']))})
    for name,rows in [('fibre_envelopes.csv',flat),('direct_evidence.csv',evidence),('world_responses.csv',worlds)]:
        with (output/name).open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',required=True)
    parser.add_argument('--fixture',help='Offline environment and archived-mask fixture; canonical generator is default')
    args=parser.parse_args()
    systems=json.loads(Path(args.fixture).read_text()) if args.fixture else canonical_systems()
    result=analyse(systems)
    if result[0]['audit']['worlds']!=768 or result[0]['audit']['current_G_fibres']!=129:raise AssertionError('parent roster changed')
    save_outputs(result,args.output_dir)
    print(json.dumps({'audit':result[0]['audit'],'joint_targets':result[0]['joint_targets'],
                     'span':[r for r in result[0]['axis_targets'] if r['metric']=='span'],
                     'fingerprint':result[0]['fingerprint']},indent=2))

if __name__=='__main__':main()
