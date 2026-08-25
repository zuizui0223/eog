from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "snapshot_japan_sika_deer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "sequence_header_contract.json").read_text())
IDENTITY = json.loads((HERE / "pensoft_xml_sequence_identity_certificate.json").read_text())
OUT = BUILD / "sequence_header_gate.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def finish(result, code=0):
    result["fingerprint"] = hashlib.sha256(canonical({k: v for k, v in result.items() if k != "fingerprint"})).hexdigest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


def main():
    result = {
        "schema": "eog.snapshot_japan_sika_deer_replication_2.sequence_header_gate.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response_values",
        "reason": None,
        "header": {},
        "response_firewall": {
            "sequence_header_get_requests": 0,
            "sequence_header_bytes_opened": 0,
            "sequence_data_row_bytes_opened": 0,
            "sequence_rows_opened": False,
            "sequence_values_opened": False,
            "model_fits": 0,
            "heldout_scores": 0,
        },
    }
    try:
        if IDENTITY["status"] != "pensoft_xml_resolves_exact_sequence_supplement_identity":
            raise RuntimeError("sequence identity certificate is not passing")
        if IDENTITY["supplement"]["binary_object_url"] != CONTRACT["binary_object_url"]:
            raise RuntimeError("binary object URL drift")
        if IDENTITY["supplement"]["published_file_name"] != CONTRACT["published_filename"]:
            raise RuntimeError("published filename drift")
        req = urllib.request.Request(
            CONTRACT["binary_object_url"],
            headers={
                "Accept": "text/csv,text/plain,application/octet-stream,*/*;q=0.5",
                "User-Agent": "Mozilla/5.0 EOG-SnapshotJapan-header-only/1.0",
                "Referer": "https://bdj.pensoft.net/article/141168/",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            result["response_firewall"]["sequence_header_get_requests"] = 1
            final_url = r.geturl()
            host = urllib.parse.urlparse(final_url).netloc.lower()
            if not host.endswith("pensoft.net"):
                raise RuntimeError(f"header GET redirected outside Pensoft: {final_url}")
            buf = bytearray()
            terminator = None
            while len(buf) < int(CONTRACT["max_header_bytes"]):
                b = r.read(1)
                if not b:
                    break
                buf.extend(b)
                if b in {b"\n", b"\r"}:
                    terminator = "LF" if b == b"\n" else "CR"
                    break
            result["response_firewall"]["sequence_header_bytes_opened"] = len(buf)
            if terminator is None:
                raise RuntimeError("no header line terminator within frozen max_header_bytes")
            raw_header = bytes(buf[:-1])
            if raw_header.endswith(b"\r"):
                raw_header = raw_header[:-1]
                terminator = "CRLF"
            try:
                text = raw_header.decode("utf-8-sig")
                encoding = "utf-8-sig"
            except UnicodeDecodeError:
                text = raw_header.decode("utf-8")
                encoding = "utf-8"
            cols = next(csv.reader(io.StringIO(text), delimiter=CONTRACT["delimiter"]))
            expected = list(CONTRACT["expected_columns_exact_order"])
            result["header"] = {
                "final_host": host,
                "content_type": r.headers.get("Content-Type"),
                "reported_content_length": r.headers.get("Content-Length"),
                "content_disposition": r.headers.get("Content-Disposition"),
                "terminator": terminator,
                "encoding": encoding,
                "column_count": len(cols),
                "columns": cols,
                "raw_header_sha256": hashlib.sha256(raw_header).hexdigest(),
            }
            if cols != expected:
                result["status"] = "stop_sequence_header_contract_mismatch"
                result["reason"] = f"observed header does not exactly match frozen published 26-column schema; observed={cols}"
                return finish(result, 0)
            result["status"] = "sequence_header_gate_pass_values_still_closed"
            result["reason"] = "exact published 26-column header reproduced; read stopped at first line terminator and no data-row bytes were opened"
            return finish(result, 0)
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return finish(result, 1)


if __name__ == "__main__":
    raise SystemExit(main())
