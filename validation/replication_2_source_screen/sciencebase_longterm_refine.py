from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'build'/'replication_2_source_screen'; BUILD.mkdir(parents=True,exist_ok=True)
OUT=BUILD/'sciencebase_longterm_refine.json'
IDS=[
 '6188c0c4d34ec04fc9c4f7a4',
 '6672de8dd34e84915adbb4f3',
 '663cdf96d34e77890839e178',
 '66520b7dd34e702fe87490d4',
]

def get(url):
 req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'EOG-longterm-metadata-refine/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read())

def slim(f):
 return {'name':f.get('name'),'title':f.get('title'),'size':f.get('size'),'contentType':f.get('contentType'),'checksum':f.get('checksum')}

def main():
 out=[]
 for iid in IDS:
  item=get(f'https://www.sciencebase.gov/catalog/item/{iid}?format=json')
  files=[slim(f) for f in item.get('files') or [] if isinstance(f,dict)]
  children=get('https://www.sciencebase.gov/catalog/items?'+urllib.parse.urlencode({'parentId':iid,'format':'json','max':100})).get('items') or []
  child=[]
  for c in children:
   cid=c.get('id')
   if not cid: continue
   full=get(f'https://www.sciencebase.gov/catalog/item/{cid}?format=json')
   child.append({'id':cid,'title':full.get('title'),'summary':(full.get('summary') or '')[:800],'files':[slim(f) for f in full.get('files') or [] if isinstance(f,dict)]})
  out.append({'id':iid,'title':item.get('title'),'summary':(item.get('summary') or '')[:1500],'files':files,'children':child,'identifiers':item.get('identifiers') or []})
 result={'schema':'eog.replication_2_source_screen.sciencebase_longterm_refine.v1','status':'metadata_only_complete','file_payload_requests':0,'file_payload_bytes_opened':0,'items':out}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 print(json.dumps({'status':result['status'],'items':[{'id':x['id'],'title':x['title'],'files':[f['name'] for f in x['files']], 'children':[{'title':c['title'],'files':[f['name'] for f in c['files']]} for c in x['children']]} for x in out],'file_payload_requests':0},indent=2,sort_keys=True))
if __name__=='__main__': main()
