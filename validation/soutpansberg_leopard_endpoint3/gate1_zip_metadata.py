from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from validation.mica_muskrat_endpoint3.gate0_archive_transport import (
    Gate0Stop as ZipMetadataStop,
    inspect_zip_metadata,
)

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "gate1_zip_metadata_contract.json"
OpenUrl = Callable[..., object]


class Gate1Stop(RuntimeError):
    """Terminal pre-response ZIP transport/container/inventory STOP."""


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


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("Gate1 contract must be a JSON object")
    return value


class FrozenRangeTransport:
    """Strict bounded-range transport using the already-frozen Figshare file size."""

    def __init__(
        self,
        url: str,
        archive_size: int,
        opener: OpenUrl = urllib.request.urlopen,
    ) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("archive URL must be absolute HTTPS")
        if isinstance(archive_size, bool) or not isinstance(archive_size, int) or archive_size <= 0:
            raise ValueError("archive_size must be a positive integer")
        self.url = url
        self.archive_size = archive_size
        self.opener = opener
        self.ledger: list[dict[str, object]] = []

    def read(self, start: int, end: int, role: str) -> bytes:
        if start < 0 or end < start or end >= self.archive_size:
            raise Gate1Stop(f"invalid bounded range {start}-{end}")
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": "EOG-Soutpansberg-Leopard-Gate1/1.0",
                "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        try:
            response_context = self.opener(request, timeout=90)
        except (OSError, urllib.error.URLError) as exc:
            raise Gate1Stop(f"bounded Range transport unavailable: {exc}") from exc

        with response_context as response:
            status = getattr(response, "status", None) or response.getcode()
            headers = {key.lower(): value for key, value in response.headers.items()}
            final = urlparse(response.geturl())
            row: dict[str, object] = {
                "role": role,
                "start": start,
                "end": end,
                "status": status,
                "content_range": headers.get("content-range"),
                "content_encoding": headers.get("content-encoding"),
                "final_scheme": final.scheme,
                "final_host": final.hostname,
                "bytes_opened": 0,
            }
            self.ledger.append(row)

            # The body is intentionally never read before these checks pass.
            if status != 206:
                raise Gate1Stop(
                    f"Range request returned HTTP {status}; response body was not opened"
                )
            match = re.fullmatch(
                rf"bytes {start}-{end}/(\d+)",
                headers.get("content-range", ""),
            )
            if match is None or int(match.group(1)) != self.archive_size:
                raise Gate1Stop("Content-Range does not preserve the frozen archive size")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate1Stop("Range response unexpectedly applied content encoding")
            if final.scheme != "https":
                raise Gate1Stop("Range redirect left HTTPS")

            expected = end - start + 1
            body = response.read(expected + 1)
            row["bytes_opened"] = len(body)
        if len(body) != expected:
            raise Gate1Stop(f"Range response length {len(body)} != {expected}")
        return body


def _compile_contract_regex(contract: dict[str, object], key: str) -> re.Pattern[str]:
    rules = contract["survey_pair_inventory"]
    if not isinstance(rules, dict):
        raise TypeError("survey_pair_inventory must be an object")
    value = rules.get(key)
    if not isinstance(value, str) or not value:
        raise TypeError(f"{key} must be a non-empty regex string")
    return re.compile(value)


