from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from validation.sebms_ochlodes_endpoint3.gate0_gbif_registry import (
    RegistryGateStop,
    evaluate_gbif_registry,
    load_contract,
    terminal_stop_result,
)


HERE = Path(__file__).resolve().parent
DEFAULT_AUTHORIZATION = HERE / "gate0_execution_authorization.json"
DEFAULT_OUTPUT = HERE / "gate0_live_registry_certificate.json"
USER_AGENT = "EOG-SeBMS-Ochlodes-Endpoint3-Gate0/1.0"


class LiveRegistryStop(RuntimeError):
    """Technical/identity STOP before any DwC-A or biological response access."""


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def _git_blob_sha(path: Path) -> str:
    result = subprocess.run(
        ["git", "hash-object", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _read_registry_metadata(
    authorization: dict[str, object],
    *,
    opener=urllib.request.urlopen,
) -> tuple[dict[str, object], dict[str, object]]:
    url = authorization["authorized_url"]
    host = authorization["allowed_final_host"]
    max_bytes = authorization["maximum_metadata_bytes"]
    if not isinstance(url, str) or not isinstance(host, str):
        raise TypeError("authorized URL/host must be strings")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise TypeError("maximum_metadata_bytes must be a positive int")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise LiveRegistryStop("authorized GBIF Registry URL/host drift")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    ledger: dict[str, object] = {
        "request_count": 1,
        "status": None,
        "final_url": None,
        "final_host": None,
        "content_type": None,
        "metadata_bytes_opened": 0,
    }
    try:
        response_context = opener(request, timeout=60)
    except (OSError, urllib.error.URLError) as exc:
        raise LiveRegistryStop(f"GBIF Registry metadata transport unavailable: {exc}") from exc

    with response_context as response:
        status = getattr(response, "status", None) or response.getcode()
        final_url = response.geturl()
        final = urlparse(final_url)
        headers = {key.lower(): value for key, value in response.headers.items()}
        ledger.update(
            {
                "status": status,
                "final_url": final_url,
                "final_host": final.hostname,
                "content_type": headers.get("content-type"),
            }
        )
        if status != 200:
            raise LiveRegistryStop(
                f"GBIF Registry metadata GET returned HTTP {status}; body was not opened"
            )
        if final.scheme != "https" or final.hostname != host:
            raise LiveRegistryStop(
                f"GBIF Registry request left frozen host: {final.hostname!r}"
            )
        if headers.get("content-encoding", "identity").casefold() != "identity":
            raise LiveRegistryStop("GBIF Registry response unexpectedly used content encoding")
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type not in {"application/json", "application/ld+json"}:
            raise LiveRegistryStop(
                f"GBIF Registry response has unexpected content type {content_type!r}; body was not opened"
            )
        body = response.read(max_bytes + 1)
        ledger["metadata_bytes_opened"] = len(body)

    if len(body) > max_bytes:
        raise LiveRegistryStop("GBIF Registry JSON exceeds frozen byte ceiling")
    try:
        metadata = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveRegistryStop(f"GBIF Registry response is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(metadata, dict):
        raise LiveRegistryStop("GBIF Registry metadata root is not a JSON object")
    return metadata, ledger


def run(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    contract_path = HERE / "source_contract.json"
    evaluator_path = HERE / "gate0_gbif_registry.py"
    contract = load_contract(contract_path)
    authorization = _load_json(authorization_path)

    if authorization.get("attempt_id") != contract.get("attempt_id"):
        raise RuntimeError("authorization attempt_id does not match frozen contract")
    if authorization.get("authorized_url") != contract["source"]["registry_api_url"]:
        raise RuntimeError("authorization URL does not match frozen source contract")
    expected_contract_blob = authorization.get("source_contract_git_blob_sha")
    expected_evaluator_blob = authorization.get("registry_evaluator_git_blob_sha")
    if not isinstance(expected_contract_blob, str) or _git_blob_sha(contract_path) != expected_contract_blob:
        raise RuntimeError("source contract blob drift; stop before external metadata access")
    if not isinstance(expected_evaluator_blob, str) or _git_blob_sha(evaluator_path) != expected_evaluator_blob:
        raise RuntimeError("registry evaluator blob drift; stop before external metadata access")

    ledger: dict[str, object] = {"request_count": 0, "metadata_bytes_opened": 0}
    try:
        metadata, ledger = _read_registry_metadata(authorization, opener=opener)
        result = evaluate_gbif_registry(metadata, contract)
    except (LiveRegistryStop, RegistryGateStop) as exc:
        result = terminal_stop_result(contract, str(exc))

    result["live_registry_transport"] = ledger
    result["authorization_sha256"] = hashlib.sha256(authorization_path.read_bytes()).hexdigest()
    result["source_contract_git_blob_sha"] = expected_contract_blob
    result["registry_evaluator_git_blob_sha"] = expected_evaluator_blob
    result["dwca_payload_requests"] = 0
    result["dwca_payload_bytes_opened"] = 0
    result["event_rows_opened"] = 0
    result["emof_rows_opened"] = 0
    result["occurrence_header_bytes_opened"] = 0
    result["occurrence_rows_opened"] = 0
    result["response_values_opened"] = False
    result["model_fits"] = 0
    result["heldout_scores"] = 0
    result["counts_as_predictive_evidence"] = False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    run()
