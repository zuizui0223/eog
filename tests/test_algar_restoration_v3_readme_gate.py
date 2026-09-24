import hashlib
import json
from pathlib import Path

import pytest

from validation.algar_restoration_v3_readme_gate import readme_gate


def _contract(tmp_path, raw: bytes):
    base = json.loads(
        Path(
            "validation/algar_restoration_v3_readme_gate/readme_contract.json"
        ).read_text(encoding="utf-8")
    )
    base["authorized_documentation_file"]["size"] = len(raw)
    base["authorized_documentation_file"]["sha256"] = hashlib.sha256(raw).hexdigest()
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(base), encoding="utf-8")
    return path


def _readme_bytes():
    return (
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv\n"
        "Independent wildlife detections at each station. Columns include station, "
        "species, date and time.\n"
        "Each record represents a 30 min independent observation event.\n"
        "\n"
        "YData_JPE_Beirne_et_al_2021.csv\n"
        "Model response matrix.\n"
    ).encode("utf-8")


def test_readme_gate_can_support_all_four_questions_without_response_csv(tmp_path, monkeypatch):
    raw = _readme_bytes()
    contract_path = _contract(tmp_path, raw)
    output_path = tmp_path / "result.json"

    monkeypatch.setattr(readme_gate, "_fetch_exact", lambda url, expected_size: raw)
    result = readme_gate.run(contract_path, output_path)

    assert result["status"] == "readme_documentation_sufficient_for_schema_freeze"
    assert result["documentation_payload_requests"] == 1
    assert result["documentation_payload_bytes_opened"] == len(raw)
    assert result["response_csv_payload_requests"] == 0
    assert result["response_csv_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False
    assert result["all_four_questions_supported"] is True
    assert all(
        value["supported"]
        for value in result["question_support"].values()
    )


def test_readme_gate_stops_if_schema_questions_are_not_supported(tmp_path, monkeypatch):
    raw = (
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv\n"
        "Processed table.\n"
        "\n"
        "YData_JPE_Beirne_et_al_2021.csv\n"
    ).encode("utf-8")
    contract_path = _contract(tmp_path, raw)
    output_path = tmp_path / "result.json"

    monkeypatch.setattr(readme_gate, "_fetch_exact", lambda url, expected_size: raw)
    result = readme_gate.run(contract_path, output_path)

    assert result["status"] == "stop_readme_documentation_insufficient"
    assert result["response_csv_payload_bytes_opened"] == 0
    assert result["all_four_questions_supported"] is False


def test_readme_gate_fails_closed_on_sha_drift(tmp_path, monkeypatch):
    raw = _readme_bytes()
    contract_path = _contract(tmp_path, raw)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["authorized_documentation_file"]["sha256"] = "0" * 64
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    output_path = tmp_path / "result.json"

    monkeypatch.setattr(readme_gate, "_fetch_exact", lambda url, expected_size: raw)
    result = readme_gate.run(contract_path, output_path)

    assert result["status"] == "stop_readme_documentation_gate"
    assert "SHA-256 drift" in result["reason"]
    assert result["response_csv_payload_bytes_opened"] == 0
