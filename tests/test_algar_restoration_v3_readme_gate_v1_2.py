import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_readme_gate.readme_gate_v1_2 import run


def _contract(tmp_path):
    source=Path(
        "validation/algar_restoration_v3_readme_gate/readme_contract_v1_2.json"
    )
    contract=json.loads(source.read_text(encoding="utf-8"))
    path=tmp_path/"contract.json"
    path.write_text(json.dumps(contract),encoding="utf-8")
    return contract,path


def _readme(*, include_species=True):
    lines=[
        "Data files",
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv",
        "This file contains independent wildlife detections summarized at 30 min intervals.",
        "Fields include Station and Date_Time for camera location and observation timestamp.",
    ]
    if include_species:
        lines.append("Species gives the taxon identity for each independent detection.")
    lines.extend([
        "",
        "YData_JPE_Beirne_et_al_2021.csv",
        "Model response matrix.",
    ])
    return ("\n".join(lines)+"\n").encode("utf-8")


def _fit_contract_to_raw(contract, raw):
    contract["authorized_documentation_file"]["size"]=len(raw)
    contract["authorized_documentation_file"]["sha256"]=hashlib.sha256(raw).hexdigest()


def test_v1_2_passes_when_all_documentation_questions_are_supported(tmp_path):
    contract,path=_contract(tmp_path)
    raw=_readme(include_species=True)
    _fit_contract_to_raw(contract,raw)
    path.write_text(json.dumps(contract),encoding="utf-8")

    def fetcher(url,maximum_bytes):
        assert maximum_bytes>=len(raw)
        return raw,{
            "role":"readme_api_get",
            "method":"GET",
            "status":200,
            "final_url":url,
            "content_length":str(len(raw)),
            "content_encoding":"identity",
            "bytes_opened":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest(),
            "error":None,
        }

    result=run(path,tmp_path/"result.json",fetcher=fetcher)
    assert result["status"]=="readme_documentation_sufficient_for_schema_freeze"
    assert result["all_four_questions_supported"] is True
    assert result["documentation_payload_requests"]==1
    assert result["documentation_payload_bytes_opened"]==len(raw)
    assert result["response_csv_payload_requests"]==0
    assert result["response_csv_payload_bytes_opened"]==0


def test_v1_2_stops_if_taxon_documentation_is_missing(tmp_path):
    contract,path=_contract(tmp_path)
    raw=_readme(include_species=False)
    _fit_contract_to_raw(contract,raw)
    path.write_text(json.dumps(contract),encoding="utf-8")

    def fetcher(url,maximum_bytes):
        return raw,{
            "role":"readme_api_get",
            "method":"GET",
            "status":200,
            "final_url":url,
            "content_length":str(len(raw)),
            "content_encoding":"identity",
            "bytes_opened":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest(),
            "error":None,
        }

    result=run(path,tmp_path/"result.json",fetcher=fetcher)
    assert result["status"]=="stop_readme_documentation_insufficient"
    assert result["question_support"]["species_or_taxon_field"]["supported"] is False
    assert result["response_csv_payload_bytes_opened"]==0


def test_v1_2_transport_stop_keeps_response_csv_closed(tmp_path):
    contract,path=_contract(tmp_path)

    def fetcher(url,maximum_bytes):
        from validation.algar_restoration_v3_readme_gate.readme_gate_v1_2 import ReadmeTransportStop
        raise ReadmeTransportStop(
            "README API GET returned HTTP 403",
            [{
                "role":"readme_api_get",
                "method":"GET",
                "status":403,
                "final_url":url,
                "content_length":None,
                "content_encoding":None,
                "bytes_opened":0,
                "sha256":None,
                "error":"HTTP 403",
            }],
        )

    result=run(path,tmp_path/"result.json",fetcher=fetcher)
    assert result["status"]=="stop_readme_transport_v1_2"
    assert result["documentation_payload_bytes_opened"]==0
    assert result["response_csv_payload_requests"]==0
    assert result["response_csv_payload_bytes_opened"]==0


def test_v1_2_wrong_sha_stops_after_only_readme_bytes(tmp_path):
    contract,path=_contract(tmp_path)
    raw=_readme()
    contract["authorized_documentation_file"]["size"]=len(raw)
    contract["authorized_documentation_file"]["sha256"]="0"*64
    path.write_text(json.dumps(contract),encoding="utf-8")

    def fetcher(url,maximum_bytes):
        return raw,{
            "role":"readme_api_get",
            "method":"GET",
            "status":200,
            "final_url":url,
            "content_length":str(len(raw)),
            "content_encoding":"identity",
            "bytes_opened":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest(),
            "error":None,
        }

    result=run(path,tmp_path/"result.json",fetcher=fetcher)
    assert result["status"]=="stop_readme_documentation_gate_v1_2"
    assert "SHA-256 drift" in result["reason"]
    assert result["documentation_payload_bytes_opened"]==len(raw)
    assert result["response_csv_payload_bytes_opened"]==0
