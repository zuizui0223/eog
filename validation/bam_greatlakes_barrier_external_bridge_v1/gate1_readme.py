"""README-only Gate1 for the Great Lakes low-head-dam A/M bridge.

Only README.md may be downloaded.  RDS data payload access remains forbidden.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
GATE0 = HERE / "gate0_dryad_identity_certificate.json"
AUTH = HERE / "gate1_execution_authorization.json"
OUTPUT = HERE / "gate1_readme_certificate.json"
BASE = "https://datadryad.org"
USER_AGENT = "EOG-GreatLakes-AM-Bridge-Gate1/1.0"


class Gate1Stop(RuntimeError):
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


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    gate0 = json.loads(GATE0.read_text(encoding="utf-8"))
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    if gate0.get("status") != "dryad_source_identity_ready":
        raise Gate1Stop("Gate0 certificate is not PASS")
    if auth.get("status") != "authorized":
        raise Gate1Stop("Gate1 is not authorized")
    if auth.get("gate0_fingerprint") != gate0.get("fingerprint"):
        raise Gate1Stop("Gate0 fingerprint mismatch")
    allowed = auth.get("allowed_payload")
    if allowed != {"README.md": "full text only"}:
        raise Gate1Stop("Gate1 allowed payload drift")
    return gate0, auth


def readme_file_metadata(gate0: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row for row in gate0["files"]
        if row.get("path") == "README.md"
    ]
    if len(rows) != 1:
        raise Gate1Stop(f"expected one README metadata row, got {len(rows)}")
    row = rows[0]
    if not row.get("required_for_bridge"):
        raise Gate1Stop("README is not marked required_for_bridge")
    return row


def fetch_exact_readme(meta: dict[str, Any]) -> bytes:
    path = str(meta["download_api_path"])
    if path != "/api/v2/files/4883247/download":
        raise Gate1Stop(f"README download path drift: {path!r}")
    request = Request(
        BASE + path,
        headers={
            "Accept": "text/plain,text/markdown,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    with urlopen(request, timeout=60) as response:
        if int(response.status) != 200:
            raise Gate1Stop(f"README download returned HTTP {response.status}")
        body = response.read(int(meta["size_bytes"]) + 1)
    if len(body) != int(meta["size_bytes"]):
        raise Gate1Stop(
            f"README size drift: expected {meta['size_bytes']}, got {len(body)}"
        )
    sha = hashlib.sha256(body).hexdigest()
    if sha != str(meta["sha256"]):
        raise Gate1Stop(
            f"README sha256 drift: expected {meta['sha256']}, got {sha}"
        )
    return body


def decode_readme(body: bytes) -> str:
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Gate1Stop("README is not UTF-8") from exc


def _normalize(text: str) -> str:
    # Preserve period and underscore tokens while normalizing markdown punctuation.
    return re.sub(r"\s+", " ", text).strip()


def evaluate_readme_text(
    text: str,
    gate0: dict[str, Any],
    auth: dict[str, Any],
) -> dict[str, Any]:
    normalized = _normalize(text)
    lower = normalized.lower()
    expectations = auth["readme_expectations"]

    missing_files = [
        token for token in expectations["required_file_names"]
        if token.lower() not in lower
    ]
    missing_habitat = [
        token for token in expectations["required_habitat_columns"]
        if token.lower() not in lower
    ]
    missing_catch = [
        token for token in expectations["required_catch_columns"]
        if token.lower() not in lower
    ]
    missing_periods = [
        token for token in expectations["required_period_tokens"]
        if token.lower() not in lower
    ]

    if missing_files:
        raise Gate1Stop(
            f"README missing required file-name documentation: {missing_files}"
        )
    if missing_habitat:
        raise Gate1Stop(
            f"README missing required habitat schema tokens: {missing_habitat}"
        )
    if missing_catch:
        raise Gate1Stop(
            f"README missing required catch schema tokens: {missing_catch}"
        )
    if missing_periods:
        raise Gate1Stop(
            f"README missing required period tokens: {missing_periods}"
        )

    meta = readme_file_metadata(gate0)
    result: dict[str, Any] = {
        "schema": "eog.bam_greatlakes_barrier_external_bridge.gate1.v1",
        "status": "readme_schema_ready",
        "gate0_fingerprint": gate0["fingerprint"],
        "readme_size_bytes": int(meta["size_bytes"]),
        "readme_sha256": str(meta["sha256"]),
        "required_file_names_confirmed": list(
            expectations["required_file_names"]
        ),
        "required_habitat_columns_confirmed": list(
            expectations["required_habitat_columns"]
        ),
        "required_catch_columns_confirmed": list(
            expectations["required_catch_columns"]
        ),
        "required_period_tokens_confirmed": list(
            expectations["required_period_tokens"]
        ),
        "readme_payload_requests": 1,
        "readme_payload_bytes_opened": int(meta["size_bytes"]),
        "rds_payload_requests": 0,
        "rds_payload_bytes_opened": 0,
        "ecological_response_values_opened": False,
        "model_fits": 0,
        "next_authorized_stage": (
            "freeze exact RDS parser, file bindings, output schema and once-only "
            "execution contract before any RDS payload access"
        ),
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def stop_certificate(reason: str, gate0_fingerprint: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "eog.bam_greatlakes_barrier_external_bridge.gate1.v1",
        "status": "stop_gate1_readme_or_transport",
        "reason": reason,
        "gate0_fingerprint": gate0_fingerprint,
        "rds_payload_requests": 0,
        "rds_payload_bytes_opened": 0,
        "ecological_response_values_opened": False,
        "model_fits": 0,
        "retry_or_parser_repair_allowed": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def main() -> int:
    gate0_fingerprint = None
    try:
        gate0, auth = load_inputs()
        gate0_fingerprint = str(gate0["fingerprint"])
        meta = readme_file_metadata(gate0)
        body = fetch_exact_readme(meta)
        result = evaluate_readme_text(
            decode_readme(body),
            gate0,
            auth,
        )
    except Exception as exc:
        result = stop_certificate(str(exc), gate0_fingerprint)

    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
