from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"


class MetadataGateStop(RuntimeError):
    """Terminal response-blind metadata identity/interface STOP."""


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


def evaluate_figshare_metadata(
    metadata: object,
    contract: dict[str, object],
) -> dict[str, object]:
    """Evaluate only Figshare article JSON metadata; never touches file payloads."""
    if not isinstance(metadata, dict):
        raise MetadataGateStop("Figshare article metadata must be a JSON object")
    if not isinstance(contract, dict):
        raise TypeError("contract must be dict")

    source = contract["source"]
    if not isinstance(source, dict):
        raise TypeError("contract source must be object")

    article_id = _required_int(metadata, "id", "Figshare article metadata")
    if article_id != source["article_id"]:
        raise MetadataGateStop(
            f"Figshare article id drift: {article_id} != {source['article_id']}"
        )

    title = _required_str(metadata, "title", "Figshare article metadata")
    if title != source["expected_title"]:
        raise MetadataGateStop(
            f"Figshare article title drift: {title!r} != {source['expected_title']!r}"
        )

    files = metadata.get("files")
    if not isinstance(files, list):
        raise MetadataGateStop("Figshare article metadata lacks files list")

    selected_id = source["required_primary_file_id"]
    selected = [
        row
        for row in files
        if isinstance(row, dict) and row.get("id") == selected_id
    ]
    if len(selected) != 1:
        raise MetadataGateStop(
            f"Figshare selected file id {selected_id} occurs {len(selected)} times; expected exactly one"
        )

    file_row = selected[0]
    file_id = _required_int(file_row, "id", "Figshare selected file metadata")
    name = _required_str(file_row, "name", "Figshare selected file metadata")
    download_url = _required_str(
        file_row, "download_url", "Figshare selected file metadata"
    )
    parsed = urlparse(download_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise MetadataGateStop("Figshare selected download_url must be absolute HTTPS")
    size = _required_int(file_row, "size", "Figshare selected file metadata")
    if size <= 0:
        raise MetadataGateStop("Figshare selected file size must be positive")

    checksum_field = None
    checksum_value = None
    gate = contract["gate0_metadata_only"]
    if not isinstance(gate, dict):
        raise TypeError("gate0_metadata_only must be object")
    checksum_fields = gate["checksum_fields_optional"]
    if not isinstance(checksum_fields, list):
        raise TypeError("checksum_fields_optional must be list")
    for key in checksum_fields:
        if not isinstance(key, str):
            raise TypeError("checksum field names must be strings")
        value = file_row.get(key)
        if isinstance(value, str) and value.strip():
            checksum_field = key
            checksum_value = value.strip()
            break

    identity = {
        "article_id": article_id,
        "title": title,
        "article_file_count": len(files),
        "selected_file_id": file_id,
        "selected_file_name": name,
        "selected_download_url": download_url,
        "selected_size": size,
        "selected_checksum_field": checksum_field,
        "selected_checksum_value": checksum_value,
    }
    result: dict[str, object] = {
        "schema": "eog.cassowary_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_metadata_ready",
        "metadata_only": True,
        "identity": identity,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_stop_result(
    contract: dict[str, object], reason: str
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.cassowary_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_metadata_identity_or_transport",
        "reason": str(reason),
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
    result["fingerprint"] = canonical_sha256(result)
    return result


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("source contract must be a JSON object")
    return value
