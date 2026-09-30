"""Metadata-only Dryad Gate0 for the Great Lakes A/M external bridge."""
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
DOI = "10.5061/dryad.gb5mkkx5s"
ENCODED = quote("doi:" + DOI, safe="")
API_VERSION = "2.1.0"
USER_AGENT = "EOG-GreatLakes-AM-Bridge-Gate0/1.0"

EXPECTED_ROSTER = (
    "README.md",
    "h_pop_dy_pois_2_habitat.stan",
    "h_pop_dy_pois_2_habitat_onePeriod.stan",
    "h_pop_dy_pois_3_habitat.stan",
    "h_pop_dy_pois_3_habitat_onePeriod.stan",
    "h_pop_dy_pois_4_habitat.stan",
    "h_pop_dy_pois_4_habitat_onePeriod.stan",
    "hab_variables.rds",
    "oikos_data_anlaysis.R",
    "pooled_catch_effort_by_species.rds",
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
    request = Request(
        BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-API-Version": API_VERSION,
        },
        method="GET",
    )
    with urlopen(request, timeout=60) as response:
        if int(response.status) != 200:
            raise Gate0Stop(f"Dryad API {path} returned HTTP {response.status}")
        body = response.read()
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise Gate0Stop(f"Dryad API {path} did not return a JSON object")
    return payload


def _embedded_list(payload: dict[str, Any], rel: str) -> list[dict[str, Any]]:
    embedded = payload.get("_embedded")
    if not isinstance(embedded, dict):
        raise Gate0Stop("Dryad payload missing _embedded object")
    rows = embedded.get(rel)
    if not isinstance(rows, list):
        raise Gate0Stop(f"Dryad payload missing embedded list {rel}")
    if not all(isinstance(row, dict) for row in rows):
        raise Gate0Stop(f"Dryad embedded list {rel} contains non-object rows")
    return rows


_VERSION_SELF_RE = re.compile(r"^/api/v2/versions/(?P<id>[1-9][0-9]*)$")


def _version_id(version: dict[str, Any]) -> int:
    raw = version.get("id")
    if isinstance(raw, int) and raw > 0:
        return raw
    links = version.get("_links")
    if not isinstance(links, dict):
        raise Gate0Stop("Dryad version item missing _links")
    self_link = links.get("self")
    if not isinstance(self_link, dict):
        raise Gate0Stop("Dryad version item missing self link")
    href = self_link.get("href")
    if not isinstance(href, str):
        raise Gate0Stop("Dryad version self link is not a string")
    match = _VERSION_SELF_RE.fullmatch(href)
    if match is None:
        raise Gate0Stop(f"unexpected Dryad version self href: {href!r}")
    return int(match.group("id"))


def evaluate(
    dataset: dict[str, Any],
    versions_payload: dict[str, Any],
    files_payload: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    if protocol.get("status") != "frozen_before_dryad_data_payload_access":
        raise Gate0Stop("source protocol is not frozen at expected boundary")

    identifier = str(dataset.get("identifier", ""))
    if identifier not in {DOI, "doi:" + DOI}:
        raise Gate0Stop(f"Dryad DOI mismatch: {identifier!r}")

    expected_title = str(protocol["source"]["title"])
    if str(dataset.get("title", "")) != expected_title:
        raise Gate0Stop("Dryad dataset title mismatch")

    versions = _embedded_list(versions_payload, "stash:versions")
    if len(versions) != 1:
        raise Gate0Stop(
            f"expected exactly one published Dryad version, found {len(versions)}"
        )
    version = versions[0]
    version_id = _version_id(version)

    files = _embedded_list(files_payload, "stash:files")
    by_name: dict[str, dict[str, Any]] = {}
    for row in files:
        path = str(row.get("path", ""))
        if not path:
            raise Gate0Stop("Dryad file metadata missing path")
        if path in by_name:
            raise Gate0Stop(f"duplicate Dryad file path: {path}")
        by_name[path] = row

    if tuple(sorted(by_name)) != tuple(sorted(EXPECTED_ROSTER)):
        raise Gate0Stop(
            "Dryad file roster drift: "
            f"missing={sorted(set(EXPECTED_ROSTER)-set(by_name))}; "
            f"unexpected={sorted(set(by_name)-set(EXPECTED_ROSTER))}"
        )

    required = set(protocol["source"]["required_files"])
    if not required.issubset(by_name):
        raise Gate0Stop(
            f"required Dryad files missing: {sorted(required-set(by_name))}"
        )

    frozen_files = []
    for path in sorted(by_name):
        row = by_name[path]
        size = row.get("size")
        digest = str(row.get("digest", ""))
        digest_type = str(row.get("digestType", ""))
        links = row.get("_links")
        if not isinstance(size, int) or size <= 0:
            raise Gate0Stop(f"invalid size for {path}")
        if not digest or digest_type.lower() != "sha-256":
            raise Gate0Stop(f"missing sha-256 digest for {path}")
        if not isinstance(links, dict):
            raise Gate0Stop(f"missing links for {path}")
        download = links.get("stash:download")
        self_link = links.get("self")
        if not isinstance(download, dict) or not isinstance(download.get("href"), str):
            raise Gate0Stop(f"missing download link for {path}")
        if not isinstance(self_link, dict) or not isinstance(self_link.get("href"), str):
            raise Gate0Stop(f"missing file self link for {path}")

        frozen_files.append(
            {
                "path": path,
                "size_bytes": size,
                "sha256": digest.lower(),
                "file_api_path": self_link["href"],
                "download_api_path": download["href"],
                "required_for_bridge": path in required,
            }
        )

    result: dict[str, Any] = {
        "schema": "eog.bam_greatlakes_barrier_external_bridge.gate0.v1",
        "status": "dryad_source_identity_ready",
        "doi": DOI,
        "title": expected_title,
        "dataset_id": dataset.get("id"),
        "version_id": version_id,
        "version_number": version.get("versionNumber"),
        "file_count": len(frozen_files),
        "files": frozen_files,
        "api_version_requested": API_VERSION,
        "data_file_payload_requests": 0,
        "data_file_payload_bytes_opened": 0,
        "model_fits": 0,
        "next_authorized_stage": "README-only Gate1",
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
        raise Gate0Stop(
            f"cannot resolve exact single Dryad version before files request: "
            f"found {len(versions)}"
        )
    version_id = _version_id(versions[0])
    files_payload = _get_json(f"/api/v2/versions/{version_id}/files")

    result = evaluate(dataset, versions_payload, files_payload, protocol)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
