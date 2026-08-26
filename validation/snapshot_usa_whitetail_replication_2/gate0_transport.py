from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "snapshot_usa_whitetail_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_transport.json"
DRYAD = "https://datadryad.org"
UA = "EOG-Snapshot-USA-current-transport-gate/1.0"


def fp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def get_json(url: str, audit: dict):
    audit["metadata_requests"].append(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", "X-API-Version": "2.1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise RuntimeError("Dryad metadata exceeded 8 MB bound")
    return json.loads(raw.decode("utf-8"))


def absolute(href: str) -> str:
    return urllib.parse.urljoin(DRYAD, href)


def file_id(row: dict) -> int:
    href = row.get("_links", {}).get("self", {}).get("href")
    if not href:
        raise RuntimeError(f"file lacks self link: {row.get('path')}")
    return int(str(href).rstrip("/").split("/")[-1])


def identity(row: dict) -> dict:
    return {
        "file_id": file_id(row),
        "path": row.get("path"),
        "size": row.get("size"),
        "digest": row.get("digest"),
        "digestType": row.get("digestType"),
        "api_download_href": row.get("_links", {}).get("stash:download", {}).get("href"),
    }


def write(result: dict):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main() -> int:
    c = CONTRACT["dataset"]
    firewall = dict(CONTRACT["response_firewall"])
    result = {
        "schema": "eog.snapshot_usa_whitetail_replication_2.gate0_transport.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "metadata_requests": [],
        "version": {},
        "deployment": {},
        "response_metadata_only": {},
        "deployment_transport": {},
        "response_firewall": firewall,
    }
    try:
        encoded = urllib.parse.quote(f"doi:{c['doi']}", safe="")
        dataset = get_json(f"{DRYAD}/api/v2/datasets/{encoded}", result)
        version_href = dataset.get("_links", {}).get("stash:version", {}).get("href")
        if not version_href:
            raise RuntimeError("Dryad dataset has no latest-version link")
        version = get_json(absolute(version_href), result)
        files_href = version.get("_links", {}).get("stash:files", {}).get("href")
        if not files_href:
            vid = version.get("id")
            if not vid:
                raise RuntimeError("Dryad latest version lacks files link and id")
            files_href = f"/api/v2/versions/{vid}/files"
        listing = get_json(absolute(files_href), result)
        rows = [x for x in listing.get("_embedded", {}).get("stash:files", []) if isinstance(x, dict)]
        by_path = {str(x.get("path")): x for x in rows}
        for required in (c["deployment_file"], c["response_file"]):
            if required not in by_path:
                raise RuntimeError(f"latest Dryad version missing required file {required}")

        dep = by_path[c["deployment_file"]]
        resp = by_path[c["response_file"]]
        result["version"] = {
            "id": version.get("id"),
            "versionNumber": version.get("versionNumber"),
            "publicationDate": version.get("publicationDate"),
            "lastModificationDate": version.get("lastModificationDate"),
        }
        result["deployment"] = identity(dep)
        result["response_metadata_only"] = {
            **identity(resp),
            "payload_requests": 0,
            "payload_bytes_opened": 0,
            "header_bytes_opened": 0,
            "rows_opened": False,
            "values_opened": False,
        }

        dep_id = file_id(dep)
        url = f"{DRYAD}/downloads/file_stream/{dep_id}"
        result["deployment_transport"] = {"url": url, "attempts": 1}
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
                "Referer": f"{DRYAD}/dataset/doi:{c['doi']}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = response.read(3_000_001)
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type")
        except Exception as exc:
            result["status"] = "stop_current_public_deployment_transport_unavailable"
            result["reason"] = f"{type(exc).__name__}: {exc}"
            result["deployment_transport"].update({"success": False, "payload_bytes_opened": 0})
            write(result)
            return 0

        if len(payload) > 3_000_000:
            raise RuntimeError("deployment payload exceeded 3 MB bound")
        expected_size = int(dep.get("size"))
        if len(payload) != expected_size:
            result["status"] = "stop_deployment_byte_size_mismatch"
            result["reason"] = f"{len(payload)} != {expected_size}"
            result["deployment_transport"].update({"success": True, "payload_bytes_opened": len(payload), "final_url": final_url})
            write(result)
            return 0
        digest_type = str(dep.get("digestType") or "").casefold()
        observed_digest = None
        if digest_type == "sha-256":
            observed_digest = hashlib.sha256(payload).hexdigest()
        elif digest_type == "md5":
            observed_digest = hashlib.md5(payload).hexdigest()
        expected_digest = dep.get("digest")
        if observed_digest is not None and expected_digest and observed_digest != expected_digest:
            result["status"] = "stop_deployment_digest_mismatch"
            result["reason"] = f"observed {observed_digest} != metadata {expected_digest}"
            result["deployment_transport"].update({"success": True, "payload_bytes_opened": len(payload), "final_url": final_url})
            write(result)
            return 0

        result["deployment_transport"].update({
            "success": True,
            "payload_bytes_opened": len(payload),
            "final_url": final_url,
            "content_type": content_type,
            "observed_digest": observed_digest,
        })
        result["status"] = "gate0_transport_pass_deployment_only_response_closed"
        result["reason"] = "current Dryad public individual deployment transport reproduced exact metadata-bound bytes; sequence payload remained unopened"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
