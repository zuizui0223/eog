from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from validation.hokkaido_streamfish_endpoint3.pre_response_geometry import (
    PreResponseStop,
    evaluate_pre_response,
    load_contract,
    terminal_stop_result,
)


HERE = Path(__file__).resolve().parent
DEFAULT_AUTHORIZATION = HERE / "pre_response_execution_authorization.json"
DEFAULT_OUTPUT = HERE / "pre_response_geometry_certificate.json"
USER_AGENT = "EOG-Hokkaido-Streamfish-Endpoint3-PreResponse/1.0"


class LiveSourceStop(RuntimeError):
    """Technical STOP before response-bearing source access."""


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


def _read_exact_source(
    label: str,
    spec: dict[str, object],
    authorization: dict[str, object],
    *,
    opener=urllib.request.urlopen,
) -> tuple[bytes, dict[str, object]]:
    url = str(spec["raw_url"])
    expected_size = int(spec["size_bytes"])
    allowed = authorization["allowed_live_sources"]
    if not isinstance(allowed, dict) or allowed.get(label) != url:
        raise RuntimeError(f"authorization/source URL drift for {label}")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise RuntimeError(f"{label} is outside frozen raw GitHub host")
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,application/octet-stream;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
        },
    )
    ledger: dict[str, object] = {
        "label": label,
        "request_count": 1,
        "status": None,
        "final_url": None,
        "final_host": None,
        "bytes_opened": 0,
    }
    try:
        context = opener(request, timeout=60)
    except (OSError, urllib.error.URLError) as exc:
        raise LiveSourceStop(f"{label} transport unavailable: {exc}") from exc
    with context as response:
        status = getattr(response, "status", None) or response.getcode()
        final_url = response.geturl()
        final = urlparse(final_url)
        headers = {key.lower(): value for key, value in response.headers.items()}
        ledger.update(
            {
                "status": int(status),
                "final_url": final_url,
                "final_host": final.hostname,
            }
        )
        if status != 200:
            raise LiveSourceStop(f"{label} GET returned HTTP {status}; body was not opened")
        if final_url != url or final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
            raise LiveSourceStop(f"{label} request changed frozen raw URL identity")
        if headers.get("content-encoding", "identity").casefold() != "identity":
            raise LiveSourceStop(f"{label} response unexpectedly used content encoding")
        body = response.read(expected_size + 1)
        ledger["bytes_opened"] = len(body)
    if len(body) != expected_size:
        raise LiveSourceStop(
            f"{label} byte-size drift: opened {len(body)}, expected {expected_size}"
        )
    return body, ledger


def run(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    contract_path = HERE / "source_contract.json"
    evaluator_path = HERE / "pre_response_geometry.py"
    runner_path = Path(__file__).resolve()
    contract = load_contract(contract_path)
    authorization = _load_json(authorization_path)
    if authorization.get("attempt_id") != contract.get("attempt_id"):
        raise RuntimeError("pre-response authorization attempt_id drift")
    bindings = {
        contract_path: authorization.get("source_contract_git_blob_sha"),
        evaluator_path: authorization.get("geometry_evaluator_git_blob_sha"),
        runner_path: authorization.get("live_runner_git_blob_sha"),
    }
    for path, expected in bindings.items():
        if not isinstance(expected, str) or _git_blob_sha(path) != expected:
            raise RuntimeError(f"Git blob drift before external source access: {path}")
    if int(authorization.get("authorized_external_gets", -1)) != 2:
        raise RuntimeError("pre-response authorization must allow exactly two GETs")
    if int(authorization.get("response_table_requests_allowed", -1)) != 0:
        raise RuntimeError("response table must remain forbidden")

    ledgers: list[dict[str, object]] = []
    coordinate_bytes = b""
    code_bytes = b""
    try:
        coordinate_bytes, ledger = _read_exact_source(
            "coordinate_registry",
            contract["source"]["coordinate_registry"],
            authorization,
            opener=opener,
        )
        ledgers.append(ledger)
        code_bytes, ledger = _read_exact_source(
            "formatting_code",
            contract["source"]["formatting_code"],
            authorization,
            opener=opener,
        )
        ledgers.append(ledger)
        result = evaluate_pre_response(coordinate_bytes, code_bytes, contract)
    except (LiveSourceStop, PreResponseStop) as exc:
        result = terminal_stop_result(contract, str(exc))

    result["source_transport_ledger"] = ledgers
    result["authorized_external_gets"] = 2
    result["completed_external_gets"] = len(ledgers)
    result["nonresponse_source_bytes_opened"] = sum(
        int(row.get("bytes_opened", 0)) for row in ledgers
    )
    result["response_table_requests"] = 0
    result["response_table_bytes_opened"] = 0
    result["response_rows_opened"] = 0
    result["response_values_opened"] = False
    result["model_fits"] = 0
    result["heldout_scores"] = 0
    result["counts_as_predictive_evidence"] = False
    result["authorization_sha256"] = hashlib.sha256(authorization_path.read_bytes()).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    run()
