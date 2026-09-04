from __future__ import annotations

import binascii
import hashlib
import json
import re
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from urllib.parse import urlparse

from validation.mica_muskrat_endpoint3.gate0_archive_transport import (
    Gate0Stop as ZipMetadataStop,
    inspect_zip_metadata,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "gate1_dwca_metadata_contract.json"
DEFAULT_AUTHORIZATION = HERE / "gate1_execution_authorization.json"
DEFAULT_OUTPUT = HERE / "gate1_live_dwca_metadata_certificate.json"
USER_AGENT = "EOG-SeBMS-Ochlodes-Endpoint3-Stage1/1.0"


class Gate1Stop(RuntimeError):
    """Terminal pre-response DwC-A transport/container/meta.xml STOP."""


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


def load_json(path: Path) -> dict[str, object]:
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


def _allowed_host(final_url: str, allowed_hosts: tuple[str, ...]) -> bool:
    final = urlparse(final_url)
    return final.scheme == "https" and final.hostname in allowed_hosts


class StrictDwcaTransport:
    """HEAD/Range-only transport; never falls back to a full archive GET."""

    def __init__(
        self,
        contract: dict[str, object],
        *,
        opener=urllib.request.urlopen,
    ) -> None:
        source = contract["source"]
        if not isinstance(source, dict):
            raise TypeError("source must be object")
        self.url = str(source["archive_url"])
        self.allowed_hosts = tuple(str(v) for v in source["allowed_final_hosts"])
        self.allowed_media_types = tuple(
            str(v).casefold() for v in source["allowed_archive_media_types"]
        )
        self.maximum_archive_size = int(source["maximum_archive_size_bytes"])
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise ValueError("archive URL is outside frozen HTTPS host set")
        self.opener = opener
        self.archive_size: int | None = None
        self.head_ledger: list[dict[str, object]] = []
        self.range_ledger: list[dict[str, object]] = []

    def _validate_common_headers(self, response, role: str) -> tuple[int, dict[str, str], str]:
        status = getattr(response, "status", None) or response.getcode()
        final_url = response.geturl()
        headers = {key.lower(): value for key, value in response.headers.items()}
        if not _allowed_host(final_url, self.allowed_hosts):
            raise Gate1Stop(f"{role} left frozen HTTPS host set: {final_url!r}")
        if headers.get("content-encoding", "identity").casefold() != "identity":
            raise Gate1Stop(f"{role} unexpectedly used content encoding")
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type and content_type not in self.allowed_media_types:
            raise Gate1Stop(f"{role} content type outside frozen archive media types: {content_type!r}")
        return int(status), headers, final_url

    def discover_size(self) -> int:
        head_row: dict[str, object] = {
            "method": "HEAD",
            "status": None,
            "final_url": None,
            "content_length": None,
            "body_bytes_opened": 0,
        }
        self.head_ledger.append(head_row)
        request = urllib.request.Request(
            self.url,
            method="HEAD",
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        )
        try:
            context = self.opener(request, timeout=90)
            with context as response:
                status, headers, final_url = self._validate_common_headers(response, "HEAD")
                head_row["status"] = status
                head_row["final_url"] = final_url
                raw_length = headers.get("content-length", "")
                if 200 <= status < 400 and re.fullmatch(r"[1-9][0-9]*", raw_length):
                    size = int(raw_length)
                    if size > self.maximum_archive_size:
                        raise Gate1Stop("HEAD archive size exceeds frozen ceiling")
                    head_row["content_length"] = size
                    self.archive_size = size
                    return size
        except urllib.error.HTTPError as exc:
            head_row["status"] = int(exc.code)
            head_row["final_url"] = exc.geturl()
        except (OSError, urllib.error.URLError) as exc:
            head_row["transport_error"] = type(exc).__name__

        # Prospectively frozen fallback: exactly one byte Range, never a full GET.
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": "bytes=0-0",
            },
        )
        row: dict[str, object] = {
            "role": "archive_size_probe",
            "start": 0,
            "end": 0,
            "status": None,
            "content_range": None,
            "final_url": None,
            "bytes_opened": 0,
        }
        self.range_ledger.append(row)
        try:
            context = self.opener(request, timeout=90)
        except (OSError, urllib.error.URLError) as exc:
            raise Gate1Stop(f"archive size Range probe unavailable: {exc}") from exc
        with context as response:
            status, headers, final_url = self._validate_common_headers(
                response, "archive size Range probe"
            )
            row["status"] = status
            row["content_range"] = headers.get("content-range")
            row["final_url"] = final_url
            if status != 206:
                raise Gate1Stop(
                    f"archive size Range probe returned HTTP {status}; body was not opened"
                )
            match = re.fullmatch(r"bytes 0-0/([1-9][0-9]*)", headers.get("content-range", ""))
            if match is None:
                raise Gate1Stop("archive size Range probe lacks exact Content-Range")
            size = int(match.group(1))
            if size > self.maximum_archive_size:
                raise Gate1Stop("Range-probed archive size exceeds frozen ceiling")
            body = response.read(2)
            row["bytes_opened"] = len(body)
        if len(body) != 1:
            raise Gate1Stop("archive size Range probe did not return exactly one byte")
        self.archive_size = size
        return size

    def read_range(self, start: int, end: int, role: str) -> bytes:
        if self.archive_size is None:
            raise RuntimeError("discover_size must pass before bounded range reads")
        if start < 0 or end < start or end >= self.archive_size:
            raise Gate1Stop(f"invalid bounded archive range {start}-{end}")
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        row: dict[str, object] = {
            "role": role,
            "start": start,
            "end": end,
            "status": None,
            "content_range": None,
            "final_url": None,
            "bytes_opened": 0,
        }
        self.range_ledger.append(row)
        try:
            context = self.opener(request, timeout=90)
        except (OSError, urllib.error.URLError) as exc:
            raise Gate1Stop(f"bounded archive Range unavailable for {role}: {exc}") from exc
        with context as response:
            status, headers, final_url = self._validate_common_headers(response, role)
            row["status"] = status
            row["content_range"] = headers.get("content-range")
            row["final_url"] = final_url
            if status != 206:
                raise Gate1Stop(
                    f"bounded archive Range for {role} returned HTTP {status}; body was not opened"
                )
            match = re.fullmatch(
                rf"bytes {start}-{end}/([1-9][0-9]*)",
                headers.get("content-range", ""),
            )
            if match is None or int(match.group(1)) != self.archive_size:
                raise Gate1Stop(f"Content-Range drift for {role}")
            expected = end - start + 1
            body = response.read(expected + 1)
            row["bytes_opened"] = len(body)
        if len(body) != expected:
            raise Gate1Stop(f"bounded archive Range length drift for {role}")
        return body


