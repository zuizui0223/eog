#!/usr/bin/env python3
"""Strict second-stage Dryad source ZIP gate, with exact first Lambda redirect.

The exact AWS Lambda URL host was discovered by a no-body HEAD-only diagnostic
of the publisher's official, version-specific download URL, before this
protocol was frozen. All biological event values remain unscored, unlogged,
and unexported. This code reuses the original v1 metadata + CSV-header gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from scripts import eog_independent_movement_source_gate_v1 as v1

PROTOCOL = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
SOURCE_PROTOCOL = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")


def _guard_host(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("STOP_REDIRECT_NON_HTTPS_OR_CREDENTIALS")
    return p.hostname.lower()


class ValidatedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, contract: dict[str, Any]) -> None:
        super().__init__()
        self.contract = contract
        self.hops = 0
        self.mandatory_first_seen = False
        self.hosts = []

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        self.hops += 1
        if self.hops > self.contract["max_http_redirects"]:
            raise ValueError("STOP_REDIRECT_CHAIN_TOO_LONG")
        old = _guard_host(request.full_url)
        new = _guard_host(newurl)
        if not self.mandatory_first_seen:
            if old != self.contract["original_https_host"]:
                raise ValueError("STOP_REDIRECT_FROM_NON_PUBLISHER_HOST")
            if new != self.contract["first_redirect_must_be_exact_host"]:
                raise ValueError("STOP_FIRST_REDIRECT_HOST_NOT_PINNED")
            self.mandatory_first_seen = True
        else:
            suffixes = tuple(self.contract["later_redirect_allowlist_suffixes"])
            if new not in (
                self.contract["original_https_host"],
                self.contract["first_redirect_must_be_exact_host"],
            ) and not new.endswith(suffixes):
                raise ValueError("STOP_UNVERIFIED_LATER_REDIRECT_HOST")
            if old not in (
                self.contract["original_https_host"],
                self.contract["first_redirect_must_be_exact_host"],
            ) and not old.endswith(suffixes):
                raise ValueError("STOP_REDIRECT_FROM_UNVERIFIED_HOST")
        self.hosts.append(new)
        return super().redirect_request(request,fp,code,msg,headers,newurl)


def _version_zip(url: str, limits: dict[str, Any], contract: dict[str, Any]) -> tuple[bytes,str]:
    if not url.startswith("https://datadryad.org/api/v2/versions/") or not url.endswith("/download"):
        raise ValueError("STOP_VERSION_DOWNLOAD_URL_NOT_FROZEN")
    handler = ValidatedRedirect(contract)
    opener = urllib.request.build_opener(handler)
    request = urllib.request.Request(url,headers={
        "User-Agent":"EOG-source-only-exact-host-Dryad/2.0",
        "Accept":"application/zip, */*",
    })
    with opener.open(request,timeout=contract["cap_timeout_sec"]) as resp:
        final_host=_guard_host(resp.geturl())
        if not handler.mandatory_first_seen:
            raise ValueError("STOP_REQUIRED_PUBLISHER_LAMBDA_REDIRECT_MISSING")
        if final_host not in (
            contract["first_redirect_must_be_exact_host"],
            contract["original_https_host"],
        ) and not final_host.endswith(tuple(contract["later_redirect_allowlist_suffixes"])):
            raise ValueError("STOP_FINAL_STORAGE_HOST_NOT_FROZEN")
        buf=resp.read(limits["max_archive_bytes"]+1)
        if len(buf)>limits["max_archive_bytes"]:
            raise ValueError("STOP_ARCHIVE_BYTE_CAP")
        return buf,final_host


def run(protocol: dict[str, Any]) -> dict[str, Any]:
    if protocol.get("status")!="PRE_BIOLOGICAL_SOURCE_ONLY_TRANSPORT_FROZEN":
        raise ValueError("STOP_SOURCE_V2_PROTOCOL_NOT_FROZEN")
    base=json.loads(SOURCE_PROTOCOL.read_text(encoding="utf-8"))
    mapping={x["id"]:x for x in protocol["sources"]}
    source_by_id={x["id"]:x for x in base["source_references"]}
    if set(mapping)!=set(source_by_id):
        raise ValueError("STOP_SOURCE_ROSTER_DRIFT")
    allowed_versions={
        f"https://datadryad.org/api/v2/versions/{x['version_id']}/download":x
        for x in protocol["sources"]
    }
    original_get=v1._get
    def pinned_get(url: str, *, byte_cap: int, timeout: int, is_payload: bool):
        if not is_payload:
            return original_get(url,byte_cap=byte_cap,timeout=timeout,is_payload=False)
        if url not in allowed_versions:
            raise ValueError("STOP_REQUEST_FOR_UNDECLARED_VERSION")
        return _version_zip(url,base["resource_limits"],
                            protocol["exact_trusted_redirect_contract"])
    results=[]
    v1._get=pinned_get
    try:
        for src_id in sorted(mapping):
            source=mapping[src_id]
            original=source_by_id[src_id]
            if original["doi"]!=source["doi"]:
                raise ValueError("STOP_DOI_CHANGED_IN_SECOND_STAGE")
            if sorted(original["publisher_landing_file_names"])!=sorted(x["name"] for x in source["expected"]):
                raise ValueError("STOP_FILES_CHANGED_IN_SECOND_STAGE")
            r=v1._qualify_one(original,base)
            r["second_stage_pinned_version"]=source["version_id"]
            r["source_files_sha256_pinned_in_v2_before_download"]=True
            if r["status"]=="SOURCE_SCHEMA_ONLY_QUALIFIED_BIOLOGICAL_OUTCOME_NOT_SCORED":
                if int(r.get("publisher_version_id",-1))!=source["version_id"]:
                    r["status"]="STOP_VERSION_ID_CHANGED"
                elif str(r.get("publisher_publication_date"))[:10]!=source["expected_date"]:
                    r["status"]="STOP_VERSION_DATE_CHANGED"
                else:
                    got={x["name"]:x for x in r.get("file_checks",[])}
                    expected={x["name"]:x for x in source["expected"]}
                    if set(got)!=set(expected):
                        r["status"]="STOP_PUBLISHER_FILESET_CHANGED"
                    elif any(got[k].get("sha256")!=e["sha256"] or got[k].get("size_bytes")!=e["size"]
                             for k,e in expected.items()):
                        r["status"]="STOP_PINNED_PUBLISHER_SHA256_OR_SIZE_MISMATCH"
                    else:
                        r["publisher_sha256_all_files_independently_matched"]=True
                        r["status"]="OFFICIAL_SOURCE_SCHEMA_AND_PINNED_SHA256_QUALIFIED_NO_BIOLOGICAL_SCORING"
            r["biological_outcome_values_analyzed"]=0
            r["new_eog_wf_endpoints"]=0
            r["models_fit"]=0
            results.append(r)
    finally:
        v1._get=original_get

    return {
        "schema":"eog.independent_marked_movement_source_gate_v2.result",
        "status":("SOURCE_SCHEMA_QUALIFIED_BUT_MOVEMENT_VALIDATION_NOT_AUTHORIZED"
                  if all(x["status"].startswith("OFFICIAL_SOURCE_SCHEMA_AND_PINNED_SHA256") for x in results)
                  else "SOURCE_TRANSPORT_OR_SCHEMA_HAS_SCIENTIFIC_STOP"),
        "source_results":results,
        "new_eog_wf_endpoints":0,
        "biological_values_analyzed":0,
        "individual_records_exported":0,
        "new_model_fits":0,
        "origin_to_destination_inference_authorized":False,
        "full_three_axis_MRR_authorized":False,
        "prior_redirect_stop_preserved":True,
        "scientific_bound":"Even passing publisher SHA and schema checks do not establish natural founder identities, per-individual time-resolved displacement, environmental edge data or any heldout model value."
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    z=run(json.loads(a.protocol.read_text(encoding="utf-8")))
    canonical=json.dumps(z,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    z["sha256_without_self_field"]=hashlib.sha256(canonical.encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":z["status"],
        "source_statuses":{x["source_id"]:x["status"] for x in z["source_results"]},
        "column_headers":{x["source_id"]:{f["name"]:f.get("csv_header") for f in x.get("file_checks",[])
                              if "csv_header" in f} for x in z["source_results"]},
        "biological_values_analyzed":0,
        "new_eog_wf_endpoints":0,
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
