"""Render a human-readable report from a verified hypothesis-survey bundle."""
from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
from typing import Sequence

from .hypothesis_survey_verify import verify_hypothesis_survey_bundle


@dataclass(frozen=True)
class HypothesisSurveyReport:
    output_path: str
    top_candidate_ids: tuple[str, ...]
    zero_information_candidate_ids: tuple[str, ...]
    pipeline_fingerprint: str


def _read_ranking(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("ranking CSV has no rows")
    return rows


def render_hypothesis_survey_report(
    scenarios_csv: str | Path,
    families_csv: str | Path,
    candidates_csv: str | Path,
    ranking_csv: str | Path,
    manifest_json: str | Path,
    output_markdown: str | Path,
    *,
    top_n: int = 10,
) -> HypothesisSurveyReport:
    """Verify a bundle and render a deterministic Markdown decision report."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    verification = verify_hypothesis_survey_bundle(
        scenarios_csv,
        families_csv,
        candidates_csv,
        ranking_csv,
        manifest_json,
    )
    if not verification.valid:
        failed = ", ".join(sorted(name for name, ok in verification.checks.items() if not ok))
        raise ValueError(f"hypothesis survey bundle verification failed: {failed}")

    manifest = json.loads(Path(manifest_json).read_text(encoding="utf-8"))
    rows = _read_ranking(Path(ranking_csv))
    selected = rows[:top_n]
    zero_information = tuple(manifest.get("zero_information_candidate_ids", ()))
    informative = tuple(manifest.get("informative_candidate_ids", ()))

    lines = [
        "# Hypothesis-discriminating survey report",
        "",
        "## Decision summary",
        "",
        f"- Verified bundle: yes",
        f"- Ranked candidates: {len(rows)}",
        f"- Informative candidates: {len(informative)}",
        f"- Zero-information candidates: {len(zero_information)}",
        f"- Pipeline fingerprint: `{manifest['pipeline_fingerprint']}`",
        "",
        "The scores quantify disagreement among declared bridge-hypothesis families, adjusted by survey deficit and accessibility. They are not occurrence probabilities, posterior model probabilities, or expected information gain.",
        "",
        f"## Top {min(top_n, len(rows))} survey candidates",
        "",
        "| Rank | Candidate | Score | Support range | Mean pairwise separation | Most separated hypotheses | Survey deficit | Accessibility cost | Already surveyed |",
        "|---:|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in selected:
        lines.append(
            "| {rank} | {node_id} | {discrimination_score} | {support_range} | "
            "{mean_pairwise_separation} | {most_separated_hypotheses} | {survey_deficit} | "
            "{accessibility_cost} | {already_surveyed} |".format(**row)
        )

    lines.extend(["", "## Interpretation", ""])
    first = selected[0]
    lines.append(
        f"The highest-ranked candidate is **{first['node_id']}**. Its strongest declared hypothesis contrast is "
        f"**{first['most_separated_hypotheses']}**, with a support range of {first['support_range']}."
    )
    if zero_information:
        lines.extend(
            [
                "",
                "## Zero-information candidates",
                "",
                ", ".join(f"`{node_id}`" for node_id in zero_information),
                "",
                "These candidates have identical support across the declared hypothesis families under the current scenario and path declarations. They may still be useful for other ecological questions, but not for discriminating the hypotheses represented in this bundle.",
            ]
        )
    lines.extend(
        [
            "",
            "## Audit identifiers",
            "",
            f"- Sensitivity fingerprint: `{manifest['sensitivity_fingerprint']}`",
            f"- Adapter fingerprint: `{manifest['adapter_fingerprint']}`",
            f"- Ranking fingerprint: `{manifest['ranking_fingerprint']}`",
            f"- Complete scenario assignment required: `{manifest['require_complete_assignment']}`",
            "",
        ]
    )

    output_path = Path(output_markdown)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return HypothesisSurveyReport(
        output_path=str(output_path),
        top_candidate_ids=tuple(row["node_id"] for row in selected),
        zero_information_candidate_ids=zero_information,
        pipeline_fingerprint=manifest["pipeline_fingerprint"],
    )
