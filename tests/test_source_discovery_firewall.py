from eog.v2.source_discovery_firewall import (
    SourceDescriptor,
    classify_discovery_batch,
    classify_source_descriptor,
)


def test_capture_file_is_blocked_before_content_open():
    result = classify_source_descriptor(
        SourceDescriptor(
            source_id="uwin-captures",
            path_or_name="week6_spatial_mapping/data/captures.csv",
        )
    )
    assert result.classification == "response_bearing"
    assert result.content_open_allowed is False
    assert "text:captures" in result.response_indicators


def test_observations_file_is_blocked_before_content_open():
    result = classify_source_descriptor(
        SourceDescriptor(
            source_id="camtrap-observations",
            path_or_name="observations.csv",
            declared_schema_fields=(
                "deploymentID",
                "scientificName",
                "observationType",
            ),
        )
    )
    assert result.classification == "response_bearing"
    assert result.content_open_allowed is False
    assert "field:scientificname" in result.response_indicators


def test_deployments_file_is_safe_candidate_from_metadata():
    result = classify_source_descriptor(
        SourceDescriptor(
            source_id="deployments",
            path_or_name="deployments.csv",
            declared_schema_fields=(
                "deploymentID",
                "locationID",
                "latitude",
                "longitude",
                "deploymentStart",
                "deploymentEnd",
            ),
        )
    )
    assert result.classification == "safe_candidate"
    assert result.content_open_allowed is True
    assert not result.response_indicators


def test_generic_unknown_csv_is_not_assumed_safe():
    result = classify_source_descriptor(
        SourceDescriptor(
            source_id="unknown",
            path_or_name="data.csv",
        )
    )
    assert result.classification == "ambiguous_do_not_open"
    assert result.content_open_allowed is False


def test_response_indicator_dominates_safe_indicator():
    result = classify_source_descriptor(
        SourceDescriptor(
            source_id="mixed",
            path_or_name="site_observations.csv",
            declared_schema_fields=("siteID", "latitude", "longitude"),
        )
    )
    assert result.classification == "response_bearing"
    assert result.content_open_allowed is False
    assert result.response_indicators
    assert result.safe_indicators


def test_schema_response_field_blocks_neutral_filename():
    result = classify_source_descriptor(
        SourceDescriptor(
            source_id="neutral-name",
            path_or_name="table.csv",
            declared_schema_fields=("siteID", "scientificName"),
        )
    )
    assert result.classification == "response_bearing"
    assert result.content_open_allowed is False


def test_batch_is_deterministic_and_sorted_by_source_id():
    a = SourceDescriptor("b", "deployments.csv")
    b = SourceDescriptor("a", "observations.csv")
    left = classify_discovery_batch((a, b))
    right = classify_discovery_batch((b, a))
    assert tuple(item.source_id for item in left) == ("a", "b")
    assert tuple(item.fingerprint for item in left) == tuple(
        item.fingerprint for item in right
    )
