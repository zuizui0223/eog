import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_response_documentation.documentation_gate import run


def base_contract():
    return json.loads(
        Path(
            "validation/algar_restoration_v3_response_documentation/"
            "documentation_contract.json"
        ).read_text(encoding="utf-8")
    )


def test_documentation_gate_opens_only_readme_and_keeps_response_locked(tmp_path):
    contract = base_contract()
    raw = (
        "Algar dataset documentation\n"
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv: "
        "independent detections\n"
        "Columns: station, species, datetime\n"
    ).encode("utf-8")
    doc = contract["authorized_documentation_file"]
    doc["size"] = len(raw)
    doc["digest"] = hashlib.sha256(raw).hexdigest()
    doc["maximum_bytes"] = len(raw) + 10

    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    calls = []

    def fetcher(url, maximum_bytes):
        calls.append((url, maximum_bytes))
        return raw, {
            "url": url,
            "final_url": url,
            "status": 200,
            "bytes_opened": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    result = run(contract_path, output_path, fetcher=fetcher)
    assert result["status"] == "documentation_opened_verified_response_still_locked"
    assert result["response_filename_documented"] is True
    assert result["response_file_payload_requests"] == 0
    assert result["response_file_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False
    assert result["model_fits"] == result["heldout_scores"] == 0
    assert len(calls) == 1


def test_documentation_byte_size_drift_stops_before_response(tmp_path):
    contract = base_contract()
    raw = b"short\n"
    doc = contract["authorized_documentation_file"]
    doc["size"] = len(raw) + 1
    doc["digest"] = hashlib.sha256(raw).hexdigest()

    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    result = run(
        contract_path,
        output_path,
        fetcher=lambda url, maximum_bytes: (
            raw,
            {
                "url": url,
                "final_url": url,
                "status": 200,
                "bytes_opened": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
        ),
    )
    assert result["status"] == "stop_documentation_gate"
    assert "byte-size drift" in result["reason"]
    assert result["response_file_payload_requests"] == 0
    assert result["response_file_payload_bytes_opened"] == 0


def test_documentation_sha_drift_stops_before_response(tmp_path):
    contract = base_contract()
    raw = b"README\n"
    doc = contract["authorized_documentation_file"]
    doc["size"] = len(raw)
    doc["digest"] = "0" * 64

    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    result = run(
        contract_path,
        output_path,
        fetcher=lambda url, maximum_bytes: (
            raw,
            {
                "url": url,
                "final_url": url,
                "status": 200,
                "bytes_opened": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
        ),
    )
    assert result["status"] == "stop_documentation_gate"
    assert "SHA-256 drift" in result["reason"]
    assert result["response_file_payload_bytes_opened"] == 0
