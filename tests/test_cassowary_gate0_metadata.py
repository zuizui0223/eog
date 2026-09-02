from copy import deepcopy

import pytest

from validation.cassowary_endpoint3.gate0_figshare_metadata import (
    MetadataGateStop,
    evaluate_figshare_metadata,
    load_contract,
    terminal_stop_result,
)


def _metadata():
    return {
        "id": 28050704,
        "title": "Range-wide camera trapping to reveal cassowary habitat associations",
        "files": [
            {
                "id": 51265058,
                "name": "primary-data-file.zip",
                "download_url": "https://ndownloader.figshare.com/files/51265058",
                "size": 123456,
                "supplied_md5": "0123456789abcdef0123456789abcdef",
            },
            {
                "id": 99999999,
                "name": "unrelated-code.R",
                "download_url": "https://ndownloader.figshare.com/files/99999999",
                "size": 42,
            },
        ],
    }


def test_gate0_selects_only_predeclared_file_id_and_keeps_response_closed():
    contract = load_contract()
    result = evaluate_figshare_metadata(_metadata(), contract)

    assert result["status"] == "gate0_metadata_ready"
    assert result["metadata_only"] is True
    assert result["identity"]["article_id"] == 28050704
    assert result["identity"]["article_file_count"] == 2
    assert result["identity"]["selected_file_id"] == 51265058
    assert result["identity"]["selected_file_name"] == "primary-data-file.zip"
    assert result["identity"]["selected_checksum_field"] == "supplied_md5"
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["counts_as_predictive_evidence"] is False
    assert len(result["fingerprint"]) == 64


def test_unrelated_article_files_do_not_change_selected_file_identity():
    contract = load_contract()
    metadata = _metadata()
    metadata["files"].append(
        {
            "id": 77777777,
            "name": "another-unrelated-file.txt",
            "download_url": "https://ndownloader.figshare.com/files/77777777",
            "size": 7,
        }
    )
    result = evaluate_figshare_metadata(metadata, contract)
    assert result["identity"]["selected_file_id"] == 51265058
    assert result["identity"]["article_file_count"] == 3


def test_gate0_fails_closed_on_article_identity_drift():
    contract = load_contract()
    metadata = _metadata()
    metadata["id"] = 1
    with pytest.raises(MetadataGateStop, match="article id drift"):
        evaluate_figshare_metadata(metadata, contract)

    metadata = _metadata()
    metadata["title"] = "changed title"
    with pytest.raises(MetadataGateStop, match="article title drift"):
        evaluate_figshare_metadata(metadata, contract)


def test_gate0_fails_closed_when_selected_file_is_missing_or_duplicated():
    contract = load_contract()
    metadata = _metadata()
    metadata["files"] = [metadata["files"][1]]
    with pytest.raises(MetadataGateStop, match="occurs 0 times"):
        evaluate_figshare_metadata(metadata, contract)

    metadata = _metadata()
    metadata["files"].append(deepcopy(metadata["files"][0]))
    with pytest.raises(MetadataGateStop, match="occurs 2 times"):
        evaluate_figshare_metadata(metadata, contract)


def test_gate0_fails_closed_on_invalid_selected_file_transport_metadata():
    contract = load_contract()
    metadata = _metadata()
    metadata["files"][0]["download_url"] = "http://example.org/file"
    with pytest.raises(MetadataGateStop, match="absolute HTTPS"):
        evaluate_figshare_metadata(metadata, contract)

    metadata = _metadata()
    metadata["files"][0]["size"] = 0
    with pytest.raises(MetadataGateStop, match="size must be positive"):
        evaluate_figshare_metadata(metadata, contract)


def test_terminal_stop_is_non_predictive_and_response_closed():
    contract = load_contract()
    result = terminal_stop_result(contract, "synthetic metadata stop")
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert result["metadata_only"] is True
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["counts_as_predictive_evidence"] is False
