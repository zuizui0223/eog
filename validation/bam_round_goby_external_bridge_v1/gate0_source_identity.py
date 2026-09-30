"""Response-blind Gate0 for the round-goby external BAM bridge.

This gate may retrieve Zenodo record metadata only. It must not download any file
content. It verifies record identity and the frozen file roster/checksums from the
source protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "source_protocol_v1.json"
ZENODO_API = "https://zenodo.org/api/records/19621892"


class Gate0Stop(RuntimeError):
    pass


@dataclass(frozen=True)
class FrozenFile:
    name: str
    md5: str


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_protocol(path: Path = PROTOCOL) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "frozen_before_local_data_payload_access":
        raise Gate0Stop("source protocol is not frozen at the expected boundary")
    return payload


def frozen_files(protocol: dict[str, Any]) -> tuple[FrozenFile, ...]:
    rows = protocol["source"]["files_seen_from_metadata"]
    out = tuple(
        FrozenFile(name=str(row["name"]), md5=str(row["md5"]).lower())
        for row in rows
    )
    if len({row.name for row in out}) != len(out):
        raise Gate0Stop("frozen file roster contains duplicate names")
    return tuple(sorted(out, key=lambda row: row.name))


def _normalize_checksum(value: object) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("md5:"):
        text = text[4:]
    return text


def evaluate_metadata(
    metadata: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    expected_record = int(protocol["source"]["zenodo_record_id"])
    actual_record = int(metadata.get("id", -1))
    if actual_record != expected_record:
        raise Gate0Stop(
            f"record id mismatch: expected {expected_record}, got {actual_record}"
        )

    expected_title = str(protocol["source"]["title"])
    actual_title = str(metadata.get("metadata", {}).get("title", ""))
    if actual_title != expected_title:
        raise Gate0Stop("Zenodo title mismatch")

    expected = frozen_files(protocol)
    actual_files = metadata.get("files")
    if not isinstance(actual_files, list):
        raise Gate0Stop("Zenodo metadata does not expose a file list")

    actual_by_name: dict[str, dict[str, Any]] = {}
    for row in actual_files:
        if not isinstance(row, dict):
            raise Gate0Stop("Zenodo file entry is not an object")
        key = str(row.get("key", ""))
        if not key:
            raise Gate0Stop("Zenodo file entry missing key")
        if key in actual_by_name:
            raise Gate0Stop(f"duplicate live file key: {key}")
        actual_by_name[key] = row

    expected_names = {row.name for row in expected}
    actual_names = set(actual_by_name)
    if actual_names != expected_names:
        raise Gate0Stop(
            "live file roster mismatch: "
            f"missing={sorted(expected_names-actual_names)}, "
            f"unexpected={sorted(actual_names-expected_names)}"
        )

    verified = []
    for row in expected:
        live = actual_by_name[row.name]
        checksum = _normalize_checksum(live.get("checksum"))
        if checksum != row.md5:
            raise Gate0Stop(
                f"checksum mismatch for {row.name}: expected {row.md5}, got {checksum}"
            )
        size = live.get("size")
        if not isinstance(size, int) or size <= 0:
            raise Gate0Stop(f"invalid live size for {row.name}")
        verified.append(
            {
                "name": row.name,
                "md5": row.md5,
                "size_bytes": size,
            }
        )

    result: dict[str, Any] = {
        "schema": "eog.bam_round_goby_external_bridge.gate0_source_identity.v1",
        "status": "source_identity_ready",
        "record_id": actual_record,
        "title": actual_title,
        "file_count": len(verified),
        "files": verified,
        "response_payload_bytes_opened": 0,
        "file_payload_requests": 0,
        "metadata_only": True,
        "next_authorized_stage": "Gate1 README/header schema only after Gate0 certificate is committed",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def fetch_live_metadata(url: str = ZENODO_API) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "EOG-Round-Goby-BAM-Bridge-Gate0/1.0",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urlopen(request, timeout=60) as response:
        if int(response.status) != 200:
            raise Gate0Stop(f"Zenodo metadata HTTP status {response.status}")
        body = response.read()
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise Gate0Stop("Zenodo metadata response is not a JSON object")
    return payload


def main() -> int:
    protocol = load_protocol()
    metadata = fetch_live_metadata()
    result = evaluate_metadata(metadata, protocol)
    output = HERE / "gate0_source_identity_certificate.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
