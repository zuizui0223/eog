from __future__ import annotations

import json
from pathlib import Path

from gate1_zip_metadata import (
    FrozenRangeTransport,
    Gate1Stop,
    evaluate_zip_metadata,
    load_contract,
    terminal_stop_result,
)

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = HERE / "gate1_execution_authorization.json"
OUTPUT = ROOT / "build" / "soutpansberg_leopard_endpoint3" / "gate1_zip_metadata.json"


def run() -> dict[str, object]:
    contract = load_contract()
    auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    identity = contract["gate0_identity"]

    if auth["attempt_id"] != contract["attempt_id"]:
        raise RuntimeError("Gate1 authorization attempt mismatch")
    if auth["gate1_contract_merge"] != "ff7e67713f53065549fb691ff440b8df4275a4fc":
        raise RuntimeError("Gate1 contract merge authorization drift")
    if auth["authorized_url"] != identity["download_url"]:
        raise RuntimeError("Gate1 authorized URL differs from frozen Gate0 identity")
    if auth["authorized_size_bytes"] != identity["size_bytes"]:
        raise RuntimeError("Gate1 authorized size differs from frozen Gate0 identity")
    if auth["full_get_allowed"] is not False:
        raise RuntimeError("full GET must remain forbidden")

    transport = FrozenRangeTransport(
        str(identity["download_url"]), int(identity["size_bytes"])
    )
    try:
        result = evaluate_zip_metadata(contract, transport.read, transport.ledger)
    except Gate1Stop as exc:
        result = terminal_stop_result(contract, str(exc), transport.ledger)

    for key in (
        "member_payload_bytes_opened",
        "deployment_payload_bytes_opened",
        "capture_header_bytes_opened",
        "capture_payload_bytes_opened",
        "response_rows_opened",
        "model_fits",
        "heldout_scores",
    ):
        if result[key] != 0:
            raise RuntimeError(f"Gate1 payload/response firewall violation: {key}={result[key]}")
    if result["response_values_opened"] is not False:
        raise RuntimeError("Gate1 response-value firewall violation")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
