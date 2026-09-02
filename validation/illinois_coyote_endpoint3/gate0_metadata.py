from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = ROOT / "build" / "illinois_coyote_endpoint3" / "gate0_metadata.json"
USER_AGENT = "EOG-Illinois-Coyote-Endpoint3-Gate0/1.0"
JsonFetcher = Callable[[str], dict[str, object]]


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
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = getattr(response, "status", None) or response.getcode()
            final = urlparse(response.geturl())
            if status != 200:
                raise MetadataGateStop(f"Dryad metadata returned HTTP {status}")
            if final.scheme != "https" or final.hostname != "datadryad.org":
                raise MetadataGateStop("Dryad metadata request left frozen host")
            payload = response.read()
    except (OSError, urllib.error.URLError) as exc:
        raise MetadataGateStop(f"Dryad metadata transport unavailable: {exc}") from exc
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
    files: list[dict[str, object]] = []
    for row in candidates:
        if not isinstance(row, dict):
            raise MetadataGateStop("Dryad file-list row is not an object")
        files.append(row)
    return files


def _file_path(row: dict[str, object]) -> str:
    for key in ("path", "filename", "name"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise MetadataGateStop("Dryad file metadata is missing path/name")


def _normalized_file_metadata(row: dict[str, object]) -> dict[str, object]:
    path = _file_path(row)
    links = row.get("_links") if isinstance(row.get("_links"), dict) else {}
    self_href = None
    download_href = None
    if isinstance(links, dict):
        for rel in ("self",):
            item = links.get(rel)
            if isinstance(item, dict) and isinstance(item.get("href"), str):
                self_href = item["href"]
        for rel in ("stash:download", "download"):
            item = links.get(rel)
            if isinstance(item, dict) and isinstance(item.get("href"), str):
                download_href = item["href"]
                break
    return {
        "path": path,
        "size": row.get("size"),
        "digest": row.get("digest"),
        "digest_type": row.get("digestType"),
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
) -> dict[str, object]:
    expected = list(contract["dryad"]["expected_exact_file_names"])
    files = [_normalized_file_metadata(row) for row in _extract_files(files_payload)]
    names = [str(row["path"]) for row in files]
    if len(names) != len(set(names)):
        raise MetadataGateStop("Dryad file-list metadata contains duplicate paths")
    if len(names) != int(contract["dryad"]["expected_file_count"]):
        raise MetadataGateStop(
            f"Dryad file count drift: {len(names)} != {contract['dryad']['expected_file_count']}"
        )
    if set(names) != set(expected):
        missing = sorted(set(expected) - set(names))
        extra = sorted(set(names) - set(expected))
        raise MetadataGateStop(f"Dryad file identity drift: missing={missing}, extra={extra}")

    identifier = dataset.get("identifier") or dataset.get("id")
    if not isinstance(identifier, (str, int)):
        raise MetadataGateStop("Dryad dataset metadata lacks a stable identifier")
    version_id = version.get("id")
    if isinstance(version_id, bool) or not isinstance(version_id, int):
        raise MetadataGateStop("Dryad current-version metadata lacks integer id")

    ordered = sorted(files, key=lambda row: str(row["path"]))
    result = {
        "schema": "eog.illinois_coyote_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_metadata_ready",
        "dataset_identifier": str(identifier),
        "current_version_id": version_id,
        "file_count": len(ordered),
        "files": ordered,
        "metadata_only": True,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "next_gate": "freeze exact file metadata receipt, then open only response-independent deployment/site/effort payloads under a separate predeclared gate",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    fetch_json: JsonFetcher = _http_fetch_json,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.illinois_coyote_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "metadata_only": True,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        dataset_url = str(contract["dryad"]["dataset_api"])
        dataset = fetch_json(dataset_url)
        version_href = _link(dataset, "stash:version")
        if version_href is None:
            raise MetadataGateStop("Dryad dataset metadata lacks current stash:version link")
        version = fetch_json(_absolute_api_url(version_href))
        version_id = version.get("id")
        if isinstance(version_id, bool) or not isinstance(version_id, int):
            raise MetadataGateStop("Dryad current-version metadata lacks integer id")
        files_href = _link(version, "stash:files")
        if files_href is None:
            files_url = f"https://datadryad.org/api/v2/versions/{version_id}/files"
        else:
            files_url = _absolute_api_url(files_href)
        files_payload = fetch_json(files_url)
        result = {**base, **evaluate_metadata(contract, dataset, version, files_payload)}
    except MetadataGateStop as exc:
        result = {
            **base,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; do not open any file payload and do not repair this attempt post-STOP",
        }
        result["fingerprint"] = canonical_sha256(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    run()
