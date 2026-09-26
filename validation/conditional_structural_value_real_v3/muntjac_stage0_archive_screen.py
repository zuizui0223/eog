#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"validation/conditional_structural_value_real_v3/muntjac_stage0_contract_v1.json"
OUT=ROOT/"build/conditional_structural_value_real_v3/muntjac_stage0_result.json"

def _get(url: str) -> tuple[int,dict[str,str],bytes]:
    req=Request(url,headers={"User-Agent":"eog-csv-v3-stage0/1.0","Accept":"text/html,*/*"})
    with urlopen(req,timeout=60) as r:  # noqa: S310
        return int(getattr(r,"status",200)), dict(r.headers.items()), r.read()

def _head(url: str) -> tuple[int,dict[str,str]]:
    req=Request(url,method="HEAD",headers={"User-Agent":"eog-csv-v3-stage0/1.0"})
    with urlopen(req,timeout=60) as r:  # noqa: S310
        return int(getattr(r,"status",200)), dict(r.headers.items())

def _range(url: str, range_value: str, max_bytes: int) -> tuple[int,dict[str,str],bytes]:
    req=Request(url,headers={"User-Agent":"eog-csv-v3-stage0/1.0","Range":range_value,"Accept":"application/zip"})
    with urlopen(req,timeout=60) as r:  # noqa: S310
        status=int(getattr(r,"status",200))
        headers=dict(r.headers.items())
        raw=r.read(max_bytes+1)
    return status,headers,raw

def _central_names(raw: bytes) -> list[str]:
    names=[]
    sig=b"PK\x01\x02"
    pos=0
    while True:
        i=raw.find(sig,pos)
        if i<0:
            break
        if i+46>len(raw):
            break
        try:
            name_len,extra_len,comment_len=struct.unpack_from("<HHH",raw,i+28)
        except struct.error:
            break
        start=i+46
        end=start+name_len
        if end>len(raw):
            break
        names.append(raw[start:end].decode("utf-8",errors="replace"))
        pos=end+extra_len+comment_len
    return names

def main() -> int:
    c=json.loads(CONTRACT.read_text())
    src=c["source_identity"]
    auth=c["authorized_stage0_access"]
    result={
        "schema":"eog.conditional_structural_value.real_v3.muntjac_stage0_result.v1",
        "candidate_id":c["candidate_id"],
        "resource_page_gets":0,
        "archive_head_requests":0,
        "archive_tail_range_gets":0,
        "archive_tail_bytes_opened":0,
        "full_archive_downloaded":False,
        "member_body_bytes_opened":0,
        "observations_body_bytes_opened":0,
        "deployments_body_bytes_opened":0,
        "response_values_opened":False,
        "model_fits":0,
        "heldout_scores":0,
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }
    try:
        page_status,page_headers,page_raw=_get(src["resource_page"])
        result["resource_page_gets"]=1
        if page_status!=200:
            raise RuntimeError(f"resource page HTTP {page_status}")
        page=page_raw.decode("utf-8",errors="replace")
        if src["dataset_title"] not in page:
            raise RuntimeError("dataset title not reproduced on resource page")
        if "Camtrap DP" not in page:
            raise RuntimeError("Camtrap DP format not reproduced on resource page")
        nums=[int(x.replace(",","")) for x in re.findall(r"(\d[\d,]*)\s*</?[^>]*>?\s*deployments",page,re.I)]
        if not nums:
            # IPT renders label before number in some locales.
            nums=[int(x.replace(",","")) for x in re.findall(r"deployments[^0-9]{0,80}(\d[\d,]*)",page,re.I)]
        reported=max(nums) if nums else None
        if reported is None or reported < int(c["stage0_gates"]["resource_page_must_report_at_least_deployments"]):
            raise RuntimeError(f"deployment count not reproduced at required scale: {reported}")

        head_status,head_headers=_head(src["archive_url"])
        result["archive_head_requests"]=1
        if head_status not in (200,204):
            raise RuntimeError(f"archive HEAD HTTP {head_status}")
        content_length=head_headers.get("Content-Length")

        range_status,range_headers,raw=_range(
            src["archive_url"],auth["archive_tail_range"],int(auth["max_archive_bytes_read"])
        )
        result["archive_tail_range_gets"]=1
        result["archive_tail_bytes_opened"]=len(raw)
        if range_status!=206:
            raise RuntimeError(f"archive Range not honored: HTTP {range_status}")
        if len(raw)>int(auth["max_archive_bytes_read"]):
            raise RuntimeError("archive tail exceeded byte ceiling")
        content_range=range_headers.get("Content-Range")
        if not content_length and not content_range:
            raise RuntimeError("stable archive size unavailable from HEAD/Range metadata")

        names=_central_names(raw)
        if not names:
            raise RuntimeError("no ZIP central-directory names found in frozen tail")
        required=c["stage0_gates"]["central_directory_must_contain_exactly_one_each"]
        matched={}
        for role in required:
            hits=[n for n in names if n==role or n.endswith("/"+role)]
            matched[role]=hits
            if len(hits)!=1:
                raise RuntimeError(f"expected one {role}, found {len(hits)}")

        result.update({
            "status":c["if_pass"]["status"],
            "next_gate":c["if_pass"]["next_gate"],
            "reported_deployments":reported,
            "archive_head_content_length":content_length,
            "archive_content_range":content_range,
            "central_directory_entries_in_tail":len(names),
            "required_members":matched,
        })
    except Exception as exc:
        result.update({
            "status":c["if_fail"]["status"],
            "reason":str(exc),
            "next_gate":"none",
            "retry_allowed":False,
            "third_candidate_allowed":False,
        })
    result["fingerprint"]=hashlib.sha256(
        json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
