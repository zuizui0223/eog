import json
from pathlib import Path

import numpy as np
import pytest

from eog.support_topology_validation import run_heldout_validation


def _write_grouped_fixture(tmp_path: Path):
    support = np.full((5, 11), 0.05, dtype=float)
    mask = np.ones_like(support, dtype=bool)
    island = np.array(
        [
            [0.82, 0.84, 0.80],
            [0.86, 0.88, 0.83],
            [0.79, 0.81, 0.78],
        ]
    )
    mask[1:4, 0:3] = False
    mask[1:4, 5:8] = False
    support[1:4, 0:3] = island
    support[1:4, 5:8] = island
    mask[1, 10] = False
    support[1, 10] = 0.75
    np.save(tmp_path / "support.npy", support)
    np.save(tmp_path / "mask.npy", mask)
    (tmp_path / "anchors.csv").write_text(
        "anchor_id,row,column\nwest,2,1\n", encoding="utf-8"
    )
    (tmp_path / "candidates.csv").write_text(
        "candidate_id,row,column,detected,group_id\n"
        "east_a,1,5,1,east\n"
        "east_b,2,5,1,east\n"
        "west_a,1,0,0,west\n"
        "transient,1,10,0,west\n",
        encoding="utf-8",
    )
    (tmp_path / "declaration.json").write_text(
        json.dumps(
            {
                "analysis_id": "grouped_fixture",
                "thresholds": [0.8, 0.7, 0.6],
                "single_threshold": 0.7,
                "neighbourhood": 4,
                "minimum_persistence_steps": 3,
                "support_distance_weight": 0.5,
                "frozen_before_outcomes": True,
            }
        ),
        encoding="utf-8",
    )
    return run_heldout_validation(
        support_path=tmp_path / "support.npy",
        mask_path=tmp_path / "mask.npy",
        anchors_path=tmp_path / "anchors.csv",
        candidates_path=tmp_path / "candidates.csv",
        declaration_path=tmp_path / "declaration.json",
    )


def test_grouped_metrics_are_emitted_without_inventing_auc(tmp_path):
    bundle = _write_grouped_fixture(tmp_path)
    assert bundle.manifest["group_count"] == 2
    assert bundle.manifest["group_candidate_counts"] == {"east": 2, "west": 2}
    assert bundle.group_metrics["east"]["support_only"]["roc_auc"] is None
    assert bundle.group_metrics["west"]["multi_threshold_persistent"]["roc_auc"] is None
    assert bundle.metrics["multi_threshold_persistent"]["roc_auc"] == 1.0
    assert "mean_squared_score_error" in bundle.metrics["support_only"]


def test_group_id_is_written_to_candidate_rows(tmp_path):
    bundle = _write_grouped_fixture(tmp_path)
    rows = {row["candidate_id"]: row for row in bundle.candidates}
    assert rows["east_a"]["group_id"] == "east"
    assert rows["west_a"]["group_id"] == "west"


def test_blank_group_id_is_rejected(tmp_path):
    _write_grouped_fixture(tmp_path)
    (tmp_path / "candidates.csv").write_text(
        "candidate_id,row,column,detected,group_id\n"
        "positive,1,5,1,\n"
        "negative,1,0,0,west\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="group_id"):
        run_heldout_validation(
            support_path=tmp_path / "support.npy",
            mask_path=tmp_path / "mask.npy",
            anchors_path=tmp_path / "anchors.csv",
            candidates_path=tmp_path / "candidates.csv",
            declaration_path=tmp_path / "declaration.json",
        )
