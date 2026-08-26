from __future__ import annotations

import csv, hashlib, io, json, statistics, sys, urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BUILD=ROOT/'build'/'peneda_roedeer_replication_2'; BUILD.mkdir(parents=True,exist_ok=True)
C=json.loads((HERE/'source_contract.json').read_text())
OUT=BUILD/'gate0_response_free.json'


def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def fp(x): return hashlib.sha256(canon(x)).hexdigest()

def get(url,accept='*/*'):
    req=urllib.request.Request(url,headers={'User-Agent':'EOG-Peneda-response-free/1.0','Accept':accept})
    with urllib.request.urlopen(req,timeout=90) as r: return r.read(),r.geturl(),r.headers.get('Content-Type'),r.headers.get('Content-Disposition')

def local(tag): return tag.split('}',1)[-1]

def xml_identity():
    raw,final,ctype,_=get(C['paper']['article_xml_url'],'application/xml,text/xml;q=0.9,*/*;q=0.1')
    root=ET.fromstring(raw)
    found={}
    for elem in root.iter():
        if local(elem.tag)!='supplementary-material': continue
        text=' '.join(''.join(elem.itertext()).split())
        attrs=[]
        for sub in elem.iter():
            for k,v in sub.attrib.items(): attrs.append(str(v))
        joined=text+' '+' '.join(attrs)
        for role,key in [('deployments','response_independent'),('observations','forbidden_response')]:
            spec=C[key]
            if spec['source_filename'] in joined and str(spec['binary_object_id']) in joined:
                found.setdefault(role,[]).append({'element_id':elem.attrib.get('id'),'fragment_sha256':hashlib.sha256(ET.tostring(elem,encoding='utf-8')).hexdigest(),'filename':spec['source_filename'],'binary_object_id':spec['binary_object_id']})
    if len(found.get('deployments',[]))!=1 or len(found.get('observations',[]))!=1:
        raise RuntimeError(f"official XML did not resolve one deployment and one observation supplement: {found}")
    return {'xml_bytes':len(raw),'xml_sha256':hashlib.sha256(raw).hexdigest(),'final_url':final,'content_type':ctype,'deployments':found['deployments'][0],'observations':found['observations'][0]}

def parse_dt(s):
    t=str(s or '').strip()
    if not t: raise RuntimeError('blank deployment datetime')
    try: return datetime.fromisoformat(t.replace('Z','+00:00'))
    except ValueError as e: raise RuntimeError(f'unsupported ISO datetime {t!r}') from e

def pct(xs,q):
    xs=sorted(xs); p=(len(xs)-1)*q; lo=int(p); hi=min(lo+1,len(xs)-1); f=p-lo; return xs[lo]*(1-f)+xs[hi]*f

def finish(r,code=0):
    r['fingerprint']=fp({k:v for k,v in r.items() if k!='fingerprint'})
    OUT.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)); return code

