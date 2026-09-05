from __future__ import annotations

import hashlib
import json
import re
import struct
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Callable


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "gate1_zip_inventory_contract.json"
DEFAULT_OUTPUT = HERE / "gate1_zip_inventory_certificate.json"
USER_AGENT = "EOG-Columbia-Shrubsteppe-Endpoint3-Gate1/1.0"
RangeReader = Callable[[int, int, str], bytes]


class Gate1Stop(RuntimeError):
    pass


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


def _safe_member_name(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise Gate1Stop("ZIP member name is empty or uses an unsafe separator")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or (path.parts and ":" in path.parts[0]):
        raise Gate1Stop(f"unsafe ZIP member name: {value!r}")
    return value


def _find_eocd(
    archive_size: int,
    suffix_start: int,
    suffix: bytes,
) -> dict[str, int]:
    signature = b"PK\x05\x06"
    search_end = len(suffix)
    while True:
        pos = suffix.rfind(signature, 0, search_end)
        if pos < 0:
            break
        if pos + 22 <= len(suffix):
            fields = struct.unpack_from("<4s4H2IH", suffix, pos)
            comment_size = int(fields[7])
            absolute_offset = suffix_start + pos
            if pos + 22 + comment_size == len(suffix) and absolute_offset + 22 + comment_size == archive_size:
                disk_number, central_disk, disk_records, total_records = map(int, fields[1:5])
                central_size, central_offset = map(int, fields[5:7])
                if disk_number != 0 or central_disk != 0 or disk_records != total_records:
                    raise Gate1Stop("multi-disk ZIP archives are outside the frozen Gate1")
                if total_records <= 0:
                    raise Gate1Stop("ZIP central directory contains no members")
                if 0xFFFF in (disk_records, total_records) or 0xFFFFFFFF in (central_size, central_offset):
                    raise Gate1Stop("ZIP64 EOCD metadata are outside the frozen Gate1")
                if central_size <= 0 or central_size > 2_000_000:
                    raise Gate1Stop("ZIP central directory size is outside the frozen bounded Gate1")
                if central_offset < 0 or central_offset + central_size != absolute_offset:
                    raise Gate1Stop("ZIP central directory is not exactly adjacent to the EOCD")
                return {
                    "eocd_offset": absolute_offset,
                    "comment_size": comment_size,
                    "central_offset": central_offset,
                    "central_size": central_size,
                    "total_records": total_records,
                }
        search_end = pos
    raise Gate1Stop("no valid standard ZIP EOCD found in the frozen suffix window")


def _parse_central_directory(central: bytes, total_records: int, central_offset: int) -> list[dict[str, object]]:
    members: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(central):
        if cursor + 46 > len(central):
            raise Gate1Stop("truncated ZIP central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", central, cursor)
        if values[0] != b"PK\x01\x02":
            raise Gate1Stop(f"invalid central-directory signature at byte {cursor}")
        flags = int(values[3])
        method = int(values[4])
        crc32 = int(values[7])
        compressed_size = int(values[8])
        uncompressed_size = int(values[9])
        name_size, extra_size, member_comment_size = map(int, values[10:13])
        disk_start = int(values[13])
        local_offset = int(values[16])
        if flags & 0x1:
            raise Gate1Stop("encrypted ZIP members are outside the frozen Gate1")
        if disk_start != 0:
            raise Gate1Stop("ZIP member starts on a nonzero disk")
        if 0xFFFFFFFF in (compressed_size, uncompressed_size, local_offset):
            raise Gate1Stop("ZIP64 member metadata are outside the frozen Gate1")
        if local_offset < 0 or local_offset >= central_offset:
            raise Gate1Stop("ZIP local-header offset is outside the member area")
        end = cursor + 46 + name_size + extra_size + member_comment_size
        if name_size <= 0 or end > len(central):
            raise Gate1Stop("ZIP central-directory variable fields are invalid")
        name_bytes = central[cursor + 46 : cursor + 46 + name_size]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        try:
            decoded = name_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            raise Gate1Stop("ZIP member name failed its frozen declared encoding") from exc
        name = _safe_member_name(decoded)
        members.append(
            {
                "name": name,
                "basename": PurePosixPath(name).name,
                "parent": PurePosixPath(name).parent.as_posix(),
                "flags": flags,
                "compression_method": method,
                "crc32": f"{crc32:08x}",
                "compressed_size": compressed_size,
                "uncompressed_size": uncompressed_size,
                "local_header_offset": local_offset,
            }
        )
        cursor = end
    if cursor != len(central) or len(members) != total_records:
        raise Gate1Stop(
            f"ZIP central-directory member count mismatch: {len(members)} != {total_records}"
        )
    names = [str(row["name"]) for row in members]
    if len(names) != len(set(names)):
        raise Gate1Stop("ZIP central directory contains duplicate member names")
    return members


def inspect_zip_inventory(
    archive_size: int,
    read_range: RangeReader,
    *,
    suffix_window_bytes: int = 65557,
    maximum_central_directory_range_bytes: int = 2_000_000,
) -> dict[str, object]:
    if isinstance(archive_size, bool) or not isinstance(archive_size, int) or archive_size < 22:
        raise Gate1Stop("archive size is invalid for ZIP inventory")
    suffix_start = max(0, archive_size - int(suffix_window_bytes))
    suffix = read_range(suffix_start, archive_size - 1, "zip_suffix")
    if len(suffix) != archive_size - suffix_start:
        raise Gate1Stop("ZIP suffix range length drift")
    eocd = _find_eocd(archive_size, suffix_start, suffix)
    central_offset = int(eocd["central_offset"])
    central_size = int(eocd["central_size"])
    if central_size > int(maximum_central_directory_range_bytes):
        raise Gate1Stop("central directory exceeds prospectively bounded range cap")
    central_end = central_offset + central_size
    if central_offset >= suffix_start and central_end <= archive_size:
        rel_start = central_offset - suffix_start
        central = suffix[rel_start : rel_start + central_size]
        central_source = "suffix_slice"
    else:
        central = read_range(
            central_offset,
            central_offset + central_size - 1,
            "zip_central_directory",
        )
        central_source = "separate_range"
    if len(central) != central_size:
        raise Gate1Stop("central-directory range length differs from EOCD metadata")
    members = _parse_central_directory(
        central,
        int(eocd["total_records"]),
        central_offset,
    )
    result: dict[str, object] = {
        "archive_size": archive_size,
        "suffix_start": suffix_start,
        "suffix_bytes": len(suffix),
        "eocd_offset": int(eocd["eocd_offset"]),
        "zip_comment_size": int(eocd["comment_size"]),
        "central_directory_offset": central_offset,
        "central_directory_size": central_size,
        "central_directory_source": central_source,
        "central_directory_sha256": hashlib.sha256(central).hexdigest(),
        "member_count": len(members),
        "members": members,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def select_focal_member(csv_inventory: dict[str, object], contract: dict[str, object]) -> dict[str, object]:
    rules = contract["focal_selection"]
    members = csv_inventory.get("members")
    if not isinstance(members, list):
        raise Gate1Stop("CSVs inventory has no member list")
    suffix = str(rules["basename_suffix"])
    matches = [
        row
        for row in members
        if isinstance(row, dict)
        and isinstance(row.get("basename"), str)
        and str(row["basename"]).endswith(suffix)
    ]
    if len(matches) < int(rules["minimum_matching_members"]):
        raise Gate1Stop(f"no CSV member matched the frozen focal suffix {suffix!r}")
    parents = {str(row.get("parent")) for row in matches}
    if rules["require_all_matching_members_share_exactly_one_parent_directory"] and len(parents) != 1:
        raise Gate1Stop(
            f"detection-history suffix matched multiple parent directories: {sorted(parents)}"
        )
    ordered = sorted(matches, key=lambda row: (str(row["basename"]), str(row["name"])))
    selected = ordered[int(rules["select_index"])]
    return {
        "matching_member_count": len(ordered),
        "shared_parent": next(iter(parents)) if len(parents) == 1 else None,
        "matching_basenames": [str(row["basename"]) for row in ordered],
        "selected_member": {
            "name": selected["name"],
            "basename": selected["basename"],
            "parent": selected["parent"],
            "compressed_size": selected["compressed_size"],
            "uncompressed_size": selected["uncompressed_size"],
            "crc32": selected["crc32"],
            "compression_method": selected["compression_method"],
            "local_header_offset": selected["local_header_offset"],
        },
        "selection_rule": "lexicographic basename, then full member name; first member",
        "member_payload_bytes_opened": 0,
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class FrozenDryadRangeTransport:
    def __init__(self, contract: dict[str, object]) -> None:
        self.contract = contract
        self.opener = urllib.request.build_opener(_NoRedirect())
        self.presign_ledger: list[dict[str, object]] = []
        self.range_ledger: list[dict[str, object]] = []

    def _validate_public_stream(self, url: str, file_id: int) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != self.contract["transport"]["dryad_host"]:
            raise Gate1Stop("Dryad public-stream URL left frozen host")
        if parsed.path != f"/downloads/file_stream/{file_id}" or parsed.query or parsed.fragment:
            raise Gate1Stop("Dryad public-stream URL identity drift")

    def _validate_presigned_url(self, url: str) -> tuple[str, str]:
        parsed = urllib.parse.urlparse(url)
        transport = self.contract["transport"]
        if parsed.scheme != transport["presigned_final_scheme"]:
            raise Gate1Stop("Dryad presigned redirect was not HTTPS")
        hostname = parsed.hostname or ""
        if not hostname.endswith(str(transport["presigned_final_hostname_suffix"])):
            raise Gate1Stop(f"Dryad presigned redirect left frozen AWS hostname class: {hostname!r}")
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        missing = [key for key in transport["required_presigned_query_keys"] if key not in query]
        if missing:
            raise Gate1Stop(f"Dryad presigned redirect lacked required AWS query keys: {missing}")
        if not parsed.path or parsed.path == "/":
            raise Gate1Stop("Dryad presigned redirect lacked an object path")
        return hostname, hashlib.sha256(parsed.path.encode("utf-8")).hexdigest()

    def discover_presigned(self, role: str, archive: dict[str, object]) -> str:
        url = str(archive["public_stream_url"])
        file_id = int(archive["file_id"])
        self._validate_public_stream(url, file_id)
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": "bytes=0-0",
            },
        )
        ledger: dict[str, object] = {
            "archive_role": role,
            "requested_url": url,
            "status": None,
            "body_bytes_opened": 0,
            "presigned_host": None,
            "presigned_path_sha256": None,
        }
        self.presign_ledger.append(ledger)
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            ledger["status"] = int(exc.code)
            if int(exc.code) not in set(self.contract["transport"]["dryad_redirect_status_allowed"]):
                raise Gate1Stop(f"Dryad presign request returned HTTP {exc.code}; body was not opened") from exc
            location = exc.headers.get("Location") if exc.headers else None
            if not isinstance(location, str) or not location:
                raise Gate1Stop("Dryad redirect lacked Location header") from exc
            host, path_sha = self._validate_presigned_url(location)
            ledger["presigned_host"] = host
            ledger["presigned_path_sha256"] = path_sha
            return location
        except (OSError, urllib.error.URLError) as exc:
            raise Gate1Stop(f"Dryad presign transport unavailable: {exc}") from exc
        else:
            with response:
                ledger["status"] = int(getattr(response, "status", response.getcode()))
            raise Gate1Stop(
                f"Dryad public stream did not return a frozen redirect; HTTP {ledger['status']} body was not opened"
            )

    def read_range(
        self,
        role: str,
        presigned_url: str,
        archive_size: int,
        start: int,
        end: int,
        range_role: str,
    ) -> bytes:
        if start < 0 or end < start or end >= archive_size:
            raise Gate1Stop(f"invalid bounded S3 range {start}-{end} for {role}")
        request = urllib.request.Request(
            presigned_url,
            method="GET",
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        ledger: dict[str, object] = {
            "archive_role": role,
            "range_role": range_role,
            "start": start,
            "end": end,
            "status": None,
            "content_range": None,
            "bytes_opened": 0,
        }
        self.range_ledger.append(ledger)
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            ledger["status"] = int(exc.code)
            raise Gate1Stop(f"S3 range returned HTTP {exc.code}; body was not opened") from exc
        except (OSError, urllib.error.URLError) as exc:
            raise Gate1Stop(f"S3 range transport unavailable: {exc}") from exc
        with response:
            status = int(getattr(response, "status", response.getcode()))
            headers = {key.lower(): value for key, value in response.headers.items()}
            ledger["status"] = status
            ledger["content_range"] = headers.get("content-range")
            if status != int(self.contract["transport"]["range_status_required"]):
                raise Gate1Stop(f"S3 range returned HTTP {status}; body was not opened")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate1Stop("S3 range unexpectedly used content encoding")
            expected_content_range = f"bytes {start}-{end}/{archive_size}"
            if headers.get("content-range") != expected_content_range:
                raise Gate1Stop("S3 Content-Range did not preserve frozen archive size")
            final_url = response.geturl()
            if final_url != presigned_url:
                raise Gate1Stop("S3 range unexpectedly redirected; body was not opened")
            body = response.read(end - start + 2)
            ledger["bytes_opened"] = len(body)
        expected = end - start + 1
        if len(body) != expected:
            raise Gate1Stop(f"S3 range length {len(body)} != {expected}")
        return body


def evaluate_live(contract: dict[str, object], transport: FrozenDryadRangeTransport) -> dict[str, object]:
    inventories: dict[str, object] = {}
    for role in ("csvs", "raw_data"):
        archive = contract["archives"][role]
        presigned = transport.discover_presigned(role, archive)

        def reader(start: int, end: int, range_role: str, *, _r=role, _p=presigned, _a=archive) -> bytes:
            return transport.read_range(
                _r,
                _p,
                int(_a["size"]),
                start,
                end,
                range_role,
            )

        inventory = inspect_zip_inventory(
            int(archive["size"]),
            reader,
            suffix_window_bytes=int(contract["transport"]["suffix_window_bytes"]),
            maximum_central_directory_range_bytes=int(
                contract["transport"]["maximum_central_directory_range_bytes"]
            ),
        )
        inventory["expected_archive_sha256"] = archive["sha256"]
        inventories[role] = inventory

    focal = select_focal_member(inventories["csvs"], contract)
    if len(transport.presign_ledger) > int(contract["transport"]["maximum_presign_requests_total"]):
        raise Gate1Stop("presign request count exceeded frozen maximum")
    if len(transport.range_ledger) > int(contract["transport"]["maximum_s3_range_requests_total"]):
        raise Gate1Stop("S3 range request count exceeded frozen maximum")
    metadata_bytes = sum(int(row["bytes_opened"]) for row in transport.range_ledger)
    result: dict[str, object] = {
        "schema": "eog.columbia_shrubsteppe_endpoint3.gate1_zip_inventory.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": contract["terminal_statuses"]["pass"],
        "dryad_version_id": contract["dryad_version_id"],
        "inventories": inventories,
        "focal_selection": focal,
        "presign_requests": len(transport.presign_ledger),
        "s3_range_requests": len(transport.range_ledger),
        "archive_metadata_bytes_opened": metadata_bytes,
        "presign_ledger": transport.presign_ledger,
        "range_ledger": transport.range_ledger,
        "local_header_bytes_opened": 0,
        "archive_member_payload_bytes_opened": 0,
        "detection_history_payload_bytes_opened": 0,
        "camera_record_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "next_gate": "freeze response-independent member identities for site/coordinate/effort/covariate extraction; selected focal payload remains unopened",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    transport_factory=FrozenDryadRangeTransport,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    pass_cert = json.loads((HERE / "gate0_metadata_pass_certificate.json").read_text(encoding="utf-8"))
    if pass_cert.get("status") != "gate0_metadata_ready":
        raise RuntimeError("Gate0 PASS certificate is not ready")
    if pass_cert.get("authoritative_execution", {}).get("result_fingerprint") != contract["gate0_result_fingerprint"]:
        raise RuntimeError("Gate0 result fingerprint drift before Gate1")
    transport = transport_factory(contract)
    try:
        result = evaluate_live(contract, transport)
    except Gate1Stop as exc:
        result = {
            "schema": "eog.columbia_shrubsteppe_endpoint3.gate1_zip_inventory.v1",
            "attempt_id": contract["attempt_id"],
            "issue": contract["issue"],
            "status": contract["terminal_statuses"]["stop"],
            "reason": str(exc),
            "dryad_version_id": contract["dryad_version_id"],
            "presign_requests": len(transport.presign_ledger),
            "s3_range_requests": len(transport.range_ledger),
            "archive_metadata_bytes_opened": sum(
                int(row.get("bytes_opened", 0)) for row in transport.range_ledger
            ),
            "presign_ledger": transport.presign_ledger,
            "range_ledger": transport.range_ledger,
            "local_header_bytes_opened": 0,
            "archive_member_payload_bytes_opened": 0,
            "detection_history_payload_bytes_opened": 0,
            "camera_record_payload_bytes_opened": 0,
            "response_rows_opened": 0,
            "response_values_opened": False,
            "model_fits": 0,
            "heldout_scores": 0,
            "counts_as_predictive_evidence": False,
            "next_gate": "none; do not repair transport, archive interpretation or focal selection after this terminal STOP",
        }
        result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    run()
