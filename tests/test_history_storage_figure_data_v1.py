from pathlib import Path

from manuscript.history_storage.build_figure_data_v1 import load, rows


def test_authoritative_fingerprints_and_figure_rows():
    data=load()
    output=rows(data)
    assert len(data) == 8
    assert any(
        row["figure"] == "3"
        and row["system"] == "microbiome"
        and row["target"] == "Rank abundance"
        and abs(row["value"] - 0.14860894599445995) < 1e-12
        for row in output
    )
    assert any(
        row["figure"] == "4"
        and row["panel"] == "B"
        and row["target"] == "Alternaria"
        and abs(row["value"] - 0.06106504481962524) < 1e-12
        for row in output
    )
