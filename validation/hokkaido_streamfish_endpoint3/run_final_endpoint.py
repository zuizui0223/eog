from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from validation.hokkaido_streamfish_endpoint3.final_endpoint import (
    FinalEndpointTerminal,
    evaluate_final_endpoint,
    git_blob_sha1,
    load_contracts,
    terminal_result,
)


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_AUTHORIZATION = HERE / "final_endpoint_execution_authorization.json"
DEFAULT_OUTPUT = HERE / "final_endpoint_certificate.json"
USER_AGENT = "EOG-Hokkaido-Streamfish-Endpoint3-Final/1.0"


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def _git_blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def _read_exact_raw(
    *,
    url: str,
    expected_size: int,
    expected_git_blob_sha1: str,
    role: str,
    opener=urllib.request.urlopen,
) -> tuple[bytes, dict[str, object]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{role} URL left frozen raw GitHub host",
        )
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
        },
    )
    ledger: dict[str, object] = {
        "role": role,
        "request_count": 1,
        "status": None,
        "final_url": None,
        "content_type": None,
        "bytes_opened": 0,
        "git_blob_sha1": None,
    }
    try:
        context = opener(request, timeout=120)
    except (OSError, urllib.error.URLError) as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{role} transport unavailable: {exc}",
        ) from exc
    with context as response:
        status = getattr(response, "status", None) or response.getcode()
        final_url = response.geturl()
        headers = {key.lower(): value for key, value in response.headers.items()}
        ledger.update(
            {
                "status": int(status),
                "final_url": final_url,
                "content_type": headers.get("content-type"),
            }
        )
        if status != 200:
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                f"{role} GET returned HTTP {status}; body was not opened",
            )
        if final_url != url:
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                f"{role} GET changed frozen raw URL identity",
            )
        if headers.get("content-encoding", "identity").casefold() != "identity":
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                f"{role} response unexpectedly used content encoding",
            )
        body = response.read(expected_size + 1)
        ledger["bytes_opened"] = len(body)
    if len(body) != expected_size:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{role} byte size drift: {len(body)} != {expected_size}",
        )
    observed_blob = git_blob_sha1(body)
    ledger["git_blob_sha1"] = observed_blob
    if observed_blob != expected_git_blob_sha1:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{role} Git blob SHA-1 drift",
        )
    return body, ledger


def run(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    source_contract, final_contract, declaration = load_contracts()
    authorization = _load_json(authorization_path)
    if authorization.get("attempt_id") != final_contract.get("attempt_id"):
        raise RuntimeError("final authorization attempt_id drift")
    if authorization.get("authorized_external_gets") != 2:
        raise RuntimeError("final endpoint must authorize exactly two external GETs")

    binding_paths = {
        "source_contract_git_blob_sha": HERE / "source_contract.json",
        "pre_response_pass_git_blob_sha": HERE / "pre_response_pass_certificate.json",
        "response_header_pass_git_blob_sha": HERE / "response_header_pass_certificate.json",
        "final_endpoint_contract_git_blob_sha": HERE / "final_endpoint_contract.json",
        "final_endpoint_declaration_git_blob_sha": HERE / "final_endpoint_declaration.json",
        "final_endpoint_evaluator_git_blob_sha": HERE / "final_endpoint.py",
        "final_endpoint_runner_git_blob_sha": Path(__file__).resolve(),
        "runtime_lock_git_blob_sha": HERE / "runtime_lock.txt",
        "pre_response_geometry_git_blob_sha": HERE / "pre_response_geometry.py",
        "dynamic_island_reachability_git_blob_sha": REPO_ROOT / "src/eog/dynamic_island_reachability.py",
        "world_reconstruction_git_blob_sha": REPO_ROOT / "src/eog/v2/world_reconstruction.py",
        "world_forecast_git_blob_sha": REPO_ROOT / "src/eog/v2/world_forecast.py",
        "world_predictive_summary_git_blob_sha": REPO_ROOT / "src/eog/v2/world_predictive_summary.py",
        "predictive_complementarity_git_blob_sha": REPO_ROOT / "src/eog/v2/predictive_complementarity.py",
    }
    for key, path in binding_paths.items():
        expected = authorization.get(key)
        if not isinstance(expected, str) or _git_blob_sha(path) != expected:
            raise RuntimeError(f"frozen Git blob drift before full response access: {key}")

    pre_pass = _load_json(HERE / "pre_response_pass_certificate.json")
    header_pass = _load_json(HERE / "response_header_pass_certificate.json")
    if pre_pass.get("status") != "pre_response_geometry_ready":
        raise RuntimeError("pre-response PASS certificate not ready")
    if header_pass.get("status") != "response_header_ready":
        raise RuntimeError("response-header PASS certificate not ready")
    if (
        pre_pass.get("authoritative_execution", {}).get("result_fingerprint")
        != final_contract["prerequisites"]["pre_response_result_fingerprint"]
    ):
        raise RuntimeError("pre-response result fingerprint drift")
    if (
        header_pass.get("authoritative_execution", {}).get("result_fingerprint")
        != final_contract["prerequisites"]["response_header_result_fingerprint"]
    ):
        raise RuntimeError("response-header result fingerprint drift")

    coordinate_source = final_contract["source"]["coordinate_registry"]
    response_source = final_contract["source"]["response_table"]
    transport_ledger: list[dict[str, object]] = []
    coordinate_bytes = b""
    response_bytes = b""
    try:
        coordinate_bytes, coordinate_ledger = _read_exact_raw(
            url=str(coordinate_source["raw_url"]),
            expected_size=int(coordinate_source["size_bytes"]),
            expected_git_blob_sha1=str(coordinate_source["git_blob_sha1"]),
            role="coordinate_registry",
            opener=opener,
        )
        transport_ledger.append(coordinate_ledger)
        response_bytes, response_ledger = _read_exact_raw(
            url=str(response_source["raw_url"]),
            expected_size=int(response_source["size_bytes"]),
            expected_git_blob_sha1=str(response_source["git_blob_sha1"]),
            role="full_response_table",
            opener=opener,
        )
        transport_ledger.append(response_ledger)
        result = evaluate_final_endpoint(
            coordinate_bytes,
            response_bytes,
            source_contract,
            final_contract,
            declaration,
        )
    except FinalEndpointTerminal as terminal:
        result = terminal_result(
            final_contract,
            terminal,
            response_bytes_opened=len(response_bytes),
            coordinate_bytes_opened=len(coordinate_bytes),
        )

    result["transport_ledger"] = transport_ledger
    result["authorized_external_gets"] = 2
    result["completed_external_gets"] = len(transport_ledger)
    result["coordinate_bytes_opened"] = len(coordinate_bytes)
    result["response_bytes_opened"] = len(response_bytes)
    result["authorization_sha256"] = hashlib.sha256(authorization_path.read_bytes()).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    run()
