import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_station_crosswalk.evaluate_crosswalk import (
    evaluate_station_crosswalk,
)


def _contract(raw: bytes):
    contract = json.loads(
        Path(
            "validation/algar_restoration_v3_station_crosswalk/"
            "crosswalk_contract.json"
        ).read_text(encoding="utf-8")
    )
    file_cfg = contract["safe_dryad_file"]
    file_cfg["size"] = len(raw)
    file_cfg["digest"] = hashlib.sha256(raw).hexdigest()
    file_cfg["digest_type"] = "sha-256"
    return contract


def _locked():
    return tuple(f"ALG{i:03d}" for i in range(1, 39))


def test_safe_station_crosswalk_can_cover_all_locked_nodes():
    raw = (
        "Station,Longitude,Latitude,Habitat\n"
        + "\n".join(
            f"ALG{i:03d},{-112-i/1000},{56+i/1000},forest"
            for i in range(1, 39)
        )
        + "\n"
    ).encode("utf-8")
    result = evaluate_station_crosswalk(
        _contract(raw),
        raw,
        _locked(),
    )
    assert result["status"] == "station_crosswalk_ready_response_blind"
    assert result["join_ready_columns"] == ["Station"]
    assert result["row_count"] == 38
    assert result["response_bearing_file_requests"] == 0
    assert result["response_bearing_file_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False


def test_incomplete_station_overlap_stops():
    raw = (
        "Station,Longitude,Latitude\n"
        + "\n".join(
            f"ALG{i:03d},{-112-i/1000},{56+i/1000}"
            for i in range(1, 38)
        )
        + "\n"
    ).encode("utf-8")
    result = evaluate_station_crosswalk(
        _contract(raw),
        raw,
        _locked(),
    )
    assert result["status"] == "stop_response_blind_station_crosswalk"
    audit = result["column_audits"][0]
    assert audit["missing_locked_ids"] == ["ALG038"]


def test_biological_response_header_stops_even_with_complete_station_ids():
    raw = (
        "Station,Longitude,Latitude,Species\n"
        + "\n".join(
            f"ALG{i:03d},{-112-i/1000},{56+i/1000},hidden"
            for i in range(1, 39)
        )
        + "\n"
    ).encode("utf-8")
    result = evaluate_station_crosswalk(
        _contract(raw),
        raw,
        _locked(),
    )
    assert result["status"] == "stop_response_blind_station_crosswalk"
    assert result["forbidden_biological_columns"] == ["Species"]
    assert result["join_ready_columns"] == ["Station"]


def test_safe_file_digest_must_match_before_csv_parse():
    raw = b"Station\nALG001\n"
    contract = _contract(raw)
    contract["safe_dryad_file"]["digest"] = "0" * 64

    try:
        evaluate_station_crosswalk(contract, raw, ("ALG001",) * 38)
    except ValueError as exc:
        assert "digest drift" in str(exc)
    else:
        raise AssertionError("digest mismatch should fail closed")
