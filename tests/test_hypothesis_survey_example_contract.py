import csv
from pathlib import Path

from eog import run_hypothesis_survey_csv


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hypothesis_survey"


def _rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_canonical_example_reproduces_frozen_ranking(tmp_path):
    bundle = run_hypothesis_survey_csv(
        EXAMPLE / "scenarios.csv",
        EXAMPLE / "families.csv",
        EXAMPLE / "candidates.csv",
        tmp_path,
    )
    observed = _rows(Path(bundle.ranking_csv_path))
    expected = _rows(EXAMPLE / "expected_ranking.csv")

    assert [row["node_id"] for row in observed] == [row["node_id"] for row in expected]
    assert [row["most_separated_hypotheses"] for row in observed] == [
        row["most_separated_hypotheses"] for row in expected
    ]
    for actual, frozen in zip(observed, expected, strict=True):
        for field in (
            "discrimination_score",
            "support_range",
            "mean_pairwise_separation",
            "survey_deficit",
            "accessibility_cost",
        ):
            assert float(actual[field]) == float(frozen[field])
        assert actual["already_surveyed"].lower() == frozen["already_surveyed"].lower()
