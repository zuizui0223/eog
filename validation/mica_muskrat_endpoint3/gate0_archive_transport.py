from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import urllib.error
import urllib.request
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_archive_transport_certificate.json"
USER_AGENT = "EOG-MICA-Muskrat-Endpoint3-Gate0/1.0"
RangeReader = Callable[[int, int, str], bytes]


class Gate0Stop(RuntimeError):
    """A terminal response-blind source/transport/container STOP."""


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
        raise Gate0Stop("ZIP member name is empty or uses an unsafe separator")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ":" in path.parts[0]:
        raise Gate0Stop(f"unsafe ZIP member name: {value!r}")
    return value


def _overlaps(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]


def inspect_zip_metadata(archive_size: int, read_range: RangeReader) -> dict[str, object]:
    """Inspect a classic zero-comment ZIP without opening any member payload."""
    if isinstance(archive_size, bool) or not isinstance(archive_size, int):
        raise TypeError("archive_size must be int")
    if archive_size < 22:
        raise Gate0Stop("archive is too small to contain a ZIP EOCD")

    eocd_offset = archive_size - 22
    eocd = read_range(eocd_offset, archive_size - 1, "zip_eocd_zero_comment")
    if len(eocd) != 22 or eocd[:4] != b"PK\x05\x06":
        raise Gate0Stop(
            "final 22 bytes are not a zero-comment ZIP EOCD; backwards scanning is forbidden"
        )
    fields = struct.unpack("<4s4H2IH", eocd)
    disk_number, central_disk, disk_records, total_records = fields[1:5]
    central_size, central_offset, comment_size = fields[5:8]
    if comment_size != 0:
        raise Gate0Stop("ZIP comments are outside the frozen bounded metadata gate")
    if disk_number != 0 or central_disk != 0 or disk_records != total_records:
        raise Gate0Stop("multi-disk ZIP archives are outside the frozen gate")
    if total_records <= 0:
        raise Gate0Stop("ZIP central directory contains no members")
    if 0xFFFF in (disk_records, total_records) or 0xFFFFFFFF in (central_size, central_offset):
        raise Gate0Stop("ZIP64 discovery is outside the frozen gate")
    if central_size <= 0 or central_offset + central_size != eocd_offset:
        raise Gate0Stop("central directory is not exactly adjacent to the EOCD")

    central = read_range(
        central_offset,
        central_offset + central_size - 1,
        "zip_central_directory",
    )
    if len(central) != central_size:
        raise Gate0Stop("central-directory range length differs from the EOCD")

    members: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(central):
        if cursor + 46 > len(central):
            raise Gate0Stop("truncated ZIP central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", central, cursor)
        if values[0] != b"PK\x01\x02":
            raise Gate0Stop(f"invalid central-directory signature at byte {cursor}")
        flags = values[3]
        method = values[4]
        crc32 = values[7]
        compressed_size = values[8]
        uncompressed_size = values[9]
        name_size, extra_size, member_comment_size = values[10:13]
        disk_start = values[13]
        local_offset = values[16]
        if flags & 0x1:
            raise Gate0Stop("encrypted ZIP members are outside the frozen gate")
        if disk_start != 0:
            raise Gate0Stop("member starts on a nonzero ZIP disk")
        if 0xFFFFFFFF in (compressed_size, uncompressed_size, local_offset):
            raise Gate0Stop("ZIP64 member metadata are outside the frozen gate")
        end = cursor + 46 + name_size + extra_size + member_comment_size
        if name_size <= 0 or end > len(central):
            raise Gate0Stop("central-directory variable fields are invalid")
        name_bytes = central[cursor + 46 : cursor + 46 + name_size]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = _safe_member_name(name_bytes.decode(encoding))
        members.append(
            {
                "name": name,
                "basename": PurePosixPath(name).name,
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
        raise Gate0Stop(
            f"central-directory member count mismatch: {len(members)} != {total_records}"
        )
    names = [str(member["name"]) for member in members]
    if len(set(names)) != len(names):
        raise Gate0Stop("ZIP central directory contains duplicate member names")

    for member in members:
        offset = int(member["local_header_offset"])
        if offset < 0 or offset + 30 > central_offset:
            raise Gate0Stop(f"local header offset outside member area: {member['name']}")
        fixed = read_range(offset, offset + 29, f"local_header:{member['name']}")
        if len(fixed) != 30:
            raise Gate0Stop(f"truncated local header: {member['name']}")
        local = struct.unpack("<4s5H3I2H", fixed)
        if local[0] != b"PK\x03\x04":
            raise Gate0Stop(f"invalid local header signature: {member['name']}")
        local_flags, local_method = local[2], local[3]
        name_size, extra_size = local[9], local[10]
        if name_size <= 0:
            raise Gate0Stop(f"empty local member name: {member['name']}")
        variable = read_range(
            offset + 30,
            offset + 30 + name_size + extra_size - 1,
            f"local_name_extra:{member['name']}",
        )
        encoding = "utf-8" if int(member["flags"]) & 0x800 else "cp437"
        local_name = variable[:name_size].decode(encoding)
        if local_name != member["name"]:
            raise Gate0Stop(f"local/central member name mismatch: {member['name']}")
        if local_flags != member["flags"] or local_method != member["compression_method"]:
            raise Gate0Stop(f"local/central ZIP flags or method mismatch: {member['name']}")
        payload_start = offset + 30 + name_size + extra_size
        compressed_size = int(member["compressed_size"])
        payload_end = payload_start + compressed_size - 1
        if compressed_size and payload_end >= central_offset:
            raise Gate0Stop(f"member payload overlaps central directory: {member['name']}")
        member["local_metadata_start"] = offset
        member["local_metadata_end"] = payload_start - 1
        member["payload_start"] = payload_start
        member["payload_end"] = payload_end if compressed_size else None

    payload_intervals = sorted(
        (int(member["payload_start"]), int(member["payload_end"]))
        for member in members
        if member["payload_end"] is not None
    )
    for left, right in pairwise(payload_intervals):
        if _overlaps(left, right):
            raise Gate0Stop("ZIP member payload intervals overlap")

    result: dict[str, object] = {
        "archive_size": archive_size,
        "central_directory_offset": central_offset,
        "central_directory_size": central_size,
        "central_directory_sha256": hashlib.sha256(central).hexdigest(),
        "eocd_offset": eocd_offset,
        "member_count": len(members),
        "members": members,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def select_frozen_members(
    inventory: dict[str, object], rules: dict[str, object]
) -> dict[str, dict[str, object]]:
    members = inventory.get("members")
    if not isinstance(members, list):
        raise Gate0Stop("ZIP inventory has no member list")
    selected: dict[str, dict[str, object]] = {}
    for role, raw_rule in rules.items():
        if not role.endswith("_member") or not isinstance(raw_rule, dict):
            continue
        basename = raw_rule.get("exact_unique_basename")
        required_count = raw_rule.get("required_count")
        if not isinstance(basename, str) or required_count != 1:
            raise Gate0Stop(f"invalid frozen member rule for {role}")
        matches = [m for m in members if isinstance(m, dict) and m.get("basename") == basename]
        if len(matches) != 1:
            raise Gate0Stop(
                f"frozen member identity {role} expected exactly one basename {basename!r}, observed {len(matches)}"
            )
        selected[role] = matches[0]
    if len({str(v["name"]) for v in selected.values()}) != len(selected):
        raise Gate0Stop("two frozen roles resolve to the same ZIP member")
    return selected


class StrictIptTransport:
    def __init__(self, url: str, allowed_hosts: tuple[str, ...], media_types: tuple[str, ...]) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValueError("archive URL must be HTTPS on a frozen allowed host")
        self.url = url
        self.allowed_hosts = allowed_hosts
        self.media_types = tuple(value.casefold() for value in media_types)
        self.archive_size: int | None = None
        self.head_metadata: dict[str, object] | None = None
        self.range_ledger: list[dict[str, object]] = []

    def head(self) -> dict[str, object]:
        request = urllib.request.Request(
            self.url,
            method="HEAD",
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        )
        try:
            context = urllib.request.urlopen(request, timeout=90)
        except (OSError, urllib.error.URLError) as exc:
            raise Gate0Stop(f"HEAD transport unavailable: {exc}") from exc
        with context as response:
            status = getattr(response, "status", None) or response.getcode()
            final = urlparse(response.geturl())
            headers = {key.lower(): value for key, value in response.headers.items()}
            if status < 200 or status >= 400:
                raise Gate0Stop(f"HEAD returned HTTP {status}")
            if final.scheme != "https" or final.hostname not in self.allowed_hosts:
                raise Gate0Stop(f"HEAD left frozen host set: {final.hostname!r}")
            content_length = headers.get("content-length", "")
            if not re.fullmatch(r"[1-9][0-9]*", content_length):
                raise Gate0Stop("HEAD did not provide a positive Content-Length")
            content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
            if content_type and content_type not in self.media_types:
                raise Gate0Stop(f"HEAD content type outside frozen archive media types: {content_type!r}")
            self.archive_size = int(content_length)
            self.head_metadata = {
                "status": status,
                "final_url": response.geturl(),
                "final_host": final.hostname,
                "content_length": self.archive_size,
                "content_type": content_type,
                "etag": headers.get("etag"),
                "last_modified": headers.get("last-modified"),
                "body_bytes_opened": 0,
            }
        return dict(self.head_metadata)

    def read_range(self, start: int, end: int, role: str) -> bytes:
        if self.archive_size is None:
            raise RuntimeError("HEAD must pass before range reads")
        if start < 0 or end < start or end >= self.archive_size:
            raise Gate0Stop(f"invalid bounded range {start}-{end}")
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        try:
            context = urllib.request.urlopen(request, timeout=90)
        except (OSError, urllib.error.URLError) as exc:
            raise Gate0Stop(f"bounded range transport unavailable: {exc}") from exc
        with context as response:
            status = getattr(response, "status", None) or response.getcode()
            headers = {key.lower(): value for key, value in response.headers.items()}
            final = urlparse(response.geturl())
            ledger = {
                "role": role,
                "start": start,
                "end": end,
                "status": status,
                "content_range": headers.get("content-range"),
                "final_host": final.hostname,
                "bytes_opened": 0,
            }
            self.range_ledger.append(ledger)
            if status != 206:
                raise Gate0Stop(
                    f"range request returned HTTP {status}; response body was not opened"
                )
            match = re.fullmatch(
                rf"bytes {start}-{end}/(\d+)", headers.get("content-range", "")
            )
            if match is None or int(match.group(1)) != self.archive_size:
                raise Gate0Stop("Content-Range does not preserve frozen HEAD archive size")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate0Stop("range response unexpectedly applied content encoding")
            if final.scheme != "https" or final.hostname not in self.allowed_hosts:
                raise Gate0Stop(f"range request left frozen host set: {final.hostname!r}")
            body = response.read(end - start + 2)
            ledger["bytes_opened"] = len(body)
        expected = end - start + 1
        if len(body) != expected:
            raise Gate0Stop(f"range response length {len(body)} != {expected}")
        return body


def run(contract_path: Path = DEFAULT_CONTRACT, output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = contract["source"]
    transport = StrictIptTransport(
        str(source["archive_url"]),
        tuple(source["allowed_final_hosts"]),
        tuple(source["archive_media_types"]),
    )
    base = {
        "schema": "eog.mica_muskrat_endpoint3.gate0_archive_transport.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "architecture_selection_boundary_commit": contract[
            "architecture_selection_boundary_commit"
        ],
        "archive_url": source["archive_url"],
        "deployment_member_payload_bytes_opened": 0,
        "observation_member_header_bytes_opened": 0,
        "observation_member_payload_bytes_opened": 0,
        "media_member_payload_bytes_opened": 0,
        "muskrat_response_rows_opened": 0,
        "muskrat_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        head = transport.head()
        if transport.archive_size is None:
            raise RuntimeError("HEAD passed without archive size")
        inventory = inspect_zip_metadata(transport.archive_size, transport.read_range)
        payload_intervals = [
            (int(m["payload_start"]), int(m["payload_end"]))
            for m in inventory["members"]
            if isinstance(m, dict) and m.get("payload_end") is not None
        ]
        for request in transport.range_ledger:
            interval = (int(request["start"]), int(request["end"]))
            if any(_overlaps(interval, payload) for payload in payload_intervals):
                raise Gate0Stop("Gate0 metadata request overlapped a ZIP member payload")
        selected = select_frozen_members(
            inventory, contract["frozen_member_identity_rules"]
        )
        result = {
            **base,
            "status": "gate0_pass_archive_metadata",
            "head_metadata": head,
            "archive_metadata_requests": len(transport.range_ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes_opened"]) for row in transport.range_ledger
            ),
            "range_ledger": transport.range_ledger,
            "inventory": inventory,
            "selected_members": selected,
            "decision": "PASS: exact deployment/observation/media/datapackage member identities are frozen without opening any member payload; deployment payload may be separately contracted next",
        }
    except Gate0Stop as exc:
        result = {
            **base,
            "status": "stop_pre_response_source_transport_or_container",
            "head_metadata": transport.head_metadata,
            "archive_metadata_requests": len(transport.range_ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes_opened"]) for row in transport.range_ledger
            ),
            "range_ledger": transport.range_ledger,
            "reason": str(exc),
            "decision": "STOP: do not full-download, scan, repair member identities, or open biological response; this attempt supplies no predictive evidence",
        }
    result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.contract, args.output)
    print(json.dumps({
        "status": result["status"],
        "fingerprint": result["fingerprint"],
        "archive_metadata_bytes_opened": result["archive_metadata_bytes_opened"],
        "observation_member_payload_bytes_opened": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
