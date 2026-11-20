#!/usr/bin/env python3
"""Dryad source transport redirect hostname diagnostic — no ZIP bytes fetched.

Only HEAD (or GET method fallback with zero response-body bytes) to the already
frozen official Dryad URLs. Follows SAME official host only, maximum three
steps. External CDN Location is recorded as hostname alone, never followed.
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

PROTOCOL = Path("validation/independent_movement_redirect_host_v1/protocol_v1.json")


class NeverFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _one_nofollow_request(url: str, method: str, timeout: float) -> tuple[int, str | None]:
    req = urllib.request.Request(
        url, method=method,
        headers={"User-Agent":"EOG-RedirectHostnameAudit/1.0 (source only)",
                 "Accept":"*/*"},
    )
    opener = urllib.request.build_opener(NeverFollow)
    try:
        with opener.open(req, timeout=timeout) as response:
            # Deliberately NO response.read() even when 200 returns file content.
            return int(response.status), response.headers.get("Location")
    except urllib.error.HTTPError as e:
        # No exception detail is printed; it might contain signed query URLs.
        try:
            return int(e.code), e.headers.get("Location")
        finally:
            e.close()


def _safe_host(url: str) -> str | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    return parsed.hostname.lower()


def probe_one(source: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    method = contract["methods"]
    initial = source["official_zip_endpoint"]
    expected_host = method["permitted_initial_host"]
    if _safe_host(initial) != expected_host:
        raise ValueError("STOP_START_HOST_NOT_FROZEN")
    output = {
        "source_id":source["source_id"],"doi":source["doi"],
        "declared_version_id":source["version_id"],
        "status":"STOP_UNSTARTED", "hostname_only":True,
        "biological_rows_read":0,"bytes_from_file_body_read":0,
        "new_eogwf_endpoints":0,
        "hop_status_codes":[],
    }
    url = initial
    for hop in range(method["max_same_host_head_hops"]):
        status, redirect = _one_nofollow_request(
            url, "HEAD", method["request_timeout_sec"]
        )
        if status in (405,501):
            status, redirect = _one_nofollow_request(
                url, "GET", method["request_timeout_sec"]
            )
            output["used_body_unread_get_fallback"] = True
        output["hop_status_codes"].append(status)
        if status in (301,302,303,307,308):
            if not redirect:
                output["status"]="STOP_NO_REDIRECT_LOCATION_HEADER"
                break
            next_url = urllib.parse.urljoin(url,redirect)
            target=_safe_host(next_url)
            if not target:
                output["status"]="STOP_INVALID_REDIRECT_HOST"
                break
            if len(target)>method["max_host_length"]:
                output["status"]="STOP_REDIRECT_HOST_OVERSIZE"
                break
            output["last_redirect_hostname"]=target
            output["external_host_observed"]=target != expected_host
            if target != expected_host:
                output["status"]="STOP_UNVERIFIED_REDIRECT_HOST"
                break
            if hop==method["max_same_host_head_hops"]-1:
                output["status"]="STOP_SAME_HOST_HOP_BUDGET"
                break
            url=next_url
        elif status==200:
            output["status"]="STOP_DIRECT_ZIP_RESPONSE_200_UNREAD"
            break
        else:
            output["status"]=f"STOP_HTTP_{status}"
            break
    return output


def run(protocol: dict[str, Any]) -> dict[str, Any]:
    if protocol.get("status")!="PRE_HEADER_PROBE_FROZEN_NO_BIOLOGICAL_PAYLOAD":
        raise ValueError("STOP_PROTOCOL_NOT_FROZEN")
    sources=[]
    for src in protocol["frozen_endpoint_roster"]:
        try:
            row=probe_one(src,protocol)
        except urllib.error.HTTPError as e:
            row={"source_id":src["source_id"],"status":f"STOP_HTTP_{e.code}"}
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            row={"source_id":src["source_id"],"status":"STOP_HEADER_TRANSPORT_NETWORK",
                 "error_type":type(e).__name__}
        row["biological_rows_read"]=0
        row["new_eogwf_endpoints"]=0
        row["body_bytes_read"]=0
        sources.append(row)
    return {
        "schema":"eog.independent_movement_redirect_host_diagnostic.v1",
        "status":"HOST_DIAGNOSTIC_COMPLETED__SOURCE_SCHEMA_STILL_STOP",
        "source_results":sources,
        "biological_rows_read":0,
        "new_eogwf_endpoints":0,
        "source_qualified":False,
        "source_file_body_read":False,
        "scientific_claim":"Only redirect host provenance, no data, outcome, or ecological transport qualification"
    }


def main() -> None:
    a=argparse.ArgumentParser()
    a.add_argument("--protocol",type=Path,default=PROTOCOL)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    result=run(protocol)
    text=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    result["sha256_without_self_hash"]=hashlib.sha256(text.encode()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"source_results":[{
        "id":x["source_id"],"status":x["status"],
        "host":x.get("last_redirect_hostname"),
        "codes":x.get("hop_status_codes",[])
    }for x in result["source_results"]],"biological_rows_read":0},sort_keys=True))


if __name__=="__main__":
    main()
