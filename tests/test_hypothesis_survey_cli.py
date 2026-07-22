from pathlib import Path

from eog.hypothesis_survey_cli import main


def test_cli_runs_example(tmp_path, capsys):
    root = Path(__file__).resolve().parents[1]
    example = root / "examples" / "hypothesis_survey"
    code = main(
        [
            "--scenarios",
            str(example / "scenarios.csv"),
            "--families",
            str(example / "families.csv"),
            "--candidates",
            str(example / "candidates.csv"),
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert code == 0
    assert (tmp_path / "hypothesis_survey_ranking.csv").exists()
    assert (tmp_path / "hypothesis_survey_manifest.json").exists()
    output = capsys.readouterr().out
    assert "bundle_fingerprint=" in output
