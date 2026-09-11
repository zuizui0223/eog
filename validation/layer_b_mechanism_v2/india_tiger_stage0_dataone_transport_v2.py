#!/usr/bin/env python3
"""Response-blind DataONE transport retry for the locked India tiger candidate.

This stage may inspect public DataONE system/package metadata, but it must never
resolve or GET the biological response object. It downloads only the three
predeclared response-independent files and verifies their frozen MD5 values.
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
        headers={"User-Agent": "eog-response-blind-qualification-v2/1", "Accept": accept},
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def _solr(params: dict[str, str]) -> dict:
    q = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return json.loads(_get(f"{SOLR}?{q}").decode("utf-8"))


def _doc_for_pid(pid: str) -> dict:
    escaped = pid.replace("\\", "\\\\").replace('"', '\\"')
    payload = _solr(
        {
            "q": f'id:"{escaped}"',
            "fl": "id,title,identifier,documents,fileName,checksum,checksumAlgorithm,dataUrl,formatType,isPublic,size",
            "rows": "5",
            "wt": "json",
        }
    )
    docs = payload.get("response", {}).get("docs", [])
    if len(docs) != 1:
        raise RuntimeError(f"expected one DataONE index record for {pid!r}, got {len(docs)}")
    return docs[0]


def _location_urls(pid: str) -> list[str]:
    encoded = urllib.parse.quote(pid, safe="")
    raw = _get(f"{RESOLVE}{encoded}", accept="application/xml")
    root = ET.fromstring(raw)
    urls = []
    for elem in root.iter():
        if elem.tag.rsplit("}", 1)[-1] == "url" and elem.text:
            urls.append(elem.text.strip())
    return urls


def _download_allowed(pid: str, filename: str) -> tuple[bytes, str]:
    urls = _location_urls(pid)
    errors = []
    for url in urls:
        try:
            return _get(url, accept="application/octet-stream"), url
        except Exception as exc:  # transport fallback across immutable replicas
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(f"no DataONE replica transport succeeded for {filename}: {errors}")


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "eog.layer_b_mechanism_v2.india_tiger_stage0_dataone_transport.v2",
        "candidate": "india_tiger",
        "response_payload_requests": 0,
        "response_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "dataone_metadata_pid": METADATA_PID,
        "allowed_files": {},
        "forbidden_response": {
            "filename": FORBIDDEN_RESPONSE,
            "frozen_md5": FORBIDDEN_RESPONSE_MD5,
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
            raise RuntimeError(f"unexpected DataONE package title: {title!r}")

        documents = package.get("documents") or []
        if isinstance(documents, str):
            documents = [documents]
        if not documents:
            raise RuntimeError("DataONE metadata record exposes no documented data-object PIDs")

        by_name: dict[str, tuple[str, dict]] = {}
        response_metadata_seen = False
        for pid in documents:
            doc = _doc_for_pid(str(pid))
            name = doc.get("fileName")
            if isinstance(name, list):
                name = name[0] if name else None
            if not name:
                continue
            by_name[str(name)] = (str(pid), doc)
            if name == FORBIDDEN_RESPONSE:
                response_metadata_seen = True
                # Deliberately do not resolve the response PID and do not request its bytes.

        result["forbidden_response"]["metadata_seen_without_payload"] = response_metadata_seen

        missing = sorted(set(ALLOWED) - set(by_name))
        if missing:
            raise RuntimeError(f"DataONE package metadata missing allowed filenames: {missing}")

        for filename, expected_md5 in ALLOWED.items():
            pid, doc = by_name[filename]
            data, source_url = _download_allowed(pid, filename)
            observed_md5 = hashlib.md5(data).hexdigest()
            if observed_md5 != expected_md5:
                raise RuntimeError(
                    f"MD5 mismatch for {filename}: expected {expected_md5}, got {observed_md5}"
                )
            path = OUTDIR / filename
            path.write_bytes(data)
            result["allowed_files"][filename] = {
                "pid": pid,
                "bytes": len(data),
                "md5": observed_md5,
                "expected_md5": expected_md5,
                "checksum_match": True,
                "source_url": source_url,
                "dataone_index_checksum": doc.get("checksum"),
                "dataone_index_checksum_algorithm": doc.get("checksumAlgorithm"),
            }

        result["status"] = "stage0_response_blind_transport_qualified"
        result["all_allowed_files_checksum_verified"] = True
        result["response_open_authorized"] = False
        result["next_gate"] = "response_independent_schema_estimability_and_execution_contract_qualification"
        rc = 0
    except Exception as exc:
        result["status"] = "stop_pre_response_dataone_transport_or_package_resolution"
        result["all_allowed_files_checksum_verified"] = False
        result["response_open_authorized"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        rc = 2

    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
