from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "response_header_contract.json"
DEFAULT_OUTPUT = HERE / "response_header_certificate.json"
USER_AGENT = "EOG-Leipzig-RoeDeer-HeaderGate/1.0"


class HeaderStop(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


class HttpByteFetcher:
    def __init__(self, contract: dict[str, object]):
        source = contract["source"]
        transport = contract["transport"]
        parsed = urlparse(str(source["raw_url"]))
        if parsed.scheme != "https" or parsed.hostname != transport["allowed_host"]:
            raise HeaderStop("frozen response URL is not the authorized HTTPS host")
        if parsed.query or parsed.fragment:
            raise HeaderStop("frozen response URL must not contain query or fragment")
        self.host = parsed.hostname
        self.path = parsed.path
        self.total = int(source["size_bytes"])
        self.required_status = int(transport["required_http_status"])
        self.conn = http.client.HTTPSConnection(self.host, timeout=30)
        self.requests = 0
        self.bytes_opened = 0

    def read_byte(self, offset: int) -> bytes:
        self.requests += 1
        self.conn.request(
            "GET",
            self.path,
            headers={
                "Range": f"bytes={offset}-{offset}",
                "Accept-Encoding": "identity",
                "User-Agent": USER_AGENT,
                "Connection": "keep-alive",
            },
        )
        response = self.conn.getresponse()
        if response.status != self.required_status:
            response.close()
            raise HeaderStop(f"byte Range at offset {offset} returned HTTP {response.status}, require 206")
        expected_range = f"bytes {offset}-{offset}/{self.total}"
        if response.getheader("Content-Range") != expected_range:
            response.close()
            raise HeaderStop(f"Content-Range drift at offset {offset}")
        encoding = response.getheader("Content-Encoding")
        if encoding not in (None, "identity"):
            response.close()
            raise HeaderStop(f"unexpected Content-Encoding at offset {offset}: {encoding!r}")
        length = response.getheader("Content-Length")
        if length is not None and length != "1":
            response.close()
            raise HeaderStop(f"unexpected Content-Length at offset {offset}: {length!r}")
        body = response.read(2)
        response.close()
        if len(body) != 1:
            raise HeaderStop(f"byte Range at offset {offset} returned {len(body)} bytes, require exactly 1")
        self.bytes_opened += 1
        return body

    def close(self) -> None:
        self.conn.close()


def read_physical_header(contract: dict[str, object], fetcher: object) -> tuple[bytes, str]:
    transport = contract["transport"]
    maximum = int(transport["maximum_requests"])
    if int(transport["range_unit_bytes"]) != 1:
        raise HeaderStop("header firewall requires one-byte ranges")
    opened = bytearray()
    for offset in range(maximum):
        value = fetcher.read_byte(offset)
        if len(value) != 1:
            raise HeaderStop("byte fetcher violated one-byte contract")
        opened.extend(value)
        if value == b"\n":
            break
    else:
        raise HeaderStop("no LF terminator found within frozen header byte ceiling")

    line = bytes(opened)
    if line.endswith(b"\r\n"):
        terminator = "CRLF"
        header = line[:-2]
    elif line.endswith(b"\n"):
        terminator = "LF"
        header = line[:-1]
    else:
        raise HeaderStop("physical line terminator is not LF/CRLF")
    return header, terminator


def evaluate(contract: dict[str, object], fetcher: object) -> dict[str, object]:
    expected = str(contract["reference_header"]["expected_header_ascii"]).encode("ascii")
    expected_length = int(contract["reference_header"]["expected_header_bytes_without_terminator"])
    if len(expected) != expected_length:
        raise HeaderStop("contract expected-header length is internally inconsistent")
    if expected_length + 2 > int(contract["transport"]["maximum_header_bytes_opened"]):
        raise HeaderStop("contract header ceiling cannot contain expected CRLF header")

    header, terminator = read_physical_header(contract, fetcher)
    try:
        header_text = header.decode("ascii")
    except UnicodeDecodeError as exc:
        raise HeaderStop("target response header is not ASCII") from exc

    expected_tokens = list(contract["reference_header"]["expected_tokens"])
    observed_tokens = header_text.split(",")
    if header_text != contract["reference_header"]["expected_header_ascii"]:
        raise HeaderStop("target response header does not exactly match prospectively frozen Camtrap DP header")
    if observed_tokens != expected_tokens:
        raise HeaderStop("target response header token/order mismatch")
    if any((not token) or token != token.strip() for token in observed_tokens):
        raise HeaderStop("target response header contains empty or padded column names")
    if len(set(observed_tokens)) != len(observed_tokens):
        raise HeaderStop("target response header contains duplicate column names")

    payload = {
        "schema": "eog.leipzig_roedeer_endpoint3.response_header_certificate.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "response_header_ready",
        "terminal_stage": "response_header_only",
        "gate0_result_fingerprint": contract["gate0"]["result_fingerprint"],
        "source_git_blob_sha1": contract["source"]["git_blob_sha1"],
        "header_ascii": header_text,
        "header_tokens": observed_tokens,
        "header_line_terminator": terminator,
        "header_fingerprint": canonical_sha256({"header": header_text, "terminator": terminator}),
        "response_header_range_requests": fetcher.requests,
        "response_header_bytes_opened": fetcher.bytes_opened,
        "response_data_row_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "next_gate": "full_response_contract_freeze",
    }
    payload["result_fingerprint"] = canonical_sha256(payload)
    return payload


def stop_certificate(contract: dict[str, object], fetcher: object, reason: str) -> dict[str, object]:
    payload = {
        "schema": "eog.leipzig_roedeer_endpoint3.response_header_certificate.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_row_response_header_transport_or_schema",
        "terminal_stage": "response_header_only",
        "reason": reason,
        "gate0_result_fingerprint": contract["gate0"]["result_fingerprint"],
        "source_git_blob_sha1": contract["source"]["git_blob_sha1"],
        "response_header_range_requests": int(getattr(fetcher, "requests", 0)),
        "response_header_bytes_opened": int(getattr(fetcher, "bytes_opened", 0)),
        "response_data_row_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "retry_or_alias_repair_allowed": False,
    }
    payload["result_fingerprint"] = canonical_sha256(payload)
    return payload


def main(contract_path: Path = DEFAULT_CONTRACT, output_path: Path = DEFAULT_OUTPUT) -> int:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    fetcher: object
    try:
        fetcher = HttpByteFetcher(contract)
    except HeaderStop as exc:
        fetcher = type("EmptyFetcher", (), {"requests": 0, "bytes_opened": 0, "close": lambda self: None})()
        result = stop_certificate(contract, fetcher, str(exc))
    else:
        try:
            result = evaluate(contract, fetcher)
        except (HeaderStop, OSError, http.client.HTTPException) as exc:
            result = stop_certificate(contract, fetcher, str(exc))
        finally:
            fetcher.close()
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