def _payload_intervals(inventory: dict[str, object]) -> list[tuple[int, int, str]]:
    members = inventory.get("members")
    if not isinstance(members, list):
        raise Gate1Stop("ZIP inventory lacks members")
    intervals: list[tuple[int, int, str]] = []
    for member in members:
        if not isinstance(member, dict) or member.get("payload_end") is None:
            continue
        intervals.append(
            (int(member["payload_start"]), int(member["payload_end"]), str(member["name"]))
        )
    return intervals


def assert_metadata_ranges_outside_member_payloads(
    inventory: dict[str, object], request_ledger: list[dict[str, object]]
) -> None:
    intervals = _payload_intervals(inventory)
    for row in request_ledger:
        if row.get("role") == "meta_xml_payload":
            continue
        start = int(row["start"])
        end = int(row["end"])
        for payload_start, payload_end, name in intervals:
            if start <= payload_end and payload_start <= end:
                raise Gate1Stop(
                    f"metadata Range {start}-{end} overlaps member payload {name!r}"
                )


def _find_exact_member(inventory: dict[str, object], name: str) -> dict[str, object]:
    members = inventory.get("members")
    if not isinstance(members, list):
        raise Gate1Stop("ZIP inventory lacks members")
    matches = [row for row in members if isinstance(row, dict) and row.get("name") == name]
    if len(matches) != 1:
        raise Gate1Stop(f"ZIP member {name!r} occurs {len(matches)} times; expected exactly one")
    return matches[0]


