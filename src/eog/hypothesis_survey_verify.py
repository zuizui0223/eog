"""Verify a hypothesis-survey result bundle against its declared inputs."""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping

from .hypothesis_discrimination import HypothesisDiscriminationWeights
from .hypothesis_survey_io import run_hypothesis_survey_csv


@dataclass(frozen=True)
class HypothesisSurveyVerification:
    valid: bool
    checks: Mapping[str, bool]
    expected_pipeline_fingerprint: str
    observed_pipeline_fingerprint: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_hypothesis_survey_bundle(
    scenarios_csv: str | Path,
    families_csv: str | Path,
    candidates_csv: str | Path,
    ranking_csv: str | Path,
    manifest_json: str | Path,
) -> HypothesisSurveyVerification:
    """Re-run a bundle and verify hashes, fingerprints, and ranked rows."""
    scenario_path = Path(scenarios_csv)
    family_path = Path(families_csv)
    candidate_path = Path(candidates_csv)
    ranking_path = Path(ranking_csv)
    manifest_path = Path(manifest_json)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    weight_data = manifest["weights"]
    weights = HypothesisDiscriminationWeights(**weight_data)
    with TemporaryDirectory() as temp_dir:
        rerun = run_hypothesis_survey_csv(
            scenario_path,
            family_path,
            candidate_path,
            temp_dir,
            weights=weights,
            require_complete_assignment=manifest["require_complete_assignment"],
        )
        rerun_manifest = json.loads(Path(rerun.manifest_json_path).read_text(encoding="utf-8"))
        checks = {
            "scenarios_hash": manifest["input_hashes"]["scenarios_csv"] == _sha256(scenario_path),
            "families_hash": manifest["input_hashes"]["families_csv"] == _sha256(family_path),
            "candidates_hash": manifest["input_hashes"]["candidates_csv"] == _sha256(candidate_path),
            "pipeline_fingerprint": manifest["pipeline_fingerprint"] == rerun_manifest["pipeline_fingerprint"],
            "adapter_fingerprint": manifest["adapter_fingerprint"] == rerun_manifest["adapter_fingerprint"],
            "ranking_fingerprint": manifest["ranking_fingerprint"] == rerun_manifest["ranking_fingerprint"],
            "ranking_rows": _canonical_csv(ranking_path) == _canonical_csv(Path(rerun.ranking_csv_path)),
        }
    return HypothesisSurveyVerification(
        valid=all(checks.values()),
        checks=checks,
        expected_pipeline_fingerprint=manifest["pipeline_fingerprint"],
        observed_pipeline_fingerprint=rerun_manifest["pipeline_fingerprint"],
    )
