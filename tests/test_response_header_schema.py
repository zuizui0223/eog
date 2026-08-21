import pytest

from eog.v2.response_header_schema import (
    ResponseHeaderSchemaDeclaration,
    ResponseHeaderSchemaEvidence,
    evaluate_response_header_schema,
)


def _decl(**kwargs):
    values = {
        "schema_id": "example-v1",
        "expected_columns": ("patch_number", "pixel_latitude", "pixel_longitude", "response"),
    }
    values.update(kwargs)
    return ResponseHeaderSchemaDeclaration(**values)


def _evidence(header, **kwargs):
    values = {
        "header_text": header,
        "terminator": "LF",
        "bytes_consumed": len(header.encode("utf-8")) + 1,
    }
    values.update(kwargs)
    return ResponseHeaderSchemaEvidence(**values)


def test_exact_header_match_is_ready():
    result = evaluate_response_header_schema(
        _decl(),
        _evidence("patch_number,pixel_latitude,pixel_longitude,response"),
    )

    assert result.ready is True
    assert result.status == "header_schema_match"
    assert result.missing_columns == ()
    assert result.unexpected_columns == ()
    assert result.order_matches is True


def test_giant_kelp_style_metadata_data_drift_stops_before_outcome_rows():
    result = evaluate_response_header_schema(
        _decl(),
        _evidence("patch_number,patch_latitude,patch_longitude,response"),
    )

    assert result.ready is False
    assert result.status == "stop_header_schema_mismatch"
    assert result.missing_columns == ("pixel_latitude", "pixel_longitude")
    assert result.unexpected_columns == ("patch_latitude", "patch_longitude")
    assert result.order_matches is False


def test_order_can_be_declared_irrelevant_without_changing_names():
    declaration = _decl(require_exact_order=False)
    result = evaluate_response_header_schema(
        declaration,
        _evidence("response,pixel_longitude,patch_number,pixel_latitude"),
    )

    assert result.ready is True
    assert result.status == "header_schema_match"
    assert result.order_matches is False


def test_exact_order_mismatch_stops_when_order_is_frozen():
    result = evaluate_response_header_schema(
        _decl(require_exact_order=True),
        _evidence("response,pixel_longitude,patch_number,pixel_latitude"),
    )

    assert result.ready is False
    assert result.status == "stop_header_schema_mismatch"
    assert result.missing_columns == ()
    assert result.unexpected_columns == ()
    assert result.order_matches is False


def test_empty_and_duplicate_columns_fail_closed():
    empty = evaluate_response_header_schema(
        _decl(),
        _evidence("patch_number,,pixel_longitude,response"),
    )
    duplicate = evaluate_response_header_schema(
        _decl(),
        _evidence("patch_number,pixel_latitude,pixel_latitude,response"),
    )

    assert empty.status == "stop_header_empty_column"
    assert duplicate.status == "stop_header_duplicate_columns"


def test_post_outcome_schema_repair_is_not_authorized():
    result = evaluate_response_header_schema(
        _decl(),
        _evidence(
            "patch_number,pixel_latitude,pixel_longitude,response",
            response_values_opened=True,
        ),
    )

    assert result.ready is False
    assert result.status == "stop_outcome_content_already_opened"
    assert result.observed_columns == ()


def test_declaration_and_evidence_validate_fail_closed():
    with pytest.raises(ValueError, match="expected_columns must be unique"):
        ResponseHeaderSchemaDeclaration(
            schema_id="bad",
            expected_columns=("x", "x"),
        )
    with pytest.raises(ValueError, match="delimiter"):
        _decl(delimiter="||")
    with pytest.raises(ValueError, match="header_text must be non-empty"):
        _evidence("")


def test_fingerprints_are_deterministic():
    declaration_a = _decl()
    declaration_b = _decl()
    evidence_a = _evidence("patch_number,pixel_latitude,pixel_longitude,response")
    evidence_b = _evidence("patch_number,pixel_latitude,pixel_longitude,response")

    result_a = evaluate_response_header_schema(declaration_a, evidence_a)
    result_b = evaluate_response_header_schema(declaration_b, evidence_b)

    assert declaration_a.fingerprint == declaration_b.fingerprint
    assert evidence_a.fingerprint == evidence_b.fingerprint
    assert result_a.fingerprint == result_b.fingerprint
