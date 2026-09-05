from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "response_header_contract.json"


class ResponseHeaderStop(RuntimeError):
    """Terminal pre-row response-header transport/schema STOP."""


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
        raise TypeError("response header contract must be a JSON object")
    return value


def evaluate_header_line(header_line: bytes, contract: dict[str, object]) -> dict[str, object]:
    rule = contract["header_rule"]
    maximum = int(rule["maximum_header_bytes_including_line_terminator"])
    if not header_line or len(header_line) > maximum:
        raise ResponseHeaderStop(
            f"response header length {len(header_line)} outside frozen 1..{maximum} byte bound"
        )
    if not header_line.endswith(b"\n"):
        raise ResponseHeaderStop("first response line did not terminate within frozen header range")
    physical = header_line[:-1]
    terminator = "LF"
    if physical.endswith(b"\r"):
        physical = physical[:-1]
        terminator = "CRLF"
    if terminator not in set(rule["line_terminators_allowed"]):
        raise ResponseHeaderStop(f"response header line terminator {terminator!r} is not allowed")
    if physical.startswith(b"\xef\xbb\xbf"):
        raise ResponseHeaderStop("UTF-8 BOM is outside the frozen response header contract")
    if b"\x00" in physical:
        raise ResponseHeaderStop("response header contains NUL byte")
    try:
        text = physical.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ResponseHeaderStop("response header is not UTF-8") from exc

    try:
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as exc:
        raise ResponseHeaderStop(f"response header CSV parse failed: {exc}") from exc
    if len(rows) != 1:
        raise ResponseHeaderStop("response header parser did not produce exactly one row")
    columns = rows[0]
    if not columns:
        raise ResponseHeaderStop("response header contains no columns")
    if any(value == "" for value in columns):
        raise ResponseHeaderStop("response header contains an empty column name")
    if any(value != value.strip() for value in columns):
        raise ResponseHeaderStop("response header column has leading/trailing whitespace")
    if len(set(columns)) != len(columns):
        raise ResponseHeaderStop("response header contains duplicate column names")

    required = [str(value) for value in rule["required_exact_tokens"]]
    missing = [value for value in required if columns.count(value) != 1]
    if missing:
        raise ResponseHeaderStop(
            f"required exact response header tokens do not each occur once: {missing!r}"
        )
    index_by_role = {value: columns.index(value) for value in required}
    result: dict[str, object] = {
        "schema": "eog.hokkaido_streamfish_endpoint3.response_header.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "response_header_ready",
        "header_bytes_opened": len(header_line),
        "line_terminator": terminator,
        "physical_columns": columns,
        "column_count": len(columns),
        "required_index_by_role": index_by_role,
        "header_sha256": hashlib.sha256(header_line).hexdigest(),
        "response_data_row_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_stop_result(contract: dict[str, object], reason: str) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.hokkaido_streamfish_endpoint3.response_header.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_row_response_header_transport_or_schema",
        "reason": str(reason),
        "header_bytes_opened": 0,
        "response_data_row_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result
