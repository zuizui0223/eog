import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_readme_gate import readme_gate_v1_1


def _contract(tmp_path, raw: bytes):
    value = json.loads(
        Path(
            "validation/algar_restoration_v3_readme_gate/readme_contract_v1_1.json"
        ).read_text(encoding="utf-8")
    )
    value["authorized_documentation_file"]["size"] = len(raw)
    value["authorized_documentation_file"]["sha256"] = hashlib.sha256(raw).hexdigest()
    value["transport_accounting"]["get_maximum_bytes"] = len(raw) + 1
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _raw():
    return (
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv\n"
        "Independent detection observations at each station with species, date and time.\n"
        "Each row is a 30 min observation event.\n"
        "\n"
        "YData_JPE_Beirne_et_al_2021.csv\n"
    ).encode()


def test_v11_passes_with_complete_documentation_and_zero_response_csv(tmp_path, monkeypatch):
    raw = _raw()
    path = _contract(tmp_path, raw)
    monkeypatch.setattr(
        readme_gate_v1_1,
        "_head",
        lambda url: {
            "role": "readme_head",
            "method": "HEAD",
            "status": 200,
            "final_url": url,
            "content_length": str(len(raw)),
            "bytes_opened": 0,
            "error": None,
        },
    )
    monkeypatch.setattr(
        readme_gate_v1_1,
        "_get_exact",
        lambda url, expected_size, maximum_bytes: (
            raw,
            {
                "role": "readme_get",
                "method": "GET",
                "status": 200,
                "final_url": url,
                "content_length": str(len(raw)),
                "content_encoding": "identity",
                "bytes_opened": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "error": None,
            },
        ),
    )
    result = readme_gate_v1_1.run(path, tmp_path / "result.json")
    assert result["status"] == "readme_documentation_sufficient_for_schema_freeze"
    assert result["documentation_payload_bytes_opened"] == len(raw)
    assert result["response_csv_payload_bytes_opened"] == 0
    assert result["all_four_questions_supported"] is True


def test_v11_transport_failure_preserves_opened_byte_ledger(tmp_path, monkeypatch):
    raw = _raw()
    path = _contract(tmp_path, raw)
    monkeypatch.setattr(
        readme_gate_v1_1,
        "_head",
        lambda url: {
            "role": "readme_head",
            "method": "HEAD",
            "status": 200,
            "final_url": url,
            "content_length": "999",
            "bytes_opened": 0,
            "error": None,
        },
    )

    item = {
        "role": "readme_get",
        "method": "GET",
        "status": 200,
        "final_url": "https://example.org/readme",
        "content_length": "999",
        "content_encoding": "identity",
        "bytes_opened": 999,
        "sha256": "a" * 64,
        "error": None,
    }

    def stop(*args, **kwargs):
        raise readme_gate_v1_1.ReadmeTransportStop(
            "README byte-size drift: 999 != 1987",
            [item],
        )

    monkeypatch.setattr(readme_gate_v1_1, "_get_exact", stop)
    result = readme_gate_v1_1.run(path, tmp_path / "result.json")
    assert result["status"] == "stop_readme_transport_v1_1"
    assert result["documentation_payload_bytes_opened"] == 999
    assert result["response_csv_payload_bytes_opened"] == 0
    assert result["request_ledger"][-1]["bytes_opened"] == 999
