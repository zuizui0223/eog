from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

from eog.v2.response_transport_preflight import (
    ResponseTransportRouteEvidence,
    evaluate_response_transport,
)


HERE=Path(__file__).resolve().parent
DEFAULT_CONTRACT=HERE/"transport_contract.json"
DEFAULT_OUTPUT=HERE/"transport_result.json"


def _head(url:str,expected_size:int)->ResponseTransportRouteEvidence:
    request=urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "Accept":"*/*",
            "Accept-Encoding":"identity",
            "User-Agent":"EOG-WF-Algar-Response-Transport/1.0",
        },
    )
    try:
        response=urllib.request.urlopen(request,timeout=90)
    except urllib.error.HTTPError as exc:
        return ResponseTransportRouteEvidence(
            route_id="",
            url=url,
            expected_size=expected_size,
            status=int(exc.code),
            final_url=url,
            content_length=None,
            payload_bytes_opened=0,
            error=f"HTTP {exc.code}",
        )
    except (OSError,urllib.error.URLError) as exc:
        return ResponseTransportRouteEvidence(
            route_id="",
            url=url,
            expected_size=expected_size,
            status=None,
            final_url=None,
            content_length=None,
            payload_bytes_opened=0,
            error=str(exc),
        )

    with response:
        status=int(getattr(response,"status",response.getcode()))
        final_url=response.geturl()
        raw_length=response.headers.get("Content-Length")
        content_length=None
        if raw_length is not None:
            text=str(raw_length).strip()
            if text.isdigit():
                content_length=int(text)
            else:
                return ResponseTransportRouteEvidence(
                    route_id="",
                    url=url,
                    expected_size=expected_size,
                    status=status,
                    final_url=final_url,
                    content_length=None,
                    payload_bytes_opened=0,
                    error=f"non-numeric Content-Length {raw_length!r}",
                )
        if response.headers.get("Content-Encoding","identity").casefold()!="identity":
            return ResponseTransportRouteEvidence(
                route_id="",
                url=url,
                expected_size=expected_size,
                status=status,
                final_url=final_url,
                content_length=content_length,
                payload_bytes_opened=0,
                error="unexpected content encoding",
            )
    return ResponseTransportRouteEvidence(
        route_id="",
        url=url,
        expected_size=expected_size,
        status=status,
        final_url=final_url,
        content_length=content_length,
        payload_bytes_opened=0,
        error=None,
    )


def run(
    contract_path:Path=DEFAULT_CONTRACT,
    output_path:Path=DEFAULT_OUTPUT,
)->dict[str,object]:
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    response=contract["response_file"]
    expected_size=int(response["expected_size"])

    routes=[]
    for route in contract["routes"]:
        evidence=_head(str(route["url"]),expected_size)
        # Replace the placeholder route ID while preserving the body-free evidence.
        evidence=ResponseTransportRouteEvidence(
            route_id=str(route["route_id"]),
            url=evidence.url,
            expected_size=evidence.expected_size,
            status=evidence.status,
            final_url=evidence.final_url,
            content_length=evidence.content_length,
            payload_bytes_opened=evidence.payload_bytes_opened,
            error=evidence.error,
        )
        routes.append(evidence)

    qualification=evaluate_response_transport(tuple(routes))
    result={
        "schema":"eog.algar_restoration_v3_response_transport_preflight.result.v1",
        "attempt_id":contract["attempt_id"],
        "contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "status":qualification.status,
        "ready":qualification.ready,
        "response_file":response,
        "routes":[
            {
                **asdict(route),
                "qualified":route.qualified,
                "fingerprint":route.fingerprint,
            }
            for route in routes
        ],
        "qualification":asdict(qualification),
        "response_payload_get_requests":0,
        "response_payload_bytes_opened":0,
        "biological_response_values_opened":False,
        "model_fits":0,
        "heldout_scores":0,
        "next_gate":(
            contract["next_if_ready"]
            if qualification.ready
            else contract["next_if_stop"]
        ),
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )
    return result


if __name__=="__main__":
    value=run()
    print(json.dumps({
        "status":value["status"],
        "ready":value["ready"],
        "routes":value["routes"],
        "response_payload_bytes_opened":value["response_payload_bytes_opened"],
        "qualification_fingerprint":value["qualification"]["fingerprint"],
    },sort_keys=True))
