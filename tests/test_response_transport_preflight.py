import pytest

from eog.v2.response_transport_preflight import (
    ResponseTransportRouteEvidence,
    evaluate_response_transport,
)


def route(
    route_id,
    *,
    status=200,
    final_url="https://data.example.org/file.csv",
    content_length=100,
    expected_size=100,
    payload_bytes=0,
    error=None,
):
    return ResponseTransportRouteEvidence(
        route_id=route_id,
        url=f"https://data.example.org/{route_id}",
        expected_size=expected_size,
        status=status,
        final_url=final_url,
        content_length=content_length,
        payload_bytes_opened=payload_bytes,
        error=error,
    )


def test_head_200_exact_size_qualifies():
    result = evaluate_response_transport((route("primary"),))
    assert result.status == "response_transport_ready"
    assert result.ready is True
    assert result.qualified_route_ids == ("primary",)
    assert result.response_payload_bytes_opened == 0


def test_head_without_content_length_can_still_qualify():
    result = evaluate_response_transport(
        (route("primary", content_length=None),)
    )
    assert result.ready is True


def test_contradictory_content_length_fails_closed():
    result = evaluate_response_transport(
        (route("primary", content_length=99),)
    )
    assert result.status == "stop_no_qualified_response_transport"
    assert result.ready is False


@pytest.mark.parametrize("status", [401, 403, 404, 500])
def test_http_failure_does_not_qualify(status):
    result = evaluate_response_transport(
        (route("primary", status=status, error=f"HTTP {status}"),)
    )
    assert result.ready is False
    assert result.response_payload_bytes_opened == 0


def test_one_failed_route_can_coexist_with_second_predeclared_ready_route():
    result = evaluate_response_transport(
        (
            route("api", status=401, error="HTTP 401"),
            route("public", status=200),
        )
    )
    assert result.ready is True
    assert result.qualified_route_ids == ("public",)


def test_payload_bytes_during_head_preflight_are_terminal():
    result = evaluate_response_transport(
        (route("bad", payload_bytes=1),)
    )
    assert result.status == "stop_response_payload_opened_during_transport_preflight"
    assert result.ready is False


def test_duplicate_route_ids_fail_closed():
    with pytest.raises(ValueError, match="route IDs must be unique"):
        evaluate_response_transport((route("same"), route("same")))


def test_route_order_does_not_change_fingerprint():
    a = route("a", status=403, error="HTTP 403")
    b = route("b", status=200)
    left = evaluate_response_transport((a, b))
    right = evaluate_response_transport((b, a))
    assert left.fingerprint == right.fingerprint
