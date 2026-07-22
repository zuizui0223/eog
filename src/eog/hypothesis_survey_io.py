"""CSV input and audited output helpers for hypothesis survey prioritization."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

from .bridge_sensitivity import BridgeScenarioResult, BridgeSensitivityResult
from .hypothesis_adapter import HypothesisFamilyDeclaration
from .hypothesis_discrimination import HypothesisDiscriminationWeights
from .hypothesis_survey_pipeline import (
    HypothesisSurveyPipelineResult,
    run_hypothesis_survey_pipeline,
)
from .survey_priority import SurveyCandidate


SCENARIO_COLUMNS = (
    "scenario_id",
    "connected",
    "minimum_cost_nodes",
    "minimum_bottleneck_nodes",
)
FAMILY_COLUMNS = ("hypothesis_id", "scenario_id", "path_mode")
CANDIDATE_COLUMNS = (
    "node_id",
    "survey_effort",
    "accessibility_cost",
    "already_surveyed",
)


@dataclass(frozen=True)
class HypothesisSurveyRunBundle:
    result: HypothesisSurveyPipelineResult
    input_hashes: Mapping[str, str]
    ranking_csv_path: str
    manifest_json_path: str
    fingerprint: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path, required: Iterable[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        missing = sorted(set(required) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"missing columns in {path}: {', '.join(missing)}")
        rows = [dict(row) for row in reader]
    if not rows:
        raise ValueError(f"CSV has no data rows: {path}")
    return rows


def _bool(value: str, *, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"{field} must be a boolean value")


def _non_negative_float(value: str, *, field: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if parsed < 0 or parsed != parsed or parsed in {float("inf"), float("-inf")}:
        raise ValueError(f"{field} must be finite and non-negative")
    return parsed


def _path(value: str) -> tuple[str, ...]:
    nodes = tuple(part.strip() for part in value.split("|") if part.strip())
    return nodes


def load_sensitivity_csv(path: str | Path) -> BridgeSensitivityResult:
    csv_path = Path(path)
    rows = _read_rows(csv_path, SCENARIO_COLUMNS)
    scenarios: list[BridgeScenarioResult] = []
    seen: set[str] = set()
    for row in rows:
        scenario_id = row["scenario_id"].strip()
        if not scenario_id:
            raise ValueError("scenario_id must be non-empty")
        if scenario_id in seen:
            raise ValueError(f"duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
        connected = _bool(row["connected"], field="connected")
        cost_nodes = _path(row["minimum_cost_nodes"])
        bottleneck_nodes = _path(row["minimum_bottleneck_nodes"])
        if connected and (len(cost_nodes) < 2 or len(bottleneck_nodes) < 2):
            raise ValueError(f"connected scenario requires both paths: {scenario_id}")
        if not connected and (cost_nodes or bottleneck_nodes):
            raise ValueError(f"disconnected scenario must not declare paths: {scenario_id}")
        scenarios.append(
            BridgeScenarioResult(
                scenario_id=scenario_id,
                scenario_fingerprint=row.get("scenario_fingerprint", "").strip()
                or hashlib.sha256(scenario_id.encode()).hexdigest(),
                graph_fingerprint=(row.get("graph_fingerprint", "").strip() or None)
                if connected
                else None,
                connected=connected,
                failure_reason=row.get("failure_reason", "").strip()
                or ("" if connected else "disconnected"),
                minimum_cost_nodes=cost_nodes,
                minimum_bottleneck_nodes=bottleneck_nodes,
                cumulative_cost=None,
                bottleneck_cost=None,
                geographic_cost=None,
                environmental_cost=None,
                barrier_cost=None,
                bridge_gain=None,
                edge_disjoint_path_count=None,
            )
        )
    scenarios.sort(key=lambda item: item.scenario_id)
    payload = [
        {
            "scenario_id": item.scenario_id,
            "connected": item.connected,
            "minimum_cost_nodes": item.minimum_cost_nodes,
            "minimum_bottleneck_nodes": item.minimum_bottleneck_nodes,
        }
        for item in scenarios
    ]
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    connected_count = sum(item.connected for item in scenarios)
    return BridgeSensitivityResult(
        source_id=scenarios[0].minimum_cost_nodes[0] if scenarios[0].connected else "source",
        target_id=scenarios[0].minimum_cost_nodes[-1] if scenarios[0].connected else "target",
        scenario_count=len(scenarios),
        connected_count=connected_count,
        connected_frequency=connected_count / len(scenarios),
        direct_edge_scenario_count=0,
        positive_bridge_gain_count=0,
        positive_bridge_gain_frequency=None,
        minimum_cost_node_support={},
        minimum_bottleneck_node_support={},
        minimum_cost_edge_support={},
        metric_summaries={},
        scenarios=tuple(scenarios),
        fingerprint=fingerprint,
    )


def load_families_csv(path: str | Path) -> tuple[HypothesisFamilyDeclaration, ...]:
    rows = _read_rows(Path(path), FAMILY_COLUMNS)
    grouped: dict[tuple[str, str], list[str]] = {}
    scenario_owner: dict[str, str] = {}
    for row in rows:
        hypothesis_id = row["hypothesis_id"].strip()
        scenario_id = row["scenario_id"].strip()
        path_mode = row["path_mode"].strip() or "minimum_cost"
        if not hypothesis_id or not scenario_id:
            raise ValueError("hypothesis_id and scenario_id must be non-empty")
        owner = scenario_owner.get(scenario_id)
        if owner is not None and owner != hypothesis_id:
            raise ValueError(f"scenario assigned to multiple hypotheses: {scenario_id}")
        scenario_owner[scenario_id] = hypothesis_id
        grouped.setdefault((hypothesis_id, path_mode), []).append(scenario_id)
    modes_by_hypothesis: dict[str, set[str]] = {}
    for hypothesis_id, path_mode in grouped:
        modes_by_hypothesis.setdefault(hypothesis_id, set()).add(path_mode)
    conflicting = sorted(key for key, modes in modes_by_hypothesis.items() if len(modes) > 1)
    if conflicting:
        raise ValueError(f"hypothesis has multiple path modes: {', '.join(conflicting)}")
    return tuple(
        HypothesisFamilyDeclaration(
            hypothesis_id=hypothesis_id,
            scenario_ids=tuple(sorted(set(scenario_ids))),
            path_mode=path_mode,
        )
        for (hypothesis_id, path_mode), scenario_ids in sorted(grouped.items())
    )


def load_candidates_csv(path: str | Path) -> tuple[SurveyCandidate, ...]:
    rows = _read_rows(Path(path), CANDIDATE_COLUMNS)
    candidates: list[SurveyCandidate] = []
    seen: set[str] = set()
    for row in rows:
        node_id = row["node_id"].strip()
        if not node_id:
            raise ValueError("node_id must be non-empty")
        if node_id in seen:
            raise ValueError(f"duplicate node_id: {node_id}")
        seen.add(node_id)
        candidates.append(
            SurveyCandidate(
                node_id=node_id,
                survey_effort=_non_negative_float(row["survey_effort"], field="survey_effort"),
                accessibility_cost=_non_negative_float(
                    row["accessibility_cost"], field="accessibility_cost"
                ),
                already_surveyed=_bool(row["already_surveyed"], field="already_surveyed"),
            )
        )
    return tuple(sorted(candidates, key=lambda item: item.node_id))


def run_hypothesis_survey_csv(
    scenarios_csv: str | Path,
    families_csv: str | Path,
    candidates_csv: str | Path,
    output_dir: str | Path,
    *,
    weights: HypothesisDiscriminationWeights = HypothesisDiscriminationWeights(),
    require_complete_assignment: bool = True,
) -> HypothesisSurveyRunBundle:
    scenario_path = Path(scenarios_csv)
    family_path = Path(families_csv)
    candidate_path = Path(candidates_csv)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    sensitivity = load_sensitivity_csv(scenario_path)
    families = load_families_csv(family_path)
    candidates = load_candidates_csv(candidate_path)
    result = run_hypothesis_survey_pipeline(
        sensitivity,
        families,
        candidates,
        weights=weights,
        require_complete_assignment=require_complete_assignment,
    )
    hashes = {
        "scenarios_csv": _sha256(scenario_path),
        "families_csv": _sha256(family_path),
        "candidates_csv": _sha256(candidate_path),
    }
    ranking_path = output_path / "hypothesis_survey_ranking.csv"
    with ranking_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = (
            "rank",
            "node_id",
            "discrimination_score",
            "support_range",
            "mean_pairwise_separation",
            "most_separated_hypotheses",
            "survey_deficit",
            "accessibility_cost",
            "already_surveyed",
        )
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(result.ranking.rows, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "node_id": row.node_id,
                    "discrimination_score": row.discrimination_score,
                    "support_range": row.support_range,
                    "mean_pairwise_separation": row.mean_pairwise_separation,
                    "most_separated_hypotheses": "|".join(row.most_separated_hypotheses),
                    "survey_deficit": row.survey_deficit,
                    "accessibility_cost": row.accessibility_cost,
                    "already_surveyed": row.already_surveyed,
                }
            )
    manifest_path = output_path / "hypothesis_survey_manifest.json"
    manifest = {
        "input_hashes": hashes,
        "sensitivity_fingerprint": sensitivity.fingerprint,
        "pipeline_fingerprint": result.fingerprint,
        "adapter_fingerprint": result.adapter.fingerprint,
        "ranking_fingerprint": result.ranking.fingerprint,
        "weights": asdict(weights),
        "require_complete_assignment": require_complete_assignment,
        "informative_candidate_ids": result.informative_candidate_ids,
        "zero_information_candidate_ids": result.zero_information_candidate_ids,
        "unassigned_scenario_ids": result.adapter.unassigned_scenario_ids,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    bundle_fingerprint = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return HypothesisSurveyRunBundle(
        result=result,
        input_hashes=hashes,
        ranking_csv_path=str(ranking_path),
        manifest_json_path=str(manifest_path),
        fingerprint=bundle_fingerprint,
    )
