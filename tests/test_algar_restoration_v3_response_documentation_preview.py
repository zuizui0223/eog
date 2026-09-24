import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_response_documentation.documentation_preview_gate import (
    parse_preview_html,
    run,
)


def _contract():
    return json.loads(
        Path(
            "validation/algar_restoration_v3_response_documentation/"
            "documentation_contract_v1_1.json"
        ).read_text(encoding="utf-8")
    )


def _html(text):
    filename = "JPE_Beirne_et_al_2021_README.txt"
    return (
        '<div class="file_preview preview_txt">'
        f'<p>Preview: {filename}</p>'
        f"<pre>{text}</pre>"
        "</div>"
    ).encode("utf-8")


def test_preview_parser_extracts_pre_text_and_filename():
    text = (
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv\n"
        "columns: Station, Species, DateTime\n"
    )
    parsed, audit = parse_preview_html(
        _html(text),
        "JPE_Beirne_et_al_2021_README.txt",
    )
    assert "30min_Independent" in parsed
    assert audit["preview_text_characters"] == len(text)


def test_preview_gate_keeps_response_csv_locked(tmp_path):
    contract = _contract()
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    text = (
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv: "
        "independent detection events\n"
        "Fields: station, species, datetime\n"
    )
    raw = _html(text)

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
    assert result["status"] == "readme_preview_opened_response_still_locked"
    assert result["response_filename_documented"] is True
    assert result["readme_preview_requests"] == 1
    assert result["response_csv_preview_requests"] == 0
    assert result["response_csv_payload_requests"] == 0
    assert result["response_csv_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False


def test_preview_unavailable_stops_without_response(tmp_path):
    contract = _contract()
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    raw = (
        '<div><p>Preview: JPE_Beirne_et_al_2021_README.txt</p>'
        "<p>Preview is currently unavailable.</p></div>"
    ).encode("utf-8")

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
    assert result["status"] == "stop_documentation_preview_gate"
    assert result["response_csv_payload_requests"] == 0
    assert result["response_csv_payload_bytes_opened"] == 0
