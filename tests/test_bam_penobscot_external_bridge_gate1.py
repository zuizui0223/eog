import json
from pathlib import Path

import pytest

from validation.bam_penobscot_external_bridge_v1.gate1_schema import (
    Gate1Stop,
    inspect_delimited_header,
    links_from_html,
    select_schema_files,
)


HERE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "bam_penobscot_external_bridge_v1"
)


def _contract():
    return json.loads(
        (HERE / "gate1_schema_contract_draft.json").read_text(encoding="utf-8")
    )


def test_exact_fish_file_selection_does_not_choose_by_content():
    links = (
        ("https://example/final.pdf", "_Fish Community - FINAL REPORT.pdf"),
        ("https://example/fish.accdb", "Penobscot Fish Data 2010 to 2012.accdb"),
    )
    selected = select_schema_files("FishCommunity", links, _contract())
    assert selected == (
        ("https://example/fish.accdb", "Penobscot Fish Data 2010 to 2012.accdb"),
    )


def test_all_supported_non_document_data_files_selected_for_open_rule():
    links = (
        ("https://example/report.pdf", "report.pdf"),
        ("https://example/a.csv", "a.csv"),
        ("https://example/b.xlsx", "b.xlsx"),
    )
    selected = select_schema_files("Geomorphology", links, _contract())
    assert tuple(name for _, name in selected) == ("a.csv", "b.xlsx")


def test_unknown_data_extension_stops_instead_of_silent_drop():
    links = (("https://example/a.sqlite", "a.sqlite"),)
    with pytest.raises(Gate1Stop, match="unsupported archive object types"):
        select_schema_files("Geomorphology", links, _contract())


def test_delimited_inspector_reads_only_first_physical_row():
    body = b"year,site,taxon,abundance\n2010,A,fish,99\n"
    result = inspect_delimited_header(body, delimiter=",")
    assert result["columns"] == ["year", "site", "taxon", "abundance"]
    assert result["data_row_bytes_interpreted"] == 0
    assert result["header_bytes_opened"] == len(b"year,site,taxon,abundance\n")