def _read_meta_xml(
    member: dict[str, object],
    contract: dict[str, object],
    read_range,
) -> bytes:
    boundary = contract["meta_xml_boundary"]
    if not isinstance(boundary, dict):
        raise TypeError("meta_xml_boundary must be object")
    compressed_size = int(member["compressed_size"])
    uncompressed_size = int(member["uncompressed_size"])
    method = int(member["compression_method"])
    if compressed_size <= 0 or compressed_size > int(boundary["maximum_compressed_bytes"]):
        raise Gate1Stop("meta.xml compressed size outside frozen bound")
    if uncompressed_size <= 0 or uncompressed_size > int(boundary["maximum_uncompressed_bytes"]):
        raise Gate1Stop("meta.xml uncompressed size outside frozen bound")
    if method not in {int(v) for v in boundary["allowed_compression_methods"]}:
        raise Gate1Stop(f"meta.xml compression method {method} is outside frozen set")
    start = int(member["payload_start"])
    end = int(member["payload_end"])
    compressed = read_range(start, end, "meta_xml_payload")
    try:
        if method == 0:
            raw = compressed
        elif method == 8:
            raw = zlib.decompress(compressed, -15)
        else:  # guarded above
            raise Gate1Stop("unsupported meta.xml compression method")
    except zlib.error as exc:
        raise Gate1Stop(f"meta.xml DEFLATE decode failed: {exc}") from exc
    if len(raw) != uncompressed_size:
        raise Gate1Stop("meta.xml uncompressed length differs from ZIP metadata")
    crc = f"{binascii.crc32(raw) & 0xFFFFFFFF:08x}"
    if crc != str(member["crc32"]):
        raise Gate1Stop("meta.xml CRC32 mismatch")
    return raw


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _row_type_token(value: str) -> str:
    stripped = value.rstrip("/#")
    token = re.split(r"[/#]", stripped)[-1]
    if not token:
        raise Gate1Stop(f"invalid rowType URI: {value!r}")
    return token


def _descriptor_schema(element: ET.Element) -> dict[str, object]:
    locations = [
        (child.text or "").strip()
        for child in element.iter()
        if _local_name(child.tag) == "location" and (child.text or "").strip()
    ]
    if len(locations) != 1:
        raise Gate1Stop(f"row descriptor has {len(locations)} file locations; expected one")
    fields: list[dict[str, object]] = []
    id_fields: list[dict[str, object]] = []
    for child in element:
        lname = _local_name(child.tag)
        if lname not in {"id", "coreid", "field"}:
            continue
        raw_index = child.attrib.get("index")
        if raw_index is None or not re.fullmatch(r"[0-9]+", raw_index):
            raise Gate1Stop(f"{lname} lacks nonnegative integer index")
        row: dict[str, object] = {"kind": lname, "index": int(raw_index)}
        if lname == "field":
            term = child.attrib.get("term")
            if not isinstance(term, str) or not term:
                raise Gate1Stop("field lacks term URI")
            row["term"] = term
            fields.append(row)
        else:
            id_fields.append(row)
    indexes = [int(row["index"]) for row in fields + id_fields]
    if len(indexes) != len(set(indexes)):
        raise Gate1Stop("row descriptor contains duplicate field indexes")
    return {
        "row_type": element.attrib.get("rowType"),
        "location": locations[0],
        "encoding": element.attrib.get("encoding"),
        "fields_terminated_by": element.attrib.get("fieldsTerminatedBy"),
        "lines_terminated_by": element.attrib.get("linesTerminatedBy"),
        "fields_enclosed_by": element.attrib.get("fieldsEnclosedBy"),
        "ignore_header_lines": element.attrib.get("ignoreHeaderLines"),
        "id_fields": id_fields,
        "fields": fields,
    }


