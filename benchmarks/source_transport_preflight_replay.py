"""Response-free replay of the new transport-qualified candidate preflight.

This benchmark asks a narrow retrospective design question without reopening outcomes:

- Louisiana had physically separate response-independent Sites/Samples assets and is
  therefore transport-qualified before candidate lock.
- Tampa had a response-independent Event core that was successfully acquired before any
  occurrence response bytes and is therefore transport-qualified before candidate lock.
- Endure reached GBIF metadata but its only frozen mixed-archive inventory route returned
  HTTP 200 to the one-byte Range probe and opened zero archive/response bytes. Under the
  new preflight it would be rejected before becoming the active fresh scientific attempt.

The benchmark is infrastructure evidence only and does not change any closed endpoint.
"""

from __future__ import annotations

import json
from pathlib import Path

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


ROOT = Path(__file__).resolve().parents[1]


def _candidate_result(
    *,
    attempt_id: str,
    source_identity: str,
    geometry_identity: str,
    response_identity: str,
    node_count: int,
    outer_units: int,
    repeated_nodes: int,
    transport_ready: bool,
    transport_fingerprint: str,
):
    declaration = CandidatePreflightDeclaration(
        attempt_id=attempt_id,
        minimum_nodes=30,
        minimum_outer_units=4,
        minimum_repeated_nodes=20,
        require_separate_geometry_and_response=True,
        require_coordinate_geometry=True,
        require_response_blind_transport_qualification=True,
    )
    evidence = CandidatePreflightEvidence(
        source_identity=source_identity,
        geometry_source_identity=geometry_identity,
        response_source_identity=response_identity,
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=node_count,
        outer_unit_count=outer_units,
        repeated_node_count=repeated_nodes,
        response_blind_transport_qualified=transport_ready,
        transport_qualification_fingerprint=transport_fingerprint,
        response_rows_opened=False,
        response_bytes_opened=False,
        note="response-free transport replay",
    )
    return evaluate_candidate_preflight(declaration, evidence)


def run_replay() -> dict[str, object]:
    endure_terminal = json.loads(
        (
            ROOT
            / "validation"
            / "endure_dune_aphid_selective_promotion"
            / "terminal_result.json"
        ).read_text(encoding="utf-8")
    )

    louisiana_transport = evaluate_source_transport_qualification(
        (
            TransportRouteEvidence(
                route_id="sciencebase_separate_sites_samples",
                route_type="separate_safe_assets",
                qualified=True,
                safe_payload_bytes_opened=2329,
                response_payload_bytes_opened=0,
                reason="Sites.csv and Samples.csv were acquired independently of KIRA.csv",
            ),
        )
    )
    tampa_transport = evaluate_source_transport_qualification(
        (
            TransportRouteEvidence(
                route_id="separate_event_core",
                route_type="separate_safe_assets",
                qualified=True,
                safe_payload_bytes_opened=24_654_717,
                response_payload_bytes_opened=0,
                reason="Event core was acquired before occurrence/eMoF response access",
            ),
        )
    )
    endure_transport = evaluate_source_transport_qualification(
        (
            TransportRouteEvidence(
                route_id="ipt_mixed_archive_range_inventory",
                route_type="mixed_archive_bounded_inventory",
                qualified=False,
                safe_payload_bytes_opened=0,
                response_payload_bytes_opened=0,
                reason=endure_terminal["terminal_reason"],
                transport_detail=(
                    "one frozen Range bytes=0-0 probe; HTTP 200; body unopened"
                ),
            ),
        )
    )

    if not louisiana_transport.ready or not tampa_transport.ready:
        raise AssertionError("known safe-source systems should be transport-qualified")
    if endure_transport.ready:
        raise AssertionError("Endure mixed archive should not qualify before candidate lock")

    louisiana_candidate = _candidate_result(
        attempt_id="louisiana_transport_replay",
        source_identity="sciencebase:5ecf119d82ce30fd980854bd",
        geometry_identity="Sites.csv",
        response_identity="KIRA.csv",
        node_count=33,
        outer_units=8,
        repeated_nodes=33,
        transport_ready=louisiana_transport.ready,
        transport_fingerprint=louisiana_transport.fingerprint,
    )
    tampa_candidate = _candidate_result(
        attempt_id="tampa_transport_replay",
        source_identity="tbep-tech/obis-example@6c567bef",
        geometry_identity="dwc/event.csv",
        response_identity="dwc/occurrence.csv",
        node_count=71,
        outer_units=5,
        repeated_nodes=71,
        transport_ready=tampa_transport.ready,
        transport_fingerprint=tampa_transport.fingerprint,
    )
    endure_candidate = _candidate_result(
        attempt_id="endure_transport_replay",
        source_identity="GBIF:24ce30dc-f5df-4236-a05c-7e9231ef7f71",
        geometry_identity="DwC-A Event core inside mixed archive",
        response_identity="DwC-A Occurrence extension inside mixed archive",
        node_count=638,
        outer_units=4,
        repeated_nodes=638,
        transport_ready=endure_transport.ready,
        transport_fingerprint=endure_transport.fingerprint,
    )

    if louisiana_candidate.status != "ready_for_geometry_gate":
        raise AssertionError(louisiana_candidate.status)
    if tampa_candidate.status != "ready_for_geometry_gate":
        raise AssertionError(tampa_candidate.status)
    if endure_candidate.status != "stop_response_blind_transport_unqualified":
        raise AssertionError(endure_candidate.status)

    return {
        "schema": "eog.source_transport_preflight_replay.v1",
        "uses_biological_response": False,
        "changes_closed_eog_wf_synthesis": False,
        "systems": {
            "louisiana": {
                "transport_status": louisiana_transport.status,
                "candidate_status": louisiana_candidate.status,
                "transport_fingerprint": louisiana_transport.fingerprint,
                "candidate_fingerprint": louisiana_candidate.fingerprint,
            },
            "tampa": {
                "transport_status": tampa_transport.status,
                "candidate_status": tampa_candidate.status,
                "transport_fingerprint": tampa_transport.fingerprint,
                "candidate_fingerprint": tampa_candidate.fingerprint,
            },
            "endure": {
                "transport_status": endure_transport.status,
                "candidate_status": endure_candidate.status,
                "transport_fingerprint": endure_transport.fingerprint,
                "candidate_fingerprint": endure_candidate.fingerprint,
                "historical_terminal_result_fingerprint": endure_terminal["gate1"][
                    "fingerprint"
                ],
            },
        },
        "interpretation": (
            "Transport mechanics are screened before fresh candidate lock. Separate safe "
            "assets qualify Louisiana and Tampa, while Endure's unindexable mixed archive "
            "is rejected before consuming a scientific attempt. HTTP 200 versus 206 is "
            "retained as route evidence rather than promoted to an ecological criterion."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
