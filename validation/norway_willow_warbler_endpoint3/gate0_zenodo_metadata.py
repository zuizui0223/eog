from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"


class MetadataGateStop(RuntimeError):
    """Terminal response-blind Zenodo metadata identity/interface STOP."""


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


def _required_int(mapping: dict[str, object], key: str, label: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MetadataGateStop(f"{label} lacks integer {key}")
    return value


def _required_str(mapping: dict[str, object], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MetadataGateStop(f"{label} lacks non-empty string {key}")
    return value.strip()


def evaluate_zenodo_metadata(
    metadata: object,
    contract: dict[str, object],
) -> dict[str, object]:
    """Evaluate exact Zenodo record metadata without touching archive bytes."""
    if not isinstance(metadata, dict):
        raise MetadataGateStop("Zenodo record metadata must be a JSON object")
    if not isinstance(contract, dict):
        raise TypeError("contract must be dict")

    source = contract.get("source")
    gate = contract.get("gate0_metadata_only")
    if not isinstance(source, dict) or not isinstance(gate, dict):
        raise TypeError("contract source/gate0_metadata_only must be objects")

    record_id = _required_int(metadata, "id", "Zenodo record metadata")
    if record_id != source["record_id"]:
        raise MetadataGateStop(
            f"Zenodo record id drift: {record_id} != {source['record_id']}"
        )

    doi = _required_str(metadata, "doi", "Zenodo record metadata")
    if doi != source["doi"]:
        raise MetadataGateStop(f"Zenodo DOI drift: {doi!r} != {source['doi']!r}")

    record_metadata = metadata.get("metadata")
    if not isinstance(record_metadata, dict):
        raise MetadataGateStop("Zenodo record lacks metadata object")
    title = _required_str(record_metadata, "title", "Zenodo metadata")
    if title != source["expected_title"]:
        raise MetadataGateStop(
            f"Zenodo title drift: {title!r} != {source['expected_title']!r}"
        )

    files = metadata.get("files")
    if not isinstance(files, list):
        raise MetadataGateStop("Zenodo record lacks files list")
    archive_name = source["archive_name"]
    selected = [
        row
        for row in files
        if isinstance(row, dict) and row.get("key") == archive_name
    ]
    if len(selected) != 1:
        raise MetadataGateStop(
            f"Zenodo archive {archive_name!r} occurs {len(selected)} times; expected exactly one"
        )
    file_row = selected[0]

    name = _required_str(file_row, "key", "Zenodo archive metadata")
    size = _required_int(file_row, "size", "Zenodo archive metadata")
    if size <= 0:
        raise MetadataGateStop("Zenodo archive size must be positive")
    checksum = _required_str(file_row, "checksum", "Zenodo archive metadata")
    match = re.fullmatch(r"md5:([0-9a-f]{32})", checksum)
    if match is None:
        raise MetadataGateStop(
            f"Zenodo archive checksum does not match frozen md5 format: {checksum!r}"
        )
    if match.group(1) != source["archive_md5"]:
        raise MetadataGateStop(
            f"Zenodo archive MD5 drift: {match.group(1)} != {source['archive_md5']}"
        )

    links = file_row.get("links")
    if not isinstance(links, dict):
        raise MetadataGateStop("Zenodo archive metadata lacks links object")
    link_key = gate["required_archive_link_key"]
    if not isinstance(link_key, str):
        raise TypeError("required_archive_link_key must be str")
    download_url = _required_str(links, link_key, "Zenodo archive links")
    parsed = urlparse(download_url)
    if parsed.scheme != gate["required_archive_download_scheme"] or not parsed.hostname:
        raise MetadataGateStop("Zenodo archive content URL is not an absolute frozen-scheme URL")

    identity = {
        "record_id": record_id,
        "doi": doi,
        "title": title,
        "record_file_count": len(files),
        "archive_name": name,
        "archive_size_bytes": size,
        "archive_md5": match.group(1),
        "archive_content_url": download_url,
        "archive_content_host": parsed.hostname,
    }
    result: dict[str, object] = {
        "schema": "eog.norway_willow_warbler_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_metadata_ready",
        "metadata_only": True,
        "identity": identity,
        "archive_payload_requests": 0,
        "archive_payload_bytes_opened": 0,
        "member_payload_requests": 0,
        "member_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_stop_result(contract: dict[str, object], reason: str) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.norway_willow_warbler_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_metadata_identity_or_transport",
        "reason": str(reason),
        "metadata_only": True,
        "archive_payload_requests": 0,
        "archive_payload_bytes_opened": 0,
        "member_payload_requests": 0,
        "member_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("source contract must be a JSON object")
    return value
