"""Metadata-only Dryad Gate0 for the Sweden river-barrier M-only bridge."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "source_protocol_v1.json"
OUTPUT = HERE / "gate0_dryad_identity_certificate.json"

BASE = "https://datadryad.org"
DOI = "10.5061/dryad.05qfttf9z"
ENCODED = quote("doi:" + DOI, safe="")
API_VERSION = "2.1.0"
USER_AGENT = "EOG-Sweden-RiverBarrier-Gate0/1.0"

EXPECTED_ROSTER = (
    "README.md",
    "all_data_synchrony.csv",
    "pop_perf_minnow.csv",
    "pop_perf_pike.csv",
    "pop_perf_trout.csv",
    "rawdf.csv",
    "synchrony_final.R",
)


class Gate0Stop(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _get_json(path: str) -> dict[str, Any]:
    req = Request(
        BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-API-Version": API_VERSION,
        },
        method="GET",
    )
    with urlopen(req, timeout=60) as response:
        if int(response.status) != 200:
            raise Gate0Stop(f"Dryad API {path} returned HTTP {response.status}")
        body = response.read()
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise Gate0Stop(f"Dryad API {path} did not return JSON object")
    return payload


def _embedded_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    embedded = payload.get("_embedded")
    if not isinstance(embedded, dict):
        raise Gate0Stop("Dryad payload missing _embedded")
    rows = embedded.get(key)
    if not isinstance(rows, list) or not all(isinstance(x, dict) for x in rows):
        raise Gate0Stop(f"Dryad payload missing embedded list {key}")
    return rows


_VERSION_SELF_RE = re.compile(r"^/api/v2/versions/(?P<id>[1-9][0-9]*)$")


def _version_id(row: dict[str, Any]) -> int:
    value = row.get("id")
    if isinstance(value, int) and value > 0:
        return value
    links = row.get("_links")
    if not isinstance(links, dict):
        raise Gate0Stop("version missing _links")
    self_link = links.get("self")
    if not isinstance(self_link, dict):
        raise Gate0Stop("version missing self link")
    href = self_link.get("href")
    if not isinstance(href, str):
        raise Gate0Stop("version self href is not string")
    match = _VERSION_SELF_RE.fullmatch(href)
    if match is None:
        raise Gate0Stop(f"unexpected version self href: {href!r}")
    return int(match.group("id"))


def evaluate(
    dataset: dict[str, Any],
    versions_payload: dict[str, Any],
    files_payload: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    if protocol.get("status") != "frozen_before_dryad_data_payload_access":
        raise Gate0Stop("protocol is not at frozen pre-payload boundary")

    identifier = str(dataset.get("identifier", ""))
    if identifier not in {DOI, "doi:" + DOI}:
        raise Gate0Stop(f"Dryad DOI mismatch: {identifier!r}")

    expected_title = str(protocol["source"]["title"])
    if str(dataset.get("title", "")) != expected_title:
        raise Gate0Stop("Dryad title mismatch")

    versions = _embedded_list(versions_payload, "stash:versions")
    if len(versions) != 1:
        raise Gate0Stop(f"expected one published version, got {len(versions)}")
    version = versions[0]
    version_id = _version_id(version)

    files = _embedded_list(files_payload, "stash:files")
    by_path: dict[str, dict[str, Any]] = {}
    for row in files:
        path = str(row.get("path", ""))
        if not path:
            raise Gate0Stop("file metadata missing path")
        if path in by_path:
            raise Gate0Stop(f"duplicate file path: {path}")
        by_path[path] = row

    if tuple(sorted(by_path)) != tuple(sorted(EXPECTED_ROSTER)):
        raise Gate0Stop(
            "Dryad roster drift: "
            f"missing={sorted(set(EXPECTED_ROSTER)-set(by_path))}; "
            f"unexpected={sorted(set(by_path)-set(EXPECTED_ROSTER))}"
        )

    required = set(protocol["source"]["required_files"])
    if not required.issubset(by_path):
        raise Gate0Stop(f"required files missing: {sorted(required-set(by_path))}")

    frozen = []
    for path in sorted(by_path):
        row = by_path[path]
        size = row.get("size")
        digest = str(row.get("digest", ""))
        digest_type = str(row.get("digestType", ""))
        links = row.get("_links")
        if not isinstance(size, int) or size <= 0:
            raise Gate0Stop(f"invalid size for {path}")
        if digest_type.lower() != "sha-256" or not digest:
            raise Gate0Stop(f"missing sha-256 digest for {path}")
        if not isinstance(links, dict):
            raise Gate0Stop(f"missing links for {path}")
        download = links.get("stash:download")
        self_link = links.get("self")
        if not isinstance(download, dict) or not isinstance(download.get("href"), str):
            raise Gate0Stop(f"missing download link for {path}")
        if not isinstance(self_link, dict) or not isinstance(self_link.get("href"), str):
            raise Gate0Stop(f"missing file self link for {path}")
        frozen.append({
            "path": path,
            "size_bytes": size,
            "sha256": digest.lower(),
            "file_api_path": self_link["href"],
            "download_api_path": download["href"],
            "required_for_bridge": path in required,
        })

    result: dict[str, Any] = {
        "schema": "eog.bam_sweden_riverbarrier_external_bridge.gate0.v1",
        "status": "dryad_source_identity_ready",
        "doi": DOI,
        "title": expected_title,
        "dataset_id": dataset.get("id"),
        "version_id": version_id,
        "version_number": version.get("versionNumber"),
        "file_count": len(frozen),
        "files": frozen,
        "api_version_requested": API_VERSION,
        "data_file_payload_requests": 0,
        "data_file_payload_bytes_opened": 0,
        "model_fits": 0,
        "next_authorized_stage": "README/documentation Gate1",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    dataset_path = f"/api/v2/datasets/{ENCODED}"
    versions_path = f"{dataset_path}/versions"

    dataset = _get_json(dataset_path)
    versions_payload = _get_json(versions_path)
    versions = _embedded_list(versions_payload, "stash:versions")
    if len(versions) != 1:
        raise Gate0Stop(f"cannot resolve single version: {len(versions)}")
    version_id = _version_id(versions[0])
    files_payload = _get_json(f"/api/v2/versions/{version_id}/files")

    result = evaluate(dataset, versions_payload, files_payload, protocol)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
