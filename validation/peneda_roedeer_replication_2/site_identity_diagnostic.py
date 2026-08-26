from __future__ import annotations
import csv, hashlib, io, json, urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
BUILD=ROOT/'build'/'peneda_roedeer_replication_2'; BUILD.mkdir(parents=True,exist_ok=True)
C=json.loads((HERE/'source_contract.json').read_text()); OUT=BUILD/'site_identity_diagnostic.json'

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'EOG-Peneda-site-diagnostic/1.0'})
    with urllib.request.urlopen(req,timeout=90) as r:return r.read()

def dt(s): return datetime.fromisoformat(str(s).strip().replace('Z','+00:00'))
def fp(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def main():
    raw=get(C['response_independent']['binary_url']); text=raw.decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text),delimiter=';'))
    by_name=defaultdict(list); by_lid=defaultdict(list)
    for r in rows:
        rec={'deploymentID':r['deploymentID'].strip(),'locationID':r['locationID'].strip(),'locationName':r['locationName'].strip(),'coord':(float(r['latitude']),float(r['longitude'])),'start_year':dt(r['start']).year}
        by_name[rec['locationName']].append(rec); by_lid[rec['locationID']].append(rec)
    name_profile=[]
    for name,rs in sorted(by_name.items()):
        coords=sorted({x['coord'] for x in rs}); years=sorted({x['start_year'] for x in rs})
        name_profile.append({'locationName':name,'deployment_count':len(rs),'coordinate_variant_count':len(coords),'years':years})
    out={'schema':'eog.peneda_roedeer_replication_2.site_identity_diagnostic.v1','deployment_rows':len(rows),'deployment_sha256':hashlib.sha256(raw).hexdigest(),'unique_locationID':len(by_lid),'unique_locationName':len(by_name),'locationID_max_deployments':max(map(len,by_lid.values())),'locationName_deployment_count_distribution':dict(sorted(Counter(len(v) for v in by_name.values()).items())),'locationName_coordinate_variant_distribution':dict(sorted(Counter(x['coordinate_variant_count'] for x in name_profile).items())),'locationName_profiles':name_profile,'locationName_registry_fingerprint':fp(name_profile),'response_firewall':dict(C['response_firewall'])}
    out['fingerprint']=fp(out); OUT.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n'); print(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False))
if __name__=='__main__':main()
