from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "response_headers_contract.json"
DEFAULT_OUTPUT = HERE / "response_headers_certificate.json"
USER_AGENT = "EOG-Tampa-Seagrass-HeadersGate/1.0"


class HeaderStop(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


class HttpByteFetcher:
    def __init__(self, source: dict[str, object], transport: dict[str, object]):
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


def read_physical_header(source: dict[str, object], transport: dict[str, object], fetcher: object) -> tuple[bytes, str]:
    maximum = int(source["maximum_requests"])
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


def evaluate_one(name: str, source: dict[str, object], transport: dict[str, object], fetcher: object) -> dict[str, object]:
    expected = str(source["expected_header_ascii"]).encode("ascii")
    expected_length = int(source["expected_header_bytes_without_terminator"])
    if len(expected) != expected_length:
        raise HeaderStop(f"{name} expected-header length is internally inconsistent")
    if expected_length + 2 > int(source["maximum_header_bytes_opened"]):
        raise HeaderStop(f"{name} header ceiling cannot contain expected CRLF header")

    header, terminator = read_physical_header(source, transport, fetcher)
    try:
        header_text = header.decode("ascii")
    except UnicodeDecodeError as exc:
        raise HeaderStop(f"{name} header is not ASCII") from exc

    expected_tokens = list(source["expected_tokens"])
    observed_tokens = header_text.split(",")
    if header_text != source["expected_header_ascii"]:
        raise HeaderStop(f"{name} header does not exactly match prospectively frozen source-code-derived header")
    if observed_tokens != expected_tokens:
        raise HeaderStop(f"{name} header token/order mismatch")
    if any((not token) or token != token.strip() for token in observed_tokens):
        raise HeaderStop(f"{name} header contains empty or padded column names")
    if len(set(observed_tokens)) != len(observed_tokens):
        raise HeaderStop(f"{name} header contains duplicate column names")

    return {
        "source_name": name,
        "source_git_blob_sha1": source["git_blob_sha1"],
        "header_ascii": header_text,
        "header_tokens": observed_tokens,
        "header_line_terminator": terminator,
        "header_fingerprint": canonical_sha256({"header": header_text, "terminator": terminator}),
        "header_range_requests": fetcher.requests,
        "header_bytes_opened": fetcher.bytes_opened,
        "data_row_bytes_opened": 0,
        "rows_opened": 0,
        "values_opened": False,
    }


def empty_counter(source: dict[str, object]) -> dict[str, object]:
    return {
        "source_git_blob_sha1": source["git_blob_sha1"],
        "header_range_requests": 0,
        "header_bytes_opened": 0,
        "data_row_bytes_opened": 0,
        "rows_opened": 0,
        "values_opened": False,
    }


def evaluate(contract: dict[str, object], fetcher_factory=HttpByteFetcher) -> dict[str, object]:
    transport = contract["transport"]
    sources = contract["sources"]
    results: dict[str, dict[str, object]] = {}
    active_fetcher = None
    active_name = None
    try:
        for name in ("occurrence", "emof"):
            active_name = name
            source = sources[name]
            active_fetcher = fetcher_factory(source, transport)
            try:
                results[name] = evaluate_one(name, source, transport, active_fetcher)
            finally:
                active_fetcher.close()
            active_fetcher = None
    except (HeaderStop, OSError, http.client.HTTPException) as exc:
        counters: dict[str, dict[str, object]] = {}
        for name in ("occurrence", "emof"):
            if name in results:
                counters[name] = results[name]
            elif name == active_name and active_fetcher is not None:
                counters[name] = {
                    "source_git_blob_sha1": sources[name]["git_blob_sha1"],
                    "header_range_requests": int(getattr(active_fetcher, "requests", 0)),
                    "header_bytes_opened": int(getattr(active_fetcher, "bytes_opened", 0)),
                    "data_row_bytes_opened": 0,
                    "rows_opened": 0,
                    "values_opened": False,
                }
            else:
                counters[name] = empty_counter(sources[name])
        payload = {
            "schema": "eog.tampa_seagrass_endpoint3.response_headers_certificate.v1",
            "attempt_id": contract["attempt_id"],
            "issue": contract["issue"],
            "status": "stop_pre_row_response_header_transport_or_schema",
            "terminal_stage": "response_headers_only",
            "reason": str(exc),
            "gate0_result_fingerprint": contract["gate0"]["result_fingerprint"],
            "headers": counters,
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

    total_requests = sum(int(results[name]["header_range_requests"]) for name in results)
    total_bytes = sum(int(results[name]["header_bytes_opened"]) for name in results)
    if total_requests > int(transport["total_maximum_requests"]):
        raise HeaderStop("combined header request ceiling exceeded")
    if total_bytes > int(transport["total_maximum_header_bytes_opened"]):
        raise HeaderStop("combined header byte ceiling exceeded")

    payload = {
        "schema": "eog.tampa_seagrass_endpoint3.response_headers_certificate.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "response_headers_ready",
        "terminal_stage": "response_headers_only",
        "gate0_result_fingerprint": contract["gate0"]["result_fingerprint"],
        "headers": results,
        "total_header_range_requests": total_requests,
        "total_header_bytes_opened": total_bytes,
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


def main(contract_path: Path = DEFAULT_CONTRACT, output_path: Path = DEFAULT_OUTPUT) -> int:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    result = evaluate(contract)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