def main():
    r={'schema':'eog.peneda_roedeer_replication_2.gate0_response_free.v1','attempt_id':C['attempt_id'],'status':'engineering_failure_pre_response','reason':None,'source_identity':{},'deployments':{},'geometry':{},'temporal':{},'response_firewall':dict(C['response_firewall'])}
    try:
        r['source_identity']=xml_identity()
        spec=C['response_independent']
        raw,final,ctype,cdisp=get(spec['binary_url'],'text/csv,text/plain;q=0.9,*/*;q=0.1')
        text=None; enc=None
        for x in ('utf-8-sig','utf-8','cp1252'):
            try: text=raw.decode(x); enc=x; break
            except UnicodeDecodeError: pass
        if text is None: raise RuntimeError('deployment CSV decode failure')
        try: delim=csv.Sniffer().sniff(text[:32768],delimiters=',;\t').delimiter
        except csv.Error: delim=','
        reader=csv.DictReader(io.StringIO(text),delimiter=delim); header=list(reader.fieldnames or []); rows=list(reader)
        miss=[x for x in spec['required_essential_columns'] if x not in header]
        if miss:
            r['status']='stop_deployment_essential_schema_mismatch'; r['reason']=f'missing prospectively documented deployment columns {miss}; observed={header}'; return finish(r)
        if len(rows)!=int(C['paper']['published_deployments']):
            r['status']='stop_published_deployment_count_not_reproduced'; r['reason']=f"deployment rows {len(rows)} != {C['paper']['published_deployments']}"; return finish(r)
        ids=[]; locations=defaultdict(list); starts=[]; ends=[]; durations=[]; startyears=Counter(); missing=Counter()
        for row in rows:
            for c in spec['required_essential_columns']:
                if not str(row.get(c) or '').strip(): missing[c]+=1
            did=str(row['deploymentID']).strip(); lid=str(row['locationID']).strip()
            if not did or not lid: raise RuntimeError('blank deploymentID/locationID')
            ids.append(did)
            lat=float(str(row['latitude']).strip()); lon=float(str(row['longitude']).strip())
            if not(-90<=lat<=90 and -180<=lon<=180): raise RuntimeError(f'bad coordinates {did}')
            s=parse_dt(row['start']); e=parse_dt(row['end'])
            if e<=s: raise RuntimeError(f'nonpositive interval {did}')
            starts.append(s); ends.append(e); durations.append((e-s).total_seconds()/86400); startyears[s.year]+=1
            locations[lid].append((lat,lon,did,s.year))
        if any(missing.values()):
            r['status']='stop_required_deployment_values_missing'; r['reason']=f'required deployment fields missing: {dict(missing)}'; return finish(r)
        if len(set(ids))!=len(ids):
            r['status']='stop_deployment_id_not_unique'; r['reason']='deploymentID not unique'; return finish(r)
        coord_variants={lid:sorted({(x[0],x[1]) for x in vals}) for lid,vals in locations.items()}
        unstable={lid:v for lid,v in coord_variants.items() if len(v)>1}
        geometry_mode='stable_location_registry' if not unstable else 'deployment_cycle_specific'
        r['deployments']={'payload_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'content_type':ctype,'content_disposition':cdisp,'final_host':urllib.request.urlparse(final).netloc if False else final.split('/')[2],'encoding':enc,'delimiter':delim,'header':header,'column_count':len(header),'row_count':len(rows),'unique_deployment_ids':len(set(ids)),'unique_location_ids':len(locations),'registry_fingerprint':fp(sorted([{'deploymentID':str(x['deploymentID']).strip(),'locationID':str(x['locationID']).strip(),'longitude':float(x['longitude']),'latitude':float(x['latitude']),'start':str(x['start']).strip(),'end':str(x['end']).strip()} for x in rows],key=lambda z:z['deploymentID']))}
        r['geometry']={'mode':geometry_mode,'unique_location_ids':len(locations),'stable_location_count':sum(len(v)==1 for v in coord_variants.values()),'varying_location_count':len(unstable),'max_coordinate_variants_per_location':max(map(len,coord_variants.values())) if coord_variants else 0,'coordinate_variation_location_ids':sorted(unstable)[:20],'rule_if_varying':'Gate1 nodes are deploymentID within survey cycle; no coordinate averaging and no cross-cycle propagation','location_geometry_fingerprint':fp({k:v for k,v in sorted(coord_variants.items())})}
        r['temporal']={'start_year_counts':dict(sorted(startyears.items())),'distinct_start_years':len(startyears),'earliest_start':min(starts).isoformat(),'latest_start':max(starts).isoformat(),'earliest_end':min(ends).isoformat(),'latest_end':max(ends).isoformat(),'duration_days_min':min(durations),'duration_days_q25':pct(durations,.25),'duration_days_median':statistics.median(durations),'duration_days_q75':pct(durations,.75),'duration_days_max':max(durations)}
        r['status']='gate0_pass_response_free_deployment_registry'; r['reason']='official XML bound physically separate deployment/observation supplements; exact deployment payload reproduced 331 deployments and complete response-independent geometry/effort while observation payload remained unopened'; return finish(r)
    except Exception as e:
        r['reason']=f'{type(e).__name__}: {e}'; return finish(r,1)

if __name__=='__main__': sys.exit(main())
