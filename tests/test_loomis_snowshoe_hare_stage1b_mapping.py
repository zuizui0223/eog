from __future__ import annotations

import pytest

from validation.loomis_snowshoe_hare_endpoint3.gate1b_mapping import (
    REQUIRED_DEPLOYMENT_ROLES,
    validate_stage1b_mapping,
)


HEADERS = {
    "camera_info_new.csv": ("camera", "model"),
    "deployment_2022.csv": ("site", "camera", "lat", "lon", "start", "end"),
    "deployment_2023.csv": ("site", "camera", "lat", "lon", "start", "end"),
    "deployment_2024.csv": ("site", "camera", "lat", "lon", "start", "end"),
}

MAPPING = {
    "site_id": "site",
    "camera_id": "camera",
    "latitude": "lat",
    "longitude": "lon",
    "deployment_start": "start",
    "deployment_end": "end",
}


def test_valid_mapping_across_all_years():
    result = validate_stage1b_mapping(
        headers=HEADERS,
        deployment_mapping=MAPPING,
        camera_info_join_field="camera",
    )
    assert result.valid is True
    assert result.normalized_mapping == MAPPING


def test_one_year_missing_field_fails_closed():
    headers = dict(HEADERS)
    headers["deployment_2024.csv"] = ("site", "camera", "lat", "lon", "start")
    result = validate_stage1b_mapping(headers=headers, deployment_mapping=MAPPING)
    assert result.valid is False
    assert "deployment_2024.csv" in result.reason


def test_mapping_roles_must_be_exact_and_ordered():
    bad = dict(MAPPING)
    bad["extra"] = "x"
    with pytest.raises(ValueError, match="REQUIRED_DEPLOYMENT_ROLES"):
        validate_stage1b_mapping(headers=HEADERS, deployment_mapping=bad)


def test_roles_must_map_to_distinct_fields():
    bad = dict(MAPPING)
    bad["camera_id"] = "site"
    with pytest.raises(ValueError, match="distinct"):
        validate_stage1b_mapping(headers=HEADERS, deployment_mapping=bad)


def test_camera_info_join_must_exist_and_equal_camera_id():
    result = validate_stage1b_mapping(
        headers=HEADERS,
        deployment_mapping=MAPPING,
        camera_info_join_field="model",
    )
    assert result.valid is False
    assert "same physical camera-id field" in result.reason


def test_missing_header_evidence_rejected():
    headers = dict(HEADERS)
    headers.pop("deployment_2023.csv")
    with pytest.raises(ValueError, match="missing Stage1A header evidence"):
        validate_stage1b_mapping(headers=headers, deployment_mapping=MAPPING)


def test_required_roles_are_stable():
    assert REQUIRED_DEPLOYMENT_ROLES == (
        "site_id",
        "camera_id",
        "latitude",
        "longitude",
        "deployment_start",
        "deployment_end",
    )
