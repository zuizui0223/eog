from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_metadata_certificate.json"
USER_AGENT = "EOG-Columbia-Shrubsteppe-Endpoint3-Gate0/1.0"
JsonFetcher = Callable[[str], dict[str, object]]
_VERSION_HREF_RE = re.compile(r"^/api/v2/versions/([1-9][0-9]*)/?$")


class MetadataGateStop(RuntimeError):
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


def _absolute_api_url(href: object) -> str:
    if not isinstance(href, str) or not href.strip():
        raise MetadataGateStop("Dryad metadata link is missing")
    url = urljoin("https://datadryad.org", href)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "datadryad.org":
        raise MetadataGateStop(f"Dryad metadata link left frozen host: {url!r}")
    return url


def _http_fetch_json(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "datadryad.org":
        raise MetadataGateStop("metadata URL must use https://datadryad.org")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-API-Version": "2.1.0",
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = getattr(response, "status", None) or response.getcode()
            final_url = response.geturl()
            final = urlparse(final_url)
            headers = {key.lower(): value for key, value in response.headers.items()}
            if status != 200:
                raise MetadataGateStop(f"Dryad metadata returned HTTP {status}")
            if final_url != url or final.scheme != "https" or final.hostname != "datadryad.org":
                raise MetadataGateStop("Dryad metadata request changed frozen URL identity")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise MetadataGateStop("Dryad metadata unexpectedly used content encoding")
            payload = response.read(2_000_001)
    except (OSError, urllib.error.URLError) as exc:
        raise MetadataGateStop(f"Dryad metadata transport unavailable: {exc}") from exc
    if len(payload) > 2_000_000:
        raise MetadataGateStop("Dryad metadata exceeded 2 MB response cap")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetadataGateStop("Dryad metadata was not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise MetadataGateStop("Dryad metadata root must be an object")
    return value


def _link(obj: dict[str, object], rel: str) -> str | None:
    links = obj.get("_links")
    if not isinstance(links, dict):
        return None
    item = links.get(rel)
    if not isinstance(item, dict):
        return None
    href = item.get("href")
    return href if isinstance(href, str) and href.strip() else None


def _version_id_from_dataset(dataset: dict[str, object]) -> tuple[int, str]:
    href = _link(dataset, "stash:version")
    if href is None:
        raise MetadataGateStop("Dryad dataset metadata lacks current stash:version link")
    parsed = urlparse(_absolute_api_url(href))
    match = _VERSION_HREF_RE.fullmatch(parsed.path)
    if match is None:
        raise MetadataGateStop(f"Dryad current-version href has unexpected shape: {href!r}")
    return int(match.group(1)), href


def _extract_files(payload: dict[str, object]) -> list[dict[str, object]]:
    embedded = payload.get("_embedded")
    candidates: object = None
    if isinstance(embedded, dict):
        for key in ("stash:files", "files"):
            if key in embedded:
                candidates = embedded[key]
                break
    if candidates is None:
        for key in ("files", "items"):
            if key in payload:
                candidates = payload[key]
                break
    if not isinstance(candidates, list):
        raise MetadataGateStop("Dryad file-list metadata did not expose a file array")
    rows: list[dict[str, object]] = []
    for row in candidates:
        if not isinstance(row, dict):
            raise MetadataGateStop("Dryad file-list row is not an object")
        rows.append(row)
    return rows


def _file_path(row: dict[str, object]) -> str:
    for key in ("path", "filename", "name"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise MetadataGateStop("Dryad file metadata is missing path/name")


def _href_from_links(row: dict[str, object], relations: tuple[str, ...]) -> str | None:
    links = row.get("_links")
    if not isinstance(links, dict):
        return None
    for rel in relations:
        item = links.get(rel)
        if isinstance(item, dict):
            href = item.get("href")
            if isinstance(href, str) and href.strip():
                return href.strip()
    return None


def _normalize_file(row: dict[str, object]) -> dict[str, object]:
    path = _file_path(row)
    size = row.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise MetadataGateStop(f"Dryad file {path!r} lacks positive integer size")
    digest = row.get("digest")
    digest_type = row.get("digestType")
    if not isinstance(digest, str) or not digest.strip():
        raise MetadataGateStop(f"Dryad file {path!r} lacks non-empty digest")
    if not isinstance(digest_type, str) or not digest_type.strip():
        raise MetadataGateStop(f"Dryad file {path!r} lacks non-empty digestType")
    self_href = _href_from_links(row, ("self",))
    download_href = _href_from_links(row, ("stash:download", "download"))
    if self_href is not None:
        _absolute_api_url(self_href)
    if download_href is not None:
        _absolute_api_url(download_href)
    return {
        "path": path,
        "size": size,
        "digest": digest.strip(),
        "digest_type": digest_type.strip(),
        "mime_type": row.get("mimeType"),
        "status": row.get("status"),
        "self_href": self_href,
        "download_href": download_href,
    }


def evaluate_metadata(
    contract: dict[str, object],
    dataset: dict[str, object],
    version: dict[str, object],
    files_payload: dict[str, object],
    *,
    version_id: int,
    version_href: str,
) -> dict[str, object]:
    dryad = contract["dryad"]
    expected_names = list(dryad["expected_exact_file_names"])
    identifier = dataset.get("identifier")
    if identifier != dryad["dataset_identifier_expected"]:
        raise MetadataGateStop(
            f"Dryad dataset identifier drift: {identifier!r} != {dryad['dataset_identifier_expected']!r}"
        )

    version_self = _link(version, "self")
    if version_self is not None:
        observed_self = urlparse(_absolute_api_url(version_self)).path.rstrip("/")
        expected_self = f"/api/v2/versions/{version_id}"
        if observed_self != expected_self:
            raise MetadataGateStop(
                f"Dryad version self-link drift: {observed_self!r} != {expected_self!r}"
            )

    files = [_normalize_file(row) for row in _extract_files(files_payload)]
    names = [str(row["path"]) for row in files]
    if len(names) != len(set(names)):
        raise MetadataGateStop("Dryad file-list metadata contains duplicate paths")
    if len(names) != int(dryad["expected_file_count"]):
        raise MetadataGateStop(
            f"Dryad file count drift: {len(names)} != {dryad['expected_file_count']}"
        )
    if set(names) != set(expected_names):
        missing = sorted(set(expected_names) - set(names))
        extra = sorted(set(names) - set(expected_names))
        raise MetadataGateStop(f"Dryad file identity drift: missing={missing}, extra={extra}")

    ordered = sorted(files, key=lambda row: str(row["path"]))
    result: dict[str, object] = {
        "schema": "eog.columbia_shrubsteppe_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_metadata_ready",
        "dataset_identifier": identifier,
        "current_version_id": version_id,
        "current_version_href": version_href,
        "file_count": len(ordered),
        "files": ordered,
        "file_manifest_fingerprint": canonical_sha256(ordered),
        "metadata_only": True,
        "metadata_requests": 3,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "archive_member_bytes_opened": 0,
        "detection_history_bytes_opened": 0,
        "camera_record_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "next_gate": "bounded ZIP metadata inventory for CSVs.zip and Raw_Data.zip only",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    fetch_json: JsonFetcher = _http_fetch_json,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base: dict[str, object] = {
        "schema": "eog.columbia_shrubsteppe_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "metadata_only": True,
        "metadata_requests": 0,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "archive_member_bytes_opened": 0,
        "detection_history_bytes_opened": 0,
        "camera_record_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    requests = 0
    try:
        dataset_url = str(contract["dryad"]["dataset_api"])
        dataset = fetch_json(dataset_url)
        requests += 1
        version_id, version_href = _version_id_from_dataset(dataset)
        version_url = _absolute_api_url(version_href)
        version = fetch_json(version_url)
        requests += 1
        files_url = f"https://datadryad.org/api/v2/versions/{version_id}/files"
        files_payload = fetch_json(files_url)
        requests += 1
        result = {
            **base,
            **evaluate_metadata(
                contract,
                dataset,
                version,
                files_payload,
                version_id=version_id,
                version_href=version_href,
            ),
        }
        result["metadata_requests"] = requests
        result["fingerprint"] = canonical_sha256({k: v for k, v in result.items() if k != "fingerprint"})
    except MetadataGateStop as exc:
        result = {
            **base,
            "metadata_requests": requests,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; do not open file payload and do not repair this attempt post-STOP",
        }
        result["fingerprint"] = canonical_sha256(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    run()
