from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from validation.sebms_ochlodes_endpoint3.gate1_dwca_metadata import (
    Gate1Stop,
    StrictDwcaTransport,
    evaluate_dwca_metadata,
    terminal_stop_result,
)


HERE = Path(__file__).resolve().parent
DEFAULT_AUTHORIZATION = HERE / "gate1_execution_authorization.json"
DEFAULT_CONTRACT = HERE / "gate1_dwca_metadata_contract.json"
DEFAULT_GATE0_PASS = HERE / "gate0_pass_certificate.json"
DEFAULT_OUTPUT = HERE / "gate1_live_dwca_metadata_certificate.json"


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


def _same_archive_identity(expected: str, observed: str, allowed_hosts: set[str]) -> bool:
    left = urlparse(expected)
    right = urlparse(observed)
    return (
        right.scheme == "https"
        and right.hostname in allowed_hosts
        and right.path == left.path
        and sorted(parse_qsl(right.query, keep_blank_values=True))
        == sorted(parse_qsl(left.query, keep_blank_values=True))
    )


class AuthorizedDwcaTransport(StrictDwcaTransport):
    def __init__(self, contract, authorization, *, opener=urllib.request.urlopen):
        super().__init__(contract, opener=opener)
        self.authorization = authorization

    def _validate_common_headers(self, response, role):
        status, headers, final_url = super()._validate_common_headers(response, role)
        if not _same_archive_identity(self.url, final_url, set(self.allowed_hosts)):
            raise Gate1Stop(f"{role} changed frozen archive path/query identity")
        return status, headers, final_url

    def read_range(self, start, end, role):
        requested = end - start + 1
        max_requests = int(self.authorization["maximum_range_requests"])
        max_single = int(self.authorization["maximum_single_metadata_range_bytes"])
        max_total = int(self.authorization["maximum_total_metadata_range_bytes"])
        if len(self.range_ledger) >= max_requests:
            raise Gate1Stop("Stage1 range-request ceiling reached before request")
        if role != "meta_xml_payload" and requested > max_single:
            raise Gate1Stop("Stage1 metadata range exceeds frozen single-request ceiling")
        requested_before = sum(
            int(row["end"]) - int(row["start"]) + 1
            for row in self.range_ledger
            if row.get("role") != "meta_xml_payload"
        )
        if role != "meta_xml_payload" and requested_before + requested > max_total:
            raise Gate1Stop("Stage1 metadata range budget exceeded before request")
        return super().read_range(start, end, role)


def run(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    contract_path: Path = DEFAULT_CONTRACT,
    gate0_pass_path: Path = DEFAULT_GATE0_PASS,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    authorization = _load_json(authorization_path)
    contract = _load_json(contract_path)
    gate0_pass = _load_json(gate0_pass_path)
    evaluator_path = HERE / "gate1_dwca_metadata.py"
    runner_path = Path(__file__).resolve()
    reused_path = HERE.parents[0] / "mica_muskrat_endpoint3" / "gate0_archive_transport.py"

    if authorization.get("attempt_id") != contract.get("attempt_id"):
        raise RuntimeError("Stage1 authorization attempt_id drift")
    if authorization.get("authorized_url") != contract["source"]["archive_url"]:
        raise RuntimeError("Stage1 authorization archive URL drift")
    if gate0_pass.get("status") != "gate0_metadata_ready":
        raise RuntimeError("Stage1 cannot execute without recorded Gate0 PASS")
    if gate0_pass["authoritative_execution"]["result_fingerprint"] != contract["gate0_pass"]["result_fingerprint"]:
        raise RuntimeError("Gate0 fingerprint drift before Stage1")

    bindings = {
        contract_path: authorization.get("gate1_contract_git_blob_sha"),
        gate0_pass_path: authorization.get("gate0_pass_git_blob_sha"),
        evaluator_path: authorization.get("gate1_evaluator_git_blob_sha"),
        runner_path: authorization.get("gate1_runner_git_blob_sha"),
        reused_path: authorization.get("reused_zip_inspector_git_blob_sha"),
    }
    for path, expected in bindings.items():
        if not isinstance(expected, str) or _git_blob_sha(path) != expected:
            raise RuntimeError(f"Git blob drift before Stage1 external access: {path}")

    transport = AuthorizedDwcaTransport(contract, authorization, opener=opener)
    try:
        archive_size = transport.discover_size()
        result = evaluate_dwca_metadata(
            contract,
            archive_size,
            transport.read_range,
            transport.range_ledger,
        )
    except Gate1Stop as exc:
        result = terminal_stop_result(contract, str(exc))

    result["head_ledger"] = transport.head_ledger
    result["range_ledger"] = transport.range_ledger
    result["archive_metadata_range_requests"] = len(
        [row for row in transport.range_ledger if row.get("role") != "meta_xml_payload"]
    )
    result["archive_metadata_range_bytes_opened"] = sum(
        int(row.get("bytes_opened", 0))
        for row in transport.range_ledger
        if row.get("role") != "meta_xml_payload"
    )
    result["meta_xml_compressed_bytes_opened"] = sum(
        int(row.get("bytes_opened", 0))
        for row in transport.range_ledger
        if row.get("role") == "meta_xml_payload"
    )
    result["event_member_payload_bytes_opened"] = 0
    result["emof_member_payload_bytes_opened"] = 0
    result["occurrence_member_header_bytes_opened"] = 0
    result["occurrence_member_payload_bytes_opened"] = 0
    result["response_rows_opened"] = 0
    result["response_values_opened"] = False
    result["model_fits"] = 0
    result["heldout_scores"] = 0
    result["counts_as_predictive_evidence"] = False
    result["authorization_sha256"] = hashlib.sha256(authorization_path.read_bytes()).hexdigest()

    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    run()
