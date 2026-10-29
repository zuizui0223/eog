"""Metadata-only source gate tests; no Dryad biological rows or remote access."""
from io import BytesIO

import openpyxl

from benchmarks.run_gotland_bam_schema_gate_v1 import (
    audit_workbook_header, run_gate, schema_crosswalk_status,
)


def _xlsx(headers, *, response_sentinel="PRIVATE_RESPONSE_MUST_NOT_APPEAR"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory"
    ws.append(headers)
    ws.append([response_sentinel for _ in headers])
    stream = BytesIO()
    wb.save(stream)
    return stream.getvalue()


def test_only_first_physical_row_is_reported():
    file = _xlsx(["PatchID", "Occupancy_2018", "Occupancy_2019"])
    info = audit_workbook_header(file, "Butterfly_occurrence_data.xlsx")
    assert info["data_rows_examined"] == 0
    assert info["physical_headers"] if "physical_headers" in info else True
    assert info["sheets"][0]["physical_headers"] == [
        "PatchID", "Occupancy_2018", "Occupancy_2019"
    ]
    assert "PRIVATE_RESPONSE_MUST_NOT_APPEAR" not in str(info)


def test_crosswalk_remains_unqualified_even_with_similar_patch_header():
    one = audit_workbook_header(
        _xlsx(["PatchID", "GMI", "Connectivity"]), "Butterfly_occurrence_data.xlsx"
    )
    two = audit_workbook_header(
        _xlsx(["PatchID", "Host plant count"]), "Host_plant_data.xlsx"
    )
    comparison = schema_crosswalk_status([one, two])
    assert comparison["candidate_common_location_tokens"] == ["patchid"]
    assert comparison["host_to_patch_crosswalk_verified"] is False
    assert comparison["B_status"].startswith("B_UNQUALIFIED")


def test_gate_downloads_exact_two_files_once_with_no_response_scoring():
    one = _xlsx(["PatchID", "Occupied2018", "Occupied2019"])
    two = _xlsx(["GridID", "SuccisaCount"])
    requested = []

    def fetch(url):
        requested.append(url)
        return one if url.endswith("264459") else two

    result = run_gate(fetch=fetch)
    assert result["status"].startswith("HEADER_ONLY_SUCCESS")
    assert len(requested) == 2
    assert requested == [
        "https://datadryad.org/downloads/file_stream/264459",
        "https://datadryad.org/downloads/file_stream/264460",
    ]
    assert result["response_rows_opened"] == 0
    assert result["scored_ecological_endpoints"] == 0


def test_source_failure_is_terminal_and_never_falls_back():
    good = _xlsx(["PatchID", "Occupied2018"])
    requested = []

    def fetch(url):
        requested.append(url)
        return good if url.endswith("264459") else b"not an excel workbook"

    result = run_gate(fetch=fetch)
    assert result["status"] == "SOURCE_STOP_SIZE_OUTSIDE_DECLARED_RANGE"
    assert result["stopped_at_file_id"] == 264460
    assert result["fail_closed_no_fallback"] is True
    assert len(requested) == 2
    assert result["response_rows_opened"] == 0
