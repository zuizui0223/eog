from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"


class RegistryGateStop(RuntimeError):
    """Terminal response-blind GBIF Registry metadata identity/interface STOP."""


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


def _required_str(mapping: Mapping[str, object], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegistryGateStop(f"{label} lacks non-empty string {key}")
    return value.strip()


def evaluate_gbif_registry(
    metadata: object,
    contract: dict[str, object],
) -> dict[str, object]:
    """Evaluate only one GBIF Registry dataset JSON object; never opens DwC-A data."""
    if not isinstance(metadata, dict):
        raise RegistryGateStop("GBIF Registry dataset metadata must be a JSON object")
    if not isinstance(contract, dict):
        raise TypeError("contract must be dict")

    source = contract.get("source")
    gate = contract.get("gate0_registry_metadata_only")
    if not isinstance(source, dict) or not isinstance(gate, dict):
        raise TypeError("contract source/gate0_registry_metadata_only must be objects")

    dataset_key = _required_str(metadata, "key", "GBIF Registry dataset metadata")
    if dataset_key != source["dataset_key"]:
        raise RegistryGateStop(
            f"GBIF dataset key drift: {dataset_key!r} != {source['dataset_key']!r}"
        )

    title = _required_str(metadata, "title", "GBIF Registry dataset metadata")
    if title != source["expected_title"]:
        raise RegistryGateStop(
            f"GBIF dataset title drift: {title!r} != {source['expected_title']!r}"
        )

    dataset_type = _required_str(metadata, "type", "GBIF Registry dataset metadata")
    if dataset_type != source["dataset_type"]:
        raise RegistryGateStop(
            f"GBIF dataset type drift: {dataset_type!r} != {source['dataset_type']!r}"
        )

    doi = _required_str(metadata, "doi", "GBIF Registry dataset metadata")
    if doi != source["doi"]:
        raise RegistryGateStop(f"GBIF dataset DOI drift: {doi!r} != {source['doi']!r}")

    endpoints = metadata.get("endpoints")
    if not isinstance(endpoints, list):
        raise RegistryGateStop("GBIF Registry dataset metadata lacks endpoints list")

    required_type = gate["required_endpoint_type"]
    required_url = gate["required_registered_endpoint_url"]
    matches: list[dict[str, str]] = []
    for row in endpoints:
        if not isinstance(row, dict):
            continue
        endpoint_type = row.get("type")
        endpoint_url = row.get("url")
        if endpoint_type == required_type and endpoint_url == required_url:
            parsed = urlparse(endpoint_url)
            if parsed.scheme != "https" or parsed.hostname != "www.gbif.se":
                raise RegistryGateStop("matching DWC_ARCHIVE endpoint is not frozen HTTPS GBIF-Sweden host")
            matches.append({"type": endpoint_type, "url": endpoint_url})

    if len(matches) != 1:
        raise RegistryGateStop(
            f"frozen DWC_ARCHIVE endpoint occurs {len(matches)} times; expected exactly one"
        )

    provenance = {
        key: metadata.get(key)
        for key in ("pubDate", "modified", "created", "installationKey", "publishingOrganizationKey")
        if metadata.get(key) is not None
    }
    result: dict[str, object] = {
        "schema": "eog.sebms_ochlodes_endpoint3.gate0_registry.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_metadata_ready",
        "metadata_only": True,
        "identity": {
            "dataset_key": dataset_key,
            "title": title,
            "type": dataset_type,
            "doi": doi,
            "registered_dwca_endpoint": matches[0]["url"],
            "frozen_version_dwca_url": source["frozen_version_dwca_url"],
        },
        "registry_provenance": provenance,
        "dwca_payload_requests": 0,
        "dwca_payload_bytes_opened": 0,
        "event_rows_opened": 0,
        "emof_rows_opened": 0,
        "occurrence_header_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_stop_result(contract: dict[str, object], reason: str) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.sebms_ochlodes_endpoint3.gate0_registry.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_metadata_identity_or_transport",
        "reason": str(reason),
        "metadata_only": True,
        "dwca_payload_requests": 0,
        "dwca_payload_bytes_opened": 0,
        "event_rows_opened": 0,
        "emof_rows_opened": 0,
        "occurrence_header_bytes_opened": 0,
        "occurrence_rows_opened": 0,
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
