"""Gate1 README + physical CSV-header audit for the round-goby BAM bridge.

Allowed:
- full README.txt (source documentation);
- one-byte HTTP Range reads from byte 0 through the first LF of the two authorized
  CSV files.

Forbidden:
- any byte after the first CSV header line;
- any other dataset file.
"""
from __future__ import annotations

import csv
import hashlib
import http.client
import io
import json
from pathlib import Path
from urllib.parse import quote


HERE = Path(__file__).resolve().parent
GATE0 = HERE / "gate0_source_identity_certificate.json"
AUTH = HERE / "gate1_execution_authorization.json"
OUTPUT = HERE / "gate1_schema_certificate.json"

HOST = "zenodo.org"
RECORD_ID = 19621892
USER_AGENT = "EOG-Round-Goby-BAM-Bridge-Gate1/1.0"
MAX_HEADER_BYTES = 512


class Gate1Stop(RuntimeError):
    pass


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _load_inputs() -> tuple[dict[str, object], dict[str, object]]:
    gate0 = json.loads(GATE0.read_text(encoding="utf-8"))
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    if gate0.get("status") != "source_identity_ready":
        raise Gate1Stop("Gate0 is not PASS")
    if gate0.get("fingerprint") != auth.get("gate0_certificate_fingerprint"):
        raise Gate1Stop("Gate0 fingerprint does not match Gate1 authorization")
    if auth.get("status") != "authorized":
        raise Gate1Stop("Gate1 authorization is not active")
    return gate0, auth


def _file_path(name: str) -> str:
    return f"/records/{RECORD_ID}/files/{quote(name)}"


class OneByteHeaderFetcher:
    def __init__(self, file_name: str, total_size: int):
        self.file_name = file_name
        self.total_size = int(total_size)
        self.path = _file_path(file_name)
        self.conn = http.client.HTTPSConnection(HOST, timeout=30)
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
        if response.status != 206:
            response.close()
            raise Gate1Stop(
                f"{self.file_name} byte Range {offset} returned HTTP "
                f"{response.status}, require 206"
            )
        expected = f"bytes {offset}-{offset}/{self.total_size}"
        if response.getheader("Content-Range") != expected:
            response.close()
            raise Gate1Stop(
                f"{self.file_name} Content-Range drift at byte {offset}"
            )
        encoding = response.getheader("Content-Encoding")
        if encoding not in (None, "identity"):
            response.close()
            raise Gate1Stop(
                f"{self.file_name} unexpected Content-Encoding {encoding!r}"
            )
        length = response.getheader("Content-Length")
        if length is not None and length != "1":
            response.close()
            raise Gate1Stop(
                f"{self.file_name} unexpected one-byte Content-Length {length!r}"
            )
        body = response.read(2)
        response.close()
        if len(body) != 1:
            raise Gate1Stop(
                f"{self.file_name} one-byte Range returned {len(body)} bytes"
            )
        self.bytes_opened += 1
        return body

    def close(self) -> None:
        self.conn.close()


def read_header(fetcher: OneByteHeaderFetcher) -> tuple[str, str]:
    opened = bytearray()
    for offset in range(MAX_HEADER_BYTES):
        value = fetcher.read_byte(offset)
        opened.extend(value)
        if value == b"\n":
            break
    else:
        raise Gate1Stop(
            f"{fetcher.file_name} header exceeded {MAX_HEADER_BYTES} byte ceiling"
        )

    line = bytes(opened)
    if line.endswith(b"\r\n"):
        raw = line[:-2]
        terminator = "CRLF"
    elif line.endswith(b"\n"):
        raw = line[:-1]
        terminator = "LF"
    else:
        raise Gate1Stop("header has no LF terminator")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Gate1Stop(f"{fetcher.file_name} header is not UTF-8") from exc
    return text, terminator


