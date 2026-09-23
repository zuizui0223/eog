from __future__ import annotations

import csv
from collections import Counter
from io import StringIO
import hashlib
import json
from pathlib import Path

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.source_discovery_firewall import SourceDescriptor
from eog.v2.source_discovery_gate import (
    DiscoveryRoleRequirement,
    DiscoverySource,
    evaluate_discovery_gate,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_discovery_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_safe_registry_result.json"


def _sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _parse_csv(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV header missing")
    return list(reader)


def run_from_safe_bytes(
    contract: dict[str, object],
    *,
    deployments_text: str,
    projects_text: str,
) -> dict[str, object]:
    discovery = contract["metadata_only_discovery"]
    source_rows = discovery["sources"]

    descriptors = []
    for row in source_rows:
        descriptors.append(
            DiscoverySource(
                SourceDescriptor(
                    source_id=row["source_id"],
                    path_or_name=row.get("path") or row.get("path_pattern"),
                    declared_schema_fields=tuple(row["declared_schema_fields"]),
                ),
                row["role"],
            )
        )
    discovery_gate = evaluate_discovery_gate(
        descriptors,
        tuple(
            DiscoveryRoleRequirement(role)
            for role in discovery["required_roles"]
        ),
    )
    if not discovery_gate.ready_for_safe_content_open:
        raise ValueError(discovery_gate.status)

    deployments = _parse_csv(deployments_text)
    projects = _parse_csv(projects_text)
    if not deployments:
        raise ValueError("safe deployment table is empty")
    if len(projects) != 1:
        raise ValueError("expected one safe project metadata row")

    required = {
        "deployment_id",
        "placename",
        "longitude",
        "latitude",
        "start_date",
        "end_date",
    }
    missing = required - set(deployments[0])
    if missing:
        raise ValueError(f"deployment schema missing {sorted(missing)!r}")

    deployment_ids = [row["deployment_id"].strip() for row in deployments]
    if any(not value for value in deployment_ids):
        raise ValueError("blank deployment_id")
    if len(deployment_ids) != len(set(deployment_ids)):
        raise ValueError("duplicate deployment_id")

    by_place: dict[str, list[tuple[float, float]]] = {}
    for index, row in enumerate(deployments, start=2):
        place = row["placename"].strip()
        if not place:
            raise ValueError(f"blank placename at row {index}")
        try:
            lon = float(row["longitude"])
            lat = float(row["latitude"])
        except ValueError as exc:
            raise ValueError(f"non-numeric coordinate at row {index}") from exc
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"coordinate outside geographic bounds at row {index}")
        by_place.setdefault(place, []).append((lon, lat))

    canonical = {}
    coordinate_drift_places = []
    for place, values in sorted(by_place.items()):
        counts = Counter(values)
        representative, count = counts.most_common(1)[0]
        canonical[place] = representative
        if len(counts) > 1:
            coordinate_drift_places.append(
                {
                    "placename": place,
                    "coordinate_variants": len(counts),
                    "most_common_count": count,
                    "deployment_count": len(values),
                }
            )

    transport = evaluate_source_transport_qualification(
        (
            TransportRouteEvidence(
                route_id="github_individual_deployments_blob",
                route_type="separate_safe_assets",
                qualified=True,
                safe_payload_bytes_opened=(
                    len(deployments_text.encode("utf-8"))
                    + len(projects_text.encode("utf-8"))
                ),
                response_payload_bytes_opened=0,
                reason=(
                    "deployments.csv and projects.csv are individually addressable "
                    "GitHub blobs and no response file is required for registry/effort"
                ),
            ),
        )
    )

    gate0 = contract["gate0_plan"]
    candidate = evaluate_candidate_preflight(
        CandidatePreflightDeclaration(
            attempt_id=contract["screen_id"],
            minimum_nodes=int(gate0["minimum_nodes"]),
            minimum_outer_units=4,
            minimum_repeated_nodes=int(gate0["minimum_repeated_nodes"]),
            require_separate_geometry_and_response=True,
            require_coordinate_geometry=True,
            require_closed_analysis_registry=bool(
                gate0["require_closed_analysis_registry"]
            ),
            require_response_blind_transport_qualification=bool(
                gate0["require_response_blind_transport_qualification"]
            ),
        ),
        CandidatePreflightEvidence(
            source_identity=(
                f"{contract['source_repository']['repository']}@"
                f"{contract['source_repository']['commit']}"
            ),
            geometry_source_identity="data/raw_data/example_data/deployments.csv",
            response_source_identity="future processed detections/observations file",
            geometry_response_separable=True,
            coordinate_geometry_present=True,
            node_count=len(canonical),
            outer_unit_count=4,
            repeated_node_count=sum(len(values) > 1 for values in by_place.values()),
            analysis_registry_closed=(len(coordinate_drift_places) == 0),
            response_blind_transport_qualified=transport.ready,
            transport_qualification_fingerprint=transport.fingerprint,
            response_rows_opened=False,
            response_bytes_opened=False,
            note="safe-source Gate0 only; no focal species or response rows opened",
        ),
    )

    result = {
        "schema": "eog.algar_restoration_v2_prelock.gate0.v1",
        "status": candidate.status,
        "candidate_ready": candidate.ready,
        "candidate_locked": False,
        "focal_species_selected": False,
        "response_rows_opened": False,
        "response_bytes_opened": False,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "discovery_gate": {
            "status": discovery_gate.status,
            "fingerprint": discovery_gate.fingerprint,
            "safe_source_ids": list(discovery_gate.safe_source_ids),
            "blocked_source_ids": list(discovery_gate.blocked_source_ids),
        },
        "transport": {
            "status": transport.status,
            "fingerprint": transport.fingerprint,
        },
        "safe_registry": {
            "deployment_count": len(deployments),
            "canonical_location_count": len(canonical),
            "repeated_location_count": sum(
                len(values) > 1 for values in by_place.values()
            ),
            "coordinate_drift_location_count": len(coordinate_drift_places),
            "coordinate_drift_locations": coordinate_drift_places,
            "canonical_registry_fingerprint": _sha256(canonical),
        },
        "candidate_preflight": {
            "status": candidate.status,
            "reason": candidate.reason,
            "fingerprint": candidate.fingerprint,
            "missing_metadata": list(candidate.missing_metadata),
        },
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }
    result["fingerprint"] = _sha256(result)
    return result


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    raise RuntimeError(
        "live source fetch is intentionally separated from evaluator; "
        "call run_from_safe_bytes only after workflow verifies frozen Git blobs"
    )


if __name__ == "__main__":
    raise SystemExit(
        "This evaluator requires workflow-supplied frozen safe bytes; "
        "it never fetches repository content itself."
    )
