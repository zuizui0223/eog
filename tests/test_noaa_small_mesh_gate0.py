from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request

import pytest

from validation.noaa_small_mesh_replication_3 import gate0_registry_effort as gate0

CONTRACT_PATH = (
    Path(__file__).parents[1]
    / "validation"
    / "noaa_small_mesh_replication_3"
    / "source_contract.json"
)
ATTEMPT_LOG_PATH = CONTRACT_PATH.with_name("pre_response_attempt_log.json")


class FakeResponse:
    def __init__(
        self,
        url: str,
        payload: bytes,
        *,
        status: int,
        headers: dict[str, str],
    ) -> None:
        self.status = status
        self.headers = headers
        self._url = url
        self._payload = payload
        self.read_calls = 0

    def __enter__(self) -> FakeResponse:  # noqa: PYI034 - Python 3.10 has no Self
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def geturl(self) -> str:
        return self._url

    def read(self) -> bytes:
        self.read_calls += 1
        return self._payload


def _headers(object_contract: dict[str, object]) -> dict[str, str]:
    return {
        "x-goog-generation": str(object_contract["generation"]),
        "ETag": f'"{object_contract["md5"]}"',
        "Content-Type": str(object_contract["content_type"]),
    }


def _haul_payload(contract: dict[str, object]) -> bytes:
    output = io.StringIO(newline="")
    header = contract["objects"]["registry_effort"]["expected_header"]
    writer = csv.DictWriter(output, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    haul = 0
    for station_index in range(12):
        for year in range(1995, 2001):
            haul += 1
            row = dict.fromkeys(header, "")
            values = {
                "region": "GOA",
                "vessel": "1",
                "cruise": f"{year}01",
                "haul": str(haul),
                "haul_type": "3",
                "performance": "0",
                "duration": "1",
                "distance_fished": "1",
                "net_width": "10",
                "net_height": "3",
                "start_latitude": str(55 + station_index / 100),
                "start_longitude": str(150 + station_index / 100),
                "stationid": f"S{station_index:02d}",
                "gear": "508",
                "subsample": "1",
            }
            row.update({key: value for key, value in values.items() if key in row})
            writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _temporary_contract(tmp_path: Path) -> tuple[Path, dict[str, object], bytes]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    payload = _haul_payload(contract)
    haul = contract["objects"]["registry_effort"]
    haul["size_bytes"] = len(payload)
    haul["md5"] = hashlib.md5(payload).hexdigest()
    path = tmp_path / "source_contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path, contract, payload


def test_gate0_closes_registry_without_opening_catch(tmp_path: Path) -> None:
    path, contract, haul_payload = _temporary_contract(tmp_path)
    catch = contract["objects"]["response"]
    haul = contract["objects"]["registry_effort"]
    catch_response = FakeResponse(
        catch["url"],
        b"X",
        status=206,
        headers={
            **_headers(catch),
            "Content-Range": f"bytes 0-0/{catch['size_bytes']}",
        },
    )
    haul_response = FakeResponse(
        haul["url"], haul_payload, status=200, headers=_headers(haul)
    )

    def opener(request: Request, **_kwargs: object) -> FakeResponse:
        return catch_response if request.full_url == catch["url"] else haul_response

    result = gate0.execute_gate0(path, opener=opener)

    assert result["status"] == "ready_for_geometry_gate"
    assert result["haul_audit"]["repeated_station_count"] == 12
    assert result["haul_audit"]["supported_heldout_years"] == list(range(1995, 2001))
    assert result["opened_roles"] == ["haul_registry_effort"]
    assert catch_response.read_calls == 0
    assert haul_response.read_calls == 1
    assert result["request_ledger"][0]["bytes_opened"] == 0


def test_catch_range_failure_does_not_read_body(tmp_path: Path) -> None:
    path, contract, _payload = _temporary_contract(tmp_path)
    catch = contract["objects"]["response"]
    response = FakeResponse(
        catch["url"],
        b"forbidden",
        status=200,
        headers=_headers(catch),
    )

    with pytest.raises(ValueError, match="read-free Range gate"):
        gate0.execute_gate0(path, opener=lambda *_args, **_kwargs: response)

    assert response.read_calls == 0


def test_contract_keeps_catch_closed_and_focal_fixed() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    catch = contract["objects"]["response"]

    assert all(
        catch[key] is False
        for key in (
            "payload_access_allowed",
            "header_access_allowed",
            "row_access_allowed",
            "value_access_allowed",
        )
    )
    assert contract["focal_taxon"]["scientific_name"] == "Pandalus borealis"
    assert contract["endpoint"]["primary_heldout_years"] == list(range(1995, 2005))
    assert contract["endpoint"][
        "catch_may_not_repair_registry_effort_geometry_or_years"
    ]


def test_attempt_log_preserves_failures_and_cumulative_firewall() -> None:
    log = json.loads(ATTEMPT_LOG_PATH.read_text(encoding="utf-8"))

    assert [row["status"] for row in log["attempts"]] == [
        "engineering_failure",
        "engineering_failure",
        "stop_analysis_registry_not_closed",
    ]
    assert log["cumulative_response_firewall"] == {
        "catch_transport_requests": 3,
        "catch_payload_bytes_opened": 0,
        "catch_header_bytes_opened": 0,
        "catch_rows_opened": False,
        "catch_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    assert log["repair_or_substitution_allowed"] is False