def parse_header(header_text: str, file_name: str) -> list[str]:
    rows = list(csv.reader(io.StringIO(header_text)))
    if len(rows) != 1:
        raise Gate1Stop(f"{file_name} physical header did not parse as one CSV row")
    tokens = rows[0]
    if not tokens or any(not token for token in tokens):
        raise Gate1Stop(f"{file_name} contains empty header tokens")
    if len(set(tokens)) != len(tokens):
        raise Gate1Stop(f"{file_name} contains duplicate header tokens")
    return tokens


def fetch_readme(expected_size: int, expected_md5: str) -> dict[str, object]:
    conn = http.client.HTTPSConnection(HOST, timeout=30)
    try:
        conn.request(
            "GET",
            _file_path("README.txt"),
            headers={
                "Accept-Encoding": "identity",
                "User-Agent": USER_AGENT,
                "Connection": "close",
            },
        )
        response = conn.getresponse()
        if response.status != 200:
            response.close()
            raise Gate1Stop(f"README GET returned HTTP {response.status}")
        body = response.read(expected_size + 1)
        response.close()
    finally:
        conn.close()

    if len(body) != expected_size:
        raise Gate1Stop(
            f"README size mismatch: expected {expected_size}, got {len(body)}"
        )
    md5 = hashlib.md5(body, usedforsecurity=False).hexdigest()
    if md5 != expected_md5:
        raise Gate1Stop(
            f"README md5 mismatch: expected {expected_md5}, got {md5}"
        )
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = body.decode("latin-1")
    return {
        "size_bytes": len(body),
        "md5": md5,
        "sha256": hashlib.sha256(body).hexdigest(),
        "line_count": len(text.splitlines()),
    }


def evaluate_live() -> dict[str, object]:
    gate0, _ = _load_inputs()
    file_rows = {row["name"]: row for row in gate0["files"]}

    readme_row = file_rows["README.txt"]
    readme = fetch_readme(
        int(readme_row["size_bytes"]),
        str(readme_row["md5"]),
    )

    header_results = {}
    total_requests = 0
    total_header_bytes = 0

    for file_name in (
        "Upstream_data_noNAs_2025_noElectro.csv",
        "Date_of_Invasion.csv",
    ):
        row = file_rows[file_name]
        fetcher = OneByteHeaderFetcher(file_name, int(row["size_bytes"]))
        try:
            header_text, terminator = read_header(fetcher)
        finally:
            fetcher.close()
        tokens = parse_header(header_text, file_name)
        total_requests += fetcher.requests
        total_header_bytes += fetcher.bytes_opened
        header_results[file_name] = {
            "header_exact_order": tokens,
            "header_ascii_or_utf8": header_text,
            "line_terminator": terminator,
            "header_fingerprint": canonical_sha256(
                {"header": header_text, "terminator": terminator}
            ),
            "one_byte_range_requests": fetcher.requests,
            "header_bytes_opened": fetcher.bytes_opened,
            "data_row_bytes_opened": 0,
            "rows_opened": 0,
        }

    result: dict[str, object] = {
        "schema": "eog.bam_round_goby_external_bridge.gate1_schema.v1",
        "status": "readme_and_headers_ready",
        "gate0_fingerprint": gate0["fingerprint"],
        "readme": readme,
        "headers": header_results,
        "total_csv_header_range_requests": total_requests,
        "total_csv_header_bytes_opened": total_header_bytes,
        "response_data_row_bytes_opened": 0,
        "response_rows_opened": 0,
        "model_fits": 0,
        "next_authorized_stage": "freeze parser and response-independent site/world construction",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def stop_certificate(reason: str) -> dict[str, object]:
    gate0 = json.loads(GATE0.read_text(encoding="utf-8"))
    result: dict[str, object] = {
        "schema": "eog.bam_round_goby_external_bridge.gate1_schema.v1",
        "status": "stop_gate1_transport_or_schema",
        "reason": reason,
        "gate0_fingerprint": gate0.get("fingerprint"),
        "response_data_row_bytes_opened": 0,
        "response_rows_opened": 0,
        "model_fits": 0,
        "retry_or_transport_repair_allowed": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def main() -> int:
    try:
        result = evaluate_live()
    except (Gate1Stop, OSError, http.client.HTTPException) as exc:
        result = stop_certificate(str(exc))
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
