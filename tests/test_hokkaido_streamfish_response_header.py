import json
from pathlib import Path

import pytest

from validation.hokkaido_streamfish_endpoint3.response_header_gate import (
    ResponseHeaderStop,
    evaluate_header_line,
    load_contract,
)
from validation.hokkaido_streamfish_endpoint3.run_response_header_gate import (
    HeaderTransportStop,
    _read_header_line,
)


ROOT = Path(__file__).resolve().parents[1] / "validation" / "hokkaido_streamfish_endpoint3"


class FakeResponse:
    def __init__(self, *, status, url, headers, line=b"", forbid_body=False):
        self.status = status
        self._url = url
        self.headers = headers
        self._line = line
        self._forbid_body = forbid_body
        self.readline_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def readline(self, limit=-1):
        self.readline_calls += 1
        if self._forbid_body:
            raise AssertionError("body must not be opened")
        if limit >= 0:
            return self._line[:limit]
        return self._line


def _authorization(contract):
    return {
        "authorized_url": contract["source"]["raw_url"],
    }


def test_header_evaluator_accepts_required_tokens_and_extra_unique_column():
    contract = load_contract()
    line = b"year,river,site,genus,latin,abundance,area,note\n"
    result = evaluate_header_line(line, contract)
    assert result["status"] == "response_header_ready"
    assert result["header_bytes_opened"] == len(line)
    assert result["physical_columns"] == [
        "year", "river", "site", "genus", "latin", "abundance", "area", "note"
    ]
    assert result["required_index_by_role"]["latin"] == 4
    assert result["response_data_row_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0


def test_header_evaluator_rejects_duplicate_or_missing_required_tokens():
    contract = load_contract()
    with pytest.raises(ResponseHeaderStop, match="duplicate"):
        evaluate_header_line(
            b"year,river,site,genus,latin,abundance,area,latin\n", contract
        )
    with pytest.raises(ResponseHeaderStop, match="required exact"):
        evaluate_header_line(b"year,river,site,genus,latin,abundance\n", contract)


def test_http_200_fallback_stops_before_body_read():
    contract = load_contract()
    auth = _authorization(contract)
    fake = FakeResponse(
        status=200,
        url=contract["source"]["raw_url"],
        headers={"Content-Type": "text/csv"},
        line=b"year,river,site,genus,latin,abundance,area\n",
        forbid_body=True,
    )

    def opener(request, timeout=60):
        return fake

    with pytest.raises(HeaderTransportStop, match="HTTP 200; body was not opened"):
        _read_header_line(contract, auth, opener=opener)
    assert fake.readline_calls == 0


def test_valid_206_reads_only_first_line_and_declares_zero_row_bytes():
    contract = load_contract()
    auth = _authorization(contract)
    line = b"year,river,site,genus,latin,abundance,area\n"
    fake = FakeResponse(
        status=206,
        url=contract["source"]["raw_url"],
        headers={
            "Content-Range": contract["transport"]["required_content_range"],
            "Content-Encoding": "identity",
            "Content-Type": "text/csv",
        },
        line=line,
    )

    def opener(request, timeout=60):
        assert request.get_header("Range") == "bytes=0-255"
        return fake

    observed, ledger = _read_header_line(contract, auth, opener=opener)
    assert observed == line
    assert fake.readline_calls == 1
    assert ledger["body_bytes_returned_to_application"] == len(line)
    assert ledger["response_data_row_bytes_returned_to_application"] == 0


def test_contract_binds_pre_response_pass_and_keeps_rows_forbidden():
    contract = json.loads((ROOT / "response_header_contract.json").read_text(encoding="utf-8"))
    assert contract["pre_response_pass_git_blob_sha"] == "dad0bba05787ed686c1095a642d956534e096bf7"
    assert contract["transport"]["range_start"] == 0
    assert contract["transport"]["range_end"] == 255
    assert contract["transport"]["required_http_status"] == 206
    assert contract["transport"]["full_body_fallback_allowed"] is False
    assert contract["firewall"]["response_data_row_bytes_allowed"] == 0
    assert contract["firewall"]["response_rows_allowed"] == 0
    assert contract["firewall"]["response_values_allowed"] is False
