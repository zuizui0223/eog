#!/usr/bin/env python3
"""Build and verify the structural manuscript submission package from frozen inputs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "structural_submission"
AIS_STRONG_RESULT = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json"
AIS_STRONG_PROVENANCE = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_execution_provenance.json"
AIS_STRONG_QA = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome_qa.json"
AIS_STRONG_FINGERPRINT = "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"


class SubmissionPackageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SubmissionPackageError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object in {path}")
    return value


def load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compare_file(generated: Path, committed: Path, label: str) -> None:
    require(generated.is_file(), f"missing generated {label}: {generated}")
    require(committed.is_file(), f"missing committed {label}: {committed}")
    require(generated.read_bytes() == committed.read_bytes(), f"{label} drift: generated {sha256(generated)} != committed {sha256(committed)}")


def copy_verified(src: Path, dst: Path, expected_sha: str | None = None) -> None:
    require(src.is_file(), f"missing package input: {src}")
    if expected_sha is not None:
        require(sha256(src) == expected_sha, f"SHA mismatch before packaging: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def build_figure_1(package: Path) -> None:
    module = load_module("figures/build_figure_1_roles.py", "submission_figure1")
    module.build(ROOT / "figures/figure_1_roles.json", package / "figures/output", package / "manuscript/figure_1_caption.md", package / "manuscript/figure_1_accessibility.md")
    for relative in ("figures/output/figure_1_roles.svg", "figures/output/figure_1_metadata.json", "manuscript/figure_1_caption.md", "manuscript/figure_1_accessibility.md"):
        compare_file(package / relative, ROOT / relative, f"Figure 1 {relative}")


def build_figure_2(package: Path) -> None:
    module = load_module("figures/build_figure_2_aislands.py", "submission_figure2")
    assets = module.build_assets()
    require(bool(assets), "Figure 2 builder returned no assets")
    for relative, text in assets.items():
        destination = package / relative
        write_text(destination, text)
        compare_file(destination, ROOT / relative, f"Figure 2 {relative}")


def build_figure_3(package: Path) -> None:
    module = load_module("figures/build_figure_3_tanzania.py", "submission_figure3")
    historical = load_json(ROOT / "figures/output/figure_3_metadata.json")
    outputs = module.build(output_dir=package / "figures/output", data_dir=package / "manuscript/figure_data", caption_path=package / "manuscript/figure_3_caption.md", accessibility_path=package / "manuscript/figure_3_accessibility.md", build_timestamp=historical["built_at_utc"])
    pairs = {
        "svg": "figures/output/figure_3_tanzania.svg",
        "caption": "manuscript/figure_3_caption.md",
        "accessibility": "manuscript/figure_3_accessibility.md",
        "species": "manuscript/figure_data/tanzania_species_loso_effects.csv",
        "contrasts": "manuscript/figure_data/tanzania_aggregate_contrasts.csv",
        "applicability": "manuscript/figure_data/tanzania_applicability.csv",
        "output_species": "figures/output/tanzania_species_loso_effects.csv",
        "output_contrasts": "figures/output/tanzania_aggregate_contrasts.csv",
        "output_applicability": "figures/output/tanzania_applicability.csv",
    }
    for key, relative in pairs.items():
        compare_file(Path(outputs[key]), ROOT / relative, f"Figure 3 {relative}")
    generated_meta = load_json(Path(outputs["metadata"]))
    frozen = load_json(ROOT / "benchmarks/tanzania_heldout_expected.json")
    require(generated_meta["source"]["result_fingerprint"] == frozen["expected_projection"]["result_fingerprint"], "Figure 3 result fingerprint drift")


def build_figure_4(package: Path) -> None:
    module = load_module("figures/build_figure_4_boundary.py", "submission_figure4")
    historical = load_json(ROOT / "figures/output/figure_4_metadata.json")
    outputs = module.build(panel_data_path=package / "manuscript/figure_data/structural_cross_system_evidence.csv", output_dir=package / "figures/output", caption_path=package / "manuscript/figure_4_caption.md", accessibility_path=package / "manuscript/figure_4_accessibility.md", build_timestamp=historical["built_at_utc"])
    pairs = {
        "svg": "figures/output/figure_4_boundary.svg",
        "panel_data": "manuscript/figure_data/structural_cross_system_evidence.csv",
        "output_panel_data": "figures/output/figure_4_panel_data.csv",
        "caption": "manuscript/figure_4_caption.md",
        "accessibility": "manuscript/figure_4_accessibility.md",
    }
    for key, relative in pairs.items():
        compare_file(Path(outputs[key]), ROOT / relative, f"Figure 4 {relative}")
    generated_meta = load_json(Path(outputs["metadata"]))
    require(generated_meta["metrics_share_axis"] is False, "Figure 4 shared-axis guard drift")
    require(generated_meta["sources"]["tanzania"]["result_fingerprint"] == load_json(ROOT / "benchmarks/tanzania_heldout_expected.json")["expected_projection"]["result_fingerprint"], "Figure 4 Tanzania fingerprint drift")


def build_result_tables(package: Path) -> None:
    module = load_module("manuscript/build_structural_results_tables.py", "submission_tables")
    manifest = module.load_json(module.MANIFEST)
    evidence = module.validate_inputs(manifest)
    table3 = module.build_table3(manifest, evidence)
    applicability = module.build_applicability(manifest, evidence)
    table3_path = package / "manuscript/result_tables/table_3_main_sensitivity_results.csv"
    table_s1_path = package / "manuscript/result_tables/table_s1_applicability_accounting.csv"
    module.write_csv(table3_path, table3)
    module.write_csv(table_s1_path, applicability)
    compare_file(table3_path, ROOT / "manuscript/result_tables/table_3_main_sensitivity_results.csv", "Table 3")
    compare_file(table_s1_path, ROOT / "manuscript/result_tables/table_s1_applicability_accounting.csv", "Table S1")
    metadata = load_json(ROOT / "manuscript/result_tables/structural_results_tables_metadata.json")
    for relative in ("manuscript/result_tables/structural_results_tables.md", "manuscript/result_tables/structural_results_tables_metadata.json", "manuscript/result_tables/result_table_manifest.json"):
        src = ROOT / relative
        if src.name in metadata.get("outputs", {}):
            require(sha256(src) == metadata["outputs"][src.name], f"results-table metadata drift: {src.name}")
        copy_verified(src, package / relative)


def build_figure_5(package: Path) -> None:
    module = load_module("figures/build_figure_5_audit.py", "submission_figure5")
    module.build(ROOT / "figures/figure_5_audit_contract.json", package / "figures/output", package / "manuscript/figure_5_caption.md", package / "manuscript/figure_5_accessibility.md")
    for relative in ("figures/output/figure_5_audit.svg", "figures/output/figure_5_metadata.json", "manuscript/figure_5_caption.md", "manuscript/figure_5_accessibility.md"):
        compare_file(package / relative, ROOT / relative, f"Figure 5 {relative}")


def copy_manuscript_and_submission_files(package: Path) -> None:
    for relative in ("manuscript/structural_reachability_manuscript.md", "manuscript/structural_highlights.txt", "manuscript/structural_verified_references.md", "manuscript/structural_submission_checklist.md"):
        copy_verified(ROOT / relative, package / relative)
    submission_dir = ROOT / "manuscript/submission"
    if submission_dir.is_dir():
        for src in sorted(submission_dir.glob("*")):
            if src.is_file():
                copy_verified(src, package / "manuscript/submission" / src.name)


def copy_island_strong_reference_evidence(package: Path) -> None:
    result = load_json(AIS_STRONG_RESULT)
    provenance = load_json(AIS_STRONG_PROVENANCE)
    qa = load_json(AIS_STRONG_QA)
    require(result.get("result_fingerprint") == AIS_STRONG_FINGERPRINT, "A-Islands strong-reference fingerprint drift")
    require(provenance.get("result_fingerprint") == AIS_STRONG_FINGERPRINT, "A-Islands strong-reference provenance drift")
    require(provenance.get("workflow_run_attempt") == 1 and provenance.get("rerun_allowed") is False, "A-Islands one-time provenance drift")
    require(qa.get("source_result_fingerprint") == AIS_STRONG_FINGERPRINT, "A-Islands strong-reference QA drift")
    for src in (AIS_STRONG_RESULT, AIS_STRONG_PROVENANCE, AIS_STRONG_QA, ROOT / "validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json", ROOT / "validation/aislands_isolation_adequacy_20260812/outcome_execution_authorization.json", ROOT / "validation/aislands_isolation_adequacy_20260812/area_gate_expected.json", ROOT / "validation/aislands_isolation_adequacy_20260812/mainland_gate_expected.json"):
        copy_verified(src, package / src.relative_to(ROOT))


def build_manifest(package: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    for path in sorted(package.rglob("*")):
        if path.is_file() and path.name != "submission_package_manifest.json":
            files[str(path.relative_to(package))] = sha256(path)
    tanzania = load_json(ROOT / "benchmarks/tanzania_heldout_expected.json")
    aislands = load_json(ROOT / "benchmarks/aislands_authoritative_expected.json")
    aislands_strong = load_json(AIS_STRONG_RESULT)
    manifest = {
        "schema_version": "eog_structural_submission_package_v2",
        "source_commit": git_commit(),
        "offline_build": True,
        "network_required": False,
        "scientific_assets_verified_against_committed_outputs": True,
        "aislands": {
            "declared_taxa": aislands["n_declared_taxa"],
            "estimable_taxa": aislands["n_species_estimable"],
            "conditional_concordance": aislands["overall_conditional_concordance"],
            "species_output_sha256": aislands["species_output_sha256"],
        },
        "aislands_strong_reference": {
            "taxa": aislands_strong["taxa_estimable"],
            "evaluable_folds": aislands_strong["folds_evaluable"],
            "heldout_predictions": aislands_strong["heldout_predictions"],
            "c_minus_r3_log_loss_difference": aislands_strong["primary"]["species_macro_mean"],
            "bootstrap_95_ci": aislands_strong["primary"]["bootstrap_95_ci"],
            "species_favourable": aislands_strong["primary"]["species_favourable_negative"],
            "species_adverse": aislands_strong["primary"]["species_adverse_positive"],
            "result_fingerprint": aislands_strong["result_fingerprint"],
            "workflow_run_id": load_json(AIS_STRONG_PROVENANCE)["workflow_run_id"],
            "rerun_allowed": False,
        },
        "tanzania": {
            "species": tanzania["expected_projection"]["n_species"],
            "result_fingerprint": tanzania["expected_projection"]["result_fingerprint"],
            "primary_loso_log_loss_difference": tanzania["expected_projection"]["contrasts"]["primary::primary_loso"]["macro_mean_species_log_loss_difference"],
        },
        "files": files,
    }
    manifest_path = package / "submission_package_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build(package: Path) -> dict[str, Any]:
    package = package.resolve()
    require(package != ROOT.resolve(), "submission package output cannot be the repository root")
    if package.exists():
        shutil.rmtree(package)
    package.mkdir(parents=True, exist_ok=True)
    build_figure_1(package)
    build_figure_2(package)
    build_figure_3(package)
    build_figure_4(package)
    build_result_tables(package)
    build_figure_5(package)
    copy_manuscript_and_submission_files(package)
    copy_island_strong_reference_evidence(package)
    return build_manifest(package)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build(args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), "source_commit": manifest["source_commit"], "file_count": len(manifest["files"]), "aislands_strong_reference_result_fingerprint": manifest["aislands_strong_reference"]["result_fingerprint"], "tanzania_result_fingerprint": manifest["tanzania"]["result_fingerprint"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
