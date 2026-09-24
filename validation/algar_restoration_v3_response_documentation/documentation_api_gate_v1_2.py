from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_response_documentation.documentation_gate import (
    DocumentationGateStop,
    _decode_utf8,
    _nonempty_lines,
    _sanitize_line,
    canonical_sha256,
    fetch_documentation,
)


HERE=Path(__file__).resolve().parent
DEFAULT_CONTRACT=HERE/"documentation_contract_v1_2.json"
DEFAULT_OUTPUT=HERE/"documentation_result_v1_2.json"


def _target_block(
    lines:list[str],
    *,
    target_path:str,
    known_paths:tuple[str,...],
)->list[str]:
    indices=[
        index
        for index,line in enumerate(lines)
        if target_path.casefold() in line.casefold()
    ]
    if not indices:
        raise DocumentationGateStop(
            "README does not document the frozen target response filename"
        )
    start=indices[0]
    other_paths=tuple(
        path for path in known_paths if path!=target_path
    )
    end=len(lines)
    for index in range(start+1,len(lines)):
        folded=lines[index].casefold()
        if any(path.casefold() in folded for path in other_paths):
            end=index
            break
    # A single preceding nonempty line may be a heading; no broader context is retained.
    context_start=max(0,start-1)
    return lines[context_start:end]


def _question_support(
    block_lines:list[str],
    groups:dict[str,list[str]],
)->dict[str,object]:
    text="\n".join(block_lines).casefold()
    result={}
    for name,tokens in groups.items():
        matched=tuple(
            token for token in tokens
            if str(token).casefold() in text
        )
        result[name]={
            "supported":bool(matched),
            "matched_terms":list(matched),
        }
    return result


def run(
    contract_path:Path=DEFAULT_CONTRACT,
    output_path:Path=DEFAULT_OUTPUT,
    *,
    fetcher=fetch_documentation,
)->dict[str,object]:
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    doc=contract["authorized_documentation_file"]
    response=contract["candidate_response_file"]
    known_paths=tuple(str(value) for value in contract["known_roster_paths"])
    target_path=str(response["path"])

    if target_path not in known_paths:
        raise ValueError("candidate response file is not in frozen Dryad roster")
    if str(doc["path"]) not in known_paths:
        raise ValueError("README file is not in frozen Dryad roster")
    if bool(contract["extraction_policy"]["save_full_documentation_text"]):
        raise ValueError("full README persistence is forbidden")

    base={
        "schema":"eog.algar_restoration_v3_response_documentation.result.v1_2",
        "attempt_id":contract["attempt_id"],
        "contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "focal_taxon":contract["focal_taxon"],
        "candidate_response_file":response,
        "documentation_payload_requests":0,
        "documentation_payload_bytes_opened":0,
        "response_csv_preview_requests":0,
        "response_csv_payload_requests":0,
        "response_csv_payload_bytes_opened":0,
        "biological_response_values_opened":False,
        "model_fits":0,
        "heldout_scores":0,
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }

    try:
        raw,request=fetcher(
            str(doc["api_download_url"]),
            int(doc["maximum_bytes"]),
        )
        base["documentation_payload_requests"]=1
        base["documentation_payload_bytes_opened"]=len(raw)

        if len(raw)!=int(doc["size"]):
            raise DocumentationGateStop(
                f"documentation byte-size drift: {len(raw)} != {doc['size']}"
            )
        observed_sha=hashlib.sha256(raw).hexdigest()
        if observed_sha!=str(doc["digest"]).lower():
            raise DocumentationGateStop(
                f"documentation SHA-256 drift: {observed_sha} != {doc['digest']}"
            )

        text=_decode_utf8(raw)
        lines=_nonempty_lines(text)
        block=_target_block(
            lines,
            target_path=target_path,
            known_paths=known_paths,
        )
        support=_question_support(
            block,
            {
                key:[str(value) for value in values]
                for key,values in contract["documentation_questions"].items()
            },
        )
        all_supported=all(
            bool(value["supported"]) for value in support.values()
        )
        max_lines=int(
            contract["extraction_policy"]["maximum_saved_lines_per_file"]
        )
        sanitized=[
            _sanitize_line(line,known_paths)
            for line in block[:max_lines]
        ]
        result={
            **base,
            "status":(
                "documentation_sufficient_for_response_schema_freeze"
                if all_supported
                else "stop_documentation_insufficient_for_response_schema"
            ),
            "documentation_file":{
                "path":doc["path"],
                "file_id":doc["file_id"],
                "version_id":doc["version_id"],
                "size":len(raw),
                "sha256":observed_sha,
                "api_download_url":doc["api_download_url"],
            },
            "documentation_request":request,
            "response_filename_documented":True,
            "target_block_nonempty_lines":len(block),
            "target_block_sha256":hashlib.sha256(
                "\n".join(block).encode("utf-8")
            ).hexdigest(),
            "target_block_sanitized":sanitized,
            "question_support":support,
            "all_documentation_questions_supported":all_supported,
            "full_documentation_text_persisted":False,
            "numeric_biological_summaries_persisted":False,
            "next_gate":(
                contract["next_if_sufficient"]
                if all_supported
                else contract["next_if_insufficient"]
            ),
        }
    except (DocumentationGateStop,KeyError,TypeError,ValueError) as exc:
        result={
            **base,
            "status":"stop_documentation_api_gate_v1_2",
            "reason":str(exc),
            "documentation_request":None,
            "full_documentation_text_persisted":False,
            "numeric_biological_summaries_persisted":False,
            "next_gate":"none; response CSV remains locked",
        }

    result["fingerprint"]=canonical_sha256(
        {key:value for key,value in result.items() if key!="fingerprint"}
    )
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )
    return result


if __name__=="__main__":
    result=run()
    print(json.dumps({
        "status":result["status"],
        "response_filename_documented":result.get("response_filename_documented"),
        "question_support":result.get("question_support"),
        "target_block_sanitized":result.get("target_block_sanitized"),
        "documentation_payload_bytes_opened":result["documentation_payload_bytes_opened"],
        "response_csv_payload_bytes_opened":result["response_csv_payload_bytes_opened"],
        "fingerprint":result["fingerprint"],
    },sort_keys=True))
