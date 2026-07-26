import csv
import json
from pathlib import Path

import numpy as np
import pytest

from eog.support_topology_validation import run_heldout_validation, write_validation_bundle


def _write_fixture(tmp_path: Path):
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

    support_path = tmp_path / "support.npy"
    mask_path = tmp_path / "mask.npy"
    np.save(support_path, support)
    np.save(mask_path, mask)

    anchors_path = tmp_path / "anchors.csv"
    anchors_path.write_text("anchor_id,row,column\nwest,2,1\n", encoding="utf-8")

    candidates_path = tmp_path / "candidates.csv"
    candidates_path.write_text(
        "candidate_id,row,column,detected\n"
        "east_a,1,5,1\n"
        "east_b,2,5,1\n"
        "west_a,1,0,0\n"
        "transient,1,10,0\n",
        encoding="utf-8",
    )

    declaration_path = tmp_path / "declaration.json"
    declaration_path.write_text(
        json.dumps(
            {
                "analysis_id": "fixture",
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
    return support_path, mask_path, anchors_path, candidates_path, declaration_path


def _run(tmp_path: Path):
    paths = _write_fixture(tmp_path)
    return run_heldout_validation(
        support_path=paths[0],
        mask_path=paths[1],
        anchors_path=paths[2],
        candidates_path=paths[3],
        declaration_path=paths[4],
    )


def test_real_taxon_adapter_is_deterministic_and_hashes_inputs(tmp_path):
    first = _run(tmp_path)
    second = run_heldout_validation(
        support_path=tmp_path / "support.npy",
        mask_path=tmp_path / "mask.npy",
        anchors_path=tmp_path / "anchors.csv",
        candidates_path=tmp_path / "candidates.csv",
        declaration_path=tmp_path / "declaration.json",
    )
    assert first.fingerprint == second.fingerprint
    assert len(first.manifest["input_sha256"]) == 5
    assert all(len(value) == 64 for value in first.manifest["input_sha256"].values())


def test_multi_threshold_distinguishes_persistent_and_transient_candidates(tmp_path):
    bundle = _run(tmp_path)
    rows = {row["candidate_id"]: row for row in bundle.candidates}
    assert rows["east_a"]["multi_threshold_class"] == "persistent_detached_component"
    assert rows["transient"]["single_threshold_class"] == "persistent_detached_component"
    assert rows["transient"]["multi_threshold_class"] == "transient_detached_component"
    assert rows["transient"]["scores"]["multi_threshold_persistent"] == 0.0
    assert bundle.metrics["multi_threshold_persistent"]["roc_auc"] == 1.0


def test_bundle_writer_emits_json_and_flat_candidate_csv(tmp_path):
    bundle = _run(tmp_path)
    output = tmp_path / "output"
    write_validation_bundle(bundle, output)
    payload = json.loads((output / "validation_bundle.json").read_text())
    assert payload["fingerprint"] == bundle.fingerprint
    with (output / "candidate_scores.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert "multi_threshold_persistent" in rows[0]


def test_adapter_rejects_unfrozen_declaration(tmp_path):
    paths = _write_fixture(tmp_path)
    declaration = json.loads(paths[4].read_text())
    declaration["frozen_before_outcomes"] = False
    paths[4].write_text(json.dumps(declaration), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen before outcomes"):
        run_heldout_validation(
            support_path=paths[0],
            mask_path=paths[1],
            anchors_path=paths[2],
            candidates_path=paths[3],
            declaration_path=paths[4],
        )


def test_adapter_rejects_candidate_on_masked_cell(tmp_path):
    paths = _write_fixture(tmp_path)
    paths[3].write_text(
        "candidate_id,row,column,detected\npositive,0,0,1\nnegative,1,0,0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unavailable cell"):
        run_heldout_validation(
            support_path=paths[0],
            mask_path=paths[1],
            anchors_path=paths[2],
            candidates_path=paths[3],
            declaration_path=paths[4],
        )
