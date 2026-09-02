from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlparse

from validation.loomis_snowshoe_hare_endpoint3.gate0_zenodo_metadata import (
    MetadataGateStop,
    evaluate_zenodo_metadata,
    load_contract,
    terminal_stop_result,
)

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = HERE / "gate0_execution_authorization.json"
CONTRACT_PATH = HERE / "source_contract.json"
OUTPUT = ROOT / "build" / "loomis_snowshoe_hare_endpoint3" / "gate0_metadata.json"
USER_AGENT = "EOG-Loomis-Snowshoe-Hare-Gate0/1.0"
MAX_METADATA_BYTES = 5_000_000


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _load_auth() -> dict[str, object]:
    value = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("authorization must be a JSON object")
    return value


def _verify_authorization(auth: dict[str, object]) -> None:
    if auth.get("attempt_id") != "loomis_snowshoe_hare_endpoint3_v1":
        raise RuntimeError("authorization attempt_id drift")
    if auth.get("source_contract_git_blob_sha1") != _git_blob_sha1(CONTRACT_PATH):
        raise RuntimeError("source contract Git blob SHA-1 drift")
    branch = os.environ.get("GITHUB_REF_NAME")
    if branch is not None and branch != auth.get("authorized_branch"):
        raise RuntimeError(f"unauthorized branch: {branch!r}")
    run_number = os.environ.get("GITHUB_RUN_NUMBER")
    if run_number is not None and int(run_number) != auth.get("authorized_workflow_run_number"):
        raise RuntimeError(f"unauthorized workflow run number: {run_number}")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
    if run_attempt is not None and int(run_attempt) != auth.get("authorized_workflow_run_attempt"):
        raise RuntimeError(f"unauthorized workflow run attempt: {run_attempt}")
    for key in (
        "file_payload_requests_authorized",
        "deployment_header_bytes_authorized",
        "deployment_rows_authorized",
        "detection_header_bytes_authorized",
        "response_rows_authorized",
        "model_fits_authorized",
        "heldout_scores_authorized",
    ):
        if auth.get(key) != 0:
            raise RuntimeError(f"authorization unexpectedly permits {key}")
    if auth.get("response_values_authorized") is not False:
        raise RuntimeError("authorization unexpectedly permits response values")


def _get_record_metadata(url: str) -> tuple[object, dict[str, object]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "zenodo.org":
        raise MetadataGateStop("Zenodo metadata URL must be HTTPS on zenodo.org")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
    )
    try:
        response_context = urllib.request.urlopen(request, timeout=90)
    except (OSError, urllib.error.URLError) as exc:
        raise MetadataGateStop(f"Zenodo metadata transport unavailable: {exc}") from exc

    with response_context as response:
        status = getattr(response, "status", None) or response.getcode()
        final = urlparse(response.geturl())
        content_type = response.headers.get("Content-Type", "")
        if status != 200:
            raise MetadataGateStop(
                f"Zenodo metadata returned HTTP {status}; response body was not opened"
            )
        if final.scheme != "https" or final.hostname != "zenodo.org":
            raise MetadataGateStop(
                f"Zenodo metadata request left frozen host: {final.hostname!r}"
            )
        if "json" not in content_type.casefold():
            raise MetadataGateStop(
                f"Zenodo metadata content type is not JSON: {content_type!r}"
            )
        body = response.read(MAX_METADATA_BYTES + 1)
        if len(body) > MAX_METADATA_BYTES:
            raise MetadataGateStop("Zenodo metadata exceeds frozen byte cap")

    try:
        metadata = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetadataGateStop(f"Zenodo metadata is not valid UTF-8 JSON: {exc}") from exc

    transport = {
        "metadata_requests": 1,
        "metadata_bytes_opened": len(body),
        "http_status": 200,
        "final_url": final.geturl(),
        "content_type": content_type,
    }
    return metadata, transport


def run(output_path: Path = OUTPUT) -> dict[str, object]:
    auth = _load_auth()
    contract = load_contract(CONTRACT_PATH)
    transport: dict[str, object] = {
        "metadata_requests": 0,
        "metadata_bytes_opened": 0,
    }
    try:
        _verify_authorization(auth)
        metadata, transport = _get_record_metadata(str(contract["source"]["record_api_url"]))
        result = evaluate_zenodo_metadata(metadata, contract)
        result["transport"] = transport
        result["source_boundary_merge"] = auth["source_boundary_merge"]
        result["authorization_git_blob_sha1"] = _git_blob_sha1(AUTH_PATH)
    except (MetadataGateStop, RuntimeError, ValueError, TypeError) as exc:
        result = terminal_stop_result(contract, str(exc))
        result["transport"] = transport
        result["source_boundary_merge"] = auth.get("source_boundary_merge")
        result["authorization_git_blob_sha1"] = _git_blob_sha1(AUTH_PATH)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