def parse_meta_xml(
    raw: bytes,
    inventory: dict[str, object],
    contract: dict[str, object],
) -> dict[str, object]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Gate1Stop(f"meta.xml parse failed: {exc}") from exc
    boundary = contract["meta_xml_boundary"]
    roles = boundary["required_roles"]
    if not isinstance(roles, dict):
        raise TypeError("required_roles must be object")
    children = [child for child in root if _local_name(child.tag) in {"core", "extension"}]
    resolved: dict[str, dict[str, object]] = {}
    used_locations: set[str] = set()
    for role, rule in roles.items():
        if not isinstance(rule, dict):
            raise TypeError(f"role {role} rule must be object")
        element_name = str(rule["element"])
        token = str(rule["row_type_terminal_token"])
        matches: list[ET.Element] = []
        for child in children:
            if _local_name(child.tag) != element_name:
                continue
            row_type = child.attrib.get("rowType")
            if isinstance(row_type, str) and _row_type_token(row_type) == token:
                matches.append(child)
        if len(matches) != 1:
            raise Gate1Stop(
                f"meta.xml role {role!r} occurs {len(matches)} times by frozen element/token rule"
            )
        schema = _descriptor_schema(matches[0])
        location = str(schema["location"])
        member = _find_exact_member(inventory, location)
        if location in used_locations:
            raise Gate1Stop("two required DwC-A roles resolve to the same member")
        used_locations.add(location)
        schema["member"] = {
            "name": member["name"],
            "crc32": member["crc32"],
            "compression_method": member["compression_method"],
            "compressed_size": member["compressed_size"],
            "uncompressed_size": member["uncompressed_size"],
            "payload_start": member["payload_start"],
            "payload_end": member["payload_end"],
        }
        resolved[role] = schema
    return resolved


def evaluate_dwca_metadata(
    contract: dict[str, object],
    archive_size: int,
    read_range,
    request_ledger: list[dict[str, object]],
) -> dict[str, object]:
    try:
        inventory = inspect_zip_metadata(archive_size, read_range)
    except ZipMetadataStop as exc:
        raise Gate1Stop(str(exc)) from exc
    assert_metadata_ranges_outside_member_payloads(inventory, request_ledger)
    meta_name = str(contract["meta_xml_boundary"]["exact_member_name"])
    meta_member = _find_exact_member(inventory, meta_name)
    raw_meta = _read_meta_xml(meta_member, contract, read_range)
    roles = parse_meta_xml(raw_meta, inventory, contract)
    result: dict[str, object] = {
        "schema": "eog.sebms_ochlodes_endpoint3.gate1_dwca_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate1_dwca_metadata_ready",
        "archive_size": archive_size,
        "zip_inventory_fingerprint": inventory["fingerprint"],
        "central_directory_sha256": inventory["central_directory_sha256"],
        "zip_member_count": inventory["member_count"],
        "meta_xml": {
            "member_name": meta_member["name"],
            "sha256": hashlib.sha256(raw_meta).hexdigest(),
            "uncompressed_bytes_opened": len(raw_meta),
        },
        "resolved_roles": roles,
        "event_member_payload_bytes_opened": 0,
        "emof_member_payload_bytes_opened": 0,
        "occurrence_member_header_bytes_opened": 0,
        "occurrence_member_payload_bytes_opened": 0,
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
        "schema": "eog.sebms_ochlodes_endpoint3.gate1_dwca_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "stop_pre_response_dwca_transport_container_or_metadata",
        "reason": str(reason),
        "event_member_payload_bytes_opened": 0,
        "emof_member_payload_bytes_opened": 0,
        "occurrence_member_header_bytes_opened": 0,
        "occurrence_member_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def run_live(
    contract_path: Path = DEFAULT_CONTRACT,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=urllib.request.urlopen,
) -> dict[str, object]:
    contract = load_json(contract_path)
    authorization = load_json(authorization_path)
    evaluator_path = HERE / "gate1_dwca_metadata.py"
    reused_path = HERE.parents[0] / "mica_muskrat_endpoint3" / "gate0_archive_transport.py"
    if authorization.get("attempt_id") != contract.get("attempt_id"):
        raise RuntimeError("Stage1 authorization attempt_id drift")
    if authorization.get("authorized_url") != contract["source"]["archive_url"]:
        raise RuntimeError("Stage1 authorization archive URL drift")
    blob_bindings = {
        contract_path: authorization.get("gate1_contract_git_blob_sha"),
        evaluator_path: authorization.get("gate1_evaluator_git_blob_sha"),
        reused_path: authorization.get("reused_zip_inspector_git_blob_sha"),
    }
    for path, expected in blob_bindings.items():
        if not isinstance(expected, str) or _git_blob_sha(path) != expected:
            raise RuntimeError(f"Git blob drift before live Stage1 access: {path}")

    transport = StrictDwcaTransport(contract, opener=opener)
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
    result["archive_metadata_range_requests"] = len(transport.range_ledger)
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    run_live()
