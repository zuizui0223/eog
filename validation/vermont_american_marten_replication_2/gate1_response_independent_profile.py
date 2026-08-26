from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BUILD=ROOT/'build'/'vermont_american_marten_replication_2'
BUILD.mkdir(parents=True,exist_ok=True)
CONTRACT=json.loads((HERE/'source_contract.json').read_text())
GATE0=json.loads((HERE/'gate0_metadata_certificate.json').read_text())
OUT=BUILD/'gate1_response_independent_profile.json'
ALLOWED=GATE0['response_independent']
FORBIDDEN=set(GATE0['biological_response'])


def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def fp(x): return hashlib.sha256(canonical(x)).hexdigest()

def get_json(url):
    req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'EOG-Vermont-Marten-label-free/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read(); return json.loads(raw),len(raw),r.geturl()

def get_bytes(url):
    req=urllib.request.Request(url,headers={'Accept':'text/csv,application/octet-stream,*/*;q=0.5','User-Agent':'EOG-Vermont-Marten-label-free/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:
        return r.read(),r.geturl(),r.headers.get('Content-Type')

def checksum_value(x):
    if isinstance(x,dict): return str(x.get('value') or '').lower()
    return str(x or '').lower()

def exact_file(item,name):
    m=[f for f in item.get('files',[]) if f.get('name')==name]
    if len(m)!=1: raise RuntimeError(f'{name}: expected one ScienceBase file object, got {len(m)}')
    return m[0]

def fetch_allowed(item,name,spec):
    if name in FORBIDDEN: raise RuntimeError(f'forbidden response file requested: {name}')
    f=exact_file(item,name)
    if int(f.get('size') or -1)!=int(spec['size']): raise RuntimeError(f'{name}: metadata size mismatch')
    if checksum_value(f.get('checksum') or f.get('md5'))!=spec['md5']: raise RuntimeError(f'{name}: metadata MD5 mismatch')
    url=f.get('downloadUri')
    if not isinstance(url,str) or not url.startswith('https://'): raise RuntimeError(f'{name}: no HTTPS downloadUri')
    raw,final,ctype=get_bytes(url)
    if len(raw)!=int(spec['size']): raise RuntimeError(f'{name}: payload size mismatch {len(raw)} != {spec["size"]}')
    md5=hashlib.md5(raw).hexdigest()
    if md5!=spec['md5']: raise RuntimeError(f'{name}: payload MD5 mismatch')
    return raw,{'size':len(raw),'md5':md5,'content_type':ctype,'final_host':urllib.parse.urlparse(final).netloc}

def decode(raw,name):
    text=None; enc=None
    for e in ('utf-8-sig','utf-8','cp1252'):
        try: text=raw.decode(e); enc=e; break
        except UnicodeDecodeError: pass
    if text is None: raise RuntimeError(f'{name}: undecodable')
    try: delim=csv.Sniffer().sniff(text[:65536],delimiters=',;\t').delimiter
    except csv.Error: delim=','
    rd=csv.DictReader(io.StringIO(text),delimiter=delim)
    header=list(rd.fieldnames or [])
    if not header: raise RuntimeError(f'{name}: empty header')
    return header,list(rd),enc,delim

def norm(s): return re.sub(r'[^a-z0-9]+','_',str(s).strip().lower()).strip('_')

def role_cols(header):
    roles={'id':[],'foreign_key':[],'location':[],'visit':[],'media':[],'taxon':[],'list':[],'date':[],'time':[],'geometry':[],'type_status':[],'definition':[]}
    for c in header:
        n=norm(c); t=set(n.split('_'))
        if n=='id' or n.startswith('pk_') or n.endswith('_id') or 'uuid' in t: roles['id'].append(c)
        if n.startswith('fk_') or 'foreign' in t: roles['foreign_key'].append(c)
        if 'location' in t or 'site' in t or 'station' in t: roles['location'].append(c)
        if 'visit' in t or 'deployment' in t or 'occasion' in t or 'survey' in t: roles['visit'].append(c)
        if 'media' in t or 'file' in t or 'filename' in t: roles['media'].append(c)
        if 'taxon' in t or 'species' in t or 'scientific' in t or 'common' in t: roles['taxon'].append(c)
        if 'list' in t or 'searchlist' in n: roles['list'].append(c)
        if 'date' in t or 'datetime' in t or 'timestamp' in t: roles['date'].append(c)
        if 'time' in t: roles['time'].append(c)
        if t.intersection({'lat','latitude','lon','long','longitude','bbox','bounding','geometry','coordinate','coordinates','easting','northing'}): roles['geometry'].append(c)
        if t.intersection({'type','status','active','enabled','kind','class','category'}): roles['type_status'].append(c)
        if t.intersection({'table','field','column','variable','description','definition','relationship','primary','foreign'}): roles['definition'].append(c)
    return {k:v for k,v in roles.items() if v}

def col_profile(rows,c,examples=15):
    vals=[]; miss=0
    for r in rows:
        v=r.get(c)
        if v is None or str(v).strip()=='': miss+=1
        else: vals.append(str(v).strip())
    u=sorted(set(vals))
    return {'nonempty':len(vals),'missing':miss,'unique_count':len(u),'examples':u[:examples]}

def targeted_dictionary(rows,header):
    tokens=('locations','visits','media','annotations','modeloutputs','taxa','librarylists','librarylistitems','medialists','medialistitems','lists','listitems','searchlist')
    out=[]
    for i,r in enumerate(rows,1):
        joined=' | '.join(str(r.get(c) or '') for c in header).lower()
        if any(x in joined for x in tokens):
            vals={c:str(r.get(c) or '').strip() for c in header if str(r.get(c) or '').strip()}
            out.append({'row_index':i,'values':vals})
    return out

def name_matches(rows,header,needles):
    out=[]
    for i,r in enumerate(rows,1):
        joined=' | '.join(str(r.get(c) or '') for c in header).lower()
        if any(n.lower() in joined for n in needles):
            out.append({'row_index':i,'values':{c:str(r.get(c) or '').strip() for c in header if str(r.get(c) or '').strip()}})
    return out

def write(r):
    r['fingerprint']=fp({k:v for k,v in r.items() if k!='fingerprint'})
    OUT.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False))

