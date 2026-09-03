from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from validation.cassowary_endpoint3.gate0_figshare_metadata import (
    MetadataGateStop,
    evaluate_figshare_metadata,
    load_contract,
    terminal_stop_result,
)

HERE = Path(__file__).resolve().parent
DEFAULT_AUTHORIZATION = HERE / "gate0_execution_authorization.json"
DEFAULT_OUTPUT = HERE / "gate0_live_metadata_certificate.json"
USER_AGENT = "EOG-Cassowary-Endpoint3-Gate0/1.0"


class LiveMetadataStop(RuntimeError):
    """Technical or identity stop before any Figshare file payload request."""


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def _read_article_metadata(
    authorization: dict[str, object],
    *,
    opener=urllib.request.urlopen,
) -> tuple[dict[str, object], dict[str, object]]:
    url = authorization["authorized_url"]
    if not isinstance(url, str):
        raise TypeError("authorized_url must be str")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != authorization["allowed_final_host"]:
        raise LiveMetadataStop("authorized metadata URL/host drift")

    max_bytes = authorization["maximum_metadata_bytes"]
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise TypeError("maximum_metadata_bytes must be a positive int")

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
        raise LiveMetadataStop(f"Figshare metadata transport unavailable: {exc}") from exc

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
            raise LiveMetadataStop(
                f"Figshare metadata GET returned HTTP {status}; response body was not opened"
            )
        if final.scheme != "https" or final.hostname != authorization["allowed_final_host"]:
            raise LiveMetadataStop(f"Figshare metadata request left frozen host: {final.hostname!r}")
        if headers.get("content-encoding", "identity").casefold() != "identity":
            raise LiveMetadataStop("Figshare metadata response unexpectedly used content encoding")
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type not in {"application/json", "application/ld+json"}:
            raise LiveMetadataStop(
                f"Figshare metadata response has unexpected content type {content_type!r}; body was not opened"
            )
        body = response.read(max_bytes + 1)
        ledger["metadata_bytes_opened"] = len(body)

    if len(body) > max_bytes:
        raise LiveMetadataStop("Figshare metadata JSON exceeds frozen byte ceiling")
    try:
        metadata = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveMetadataStop(f"Figshare metadata is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(metadata, dict):
        raise LiveMetadataStop("Figshare metadata root is not a JSON object")
    return metadata, ledger


def run(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    contract = load_contract()
    authorization = _load_json(authorization_path)
    if authorization.get("attempt_id") != contract.get("attempt_id"):
        raise RuntimeError("authorization attempt_id does not match frozen contract")
    if authorization.get("frozen_gate0_boundary_merge") != "e783a89b0dcdf8c68161ec8dc45073d22b816d80":
        raise RuntimeError("authorization is not bound to the merged Gate0 boundary")
    if authorization.get("authorized_url") != contract["source"]["article_api_url"]:
        raise RuntimeError("authorization URL does not match frozen source contract")

    ledger: dict[str, object] = {
        "request_count": 0,
        "metadata_bytes_opened": 0,
    }
    try:
        metadata, ledger = _read_article_metadata(authorization, opener=opener)
        result = evaluate_figshare_metadata(metadata, contract)
    except (LiveMetadataStop, MetadataGateStop) as exc:
        result = terminal_stop_result(contract, str(exc))

    result["live_metadata_transport"] = ledger
    result["authorization_sha256"] = hashlib.sha256(
        authorization_path.read_bytes()
    ).hexdigest()
    result["source_contract_sha256"] = hashlib.sha256(
        (HERE / "source_contract.json").read_bytes()
    ).hexdigest()
    result["file_payload_requests"] = 0
    result["file_payload_bytes_opened"] = 0
    result["response_header_bytes_opened"] = 0
    result["response_rows_opened"] = 0
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
