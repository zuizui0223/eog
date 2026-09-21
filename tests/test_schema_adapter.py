import pytest

from eog.v2.schema_adapter import SchemaAliasContract, SchemaRole


def contract(*, allow_unmapped=True):
    return SchemaAliasContract(
        roles=(
            SchemaRole("x", ("X_WGS84", "x_wgs84")),
            SchemaRole("y", ("Y_WGS84", "y_wgs84")),
            SchemaRole("node_id", ("site_id", "SiteID")),
            SchemaRole("effort", ("effort_days",), required=False),
        ),
        allow_unmapped_columns=allow_unmapped,
    )


def test_predeclared_aliases_accept_known_physical_spellings():
    upper = contract().resolve(("X_WGS84", "Y_WGS84", "site_id"))
    lower = contract().resolve(("x_wgs84", "y_wgs84", "SiteID"))

    assert upper.mapping == {
        "x": "X_WGS84",
        "y": "Y_WGS84",
        "node_id": "site_id",
        "effort": None,
    }
    assert lower.mapping == {
        "x": "x_wgs84",
        "y": "y_wgs84",
        "node_id": "SiteID",
        "effort": None,
    }
    assert upper.contract_fingerprint == lower.contract_fingerprint
    assert upper.semantic_fingerprint != lower.semantic_fingerprint


def test_undeclared_spelling_still_fails_closed():
    with pytest.raises(ValueError, match="required role 'x'"):
        contract().resolve(("x_WGS84_typo", "Y_WGS84", "site_id"))


def test_multiple_declared_aliases_present_is_ambiguous_not_auto_selected():
    with pytest.raises(ValueError, match="multiple declared aliases"):
        contract().resolve(("X_WGS84", "x_wgs84", "Y_WGS84", "site_id"))


def test_alias_cannot_be_shared_by_two_semantic_roles():
    with pytest.raises(ValueError, match="declared for both"):
        SchemaAliasContract(
            roles=(
                SchemaRole("x", ("coord",)),
                SchemaRole("y", ("coord",)),
            )
        )


def test_optional_role_is_none_and_record_is_canonicalized():
    resolution = contract().resolve(("x_wgs84", "y_wgs84", "site_id", "comment"))
    record = {
        "x_wgs84": 140.0,
        "y_wgs84": 38.0,
        "site_id": "A",
        "comment": "safe metadata",
    }
    assert resolution.canonicalize_record(record) == {
        "x": 140.0,
        "y": 38.0,
        "node_id": "A",
        "effort": None,
    }
    assert resolution.unmapped_physical_columns == ("comment",)


def test_missing_frozen_physical_column_in_record_fails_closed():
    resolution = contract().resolve(("x_wgs84", "y_wgs84", "site_id"))
    with pytest.raises(ValueError, match="missing frozen physical column"):
        resolution.canonicalize_record(
            {"x_wgs84": 140.0, "site_id": "A"}
        )


def test_unmapped_columns_can_be_forbidden_prospectively():
    with pytest.raises(ValueError, match="unmapped physical columns"):
        contract(allow_unmapped=False).resolve(
            ("x_wgs84", "y_wgs84", "site_id", "unexpected")
        )


def test_duplicate_physical_header_names_fail_closed():
    with pytest.raises(ValueError, match="unique columns"):
        contract().resolve(("x_wgs84", "y_wgs84", "site_id", "site_id"))


def test_resolution_is_deterministic():
    left = contract().resolve(("x_wgs84", "y_wgs84", "site_id", "effort_days"))
    right = contract().resolve(("x_wgs84", "y_wgs84", "site_id", "effort_days"))
    assert left.fingerprint == right.fingerprint
    assert left.physical_header_fingerprint == right.physical_header_fingerprint


def test_schema_contract_requires_real_booleans():
    with pytest.raises(TypeError, match="required must be bool"):
        SchemaRole("x", ("x",), required="false")
    with pytest.raises(TypeError, match="allow_unmapped_columns must be bool"):
        SchemaAliasContract(
            roles=(SchemaRole("x", ("x",)),),
            allow_unmapped_columns="false",
        )