def main():
    r={'schema':'eog.vermont_american_marten_replication_2.gate1_response_independent_profile.v1','attempt_id':CONTRACT['attempt_id'],'status':'engineering_failure_pre_response','reason':None,'files':{},'dictionary_relationship_rows':[],'marten_lookup_matches':{},'biological_response_firewall':dict(CONTRACT['biological_response_firewall'])}
    try:
        item_id=CONTRACT['sciencebase']['item_id']; item,_,_=get_json(f'https://www.sciencebase.gov/catalog/item/{item_id}?format=json')
        if item.get('id')!=item_id: raise RuntimeError('ScienceBase item mismatch')
        parsed={}
        for name,spec in ALLOWED.items():
            raw,meta=fetch_allowed(item,name,spec)
            header,rows,enc,delim=decode(raw,name)
            roles=role_cols(header); cols=sorted(set(c for vv in roles.values() for c in vv))
            parsed[name]=(header,rows)
            r['files'][name]={**meta,'header':header,'row_count':len(rows),'encoding':enc,'delimiter':delim,'candidate_roles':roles,'candidate_profiles':{c:col_profile(rows,c) for c in cols},'blank_header_columns':[i for i,c in enumerate(header) if not str(c).strip()],'duplicate_headers':sorted(k for k,v in Counter(header).items() if v>1)}
        dh,dr=parsed['dbdictionary.csv']; r['dictionary_relationship_rows']=targeted_dictionary(dr,dh)
        for name in ('taxa.csv','librarylists.csv','librarylistitems.csv','medialists.csv','medialistitems.csv','lists.csv','listitems.csv'):
            h,rows=parsed[name]; r['marten_lookup_matches'][name]=name_matches(rows,h,['martes americana','american marten','marten'])
        # Published media count is response-independent and should reproduce exactly.
        media_count=len(parsed['media.csv'][1])
        if media_count!=int(CONTRACT['sciencebase']['published_media_count']):
            r['status']='stop_published_media_count_not_reproduced'; r['reason']=f'observed {media_count} media rows != published {CONTRACT["sciencebase"]["published_media_count"]}'; write(r); return 0
        r['status']='gate1_response_independent_profile_complete'
        r['reason']='All prospectively allowed label-free/lookup tables were checksum-verified and profiled; 41,933 media rows reproduced; biological-response files remained unopened'
        write(r); return 0
    except Exception as exc:
        r['reason']=f'{type(exc).__name__}: {exc}'; write(r); return 1

if __name__=='__main__': sys.exit(main())