def _survey_map(
    members: list[dict[str, object]], pattern: re.Pattern[str], role: str
) -> dict[str, dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    for member in members:
        basename = member.get("basename")
        if not isinstance(basename, str):
            continue
        match = pattern.fullmatch(basename)
        if match is None:
            continue
        survey_id = f"s{match.group(1)}"
        if survey_id in selected:
            raise Gate1Stop(f"duplicate {role} member for {survey_id}")
        selected[survey_id] = member
    return selected


def validate_survey_pair_inventory(
    inventory: dict[str, object], contract: dict[str, object]
) -> dict[str, object]:
    members = inventory.get("members")
    if not isinstance(members, list) or not all(isinstance(row, dict) for row in members):
        raise Gate1Stop("ZIP inventory does not contain a valid member list")

    deployment_pattern = _compile_contract_regex(contract, "deployment_basename_regex")
    capture_pattern = _compile_contract_regex(contract, "capture_basename_regex")
    deployments = _survey_map(members, deployment_pattern, "deployment")
    captures = _survey_map(members, capture_pattern, "capture")

    expected_list = contract["survey_pair_inventory"].get("survey_ids")
    if not isinstance(expected_list, list) or not all(isinstance(v, str) for v in expected_list):
        raise TypeError("survey_ids must be a list of strings")
    expected = set(expected_list)
    if set(deployments) != expected:
        raise Gate1Stop(
            f"deployment survey inventory drift: {sorted(deployments)} != {sorted(expected)}"
        )
    if set(captures) != expected:
        raise Gate1Stop(
            f"capture survey inventory drift: {sorted(captures)} != {sorted(expected)}"
        )
    if set(deployments) != set(captures):
        raise Gate1Stop("deployment/capture survey identities do not match")

    def slim(member: dict[str, object]) -> dict[str, object]:
        return {
            "name": member["name"],
            "basename": member["basename"],
            "crc32": member["crc32"],
            "compression_method": member["compression_method"],
            "compressed_size": member["compressed_size"],
            "uncompressed_size": member["uncompressed_size"],
            "local_header_offset": member["local_header_offset"],
            "payload_start": member["payload_start"],
            "payload_end": member["payload_end"],
        }

    pairs = {
        survey_id: {
            "deployment": slim(deployments[survey_id]),
            "capture": slim(captures[survey_id]),
        }
        for survey_id in expected_list
    }
    return {
        "survey_count": len(expected_list),
        "deployment_member_count": len(deployments),
        "capture_member_count": len(captures),
        "pairs": pairs,
    }


def assert_metadata_requests_do_not_overlap_payloads(
    inventory: dict[str, object], ledger: list[dict[str, object]]
) -> None:
    members = inventory.get("members")
    if not isinstance(members, list):
        raise Gate1Stop("ZIP inventory has no members")
    payloads: list[tuple[int, int]] = []
    for member in members:
        if not isinstance(member, dict) or member.get("payload_end") is None:
            continue
        payloads.append((int(member["payload_start"]), int(member["payload_end"])))
    for request in ledger:
        request_interval = (int(request["start"]), int(request["end"]))
        for payload in payloads:
            if request_interval[0] <= payload[1] and payload[0] <= request_interval[1]:
                raise Gate1Stop(
                    f"metadata Range request {request_interval} overlaps member payload {payload}"
                )


def evaluate_zip_metadata(
    contract: dict[str, object],
    read_range: Callable[[int, int, str], bytes],
    request_ledger: list[dict[str, object]],
) -> dict[str, object]:
    identity = contract["gate0_identity"]
    archive_size = identity["size_bytes"]
    try:
        inventory = inspect_zip_metadata(archive_size, read_range)
    except ZipMetadataStop as exc:
        raise Gate1Stop(str(exc)) from exc
    assert_metadata_requests_do_not_overlap_payloads(inventory, request_ledger)
    pair_inventory = validate_survey_pair_inventory(inventory, contract)

    result: dict[str, object] = {
        "schema": "eog.soutpansberg_leopard_endpoint3.gate1_zip_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate1_zip_metadata_ready",
        "gate0_identity": identity,
        "archive_metadata_request_count": len(request_ledger),
        "archive_metadata_bytes_opened": sum(int(row.get("bytes_opened", 0)) for row in request_ledger),
        "request_ledger": request_ledger,
        "inventory_fingerprint": inventory["fingerprint"],
        "central_directory_sha256": inventory["central_directory_sha256"],
        "member_count": inventory["member_count"],
        "survey_pair_inventory": pair_inventory,
        "member_payload_bytes_opened": 0,
        "deployment_payload_bytes_opened": 0,
        "capture_header_bytes_opened": 0,
        "capture_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_stop_result(
    contract: dict[str, object],
    reason: str,
    request_ledger: list[dict[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.soutpansberg_leopard_endpoint3.gate1_zip_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_zip_transport_container_or_inventory",
        "reason": str(reason),
        "archive_metadata_request_count": len(request_ledger),
        "archive_metadata_bytes_opened": sum(int(row.get("bytes_opened", 0)) for row in request_ledger),
        "request_ledger": request_ledger,
        "member_payload_bytes_opened": 0,
        "deployment_payload_bytes_opened": 0,
        "capture_header_bytes_opened": 0,
        "capture_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result
