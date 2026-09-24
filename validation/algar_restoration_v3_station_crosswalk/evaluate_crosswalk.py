from __future__ import annotations

import csv
from io import StringIO
import hashlib
import json
import re
from pathlib import Path
from typing import Sequence

from eog.v2.dryad_metadata import (
    resolve_dryad_file_identity,
    verify_dryad_file_bytes,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "crosswalk_contract.json"
DEFAULT_OUTPUT = HERE / "station_crosswalk_result.json"


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


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _dryad_identity(contract: dict[str, object]):
    row = contract["safe_dryad_file"]
    return resolve_dryad_file_identity(
        {
            "path": row["path"],
            "size": row["size"],
            "mimeType": "text/csv",
            "status": "copied",
            "digestType": row["digest_type"],
            "digest": row["digest"],
            "_links": {
                "self": {"href": row["self_href"]},
                "stash:version": {
                    "href": f"/api/v2/versions/{row['version_id']}"
                },
                "stash:download": {"href": row["download_href"]},
            },
        },
        expected_version_id=int(row["version_id"]),
    )


def evaluate_station_crosswalk(
    contract: dict[str, object],
    raw_station: bytes,
    locked_node_ids: Sequence[str],
) -> dict[str, object]:
    """Audit one safe Dryad station table against the locked Algar node registry."""

    expected_locked = int(
        contract["locked_registry_source"]["expected_locked_node_count"]
    )
    locked = tuple(sorted(str(value).strip() for value in locked_node_ids))
    if len(locked) != expected_locked or len(set(locked)) != len(locked):
        raise ValueError("locked node universe does not match frozen count/uniqueness")

    identity = _dryad_identity(contract)
    derived_sha256 = verify_dryad_file_bytes(identity, raw_station)

    try:
        text = raw_station.decode(str(contract["parser_policy"]["csv_encoding"]))
    except UnicodeDecodeError as exc:
        raise ValueError("safe station file is not valid frozen encoding") from exc

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("safe station file has no CSV header")
    header = tuple(str(value).strip() for value in reader.fieldnames)
    if not header or any(not value for value in header):
        raise ValueError("safe station file has blank header fields")
    rows = list(reader)
    if not rows:
        raise ValueError("safe station file has no data rows")

    policy = contract["parser_policy"]
    forbidden_tokens = tuple(
        _normalized(value) for value in policy["forbidden_header_tokens"]
    )
    forbidden_columns = []
    for name in header:
        normalized = _normalized(name)
        if any(token and token in normalized for token in forbidden_tokens):
            forbidden_columns.append(name)

    candidate_tokens = tuple(
        _normalized(value) for value in policy["candidate_identifier_name_tokens"]
    )
    coordinate_tokens = tuple(
        _normalized(value) for value in policy["coordinate_name_tokens"]
    )

    identifier_columns = [
        name
        for name in header
        if any(token and token in _normalized(name) for token in candidate_tokens)
    ]
    coordinate_columns = [
        name
        for name in header
        if any(token and token in _normalized(name) for token in coordinate_tokens)
    ]

    locked_set = set(locked)
    column_audits = []
    join_ready_columns = []
    for column in identifier_columns:
        values = tuple(
            sorted(
                {
                    str(row.get(column) or "").strip()
                    for row in rows
                    if str(row.get(column) or "").strip()
                }
            )
        )
        value_set = set(values)
        overlap = tuple(sorted(value_set & locked_set))
        missing_locked = tuple(sorted(locked_set - value_set))
        extra_values = tuple(sorted(value_set - locked_set))
        complete = not missing_locked
        if complete:
            join_ready_columns.append(column)
        column_audits.append(
            {
                "column": column,
                "distinct_value_count": len(values),
                "values": list(values),
                "overlap_locked_count": len(overlap),
                "overlap_locked_ids": list(overlap),
                "missing_locked_ids": list(missing_locked),
                "extra_values": list(extra_values),
                "covers_all_locked_nodes": complete,
            }
        )

    forbidden_absent = not forbidden_columns
    join_ready = bool(join_ready_columns) and forbidden_absent

    result = {
        "schema": "eog.algar_restoration_v3_station_crosswalk.result.v1",
        "status": (
            "station_crosswalk_ready_response_blind"
            if join_ready
            else "stop_response_blind_station_crosswalk"
        ),
        "safe_file": {
            "path": identity.path,
            "file_id": identity.file_id,
            "version_id": identity.version_id,
            "size": identity.size,
            "repository_digest_type": identity.digest_type,
            "repository_digest": identity.digest,
            "derived_sha256": derived_sha256,
            "identity_fingerprint": identity.fingerprint,
        },
        "header": list(header),
        "row_count": len(rows),
        "candidate_identifier_columns": identifier_columns,
        "coordinate_columns": coordinate_columns,
        "forbidden_biological_columns": forbidden_columns,
        "join_ready_columns": join_ready_columns,
        "locked_node_count": len(locked),
        "column_audits": column_audits,
        "file_payload_requests": 1,
        "file_payload_bytes_opened": len(raw_station),
        "response_bearing_file_requests": 0,
        "response_bearing_file_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "focal_species": contract["response_firewall"]["focal_species"],
        "focal_taxon_change_allowed": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }
    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    return result


if __name__ == "__main__":
    raise SystemExit(
        "workflow must provide the exact Dryad safe file and locked node IDs"
    )
