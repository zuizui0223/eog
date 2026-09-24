import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_response_documentation.documentation_api_gate_v1_2 import run


def base_contract():
    return json.loads(
        Path(
            "validation/algar_restoration_v3_response_documentation/"
            "documentation_contract_v1_2.json"
        ).read_text(encoding="utf-8")
    )


def _readme(*, include_species=True):
    lines=[
        "Files:",
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv",
        "Independent wildlife detections at 30 min intervals.",
        "Fields include station and datetime for camera location and detection date/time.",
    ]
    if include_species:
        lines.append("Species identifies the taxon for each independent detection.")
    lines.extend([
        "YData_JPE_Beirne_et_al_2021.csv",
        "Response matrix used in the published models.",
    ])
    return ("\n".join(lines)+"\n").encode("utf-8")


def _freeze_readme_identity(contract,raw):
    doc=contract["authorized_documentation_file"]
    doc["size"]=len(raw)
    doc["digest"]=hashlib.sha256(raw).hexdigest()
    doc["maximum_bytes"]=len(raw)+1


def test_v1_2_passes_only_documented_schema_questions(tmp_path):
    contract=base_contract()
    raw=_readme(include_species=True)
    _freeze_readme_identity(contract,raw)
    contract_path=tmp_path/"contract.json"
    output_path=tmp_path/"result.json"
    contract_path.write_text(json.dumps(contract),encoding="utf-8")

    def fetcher(url,maximum_bytes):
        assert maximum_bytes>=len(raw)
        return raw,{
            "url":url,
            "final_url":url,
            "status":200,
            "bytes_opened":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest(),
        }

    result=run(contract_path,output_path,fetcher=fetcher)
    assert result["status"]=="documentation_sufficient_for_response_schema_freeze"
    assert result["all_documentation_questions_supported"] is True
    assert result["response_filename_documented"] is True
    assert result["documentation_payload_requests"]==1
    assert result["response_csv_preview_requests"]==0
    assert result["response_csv_payload_requests"]==0
    assert result["response_csv_payload_bytes_opened"]==0
    assert result["full_documentation_text_persisted"] is False


def test_v1_2_stops_if_taxon_semantics_are_not_documented(tmp_path):
    contract=base_contract()
    raw=_readme(include_species=False)
    _freeze_readme_identity(contract,raw)
    contract_path=tmp_path/"contract.json"
    output_path=tmp_path/"result.json"
    contract_path.write_text(json.dumps(contract),encoding="utf-8")

    result=run(
        contract_path,
        output_path,
        fetcher=lambda url,maximum_bytes:(
            raw,
            {
                "url":url,
                "final_url":url,
                "status":200,
                "bytes_opened":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(),
            },
        ),
    )
    assert result["status"]=="stop_documentation_insufficient_for_response_schema"
    assert result["question_support"]["species_or_taxon_field"]["supported"] is False
    assert result["response_csv_payload_bytes_opened"]==0


def test_v1_2_numeric_content_is_redacted_in_saved_lines(tmp_path):
    contract=base_contract()
    raw=(
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv\n"
        "30 min independent detections from 38 stations with species and datetime fields\n"
        "YData_JPE_Beirne_et_al_2021.csv\n"
    ).encode()
    _freeze_readme_identity(contract,raw)
    contract_path=tmp_path/"contract.json"
    output_path=tmp_path/"result.json"
    contract_path.write_text(json.dumps(contract),encoding="utf-8")

    result=run(
        contract_path,
        output_path,
        fetcher=lambda url,maximum_bytes:(
            raw,
            {
                "url":url,
                "final_url":url,
                "status":200,
                "bytes_opened":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(),
            },
        ),
    )
    saved="\n".join(result["target_block_sanitized"])
    assert "38" not in saved
    assert "<n>" in saved
    assert result["numeric_biological_summaries_persisted"] is False


def test_v1_2_sha_drift_stops_without_response_csv(tmp_path):
    contract=base_contract()
    raw=_readme()
    contract["authorized_documentation_file"]["size"]=len(raw)
    contract["authorized_documentation_file"]["digest"]="0"*64
    contract["authorized_documentation_file"]["maximum_bytes"]=len(raw)+1
    contract_path=tmp_path/"contract.json"
    output_path=tmp_path/"result.json"
    contract_path.write_text(json.dumps(contract),encoding="utf-8")

    result=run(
        contract_path,
        output_path,
        fetcher=lambda url,maximum_bytes:(
            raw,
            {
                "url":url,
                "final_url":url,
                "status":200,
                "bytes_opened":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(),
            },
        ),
    )
    assert result["status"]=="stop_documentation_api_gate_v1_2"
    assert "SHA-256 drift" in result["reason"]
    assert result["response_csv_payload_requests"]==0
    assert result["response_csv_payload_bytes_opened"]==0
