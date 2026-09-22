import pytest

from eog.v2.schema_adapter import SchemaAliasContract, SchemaRole
from eog.v2.tabular_adapter import StrictCSVPolicy, parse_response_blind_csv


def _schema():
    return SchemaAliasContract(
        roles=(
            SchemaRole("node_id", ("site_id", "SiteID")),
            SchemaRole("x", ("X_WGS84", "x_wgs84")),
            SchemaRole("y", ("Y_WGS84", "y_wgs84")),
            SchemaRole("effort", ("effort_days",), required=False),
        ),
        allow_unmapped_columns=True,
    )


def test_generic_csv_adapter_resolves_declared_aliases_and_preserves_values():
    raw = (
        b"site_id,x_wgs84,y_wgs84,note\n"
        b"A,140.0,38.0, padded value \n"
        b"B,141.0,39.0,raw\n"
    )
    parsed = parse_response_blind_csv(raw, schema_contract=_schema())
    assert parsed.physical_row_count == 2
    assert parsed.schema_resolution.mapping["x"] == "x_wgs84"
    assert parsed.records()[0] == {
        "node_id": "A",
        "x": "140.0",
        "y": "38.0",
        "effort": None,
    }
    assert parsed.source_sha256
    assert parsed.canonical_rows_fingerprint


def test_unknown_required_spelling_fails_closed():
    raw = b"site_id,x_wgs84_typo,y_wgs84\nA,140,38\n"
    with pytest.raises(ValueError, match="required role 'x'"):
        parse_response_blind_csv(raw, schema_contract=_schema())


def test_duplicate_header_fails_before_schema_resolution():
    raw = b"site_id,x_wgs84,y_wgs84,site_id\nA,140,38,A\n"
    with pytest.raises(ValueError, match="duplicate columns"):
        parse_response_blind_csv(raw, schema_contract=_schema())


def test_row_width_mismatch_fails_closed():
    raw = b"site_id,x_wgs84,y_wgs84\nA,140\n"
    with pytest.raises(ValueError, match="cells for"):
        parse_response_blind_csv(raw, schema_contract=_schema())


def test_utf8_bom_requires_explicit_policy():
    raw = b"\xef\xbb\xbfsite_id,x_wgs84,y_wgs84\nA,140,38\n"
    with pytest.raises(ValueError, match="BOM is forbidden"):
        parse_response_blind_csv(raw, schema_contract=_schema())

    parsed = parse_response_blind_csv(
        raw,
        schema_contract=_schema(),
        policy=StrictCSVPolicy(allow_utf8_bom=True),
    )
    assert parsed.records()[0]["node_id"] == "A"


def test_invalid_utf8_fails_closed():
    raw = b"site_id,x_wgs84,y_wgs84\nA,140,\xff\n"
    with pytest.raises(ValueError, match="not valid UTF-8"):
        parse_response_blind_csv(raw, schema_contract=_schema())


def test_empty_data_requires_explicit_opt_out():
    raw = b"site_id,x_wgs84,y_wgs84\n"
    with pytest.raises(ValueError, match="no data rows"):
        parse_response_blind_csv(raw, schema_contract=_schema())

    parsed = parse_response_blind_csv(
        raw,
        schema_contract=_schema(),
        policy=StrictCSVPolicy(require_data_rows=False),
    )
    assert parsed.physical_row_count == 0
    assert parsed.records() == ()


def test_unmapped_physical_column_remains_outside_canonical_records():
    raw = b"site_id,x_wgs84,y_wgs84,irrelevant\nA,140,38,secret-free-metadata\n"
    parsed = parse_response_blind_csv(raw, schema_contract=_schema())
    assert parsed.schema_resolution.unmapped_physical_columns == ("irrelevant",)
    assert "irrelevant" not in parsed.records()[0]


def test_adapter_is_deterministic_for_same_bytes_and_contract():
    raw = b"site_id,x_wgs84,y_wgs84\nA,140,38\n"
    left = parse_response_blind_csv(raw, schema_contract=_schema())
    right = parse_response_blind_csv(raw, schema_contract=_schema())
    assert left.fingerprint == right.fingerprint
    assert left.canonical_rows_fingerprint == right.canonical_rows_fingerprint


def test_only_explicit_utf8_policy_is_supported():
    with pytest.raises(ValueError, match="only explicit utf-8"):
        StrictCSVPolicy(encoding="latin-1")
