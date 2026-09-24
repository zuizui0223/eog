from __future__ import annotations

import csv
from collections import Counter
from io import StringIO
import json
from pathlib import Path

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.git_blob_identity import verify_expected_git_blob
from eog.v2.source_discovery_firewall import SourceDescriptor
from eog.v2.source_discovery_gate import (
    DiscoveryRoleRequirement,
    DiscoverySource,
    evaluate_discovery_gate,
)
from eog.v2.source_qualification_certificate import (
    freeze_source_qualification_certificate,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


def _rows(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV header missing")
    return list(reader)


def evaluate(contract: dict[str, object], raw: dict[str, bytes]) -> dict[str, object]:
    safe = {row["source_id"]: row for row in contract["source"]["safe_sources"]}
    if set(raw) != set(safe):
        raise ValueError("raw safe-source set differs from frozen source set")

    identities = {}
    for source_id, row in safe.items():
        identity = verify_expected_git_blob(
            raw[source_id],
            expected_git_blob_sha1=row["git_blob_sha1"],
        )
        identities[source_id] = identity

    discovery = evaluate_discovery_gate(
        (
            DiscoverySource(
                SourceDescriptor(
                    "deployments",
                    safe["deployments"]["path"],
                    (
                        "deployment_id",
                        "placename",
                        "longitude",
                        "latitude",
                        "start_date",
                        "end_date",
                    ),
                ),
                "registry_effort",
            ),
        ),
        (DiscoveryRoleRequirement("registry_effort"),),
    )

    deployments = _rows(raw["deployments"])
    if not deployments:
        raise ValueError("deployments safe source is empty")

    grouped: dict[str, list[tuple[float, float]]] = {}
    for index, row in enumerate(deployments, start=2):
        place = row["placename"].strip()
        if not place:
            raise ValueError(f"blank placename at row {index}")
        pair = (float(row["longitude"]), float(row["latitude"]))
        if not (-180 <= pair[0] <= 180 and -90 <= pair[1] <= 90):
            raise ValueError(f"coordinate outside bounds at row {index}")
        grouped.setdefault(place, []).append(pair)

    canonical: dict[str, tuple[float, float]] = {}
    coordinate_audit = []
    registry_closed = True
    for place, pairs in sorted(grouped.items()):
        counts = Counter(pairs)
        ordered = counts.most_common()
        top_pair, top_count = ordered[0]
        tied = len(ordered) > 1 and ordered[1][1] == top_count
        support = top_count / len(pairs)
        accepted = (not tied) and support >= (2 / 3)
        if not accepted:
            registry_closed = False
        else:
            canonical[place] = top_pair
        coordinate_audit.append(
            {
                "placename": place,
                "deployment_count": len(pairs),
                "coordinate_variant_count": len(counts),
                "modal_support": support,
                "unique_mode": not tied,
                "accepted": accepted,
            }
        )

    repeated = sum(
        place in canonical and len(pairs) > 1
        for place, pairs in grouped.items()
    )
    transport = evaluate_source_transport_qualification(
        (
            TransportRouteEvidence(
                route_id="github_individual_raw_blobs",
                route_type="separate_safe_assets",
                qualified=True,
                safe_payload_bytes_opened=sum(len(value) for value in raw.values()),
                response_payload_bytes_opened=0,
                reason="exact frozen Git blobs for deployments and project metadata verified without response access",
            ),
        )
    )
    pre = contract["candidate_preflight"]
    policy = contract["registry_policy"]
    candidate = evaluate_candidate_preflight(
        CandidatePreflightDeclaration(
            attempt_id=contract["attempt_id"],
            minimum_nodes=int(policy["minimum_nodes"]),
            minimum_outer_units=int(contract["outer_split_policy"]["outer_unit_count"]),
            minimum_repeated_nodes=int(policy["minimum_repeated_nodes"]),
            require_separate_geometry_and_response=bool(pre["require_separate_geometry_and_response"]),
            require_coordinate_geometry=bool(pre["require_coordinate_geometry"]),
            require_closed_analysis_registry=bool(pre["require_closed_analysis_registry"]),
            require_response_blind_transport_qualification=bool(pre["require_response_blind_transport_qualification"]),
        ),
        CandidatePreflightEvidence(
            source_identity=f"{contract['source']['repository']}@{contract['source']['commit']}",
            geometry_source_identity="deployments raw Git blob",
            response_source_identity="future separately named response file",
            geometry_response_separable=True,
            coordinate_geometry_present=True,
            node_count=len(canonical),
            outer_unit_count=int(contract["outer_split_policy"]["outer_unit_count"]),
            repeated_node_count=repeated,
            analysis_registry_closed=registry_closed,
            response_blind_transport_qualified=transport.ready,
            transport_qualification_fingerprint=transport.fingerprint,
            response_rows_opened=False,
            response_bytes_opened=False,
            note="Algar v2 source qualification only",
        ),
    )
    cert = freeze_source_qualification_certificate(
        discovery=discovery,
        source_identity_fingerprints={
            source_id: identity.fingerprint
            for source_id, identity in identities.items()
            if source_id in discovery.safe_source_ids
        },
        transport=transport,
        candidate_preflight=candidate,
    )
    return {
        "schema":"eog.algar_restoration_v2_source_qualification.result.v2",
        "status":cert.status,
        "candidate_lock_allowed":cert.candidate_lock_allowed,
        "certificate_fingerprint":cert.fingerprint,
        "candidate_locked":False,
        "focal_species_selected":False,
        "response_bytes_opened":0,
        "model_fits":0,
        "heldout_scores":0,
        "raw_identities":{
            key:{
                "git_blob_sha1":value.git_blob_sha1,
                "raw_byte_count":value.raw_byte_count,
                "raw_sha256":value.raw_sha256,
                "fingerprint":value.fingerprint,
            } for key,value in identities.items()
        },
        "registry":{
            "deployment_count":len(deployments),
            "placename_count":len(grouped),
            "canonical_node_count":len(canonical),
            "repeated_node_count":repeated,
            "registry_closed":registry_closed,
            "coordinate_audit":coordinate_audit,
            "canonical_nodes":{
                key:{"longitude":value[0],"latitude":value[1]}
                for key,value in canonical.items()
            },
        },
        "layers":{
            "discovery":discovery.status,
            "transport":transport.status,
            "candidate_preflight":candidate.status,
        },
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }


if __name__ == "__main__":
    raise SystemExit("workflow supplies exact raw safe blobs")
