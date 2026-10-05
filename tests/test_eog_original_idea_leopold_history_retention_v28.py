import hashlib
import json
from pathlib import Path

import numpy as np

from benchmarks.run_eog_original_idea_leopold_history_retention_v28 import (
    bray_curtis,
    git_blob_sha,
)


def test_git_blob_sha_matches_git_object_contract():
    payload = b"abc\n"
    expected = hashlib.sha1(b"blob 4\0abc\n").hexdigest()
    assert git_blob_sha(payload) == expected


def test_bray_curtis_is_symmetric_and_has_expected_values():
    matrix = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.5, 0.5, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    distance = bray_curtis(matrix)
    assert np.allclose(distance, distance.T)
    assert np.allclose(np.diag(distance), 0.0)
    assert np.isclose(distance[0, 1], 0.5)
    assert np.isclose(distance[0, 2], 1.0)


def test_v28_protocol_and_common_panel_are_frozen():
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads(
        (
            root
            / "validation/eog_original_idea_leopold_history_retention_v28/protocol_v28.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (
            root
            / "validation/eog_original_idea_leopold_history_retention_v28/common_panel_manifest_v28.json"
        ).read_text(encoding="utf-8")
    )
    assert protocol["status"] == "frozen_before_v28_target_scoring"
    assert manifest["status"] == "frozen_before_target_scoring"
    assert manifest["counts"]["common_panel"] == 233
    assert manifest["counts"]["genotype_count"] == 12
    assert manifest["counts"]["treatment_count"] == 5
    assert manifest["counts"]["occupied_genotype_treatment_cells"] == 60
