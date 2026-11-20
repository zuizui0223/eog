"""Synthetic parser and publisher-byte-identity tests: NO toad event rows."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

import pytest

from scripts import toad_publisher_readme_definition_audit_v1 as m

SPEC = json.loads(Path("validation/toad_release_distance_publisher_readme_v1/protocol_v1.json").read_text(encoding="utf-8"))


def _mock_source():
    readme = rb"{\rtf1\ansi{\fonttbl{\f0 Arial;}}\pard Original release-final is not a substitute for a historical capture point.\par Distance capture-final: another definition.\par}"
    csv = b"TEST_ONLY_UNINTERPRETED_BYTES_NOT_TOAD_EVENT_ROWS"
    files = [
        {"name":"README_file.rtf", "bytes":len(readme), "sha256":sha256(readme).hexdigest()},
        {"name":"Jreidini_and_Green_homing_toads_2021.csv", "bytes":len(csv), "sha256":sha256(csv).hexdigest()},
    ]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("public/README_file.rtf", readme)
        z.writestr("public/Jreidini_and_Green_homing_toads_2021.csv", csv)
    return out.getvalue(), files, readme


def test_protocol_origin_and_non_promotion_are_frozen():
    assert SPEC["status"] == "FROZEN_BEFORE_README_CONTENT_RETRIEVAL"
    assert SPEC["source"]["version_id"] == 198534
    assert SPEC["parent_stop"]["status"] == "STOP_GEO_UNIT_CONCORDANCE"
    assert SPEC["parent_stop"]["original_h1_run_id"] == 44756566395
    assert SPEC["execution_limits"]["read_csv_rows"] is False
    assert SPEC["execution_limits"]["may_modify_original_STOP"] is False
    assert SPEC["execution_limits"]["new_EOG_WF_endpoints"] == 0


def test_rtf_parser_preserves_public_readme_words_but_not_font_table():
    archive, files, expected = _mock_source()
    doc = m.verify_readme_bytes(archive, files)
    assert doc == expected
    text = m.rtf_plaintext(doc)
    assert "Original release-final" in text
    assert "Distance capture-final" in text
    assert "Arial" not in text
    assert "\n" in text
    receipt = m._documentation_receipt(doc, SPEC)
    assert receipt["status"] == "AUTHENTICATED_PUBLISHER_README_DOCUMENT_RETRIEVED_NOT_MOVEMENT_SCORE"
    assert receipt["biological_data_rows_decoded"] == 0
    assert receipt["field_outcomes_scored"] == 0
    assert receipt["new_EOG_WF_endpoints"] == 0
    assert receipt["original_STOP_overridden"] is False
    assert "TEST_ONLY_UNINTERPRETED_BYTES" not in json.dumps(receipt)


def test_rtf_unicode_and_ignorable_group():
    example = rb"{\rtf1\ansi\uc1 Release\u8211?final{\*\unknown Ignore these words.}\par Distance}"
    text = m.rtf_plaintext(example)
    assert "Release\u2013final" in text
    assert "Ignore these words" not in text
    assert "Distance" in text
    with pytest.raises(ValueError, match="STOP_SOURCE_README_NOT_RTF"):
        m.rtf_plaintext(b"not rtf")
    with pytest.raises(ValueError, match="STOP_RTF_UNBALANCED"):
        m.rtf_plaintext(rb"{\rtf1\ansi broken")


def test_wrong_member_digest_fails_closed_without_model_scoring():
    archive, files, _ = _mock_source()
    fake = deepcopy(files)
    fake[1]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="STOP_ORIGINAL_PUBLISHER_MEMBER_HASH_MISMATCH"):
        m.verify_readme_bytes(archive, fake)
    fake2 = deepcopy(files)
    fake2[0]["bytes"] += 1
    with pytest.raises(ValueError, match="STOP_ORIGINAL_PUBLISHER_MEMBER_HASH_MISMATCH"):
        m.verify_readme_bytes(archive, fake2)


def test_zip_member_path_violation_and_missing_file_fails_closed():
    raw, files, rtf = _mock_source()
    out=io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("../README_file.rtf", rtf)
        z.writestr("Jreidini_and_Green_homing_toads_2021.csv", b"test")
    with pytest.raises(ValueError, match="STOP_ZIP_UNSAFE_MEMBER"):
        m.verify_readme_bytes(out.getvalue(), files)
    out=io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("README_file.rtf", rtf)
    with pytest.raises(ValueError, match="STOP_SOURCE_ZIP_MEMBER_COUNT_CHANGED"):
        m.verify_readme_bytes(out.getvalue(), files)


def test_unknown_publisher_document_not_silently_used_as_readme():
    with pytest.raises(ValueError, match="STOP_SOURCE_README_NOT_RTF"):
        m._documentation_receipt(b"maybe a CSV file", SPEC)
