import json
from pathlib import Path

from benchmarks import finland_strict_source_score as score


FREEZE = Path("benchmarks/frozen/finland_strict_source_cohort/feature_freeze.json")
FORMAT = Path("benchmarks/frozen/finland_strict_source_cohort/csv_format_manifest.json")


def test_strict_scoring_freeze_is_response_free_and_exact():
    record = score._verify_freeze_record(FREEZE)
    fmt = json.loads(FORMAT.read_text(encoding="utf-8"))

    assert record["outcome_values_accessed"] is False
    assert record["n_sourceful_species"] == 180
    assert record["n_analysis_species_response_free"] == 180
    assert record["features_sha256"] == score.EXPECTED_FEATURES_SHA256
    assert record["feature_bundle_fingerprint"] == score.EXPECTED_FEATURE_BUNDLE_FINGERPRINT
    assert record["strict_admission_fingerprint"] == score.EXPECTED_STRICT_ADMISSION_FINGERPRINT
    assert record["strict_species_list_sha256"] == score.EXPECTED_STRICT_SPECIES_SHA256
    assert record["fingerprint"] == score.EXPECTED_FREEZE_FINGERPRINT

    assert fmt["schema"] == score.FORMAT_SCHEMA
    assert fmt["outcome_values_accessed"] is False
    assert fmt["outcome_column_exists"] is True
    assert fmt["raw_sha256"] == score.EXPECTED_RAW_SHA256
    assert fmt["delimiter"] == ";"
    assert fmt["header_sha256"] == "f2ca1ad8e68726b68a7e977e9897d895d0f6147d4c7cffcf36f47b4b07e5565f"


def test_strict_scoring_does_not_weaken_frozen_base_contract():
    assert score.STRICT_BUNDLE_SCHEMA == "eog_v2_finland_strict_source_response_free_bundle_v1"
    assert score.STRICT_RESULT_SCHEMA == "eog_v2_finland_strict_source_empirical_result_v1"
    assert score.EXPECTED_FREEZE_RUN == 31689131928
    assert score.EXPECTED_FREEZE_ARTIFACT == 9176686695
    assert score.EXPECTED_FREEZE_ARTIFACT_DIGEST.startswith("sha256:")
