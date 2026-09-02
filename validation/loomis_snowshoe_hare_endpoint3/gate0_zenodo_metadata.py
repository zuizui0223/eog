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


def _first_https_link(links: object, label: str) -> tuple[str, str]:
    if not isinstance(links, dict):
        raise MetadataGateStop(f"{label} lacks links object")
    for key in sorted(links):
        value = links[key]
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        parsed = urlparse(value)
        if parsed.scheme == "https" and parsed.hostname:
            return key, value
    raise MetadataGateStop(f"{label} has no absolute HTTPS link")


def evaluate_zenodo_metadata(
    metadata: object,
    contract: dict[str, object],
) -> dict[str, object]:
    """Evaluate only Zenodo record metadata; never touches file payloads."""
    if not isinstance(metadata, dict):
        raise MetadataGateStop("Zenodo record metadata must be a JSON object")
    if not isinstance(contract, dict):
        raise TypeError("contract must be dict")

    source = contract.get("source")
    if not isinstance(source, dict):
        raise TypeError("contract source must be object")

    record_id = _required_int(metadata, "id", "Zenodo record metadata")
    if record_id != source["record_id"]:
        raise MetadataGateStop(
            f"Zenodo record id drift: {record_id} != {source['record_id']}"
        )

    files = metadata.get("files")
    if not isinstance(files, list):
        raise MetadataGateStop("Zenodo record metadata lacks files list")

    observed: dict[str, dict[str, object]] = {}
    for index, row in enumerate(files):
        if not isinstance(row, dict):
            raise MetadataGateStop(f"Zenodo file entry {index} must be an object")
        key = _required_str(row, "key", f"Zenodo file entry {index}")
        if key in observed:
            raise MetadataGateStop(f"duplicate Zenodo file key: {key!r}")
        checksum = _required_str(row, "checksum", f"Zenodo file {key}")
        size = _required_int(row, "size", f"Zenodo file {key}")
        if size <= 0:
            raise MetadataGateStop(f"Zenodo file {key} size must be positive")
        link_name, link_url = _first_https_link(row.get("links"), f"Zenodo file {key}")
        observed[key] = {
            "key": key,
            "checksum": checksum,
            "size": size,
            "https_link_name": link_name,
            "https_link": link_url,
        }

    required = source.get("required_files")
    if not isinstance(required, dict) or not required:
        raise TypeError("contract required_files must be a non-empty object")

    identities: list[dict[str, object]] = []
    for name in sorted(required):
        expected_checksum = required[name]
        if not isinstance(name, str) or not isinstance(expected_checksum, str):
            raise TypeError("required file names/checksums must be strings")
        row = observed.get(name)
        if row is None:
            raise MetadataGateStop(f"required Zenodo file missing: {name}")
        if row["checksum"] != expected_checksum:
            raise MetadataGateStop(
                f"required Zenodo checksum drift for {name}: "
                f"{row['checksum']!r} != {expected_checksum!r}"
            )
        identities.append(row)

    result: dict[str, object] = {
        "schema": "eog.loomis_snowshoe_hare_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_metadata_ready",
        "metadata_only": True,
        "record_id": record_id,
        "record_file_count": len(files),
        "required_file_count": len(required),
        "required_file_identities": identities,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "deployment_header_bytes_opened": 0,
        "deployment_rows_opened": 0,
        "detection_header_bytes_opened": 0,
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
        "schema": "eog.loomis_snowshoe_hare_endpoint3.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_metadata_identity_or_transport",
        "reason": str(reason),
        "metadata_only": True,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "deployment_header_bytes_opened": 0,
        "deployment_rows_opened": 0,
        "detection_header_bytes_opened": 0,
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
