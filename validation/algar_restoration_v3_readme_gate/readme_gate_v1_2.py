from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Callable

from validation.algar_restoration_v3_readme_gate.readme_gate import (
    ReadmeGateStop,
    _canonical_sha256,
    _extract_target_section,
    _normalise_lines,
    _question_support,
)


HERE=Path(__file__).resolve().parent
DEFAULT_CONTRACT=HERE/"readme_contract_v1_2.json"
DEFAULT_OUTPUT=HERE/"readme_gate_result_v1_2.json"

Fetcher=Callable[[str,int],tuple[bytes,dict[str,object]]]


class ReadmeTransportStop(ReadmeGateStop):
    def __init__(self,message:str,ledger:list[dict[str,object]]):
        super().__init__(message)
        self.ledger=list(ledger)


def fetch_exact_api(url:str,maximum_bytes:int)->tuple[bytes,dict[str,object]]:
    request=urllib.request.Request(
        url,
        headers={
            "Accept":"text/plain,*/*",
            "Accept-Encoding":"identity",
            "User-Agent":"EOG-WF-Algar-README-Gate/1.2",
        },
    )
    try:
        response=urllib.request.urlopen(request,timeout=90)
    except urllib.error.HTTPError as exc:
        item={
            "role":"readme_api_get",
            "method":"GET",
            "status":int(exc.code),
            "final_url":url,
            "content_length":None,
            "content_encoding":None,
            "bytes_opened":0,
            "sha256":None,
            "error":f"HTTP {exc.code}",
        }
        raise ReadmeTransportStop(
            f"README API GET returned HTTP {exc.code}",
            [item],
        ) from exc
    except (OSError,urllib.error.URLError) as exc:
        item={
            "role":"readme_api_get",
            "method":"GET",
            "status":None,
            "final_url":url,
            "content_length":None,
            "content_encoding":None,
            "bytes_opened":0,
            "sha256":None,
            "error":str(exc),
        }
        raise ReadmeTransportStop(
            f"README API GET transport unavailable: {exc}",
            [item],
        ) from exc

    with response:
        status=int(getattr(response,"status",response.getcode()))
        final_url=response.geturl()
        content_length=response.headers.get("Content-Length")
        content_encoding=response.headers.get("Content-Encoding","identity")
        base={
            "role":"readme_api_get",
            "method":"GET",
            "status":status,
            "final_url":final_url,
            "content_length":content_length,
            "content_encoding":content_encoding,
            "bytes_opened":0,
            "sha256":None,
            "error":None,
        }
        if status!=200:
            base["error"]=f"HTTP {status}"
            raise ReadmeTransportStop(
                f"README API GET returned HTTP {status}",
                [base],
            )
        if str(content_encoding).casefold()!="identity":
            base["error"]="unexpected content encoding"
            raise ReadmeTransportStop(
                "README API GET unexpectedly used content encoding",
                [base],
            )
        body=response.read(maximum_bytes)

    item={
        **base,
        "bytes_opened":len(body),
        "sha256":hashlib.sha256(body).hexdigest(),
    }
    return body,item


def run(
    contract_path:Path=DEFAULT_CONTRACT,
    output_path:Path=DEFAULT_OUTPUT,
    *,
    fetcher:Fetcher=fetch_exact_api,
)->dict[str,object]:
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    doc=contract["authorized_documentation_file"]
    target=contract["documentation_extraction"]["target_response_file"]

    response_paths=[
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv",
        "YData_JPE_Beirne_et_al_2021.csv",
        "YData_dataframe_format_JPE_Beirne_et_al_2021.csv",
        "monthly_counts_JPE_Beirne_et_al_2021.csv",
        "total_observations_JPE_Beirne_et_al_2021.csv",
        "Species_comon_names_JPE_Beirne_et_al_2021.csv",
    ]
    ledger:list[dict[str,object]]=[]

    base={
        "schema":"eog.algar_restoration_v3_readme_documentation_gate.result.v1_2",
        "attempt_id":contract["attempt_id"],
        "contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "documentation_payload_requests":0,
        "documentation_payload_bytes_opened":0,
        "response_csv_payload_requests":0,
        "response_csv_payload_bytes_opened":0,
        "biological_response_values_opened":False,
        "focal_taxon_changed":False,
        "model_fits":0,
        "heldout_scores":0,
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }

    try:
        raw,item=fetcher(
            str(doc["api_download_url"]),
            int(contract["transport_accounting"]["get_maximum_bytes"]),
        )
        ledger.append(item)
        base["documentation_payload_requests"]=1
        base["documentation_payload_bytes_opened"]=len(raw)

        if len(raw)!=int(doc["size"]):
            raise ReadmeGateStop(
                f"README byte-size drift: {len(raw)} != {doc['size']}"
            )
        observed_sha=hashlib.sha256(raw).hexdigest()
        if observed_sha!=str(doc["sha256"]):
            raise ReadmeGateStop(
                f"README SHA-256 drift: {observed_sha} != {doc['sha256']}"
            )
        try:
            text=raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReadmeGateStop("README is not valid UTF-8 text") from exc

        lines=_normalise_lines(text)
        section=_extract_target_section(
            lines,
            target_file=str(target),
            known_file_paths=response_paths+[doc["path"]],
        )
        support=_question_support(list(section["lines"]))
        all_supported=all(
            bool(value["supported"]) for value in support.values()
        )
        result={
            **base,
            "status":(
                "readme_documentation_sufficient_for_schema_freeze"
                if all_supported
                else "stop_readme_documentation_insufficient"
            ),
            "documentation_file":{
                "path":doc["path"],
                "file_id":doc["file_id"],
                "bytes":len(raw),
                "sha256":observed_sha,
                "api_download_url":doc["api_download_url"],
            },
            "target_response_file":target,
            "target_section":section,
            "question_support":support,
            "all_four_questions_supported":all_supported,
            "next_gate":(
                contract["next_if_pass"]
                if all_supported
                else "none; do not open any response CSV payload"
            ),
        }
    except ReadmeTransportStop as exc:
        ledger.extend(exc.ledger)
        result={
            **base,
            "status":"stop_readme_transport_v1_2",
            "reason":str(exc),
            "next_gate":"none; do not open any response CSV payload",
        }
    except (ReadmeGateStop,ValueError,TypeError,KeyError) as exc:
        result={
            **base,
            "status":"stop_readme_documentation_gate_v1_2",
            "reason":str(exc),
            "next_gate":"none; do not open any response CSV payload",
        }

    result["request_ledger"]=ledger
    result["documentation_payload_bytes_opened"]=sum(
        int(item.get("bytes_opened",0))
        for item in ledger
    )
    result["fingerprint"]=_canonical_sha256(
        {key:value for key,value in result.items() if key!="fingerprint"}
    )
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
        "reason":value.get("reason"),
        "documentation_payload_bytes_opened":value["documentation_payload_bytes_opened"],
        "response_csv_payload_bytes_opened":value["response_csv_payload_bytes_opened"],
        "question_support":value.get("question_support"),
        "target_section":value.get("target_section"),
        "fingerprint":value["fingerprint"],
    },sort_keys=True))
