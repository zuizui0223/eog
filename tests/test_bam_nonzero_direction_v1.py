"""Unit tests for the source-pinned post-exposure BAM span audit."""
from pathlib import Path
import importlib.util

import pytest

MODULE = Path(__file__).resolve().parents[1] / "benchmarks" / "audit_bam_nonzero_direction_v1.py"
spec = importlib.util.spec_from_file_location("bam_nonzero_audit", MODULE)
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)


def test_sign_classification_is_strict():
    assert audit_mod.signs("1") == (1,)
    assert audit_mod.signs("-1|1") == (-1, 1)
    assert audit_mod.signs("0|1") == (0, 1)
    with pytest.raises(ValueError, match="invalid direction"):
        audit_mod.signs("1|-1")
    with pytest.raises(ValueError, match="invalid direction"):
        audit_mod.signs("1|1")


def test_missing_original_artifact_fails_closed(tmp_path):
    (tmp_path / "fibre_envelopes.csv").write_text("tampered data\n")
    (tmp_path / "result.json").write_text("{}\n")
    with pytest.raises(ValueError, match="original source hash mismatch"):
        audit_mod.audit(tmp_path)
