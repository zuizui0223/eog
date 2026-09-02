import io
import json
from pathlib import Path
import zipfile

import pytest

from validation.soutpansberg_leopard_endpoint3.gate1_zip_metadata import (
    FrozenRangeTransport,
    Gate1Stop,
    evaluate_zip_metadata,
    terminal_stop_result,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "validation" / "soutpansberg_leopard_endpoint3" / "gate1_zip_metadata_contract.json"
)


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _zip_bytes():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for i in range(1, 25):
            sid = f"s{i:02d}"
            archive.writestr(f"SPACECAP/deployment_{sid}.csv", "LOC_ID,X,Y,SO1\nA,1,2,1\n")
            archive.writestr(f"SPACECAP/capture_{sid}.csv", "ANIMAL_ID,TRAP_ID,SO\nL1,A,1\n")
            archive.writestr(f"SPACECAP/HRC_{sid}.csv", "X,Y\n1,2\n")
        archive.writestr("SPACECAP/notes.txt", "synthetic only")
    return stream.getvalue()


def _reader_with_ledger(data):
    ledger = []

    def read(start, end, role):
        body = data[start : end + 1]
        ledger.append(
            {
                "role": role,
                "start": start,
                "end": end,
                "status": 206,
                "content_range": f"bytes {start}-{end}/{len(data)}",
                "final_scheme": "https",
                "final_host": "example.org",
                "bytes_opened": len(body),
            }
        )
        return body

    return read, ledger


def test_gate1_recovers_exact_24_survey_pairs_without_payload_access():
    data = _zip_bytes()
    contract = _contract()
    contract["gate0_identity"]["size_bytes"] = len(data)
    read, ledger = _reader_with_ledger(data)
    result = evaluate_zip_metadata(contract, read, ledger)
    assert result["status"] == "gate1_zip_metadata_ready"
    pairs = result["survey_pair_inventory"]
    assert pairs["survey_count"] == 24
    assert pairs["deployment_member_count"] == 24
    assert pairs["capture_member_count"] == 24
    assert list(pairs["pairs"]) == [f"s{i:02d}" for i in range(1, 25)]
    assert pairs["pairs"]["s01"]["deployment"]["basename"] == "deployment_s01.csv"
    assert pairs["pairs"]["s24"]["capture"]["basename"] == "capture_s24.csv"
    assert result["member_payload_bytes_opened"] == 0
    assert result["deployment_payload_bytes_opened"] == 0
    assert result["capture_header_bytes_opened"] == 0
    assert result["capture_payload_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["model_fits"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_gate1_fails_if_one_capture_survey_is_missing():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for i in range(1, 25):
            sid = f"s{i:02d}"
            archive.writestr(f"deployment_{sid}.csv", "x")
            if i != 24:
                archive.writestr(f"capture_{sid}.csv", "x")
    data = stream.getvalue()
    contract = _contract()
    contract["gate0_identity"]["size_bytes"] = len(data)
    read, ledger = _reader_with_ledger(data)
    with pytest.raises(Gate1Stop, match="capture survey inventory drift"):
        evaluate_zip_metadata(contract, read, ledger)


def test_gate1_allows_unrelated_hrc_and_note_members_without_changing_denominator():
    data = _zip_bytes()
    contract = _contract()
    contract["gate0_identity"]["size_bytes"] = len(data)
    read, ledger = _reader_with_ledger(data)
    result = evaluate_zip_metadata(contract, read, ledger)
    assert result["member_count"] > 48
    assert result["survey_pair_inventory"]["survey_count"] == 24


class _FakeHeaders(dict):
    def items(self):
        return super().items()


class _FakeResponse:
    def __init__(self, status, headers, body=b"should-not-be-read", url="https://example.org/file.zip"):
        self.status = status
        self.headers = _FakeHeaders(headers)
        self._body = body
        self._url = url
        self.read_calls = 0

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def read(self, n=-1):
        self.read_calls += 1
        return self._body if n < 0 else self._body[:n]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_non_206_range_stops_before_body_read():
    response = _FakeResponse(200, {"Content-Type": "application/zip"})

    def opener(request, timeout):
        return response

    transport = FrozenRangeTransport("https://example.org/file.zip", 100, opener=opener)
    with pytest.raises(Gate1Stop, match="HTTP 200"):
        transport.read(78, 99, "eocd")
    assert response.read_calls == 0
    assert transport.ledger[0]["bytes_opened"] == 0


def test_bad_content_range_stops_before_body_read():
    response = _FakeResponse(
        206,
        {"Content-Range": "bytes 78-99/101", "Content-Encoding": "identity"},
    )

    def opener(request, timeout):
        return response

    transport = FrozenRangeTransport("https://example.org/file.zip", 100, opener=opener)
    with pytest.raises(Gate1Stop, match="frozen archive size"):
        transport.read(78, 99, "eocd")
    assert response.read_calls == 0


def test_terminal_stop_is_never_predictive_evidence():
    result = terminal_stop_result(_contract(), "synthetic stop", [])
    assert result["status"] == "stop_pre_response_zip_transport_container_or_inventory"
    assert result["member_payload_bytes_opened"] == 0
    assert result["capture_payload_bytes_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_contract_pins_gate0_identity_and_no_rescue_rules():
    contract = _contract()
    assert contract["gate0_execution_merge"] == "99dce20bdcad561ae481aa84f534bd3c4c0a2417"
    assert contract["gate0_identity"] == {
        "figshare_article_id": 4235546,
        "file_id": 6906950,
        "file_name": "SPACECAP input files.zip",
        "download_url": "https://ndownloader.figshare.com/files/6906950",
        "size_bytes": 467246,
        "supplied_md5": "b3cbad3bd91096a9917b469f46c7f6d5",
        "gate0_fingerprint": "bc47dc09dd71d2dbc2653fe0e97982ddbe67a00e4b9efab66d0706ee5401bd14",
    }
    assert contract["bounded_range_transport"]["full_get_forbidden"] is True
    assert contract["bounded_range_transport"]["every_range_requires_http_206"] is True
    assert contract["survey_pair_inventory"]["hrc_members_not_required_for_gate1"] is True
    assert contract["survey_pair_inventory"]["crosswalk_member_not_required_inside_this_zip"] is True
    assert contract["post_gate_repair"]["fallback_archive_allowed"] is False
    assert contract["post_gate_repair"]["rerun_after_terminal_stop_allowed"] is False
