from __future__ import annotations

import json
from pathlib import Path
import urllib.error
import urllib.request

from gate0_figshare_metadata import (
    MetadataGateStop,
    evaluate_figshare_metadata,
    load_contract,
    terminal_stop_result,
)

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = HERE / "gate0_execution_authorization.json"
OUTPUT = ROOT / "build" / "cassowary_endpoint3" / "gate0_metadata.json"
USER_AGENT = "EOG-Cassowary-Gate0/1.0"
SOURCE_BOUNDARY = "e783a89b0dcdf8c68161ec8dc45073d22b816d80"


def run() -> dict[str, object]:
    contract = load_contract()
    auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    if auth["attempt_id"] != contract["attempt_id"]:
        raise RuntimeError("authorization attempt does not match source contract")
    if auth["source_boundary_merge"] != SOURCE_BOUNDARY:
        raise RuntimeError("source-boundary merge authorization drift")
    if auth["allowed_url"] != contract["source"]["article_api_url"]:
        raise RuntimeError("authorized URL differs from frozen source URL")
    if auth["allowed_live_request_count"] != 1:
        raise RuntimeError("metadata Gate0 requires exactly one authorized request")
    if auth["file_payload_requests_allowed"] != 0:
        raise RuntimeError("file payload access must remain forbidden")
    if auth["response_rows_allowed"] != 0 or auth["model_fits_allowed"] != 0:
        raise RuntimeError("response/model access must remain forbidden")

    request = urllib.request.Request(
        auth["allowed_url"],
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
    )
    metadata_bytes = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = getattr(response, "status", None) or response.getcode()
            if status != 200:
                raise MetadataGateStop(f"Figshare metadata returned HTTP {status}")
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.casefold():
                raise MetadataGateStop(
                    f"Figshare metadata Content-Type is not JSON: {content_type!r}"
                )
            body = response.read(2_000_001)
            metadata_bytes = len(body)
            if metadata_bytes > 2_000_000:
                raise MetadataGateStop("Figshare metadata exceeds frozen 2 MB bound")
        metadata = json.loads(body.decode("utf-8"))
        result = evaluate_figshare_metadata(metadata, contract)
    except (MetadataGateStop, OSError, urllib.error.URLError, UnicodeError, json.JSONDecodeError) as exc:
        result = terminal_stop_result(contract, str(exc))

    result["metadata_request_count"] = 1
    result["metadata_bytes_opened"] = metadata_bytes

    for key in (
        "file_payload_requests",
        "file_payload_bytes_opened",
        "response_header_bytes_opened",
        "response_rows_opened",
        "model_fits",
        "heldout_scores",
    ):
        if result[key] != 0:
            raise RuntimeError(f"Gate0 firewall violation: {key}={result[key]}")
    if result["response_values_opened"] is not False:
        raise RuntimeError("Gate0 firewall violation: response value opened")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
