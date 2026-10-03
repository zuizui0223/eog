import pytest

from validation.izu_microdonta_relational_genetics_v1.gate0_sample_registry import (
    IzuRegistryStop,
    PRIMARY_ISLANDS,
    REQUIRED_COLUMNS,
    validate_registry_rows,
)


def _rows():
    rows = []
    sample = 1
    # 25 per island -> exactly 125 response-free fixture rows.
    for island_index, island in enumerate(PRIMARY_ISLANDS):
        for i in range(25):
            rows.append(
                {
                    "sample_id": f"S{sample:03d}",
                    "island": island,
                    "site_id": f"site_{island_index + 1}",
                    "latitude": 34.0 - island_index * 0.1,
                    "longitude": 139.0 + island_index * 0.1,
                    "leaf_available": "true",
                }
            )
            sample += 1
    return rows


def test_exact_five_island_registry_passes_and_freezes_ten_pairs():
    result = validate_registry_rows(REQUIRED_COLUMNS, _rows())
    assert result["status"] == "response_free_registry_ready"
    assert result["row_count"] == 125
    assert result["primary_pair_count"] == 10
    assert set(result["island_sample_counts"]) == set(PRIMARY_ISLANDS)
    assert result["genetic_response_opened"] is False


def test_genetic_response_column_is_forbidden():
    columns = (*REQUIRED_COLUMNS, "pairwise_FST")
    rows = _rows()
    for row in rows:
        row["pairwise_FST"] = ""
    with pytest.raises(IzuRegistryStop, match="genetic-response-derived"):
        validate_registry_rows(columns, rows)


def test_unknown_island_stops_before_genetics():
    rows = _rows()
    rows[0]["island"] = "Hachijojima"
    with pytest.raises(IzuRegistryStop, match="unknown island"):
        validate_registry_rows(REQUIRED_COLUMNS, rows)


def test_row_count_must_remain_exactly_125():
    with pytest.raises(IzuRegistryStop, match="row count must be 125"):
        validate_registry_rows(REQUIRED_COLUMNS, _rows()[:-1])


def test_within_site_individual_coordinate_variation_is_aggregated_response_free():
    rows = _rows()
    rows[1]["latitude"] = 33.9
    result = validate_registry_rows(REQUIRED_COLUMNS, rows)
    assert result["status"] == "response_free_registry_ready"
    assert "Izu_Oshima|site_1" in result["site_centroids"]
    assert result["island_centroids"]["Izu_Oshima"]["site_count"] == 1
