from pathlib import Path

import pytest

from eog import render_hypothesis_survey_report, run_hypothesis_survey_csv


EXAMPLE = Path("examples/hypothesis_survey")


def make_bundle(tmp_path):
    return run_hypothesis_survey_csv(
        EXAMPLE / "scenarios.csv",
        EXAMPLE / "families.csv",
        EXAMPLE / "candidates.csv",
        tmp_path / "bundle",
    )


def test_report_renders_verified_decision_summary(tmp_path):
    bundle = make_bundle(tmp_path)
    output = tmp_path / "report.md"
    report = render_hypothesis_survey_report(
        EXAMPLE / "scenarios.csv",
        EXAMPLE / "families.csv",
        EXAMPLE / "candidates.csv",
        bundle.ranking_csv_path,
        bundle.manifest_json_path,
        output,
        top_n=2,
    )
    text = output.read_text(encoding="utf-8")
    assert report.top_candidate_ids == ("south", "north")
    assert "Verified bundle: yes" in text
    assert "The highest-ranked candidate is **south**" in text
    assert "not occurrence probabilities" in text
    assert report.pipeline_fingerprint in text


def test_report_refuses_tampered_ranking(tmp_path):
    bundle = make_bundle(tmp_path)
    ranking = Path(bundle.ranking_csv_path)
    ranking.write_text(
        ranking.read_text(encoding="utf-8").replace("2.9", "99.0"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="verification failed"):
        render_hypothesis_survey_report(
            EXAMPLE / "scenarios.csv",
            EXAMPLE / "families.csv",
            EXAMPLE / "candidates.csv",
            ranking,
            bundle.manifest_json_path,
            tmp_path / "report.md",
        )


def test_report_rejects_invalid_top_n(tmp_path):
    bundle = make_bundle(tmp_path)
    with pytest.raises(ValueError, match="top_n"):
        render_hypothesis_survey_report(
            EXAMPLE / "scenarios.csv",
            EXAMPLE / "families.csv",
            EXAMPLE / "candidates.csv",
            bundle.ranking_csv_path,
            bundle.manifest_json_path,
            tmp_path / "report.md",
            top_n=0,
        )
