from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict
from io import StringIO
import hashlib
import json
from pathlib import Path
from typing import Callable

from eog.v2.http_range_transport import (
    HttpRangeTransportError,
    StrictHttpRangeTransport,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)
from eog.v2.zip_safe_member import (
    ZipSafeMemberError,
    extract_safe_member,
    inspect_classic_zip,
    require_unique_basenames,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_screen_contract.json"
DEFAULT_OUTPUT = HERE / "prelock_transport_screen_result.json"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _safe_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _parse_deployments(payload: bytes) -> dict[str, object]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("deployments.csv is not valid UTF-8") from exc

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("deployments.csv has no header")

    required = {
        "deploymentID",
        "latitude",
        "longitude",
        "deploymentStart",
        "deploymentEnd",
    }
    missing = sorted(required - set(reader.fieldnames))
    if missing:
        raise ValueError(f"deployments.csv missing required columns: {missing!r}")

    rows = list(reader)
    if not rows:
        raise ValueError("deployments.csv has no rows")

    deployment_ids = []
    coordinates = []
    location_ids = []
    starts = []
    ends = []
    invalid_coordinate_rows = 0
    for row_number, row in enumerate(rows, start=2):
        deployment_id = _safe_text(row.get("deploymentID"))
        if not deployment_id:
            raise ValueError(f"deploymentID is empty at row {row_number}")
        deployment_ids.append(deployment_id)

        raw_lat = _safe_text(row.get("latitude"))
        raw_lon = _safe_text(row.get("longitude"))
        if raw_lat and raw_lon:
            try:
                lat = float(raw_lat)
                lon = float(raw_lon)
            except ValueError as exc:
                raise ValueError(
                    f"non-numeric coordinate at deployment row {row_number}"
                ) from exc
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(
                    f"coordinate outside geographic bounds at deployment row {row_number}"
                )
            coordinates.append((lat, lon))
        else:
            invalid_coordinate_rows += 1

        location_id = _safe_text(row.get("locationID"))
        if location_id:
            location_ids.append(location_id)

        start = _safe_text(row.get("deploymentStart"))
        end = _safe_text(row.get("deploymentEnd"))
        if not start or not end:
            raise ValueError(f"deployment dates are incomplete at row {row_number}")
        starts.append(start)
        ends.append(end)

    if len(deployment_ids) != len(set(deployment_ids)):
        raise ValueError("deploymentID values are not unique")

    coordinate_counts = Counter(coordinates)
    location_counts = Counter(location_ids)
    return {
        "header": list(reader.fieldnames),
        "deployment_count": len(rows),
        "valid_coordinate_rows": len(coordinates),
        "missing_coordinate_rows": invalid_coordinate_rows,
        "unique_exact_coordinate_count": len(coordinate_counts),
        "exact_coordinates_repeated_across_deployments": sum(
            count > 1 for count in coordinate_counts.values()
        ),
        "nonempty_location_id_rows": len(location_ids),
        "unique_nonempty_location_id_count": len(location_counts),
        "location_ids_repeated_across_deployments": sum(
            count > 1 for count in location_counts.values()
        ),
        "deployment_start_min_lexical": min(starts),
        "deployment_start_max_lexical": max(starts),
        "deployment_end_min_lexical": min(ends),
        "deployment_end_max_lexical": max(ends),
    }


def _size_bind(transport) -> tuple[int, list[dict[str, object]]]:
    attempts: list[dict[str, object]] = []
    try:
        size = transport.discover_size_by_head()
        attempts.append({"route": "HEAD", "status": "qualified", "reason": None})
        return size, attempts
    except HttpRangeTransportError as exc:
        attempts.append({"route": "HEAD", "status": "failed", "reason": str(exc)})

    try:
        size = transport.discover_size_by_range_probe()
        attempts.append(
            {"route": "Range bytes=0-0", "status": "qualified", "reason": None}
        )
        return size, attempts
    except HttpRangeTransportError as exc:
        attempts.append(
            {"route": "Range bytes=0-0", "status": "failed", "reason": str(exc)}
        )
        raise HttpRangeTransportError(
            "all prospectively declared archive-size routes failed"
        ) from exc


def screen_source(
    source: dict[str, object],
    contract: dict[str, object],
    *,
    transport_factory: Callable[..., object] = StrictHttpRangeTransport,
) -> dict[str, object]:
    archive_bounds = contract["archive_bounds"]
    safe_config = contract["safe_member"]
    response_config = contract["response_member"]

    base = {
        "source_id": source["source_id"],
        "gbif_dataset_key": source["gbif_dataset_key"],
        "doi": source["doi"],
        "title": source["title"],
        "archive_url": source["archive_url"],
        "candidate_locked": False,
        "focal_species_selected": False,
        "response_member_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }

    transport = transport_factory(
        str(source["archive_url"]),
        tuple(source["allowed_hosts"]),
        int(archive_bounds["maximum_archive_size_bytes"]),
    )

    size_attempts: list[dict[str, object]] = []
    try:
        archive_size, size_attempts = _size_bind(transport)
        inventory = inspect_classic_zip(
            archive_size,
            transport.read_range,
            maximum_central_directory_bytes=int(
                archive_bounds["maximum_central_directory_bytes"]
            ),
        )
        members = require_unique_basenames(
            inventory,
            (
                str(safe_config["basename"]),
                str(response_config["basename"]),
            ),
        )
        safe_member = members[str(safe_config["basename"])]
        response_member = members[str(response_config["basename"])]
        safe_payload = extract_safe_member(
            inventory,
            safe_member,
            transport.read_range,
            maximum_compressed_bytes=int(safe_config["maximum_compressed_bytes"]),
            maximum_uncompressed_bytes=int(
                safe_config["maximum_uncompressed_bytes"]
            ),
        )
        deployment_audit = _parse_deployments(safe_payload.payload)

        route = TransportRouteEvidence(
            route_id=f"{source['source_id']}::mixed_archive_safe_member",
            route_type="mixed_archive_bounded_inventory",
            qualified=True,
            safe_payload_bytes_opened=(
                inventory.metadata_bytes_opened
                + safe_payload.local_header_bytes_opened
                + safe_payload.compressed_payload_bytes_opened
            ),
            response_payload_bytes_opened=0,
            reason=(
                "archive inventory passed and deployments.csv was extracted with "
                "CRC/SHA verification while observations.csv remained unopened"
            ),
            transport_detail=json.dumps(size_attempts, sort_keys=True),
        )
        qualification = evaluate_source_transport_qualification((route,))
        result = {
            **base,
            "status": "transport_qualified_prelock",
            "archive_size": archive_size,
            "size_discovery_attempts": size_attempts,
            "inventory": {
                "fingerprint": inventory.fingerprint,
                "central_directory_sha256": inventory.central_directory_sha256,
                "member_count": len(inventory.members),
                "metadata_bytes_opened": inventory.metadata_bytes_opened,
            },
            "safe_member": {
                "name": safe_member.name,
                "compressed_size": safe_member.compressed_size,
                "uncompressed_size": safe_member.uncompressed_size,
                "crc32": safe_member.crc32,
                "member_fingerprint": safe_member.fingerprint,
                "payload_sha256": safe_payload.payload_sha256,
                "payload_fingerprint": safe_payload.fingerprint,
                "local_header_bytes_opened": safe_payload.local_header_bytes_opened,
                "compressed_payload_bytes_opened": (
                    safe_payload.compressed_payload_bytes_opened
                ),
            },
            "response_member": {
                "name": response_member.name,
                "compressed_size": response_member.compressed_size,
                "uncompressed_size": response_member.uncompressed_size,
                "crc32": response_member.crc32,
                "member_fingerprint": response_member.fingerprint,
                "payload_bytes_opened": 0,
            },
            "deployment_audit": deployment_audit,
            "transport_qualification": asdict(qualification),
        }
    except (
        HttpRangeTransportError,
        ZipSafeMemberError,
        ValueError,
        TypeError,
    ) as exc:
        route = TransportRouteEvidence(
            route_id=f"{source['source_id']}::mixed_archive_safe_member",
            route_type="mixed_archive_bounded_inventory",
            qualified=False,
            safe_payload_bytes_opened=0,
            response_payload_bytes_opened=0,
            reason=str(exc),
            transport_detail=json.dumps(size_attempts, sort_keys=True),
        )
        qualification = evaluate_source_transport_qualification((route,))
        result = {
            **base,
            "status": "transport_unqualified_prelock",
            "reason": str(exc),
            "size_discovery_attempts": size_attempts,
            "transport_qualification": asdict(qualification),
        }

    result["http_ledger"] = [
        asdict(row) for row in getattr(transport, "ledger", ())
    ]
    result["http_bytes_opened"] = sum(
        int(row["bytes_opened"]) for row in result["http_ledger"]
    )
    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    return result


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    transport_factory: Callable[..., object] = StrictHttpRangeTransport,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    results = [
        screen_source(source, contract, transport_factory=transport_factory)
        for source in contract["sources"]
    ]

    selected = [
        result["source_id"]
        for result in results
        if result["status"] == "transport_qualified_prelock"
    ]
    output = {
        "schema": "eog.inbo_camtrap_prelock_transport_screen_result.v1",
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "candidate_locked": False,
        "focal_species_selected": False,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "qualified_source_ids": selected,
        "results": results,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }
    output["fingerprint"] = canonical_sha256(
        {key: value for key, value in output.items() if key != "fingerprint"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "qualified_source_ids": result["qualified_source_ids"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
