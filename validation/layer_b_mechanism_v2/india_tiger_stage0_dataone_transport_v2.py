#!/usr/bin/env python3
"""Final response-blind DataONE transport diagnostic for locked India tiger.

Only the three predeclared response-independent filenames/checksums may be
searched, resolved, or downloaded. The biological response filename/checksum is
never queried, resolved, previewed, or downloaded. A retrieved object is
accepted only when its bytes match the frozen MD5.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "build" / "layer_b_mechanism_v2" / "india_tiger_dataone_transport_v2"
OUTPUT = OUTDIR / "transport.json"

SOLR = "https://cn.dataone.org/cn/v2/query/solr/"
RESOLVE = "https://cn.dataone.org/cn/v2/resolve/"
METADATA_PID = "sha256:da5c10209e3fa2ecd31a27d2e59d8f11ee517b44a471e2e80668e72e063435d6"
EXPECTED_TITLE = "Ten year camera trap dataset of tigers in India"

ALLOWED = {
    "EECam_act.csv": "93c958bf9a150438d379a9f1e4e1cc59",
    "EEtraplocs.csv": "e1a522dc2681371899ff3277361b965f",
    "ReadMeTigers.txt": "8982e718365af1d2eef910a5ea9353d9",
}
FORBIDDEN_RESPONSE = "EERecords.csv"
FORBIDDEN_RESPONSE_MD5 = "5775abe5e15d2392050cdfc5c59c99a1"


def _get(url: str, *, accept: str = "application/json") -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "eog-response-blind-qualification-v2/3", "Accept": accept},
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def _solr(params: dict[str, str]) -> dict:
    q = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return json.loads(_get(f"{SOLR}?{q}").decode("utf-8"))


def _escape_solr(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _doc_for_pid(pid: str) -> dict:
    payload = _solr(
        {
            "q": f'id:"{_escape_solr(pid)}"',
            "fl": "id,title,identifier,fileName,checksum,checksumAlgorithm,dataUrl,formatType,isPublic,size,datasource",
            "rows": "5",
            "wt": "json",
        }
    )
    docs = payload.get("response", {}).get("docs", [])
    if len(docs) != 1:
        raise RuntimeError(f"expected one DataONE index record for {pid!r}, got {len(docs)}")
    return docs[0]


def _docs_for_allowed(filename: str, expected_md5: str) -> tuple[list[dict], str]:
    if filename not in ALLOWED or ALLOWED[filename] != expected_md5:
        raise RuntimeError(f"non-allowed object lookup blocked: {filename!r}")
    fields = "id,fileName,checksum,checksumAlgorithm,dataUrl,formatType,isPublic,size,datasource,isDocumentedBy,resourceMap"
    # Prefer the immutable checksum. Fall back to exact allowed filename only;
    # no response filename/checksum is ever submitted to DataONE.
    for mode, query in (
        ("frozen_md5", f'checksum:"{_escape_solr(expected_md5)}"'),
        ("allowed_filename", f'fileName:"{_escape_solr(filename)}"'),
    ):
        payload = _solr({"q": query, "fl": fields, "rows": "100", "wt": "json"})
        docs = payload.get("response", {}).get("docs", [])
        if docs:
            return docs, mode
    return [], "none"


def _location_urls(pid: str) -> list[str]:
    encoded = urllib.parse.quote(pid, safe="")
    raw = _get(f"{RESOLVE}{encoded}", accept="application/xml")
    root = ET.fromstring(raw)
    return [
        elem.text.strip()
        for elem in root.iter()
        if elem.tag.rsplit("}", 1)[-1] == "url" and elem.text
    ]


def _download_pid(pid: str, filename: str) -> tuple[bytes, str]:
    if filename not in ALLOWED:
        raise RuntimeError(f"non-allowed file resolution blocked: {filename!r}")
    urls = _location_urls(pid)
    errors = []
    for url in urls:
        try:
            return _get(url, accept="application/octet-stream"), url
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(f"no DataONE replica transport succeeded for {filename}: {errors}")


def _acquire_allowed(filename: str, expected_md5: str) -> dict:
    docs, lookup_mode = _docs_for_allowed(filename, expected_md5)
    if not docs:
        raise RuntimeError(
            f"DataONE index returned no object for allowed filename/checksum: {filename!r}/{expected_md5}"
        )
    failures = []
    for doc in docs:
        pid = str(doc.get("id", ""))
        if not pid:
            continue
        try:
            data, source_url = _download_pid(pid, filename)
        except Exception as exc:
            failures.append(f"{pid}: {type(exc).__name__}: {exc}")
            continue
        observed_md5 = hashlib.md5(data).hexdigest()
        if observed_md5 != expected_md5:
            failures.append(f"{pid}: md5={observed_md5}")
            continue
        (OUTDIR / filename).write_bytes(data)
        return {
            "pid": pid,
            "bytes": len(data),
            "md5": observed_md5,
            "expected_md5": expected_md5,
            "checksum_match": True,
            "lookup_mode": lookup_mode,
            "source_url": source_url,
            "dataone_index_checksum": doc.get("checksum"),
            "dataone_index_checksum_algorithm": doc.get("checksumAlgorithm"),
            "dataone_datasource": doc.get("datasource"),
            "is_documented_by": doc.get("isDocumentedBy"),
            "resource_map": doc.get("resourceMap"),
            "candidate_object_count": len(docs),
        }
    raise RuntimeError(
        f"no byte-identical DataONE object could be transported for allowed file {filename!r}; attempts={failures}"
    )


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "eog.layer_b_mechanism_v2.india_tiger_stage0_dataone_transport.v2",
        "candidate": "india_tiger",
        "diagnostic_attempt": "final_dataone_lookup_by_frozen_md5_then_allowed_filename",
        "response_payload_requests": 0,
        "response_bytes_opened": 0,
        "response_values_opened": False,
        "response_metadata_queried": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "dataone_metadata_pid": METADATA_PID,
        "allowed_files": {},
        "forbidden_response": {
            "filename": FORBIDDEN_RESPONSE,
            "frozen_md5": FORBIDDEN_RESPONSE_MD5,
            "queried": False,
            "resolved": False,
            "downloaded": False,
        },
    }
    try:
        package = _doc_for_pid(METADATA_PID)
        title = package.get("title")
        if isinstance(title, list):
            title = title[0] if title else None
        if title != EXPECTED_TITLE:
            raise RuntimeError(f"unexpected DataONE metadata title: {title!r}")
        result["dataone_metadata_title_verified"] = True

        for filename, expected_md5 in ALLOWED.items():
            result["allowed_files"][filename] = _acquire_allowed(filename, expected_md5)

        result["status"] = "stage0_response_blind_transport_qualified"
        result["all_allowed_files_checksum_verified"] = True
        result["response_open_authorized"] = False
        result["next_gate"] = "response_independent_schema_estimability_and_execution_contract_qualification"
        rc = 0
    except Exception as exc:
        result["status"] = "terminal_pre_response_transport_stop_after_final_dataone_diagnostic"
        result["all_allowed_files_checksum_verified"] = False
        result["response_open_authorized"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        rc = 2

    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
