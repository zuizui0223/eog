#!/usr/bin/env python3
"""Arctic tern real-known-departure source metadata gate: no movement rows.

Public official Dryad dataset, version and file manifest are retrieved
without downloading any archived event data. All file/DOI and year checks
were frozen before any source query. No ecological scoring permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
from typing import Any

from scripts import eog_independent_movement_source_gate_v1 as dryad

PROTOCOL = Path("validation/tern_published_departure_source_gate_v1/protocol_v1.json")


def _sha(payload: object) -> str:
    return hashlib.sha256((
        json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    ).encode("utf-8")).hexdigest()


def qualify_metadata(protocol: dict[str,Any], *,
                    fetch_json=dryad._json_get) -> dict[str,Any]:
    """Only publisher metadata. Dependency-injected for offline guard tests."""
    status = {
        "schema": "eog.tern_published_departure_source_metadata_v1.receipt",
        "status": "STOP_UNSTARTED",
        "declared_doi":protocol["declared_source"]["dataset_doi"],
        "models_fit":0, "event_rows_read":0, "predictions_scored":0,
        "movement_events_scored":0,"new_eog_wf_endpoints":0,
        "source_holdout_authorized":False,
    }
    if protocol.get("status") != "PRE_METADATA_SOURCE_ONLY_FROZEN":
        status["status"]="STOP_PROTOCOL_NOT_FROZEN"
        return status
    src = protocol["declared_source"]
    gate=protocol["stage0_transport"]
    limits={
        "max_metadata_bytes":min(
            gate["dataset_metadata_max_bytes"],
            gate["version_metadata_max_bytes"],
            gate["files_metadata_max_bytes"],
        ),
        "request_timeout_seconds":gate["timeout_seconds"],
    }
    url="https://datadryad.org/api/v2"
    try:
        encoded=urllib.parse.quote("doi:"+src["dataset_doi"],safe="")
        meta, meta_sha=fetch_json(url+"/datasets/"+encoded,limits)
        status["dataset_metadata_sha256"]=meta_sha
        ident=str(meta.get("identifier") or meta.get("doi") or "").lower()
        if src["dataset_doi"].lower() not in ident:
            raise ValueError("STOP_DATASET_DOI_IDENTITY")
        title=str(meta.get("title") or "")
        title_lower=title.lower()
        if any(term not in title_lower for term in ("natal", "breeding", "dispersal", "arctic", "tern")):
            raise ValueError("STOP_TITLE_SCOPE_MISMATCH")
        status["title"]=title[:220]
        version_id=dryad._version_id(meta)
        if not version_id.isdigit():
            raise ValueError("STOP_VERSION_ID_SCHEMA")
        version,version_sha=fetch_json(f"{url}/versions/{version_id}",limits)
        status["version_metadata_sha256"]=version_sha
        manifest,manifest_sha=fetch_json(f"{url}/versions/{version_id}/files?per_page=100",limits)
        status["files_metadata_sha256"]=manifest_sha
        all_files=dryad._metadata_files(manifest,gate["file_count_max"])
        expected=sorted(src["prelisted_files"])
        actual=sorted(f["name"] for f in all_files)
        if actual!=expected:
            raise ValueError("STOP_PUBLISHED_FILE_ROSTER_MISMATCH")
        if any(x["size_bytes"]<=0 for x in all_files):
            raise ValueError("STOP_MISSING_PUBLISHER_FILE_SIZE")
        pubdate=str(version.get("publicationDate") or meta.get("publicationDate") or "")
        if not pubdate.startswith(src["expected_first_publication_date"]):
            raise ValueError("STOP_VERSION_PUBLICATION_DATE_MISMATCH")
        status.update({
            "status":"SOURCE_METADATA_AND_FILE_MANIFEST_QUALIFIED_NO_EVENTS",
            "publisher_version_id":int(version_id),
            "published_date":pubdate[:10],
            "file_manifest":all_files,
            "file_manifest_sha256":_sha(all_files),
            "publisher_data_version_is_predeclared":True,
            "data_files_downloaded":0,
            "all_candidate_event_rows_unread":True,
        })
    except urllib.error.HTTPError as e:
        status["status"]=f"STOP_SOURCE_HTTP_{e.code}"
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        status["status"]="STOP_SOURCE_TRANSPORT"
        status["error_type"]=type(e).__name__
    except (ValueError,KeyError,TypeError,IndexError,OverflowError,json.JSONDecodeError) as e:
        status["status"]=str(e) if str(e).startswith("STOP_") else "STOP_SOURCE_METADATA_SCHEMA"
        status["error_type"]=type(e).__name__
    return status


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    protocol=json.loads(a.protocol.read_text(encoding="utf-8"))
    result=qualify_metadata(protocol)
    result["receipt_sha256_without_self"]=_sha(result)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "version_id":result.get("publisher_version_id"),
        "file_manifest":result.get("file_manifest"),
        "event_rows_read":0,
        "new_eog_wf_endpoints":0,
        "receipt_sha256":result["receipt_sha256_without_self"],
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
