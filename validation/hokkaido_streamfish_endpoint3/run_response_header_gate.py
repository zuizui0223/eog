from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from validation.hokkaido_streamfish_endpoint3.response_header_gate import (
    ResponseHeaderStop,
    evaluate_header_line,
    load_contract,
    terminal_stop_result,
)


HERE = Path(__file__).resolve().parent
DEFAULT_AUTHORIZATION = HERE / "response_header_execution_authorization.json"
DEFAULT_OUTPUT = HERE / "response_header_certificate.json"
USER_AGENT = "EOG-Hokkaido-Streamfish-Endpoint3-ResponseHeader/1.0"


class HeaderTransportStop(RuntimeError):
    """Technical STOP before any response data-row byte is opened."""


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def _git_blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def _read_header_line(
    contract: dict[str, object],
    authorization: dict[str, object],
    *,
    opener=urllib.request.urlopen,
) -> tuple[bytes, dict[str, object]]:
    source = contract["source"]
    transport = contract["transport"]
    url = str(source["raw_url"])
    if authorization.get("authorized_url") != url:
        raise RuntimeError("response header authorization URL drift")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise RuntimeError("response header source is outside frozen raw GitHub host")

    start = int(transport["range_start"])
    end = int(transport["range_end"])
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "Range": f"bytes={start}-{end}",
        },
    )
    ledger: dict[str, object] = {
        "request_count": 1,
        "range": f"bytes={start}-{end}",
        "status": None,
        "content_range": None,
        "final_url": None,
        "body_bytes_returned_to_application": 0,
        "response_data_row_bytes_returned_to_application": 0,
    }
    try:
        context = opener(request, timeout=60)
    except (OSError, urllib.error.URLError) as exc:
        raise HeaderTransportStop(f"response header Range transport unavailable: {exc}") from exc

    with context as response:
        status = getattr(response, "status", None) or response.getcode()
        final_url = response.geturl()
        headers = {key.lower(): value for key, value in response.headers.items()}
        ledger.update(
            {
                "status": int(status),
                "content_range": headers.get("content-range"),
                "final_url": final_url,
            }
        )
        if status != int(transport["required_http_status"]):
            raise HeaderTransportStop(
                f"response header Range returned HTTP {status}; body was not opened"
            )
        if final_url != url:
            raise HeaderTransportStop("response header Range changed frozen raw URL identity")
        if headers.get("content-range") != transport["required_content_range"]:
            raise HeaderTransportStop(
                f"response header Content-Range drift: {headers.get('content-range')!r}"
            )
        if headers.get("content-encoding", "identity").casefold() != "identity":
            raise HeaderTransportStop("response header Range unexpectedly used content encoding")
        maximum = int(contract["header_rule"]["maximum_header_bytes_including_line_terminator"])
        line = response.readline(maximum + 1)
        ledger["body_bytes_returned_to_application"] = len(line)
        if b"\n" not in line:
            raise HeaderTransportStop(
                "first response line did not terminate within the frozen Range/header bound"
            )
        # readline stops at the first LF; no response data-row byte is returned to this application.
        ledger["response_data_row_bytes_returned_to_application"] = 0
    return line, ledger


def run(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    contract_path = HERE / "response_header_contract.json"
    evaluator_path = HERE / "response_header_gate.py"
    runner_path = Path(__file__).resolve()
    pass_path = HERE / "pre_response_pass_certificate.json"
    contract = load_contract(contract_path)
    authorization = _load_json(authorization_path)

    if authorization.get("attempt_id") != contract.get("attempt_id"):
        raise RuntimeError("response header authorization attempt_id drift")
    bindings = {
        pass_path: authorization.get("pre_response_pass_git_blob_sha"),
        contract_path: authorization.get("response_header_contract_git_blob_sha"),
        evaluator_path: authorization.get("response_header_evaluator_git_blob_sha"),
        runner_path: authorization.get("response_header_runner_git_blob_sha"),
    }
    for path, expected in bindings.items():
        if not isinstance(expected, str) or _git_blob_sha(path) != expected:
            raise RuntimeError(f"Git blob drift before response header access: {path}")
    pass_certificate = _load_json(pass_path)
    if pass_certificate.get("status") != "pre_response_geometry_ready":
        raise RuntimeError("pre-response PASS certificate is not ready")
    if (
        pass_certificate.get("authoritative_execution", {}).get("result_fingerprint")
        != contract.get("pre_response_result_fingerprint")
    ):
        raise RuntimeError("pre-response fingerprint drift before header access")
    if authorization.get("authorized_range_requests") != 1:
        raise RuntimeError("response header authorization must allow exactly one Range request")
    if authorization.get("response_data_row_bytes_allowed") != 0:
        raise RuntimeError("response data-row bytes must remain forbidden")

    ledger: dict[str, object] = {"request_count": 0, "body_bytes_returned_to_application": 0}
    try:
        header_line, ledger = _read_header_line(contract, authorization, opener=opener)
        result = evaluate_header_line(header_line, contract)
    except (HeaderTransportStop, ResponseHeaderStop) as exc:
        result = terminal_stop_result(contract, str(exc))

    result["transport_ledger"] = ledger
    result["authorized_range_requests"] = 1
    result["response_data_row_bytes_opened"] = 0
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
