from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "validation/azores_yellow_eel_paired_complementarity"
STAGE1 = json.loads((HERE / "stage1_certificate.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((HERE / "header_contract.json").read_text(encoding="utf-8"))
OUT_DIR = ROOT / "build/azores_yellow_eel_header"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "header_preflight.json"

result = {
    "attempt_id": CONTRACT["attempt_id"],
    "status": "not_evaluated",
    "zenodo_metadata_requests": 0,
    "response_header_requests": 0,
    "response_header_bytes_opened": 0,
    "response_payload_requests": 0,
    "response_payload_bytes_opened": 0,
    "response_rows_opened": False,
    "response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def finish(status: str, **extra) -> None:
    result.update(extra)
    result["status"] = status
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def fail(status: str, reason: str, **extra) -> None:
    finish(status, reason=reason, **extra)
    raise SystemExit(3)


# The response-blind geometry/availability certificate must be finalized first.
if STAGE1["attempt_id"] != CONTRACT["attempt_id"]:
    fail("stop_stage1_certificate_mismatch", "attempt IDs differ")
if STAGE1["status"] != CONTRACT["stage1_certificate_required_status"]:
    fail("stop_stage1_certificate_mismatch", "stage1 did not pass")
fw = STAGE1["response_firewall"]
if any(
    [
        fw["response_payload_requests"] != 0,
        fw["response_payload_bytes_opened"] != 0,
        fw["response_header_bytes_opened"] != 0,
        fw["response_rows_opened"] is not False,
        fw["response_values_opened"] is not False,
        fw["model_fits"] != 0,
        fw["heldout_scores"] != 0,
    ]
):
    fail("stop_stage1_certificate_mismatch", "stage1 response firewall is not pristine")

source = CONTRACT["response_source"]
record_id = int(source["zenodo_record_id"])
metadata_url = f"https://zenodo.org/api/records/{record_id}"
request = urllib.request.Request(
    metadata_url,
    headers={"User-Agent": "EOG-Azores-eel-header/1.0", "Accept": "application/json", "Accept-Encoding": "identity"},
)
result["zenodo_metadata_requests"] = 1
with urllib.request.urlopen(request, timeout=60) as response:
    body = response.read(5_000_001)
    status = int(getattr(response, "status", 200))
if status != 200 or len(body) > 5_000_000:
    fail("stop_response_source_transport", "bounded Zenodo metadata request failed", http_status=status, observed_bytes=len(body))
metadata = json.loads(body.decode("utf-8"))
if int(metadata.get("id")) != record_id:
    fail("stop_response_source_identity", "Zenodo record id mismatch")
files = [row for row in (metadata.get("files") or []) if str(row.get("key") or "") == source["file_name"]]
if len(files) != 1:
    fail("stop_response_source_identity", "response file did not resolve uniquely", match_count=len(files))
row = files[0]
checksum = str(row.get("checksum") or "")
observed_md5 = checksum.split(":", 1)[-1] if checksum else ""
observed_size = int(row.get("size") or 0)
if observed_md5 != source["md5"] or observed_size != int(source["size"]):
    fail(
        "stop_response_source_identity",
        "response file identity changed",
        observed_md5=observed_md5,
        expected_md5=source["md5"],
        observed_size=observed_size,
        expected_size=source["size"],
    )
links = row.get("links") or {}
content_url = str(links.get("content") or links.get("self") or "")
if not content_url:
    fail("stop_response_source_identity", "response file content URL missing")

# Strict bounded first-physical-record access: one byte at a time, stop on first CR or LF.
firewall = CONTRACT["firewall"]
limit = int(firewall["maximum_first_physical_record_bytes"])
req = urllib.request.Request(
    content_url,
    headers={"User-Agent": "EOG-Azores-eel-header/1.0", "Accept-Encoding": "identity", "Accept": "text/csv,application/octet-stream"},
)
result["response_header_requests"] = 1
buffer = bytearray()
terminator = None
with urllib.request.urlopen(req, timeout=90) as response:
    http_status = int(getattr(response, "status", 200))
    if http_status != 200:
        fail("stop_response_header_transport", "response header request did not return HTTP 200", http_status=http_status)
    while len(buffer) < limit:
        value = response.read(1)
        if value == b"":
            fail("stop_response_header_firewall", "physical record terminator not found before EOF")
        if value == b"\r":
            terminator = "CR"
            result["response_header_bytes_opened"] = len(buffer) + 1
            break
        if value == b"\n":
            terminator = "LF"
            result["response_header_bytes_opened"] = len(buffer) + 1
            break
        buffer.extend(value)
if terminator is None:
    fail("stop_response_header_firewall", f"first physical record exceeds frozen {limit}-byte limit")

try:
    header_text = bytes(buffer).decode("utf-8-sig")
except UnicodeDecodeError:
    fail("stop_response_header_schema", "first physical record is not UTF-8 decodable")
try:
    parsed_rows = list(csv.reader(io.StringIO(header_text)))
except csv.Error as exc:
    fail("stop_response_header_schema", "first physical record is not valid CSV", csv_error=str(exc))
if len(parsed_rows) != 1:
    fail("stop_response_header_schema", "bounded first record did not parse as exactly one CSV record")
observed_header = parsed_rows[0]
expected_header = list(CONTRACT["expected_physical_header"])
if observed_header != expected_header:
    fail(
        "stop_response_header_schema_mismatch",
        "physical response header differs from prospectively frozen source-code contract",
        observed_header=observed_header,
        expected_header=expected_header,
        terminator=terminator,
    )

finish(
    "response_header_schema_pass",
    zenodo_record_id=record_id,
    response_file_name=source["file_name"],
    response_file_md5=observed_md5,
    response_file_size=observed_size,
    physical_header=observed_header,
    physical_terminator=terminator,
    first_record_data_bytes=len(buffer),
    response_header_bytes_opened=result["response_header_bytes_opened"],
    response_payload_requests=0,
    response_payload_bytes_opened=0,
    response_rows_opened=False,
    response_values_opened=False,
    model_fits=0,
    heldout_scores=0,
)
