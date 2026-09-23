from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validation.forest_first_endpoint3.gate0_zip_inventory import (
    Gate0Stop,
    StrictIptRangeTransport,
    inspect_zip_inventory,
    select_required_members,
)

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_selection_contract.json"
DEFAULT_GATE0 = HERE / "gate0_metadata_certificate.json"
DEFAULT_OUTPUT = HERE / "gate1_zip_inventory_certificate.json"


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


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    gate0_path: Path = DEFAULT_GATE0,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    transport_factory=StrictIptRangeTransport,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    gate0 = json.loads(gate0_path.read_text(encoding="utf-8"))
    gate = contract["gate1_archive_inventory"]
    source = contract["source_identity"]

    base: dict[str, object] = {
        "schema": "eog.endure_dune_aphid_selective_promotion.gate1_zip_inventory.v1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "gate0_fingerprint": gate0.get("fingerprint"),
        "status": None,
        "range_requests": 0,
        "archive_metadata_bytes_opened": 0,
        "local_header_bytes_opened": 0,
        "member_payload_bytes_opened": 0,
        "event_member_bytes_opened": 0,
        "occurrence_member_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }

    if gate0.get("status") != "gate0_metadata_ready_for_zip_inventory":
        result = {
            **base,
            "status": "not_run_gate0_not_ready",
            "reason": f"Gate0 status was {gate0.get('status')!r}",
            "next_gate": "none",
        }
        result["fingerprint"] = canonical_sha256(
            {k: v for k, v in result.items() if k != "fingerprint"}
        )
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result

    transport = transport_factory(
        str(source["archive_url"]),
        tuple(source["allowed_archive_hosts"]),
        int(gate["maximum_archive_size_bytes"]),
    )
    try:
        archive_size = transport.probe_size()
        inventory = inspect_zip_inventory(
            archive_size,
            transport.read_range,
            maximum_central_directory_bytes=int(
                gate["maximum_central_directory_bytes"]
            ),
        )
        required = select_required_members(
            inventory,
            list(gate["required_unique_basenames"]),
        )
        result = {
            **base,
            "status": "gate1_zip_inventory_ready_for_meta_schema_freeze",
            "archive_size": archive_size,
            "central_directory_sha256": inventory["central_directory_sha256"],
            "member_count": inventory["member_count"],
            "members": inventory["members"],
            "required_members": required,
            "next_gate": (
                "freeze exact meta.xml member identity and open only meta.xml "
                "under a new bounded member gate; occurrence member remains unopened"
            ),
        }
    except (Gate0Stop, ValueError, TypeError) as exc:
        result = {
            **base,
            "status": "stop_pre_response_zip_transport_or_inventory",
            "reason": str(exc),
            "next_gate": "none; terminal for this attempt and no repair/rerun",
        }

    ledger = list(getattr(transport, "range_ledger", []))
    result["range_requests"] = len(ledger)
    result["archive_metadata_bytes_opened"] = sum(
        int(row.get("bytes_opened", 0)) for row in ledger
    )
    result["range_ledger"] = ledger
    result["fingerprint"] = canonical_sha256(
        {k: v for k, v in result.items() if k != "fingerprint"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "status": result["status"],
                "fingerprint": result["fingerprint"],
                "range_requests": result["range_requests"],
                "archive_metadata_bytes_opened": result[
                    "archive_metadata_bytes_opened"
                ],
            },
            sort_keys=True,
        )
    )
