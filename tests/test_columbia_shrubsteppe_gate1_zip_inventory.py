import copy
import io
import json
import struct
import zipfile
from pathlib import Path

import pytest

from validation.columbia_shrubsteppe_endpoint3.gate1_zip_inventory import (
    Gate1Stop,
    evaluate_live,
    inspect_zip_inventory,
    select_focal_member,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "validation"
    / "columbia_shrubsteppe_endpoint3"
    / "gate1_zip_inventory_contract.json"
)


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def make_zip(names, *, comment=b""):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, name in enumerate(names):
            zf.writestr(name, (f"payload-{idx}-" * 20).encode("utf-8"))
        zf.comment = comment
    return buf.getvalue()


def inventory(payload):
    calls = []

    def read_range(start, end, role):
        calls.append((start, end, role))
        return payload[start : end + 1]

    result = inspect_zip_inventory(
        len(payload),
        read_range,
        suffix_window_bytes=22,
        maximum_central_directory_range_bytes=2_000_000,
    )
    return result, calls


def test_zero_comment_inventory_reads_only_eocd_and_central_directory():
    payload = make_zip(
        [
            "Mammals/Badger_dh.csv",
            "Mammals/Coyote_dh.csv",
            "Raw/Camera Problem Sheet.csv",
        ]
    )
    result, calls = inventory(payload)
    assert result["zip_comment_size"] == 0
    assert result["member_count"] == 3
    assert [call[2] for call in calls] == ["zip_suffix", "zip_central_directory"]
    assert calls[0][1] == len(payload) - 1
    assert calls[0][0] == len(payload) - 22
    assert calls[1][0] == result["central_directory_offset"]
    assert calls[1][1] == result["eocd_offset"] - 1
    assert calls[1][1] < calls[0][0]


def test_zip_comment_stops_instead_of_widening_into_possible_member_payload():
    payload = make_zip(["Mammals/Badger_dh.csv"], comment=b"comment")
    with pytest.raises(Gate1Stop, match="EOCD"):
        inventory(payload)


def test_zip64_sentinel_stops_fail_closed():
    payload = bytearray(make_zip(["Mammals/Badger_dh.csv"]))
    eocd = len(payload) - 22
    struct.pack_into("<I", payload, eocd + 12, 0xFFFFFFFF)
    with pytest.raises(Gate1Stop, match="ZIP64"):
        inventory(bytes(payload))


def test_focal_selection_is_lexicographic_and_response_blind():
    payload = make_zip(
        [
            "Mammals/Coyote_dh.csv",
            "Mammals/Badger_dh.csv",
            "Mammals/Active_days_z.csv",
        ]
    )
    inv, _ = inventory(payload)
    selected = select_focal_member(inv, contract())
    assert selected["matching_basenames"] == ["Badger_dh.csv", "Coyote_dh.csv"]
    assert selected["selected_member"]["basename"] == "Badger_dh.csv"
    assert selected["member_payload_bytes_opened"] == 0


def test_focal_selection_stops_if_suffix_matches_multiple_parent_directories():
    payload = make_zip(["Mammals/A_dh.csv", "Birds/B_dh.csv"])
    inv, _ = inventory(payload)
    with pytest.raises(Gate1Stop, match="multiple parent"):
        select_focal_member(inv, contract())


class FakeTransport:
    def __init__(self, contract_value, payloads):
        self.contract = contract_value
        self.payloads = payloads
        self.presign_ledger = []
        self.range_ledger = []

    def discover_presigned(self, role, archive):
        self.presign_ledger.append(
            {
                "archive_role": role,
                "requested_url": archive["public_stream_url"],
                "status": 302,
                "body_bytes_opened": 0,
                "presigned_host": "bucket.s3.us-west-2.amazonaws.com",
                "presigned_path_sha256": "0" * 64,
            }
        )
        return f"https://bucket.s3.us-west-2.amazonaws.com/{role}?X-Amz-Signature=x"

    def read_range(self, role, presigned_url, archive_size, start, end, range_role):
        payload = self.payloads[role]
        assert archive_size == len(payload)
        body = payload[start : end + 1]
        self.range_ledger.append(
            {
                "archive_role": role,
                "range_role": range_role,
                "start": start,
                "end": end,
                "status": 206,
                "content_range": f"bytes {start}-{end}/{archive_size}",
                "bytes_opened": len(body),
            }
        )
        return body


def test_evaluate_live_keeps_all_response_payloads_closed():
    csvs = make_zip(
        [
            "Mammals/Badger_dh.csv",
            "Mammals/Coyote_dh.csv",
            "Mammals/Active_days_z.csv",
            "Mammals/Mammal_site_covs_unstand.csv",
        ]
    )
    raw = make_zip(
        [
            "Camera Problem Sheets/site1.csv",
            "Camera Record Tables/site1.csv",
        ]
    )
    c = copy.deepcopy(contract())
    c["archives"]["csvs"]["size"] = len(csvs)
    c["archives"]["raw_data"]["size"] = len(raw)
    fake = FakeTransport(c, {"csvs": csvs, "raw_data": raw})
    result = evaluate_live(c, fake)
    assert result["status"] == "gate1_zip_inventory_ready"
    assert result["focal_selection"]["selected_member"]["basename"] == "Badger_dh.csv"
    assert result["presign_requests"] == 2
    assert result["s3_range_requests"] == 4
    assert result["local_header_bytes_opened"] == 0
    assert result["archive_member_payload_bytes_opened"] == 0
    assert result["detection_history_payload_bytes_opened"] == 0
    assert result["camera_record_payload_bytes_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == result["heldout_scores"] == 0
