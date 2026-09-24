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
from eog.v2.source_qualification_certificate import (
    freeze_source_qualification_certificate,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


def discovery(ready=True):
    source = DiscoverySource(
        SourceDescriptor(
            "registry",
            "deployments.csv" if ready else "observations.csv",
            ("deploymentID", "latitude", "longitude")
            if ready
            else ("deploymentID", "scientificName"),
        ),
        "registry",
    )
    return evaluate_discovery_gate(
        (source,),
        (DiscoveryRoleRequirement("registry"),),
    )


def transport(ready=True):
    return evaluate_source_transport_qualification(
        (
            TransportRouteEvidence(
                route_id="route",
                route_type="separate_safe_assets",
                qualified=ready,
                safe_payload_bytes_opened=100 if ready else 0,
                response_payload_bytes_opened=0,
                reason="safe route" if ready else "route unavailable",
            ),
        )
    )


def candidate(ready=True):
    declaration = CandidatePreflightDeclaration(
        attempt_id="joined-certificate-test",
        minimum_nodes=30,
        minimum_outer_units=4,
        minimum_repeated_nodes=20,
        require_response_blind_transport_qualification=True,
    )
    evidence = CandidatePreflightEvidence(
        source_identity="source",
        geometry_source_identity="registry",
        response_source_identity="response",
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=40 if ready else 10,
        outer_unit_count=5,
        repeated_node_count=40,
        response_blind_transport_qualified=True,
        transport_qualification_fingerprint="transport-fingerprint",
        response_rows_opened=False,
        response_bytes_opened=False,
    )
    return evaluate_candidate_preflight(declaration, evidence)


def identities():
    return {"registry": "a" * 64}


def test_all_prelock_layers_ready_allow_candidate_lock():
    result = freeze_source_qualification_certificate(
        discovery=discovery(),
        source_identity_fingerprints=identities(),
        transport=transport(),
        candidate_preflight=candidate(),
    )
    assert result.status == "ready_for_candidate_lock"
    assert result.candidate_lock_allowed is True
    assert result.blocking_layer is None


def test_discovery_stop_dominates_downstream_ready_layers():
    result = freeze_source_qualification_certificate(
        discovery=discovery(False),
        source_identity_fingerprints={"registry": "a" * 64},
        transport=transport(),
        candidate_preflight=candidate(),
    )
    assert result.status == "stop_discovery"
    assert result.candidate_lock_allowed is False
    assert result.blocking_layer == "discovery"


def test_transport_stop_blocks_candidate_lock():
    result = freeze_source_qualification_certificate(
        discovery=discovery(),
        source_identity_fingerprints=identities(),
        transport=transport(False),
        candidate_preflight=candidate(),
    )
    assert result.status == "stop_transport"
    assert result.candidate_lock_allowed is False


def test_candidate_preflight_stop_blocks_lock():
    result = freeze_source_qualification_certificate(
        discovery=discovery(),
        source_identity_fingerprints=identities(),
        transport=transport(),
        candidate_preflight=candidate(False),
    )
    assert result.status == "stop_candidate_preflight"
    assert result.candidate_lock_allowed is False


def test_safe_discovery_source_requires_bound_raw_identity():
    try:
        freeze_source_qualification_certificate(
            discovery=discovery(),
            source_identity_fingerprints={"other": "b" * 64},
            transport=transport(),
            candidate_preflight=candidate(),
        )
    except ValueError as exc:
        assert "missing raw identity fingerprints" in str(exc)
    else:
        raise AssertionError("missing safe-source identity should fail closed")


def test_certificate_is_deterministic_under_identity_mapping_order():
    left = freeze_source_qualification_certificate(
        discovery=discovery(),
        source_identity_fingerprints={
            "registry": "a" * 64,
            "extra": "b" * 64,
        },
        transport=transport(),
        candidate_preflight=candidate(),
    )
    right = freeze_source_qualification_certificate(
        discovery=discovery(),
        source_identity_fingerprints={
            "extra": "b" * 64,
            "registry": "a" * 64,
        },
        transport=transport(),
        candidate_preflight=candidate(),
    )
    assert left.fingerprint == right.fingerprint
