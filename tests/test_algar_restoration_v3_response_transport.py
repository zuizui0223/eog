import json
from pathlib import Path

from eog.v2.response_transport_preflight import ResponseTransportRouteEvidence
from validation.algar_restoration_v3_response_transport.preflight import run


def _contract(tmp_path):
    source=Path(
        "validation/algar_restoration_v3_response_transport/"
        "transport_contract.json"
    )
    contract=json.loads(source.read_text(encoding="utf-8"))
    path=tmp_path/"contract.json"
    path.write_text(json.dumps(contract),encoding="utf-8")
    return contract,path


def test_algar_response_transport_ready_if_one_declared_head_route_works(tmp_path):
    contract,path=_contract(tmp_path)
    expected=contract["response_file"]["expected_size"]

    def head_fn(route_id,url,expected_size):
        if route_id=="dryad_api_download":
            return ResponseTransportRouteEvidence(
                route_id=route_id,
                url=url,
                expected_size=expected_size,
                status=401,
                final_url=url,
                content_length=None,
                payload_bytes_opened=0,
                error="HTTP 401",
            )
        return ResponseTransportRouteEvidence(
            route_id=route_id,
            url=url,
            expected_size=expected_size,
            status=200,
            final_url=url,
            content_length=expected,
            payload_bytes_opened=0,
            error=None,
        )

    result=run(path,tmp_path/"result.json",head_fn=head_fn)
    assert result["status"]=="response_transport_ready"
    assert result["ready"] is True
    assert result["response_payload_get_requests"]==0
    assert result["response_payload_bytes_opened"]==0
    assert result["qualification"]["qualified_route_ids"]==[
        "dryad_public_file_stream"
    ]


def test_algar_response_transport_stops_if_all_declared_routes_fail(tmp_path):
    _,path=_contract(tmp_path)

    def head_fn(route_id,url,expected_size):
        return ResponseTransportRouteEvidence(
            route_id=route_id,
            url=url,
            expected_size=expected_size,
            status=403,
            final_url=url,
            content_length=None,
            payload_bytes_opened=0,
            error="HTTP 403",
        )

    result=run(path,tmp_path/"result.json",head_fn=head_fn)
    assert result["status"]=="stop_no_qualified_response_transport"
    assert result["ready"] is False
    assert result["response_payload_bytes_opened"]==0
    assert result["model_fits"]==0
    assert result["heldout_scores"]==0


def test_contradictory_head_size_does_not_qualify(tmp_path):
    _,path=_contract(tmp_path)

    def head_fn(route_id,url,expected_size):
        return ResponseTransportRouteEvidence(
            route_id=route_id,
            url=url,
            expected_size=expected_size,
            status=200,
            final_url=url,
            content_length=expected_size+1,
            payload_bytes_opened=0,
            error=None,
        )

    result=run(path,tmp_path/"result.json",head_fn=head_fn)
    assert result["ready"] is False
    assert result["status"]=="stop_no_qualified_response_transport"
