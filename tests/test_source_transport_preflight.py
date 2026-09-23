import pytest

from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


def route(
    route_id,
    *,
    route_type="separate_safe_assets",
    qualified,
    safe_bytes=0,
    response_bytes=0,
    reason="declared route result",
    detail="",
):
    return TransportRouteEvidence(
        route_id=route_id,
        route_type=route_type,
        qualified=qualified,
        safe_payload_bytes_opened=safe_bytes,
        response_payload_bytes_opened=response_bytes,
        reason=reason,
        transport_detail=detail,
    )


def test_separate_safe_assets_can_qualify_candidate_lock():
    result = evaluate_source_transport_qualification(
        (
            route(
                "safe_registry_files",
                qualified=True,
                safe_bytes=2329,
                reason="registry and effort payloads acquired independently",
            ),
        )
    )
    assert result.status == "ready_for_candidate_lock"
    assert result.ready is True
    assert result.qualified_route_ids == ("safe_registry_files",)
    assert result.response_payload_bytes_opened == 0


def test_mixed_archive_range_failure_is_transport_unqualified_not_biological():
    result = evaluate_source_transport_qualification(
        (
            route(
                "ipt_range_inventory",
                route_type="mixed_archive_bounded_inventory",
                qualified=False,
                safe_bytes=0,
                response_bytes=0,
                reason="Range bytes=0-0 returned HTTP 200 rather than usable partial content",
                detail="HTTP 200; response body deliberately unopened",
            ),
        )
    )
    assert result.status == "stop_no_response_blind_transport_route"
    assert result.ready is False
    assert result.response_payload_bytes_opened == 0
    assert "response-blind transport route" in result.reason


def test_one_failed_route_does_not_poison_an_independently_qualified_route():
    result = evaluate_source_transport_qualification(
        (
            route(
                "range_route",
                route_type="mixed_archive_bounded_inventory",
                qualified=False,
                reason="server ignored Range",
            ),
            route(
                "published_inventory_route",
                route_type="published_member_inventory",
                qualified=True,
                safe_bytes=800,
                reason="public member inventory identified safe registry member without payload",
            ),
        )
    )
    assert result.status == "ready_for_candidate_lock"
    assert result.ready is True
    assert result.qualified_route_ids == ("published_inventory_route",)


def test_response_bytes_opened_during_transport_qualification_is_terminal():
    result = evaluate_source_transport_qualification(
        (
            route(
                "unsafe_full_archive",
                route_type="other_response_blind_route",
                qualified=False,
                safe_bytes=1000,
                response_bytes=25,
                reason="full mixed archive body was opened",
            ),
        )
    )
    assert result.status == "stop_response_opened_during_transport_qualification"
    assert result.ready is False
    assert result.response_payload_bytes_opened == 25


def test_qualified_route_cannot_claim_response_bytes_opened():
    with pytest.raises(ValueError, match="cannot have opened response payload bytes"):
        route(
            "contradiction",
            qualified=True,
            response_bytes=1,
        )


def test_empty_transport_evidence_is_incomplete_not_pass():
    result = evaluate_source_transport_qualification(())
    assert result.status == "incomplete_transport_evidence"
    assert result.ready is False
    assert result.qualified_route_ids == ()


def test_duplicate_route_ids_fail_closed():
    item = route("same", qualified=False)
    with pytest.raises(ValueError, match="route IDs must be unique"):
        evaluate_source_transport_qualification((item, item))


def test_transport_result_is_order_invariant():
    a = route(
        "a",
        qualified=False,
        route_type="mixed_archive_bounded_inventory",
        reason="not available",
    )
    b = route(
        "b",
        qualified=True,
        route_type="separate_safe_assets",
        reason="safe files available",
    )
    left = evaluate_source_transport_qualification((a, b))
    right = evaluate_source_transport_qualification((b, a))
    assert left.fingerprint == right.fingerprint



def test_validation_facade_exports_transport_preflight():
    from eog.v2 import validation
    from eog.v2.source_transport_preflight import (
        TransportRouteEvidence as Route,
        evaluate_source_transport_qualification as evaluate,
    )

    assert validation.TransportRouteEvidence is Route
    assert validation.evaluate_source_transport_qualification is evaluate
