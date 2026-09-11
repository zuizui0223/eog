#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build/structural_submission_v2"
BOUNDARY = ROOT / "manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json"


class StructuralPackageV2Error(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StructuralPackageV2Error(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_assets(package: Path, assets: dict[str, str]) -> None:
    for relative, content in assets.items():
        destination = package / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def build(output_dir: Path) -> dict:
    output_dir = output_dir.resolve()
    require(output_dir != ROOT.resolve(), "output cannot be repository root")

    legacy = load_module("manuscript/build_structural_submission_package.py", "structural_package_v1")
    manifest = legacy.build(output_dir)

    fig1 = load_module("figures/build_figure_1_reference_conditioned.py", "structural_fig1_v2")
    fig2 = load_module("figures/build_figure_2_aislands_reference_conditioned.py", "structural_fig2_v2")
    fig1_assets = fig1.build_assets()
    fig2_assets = fig2.build_assets()
    write_assets(output_dir, fig1_assets)
    write_assets(output_dir, fig2_assets)

    boundary_dst = output_dir / BOUNDARY.relative_to(ROOT)
    boundary_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BOUNDARY, boundary_dst)

    canonical = {
        "figure_1": "figures/output/figure_1_reference_conditioned.svg",
        "figure_2": "figures/output/figure_2_aislands_reference_conditioned.svg",
        "figure_3": "figures/output/figure_3_tanzania.svg",
        "figure_4": "figures/output/figure_4_boundary.svg",
        "figure_5": "figures/output/figure_5_audit.svg",
    }
    for path in canonical.values():
        require((output_dir / path).is_file(), f"missing canonical structural figure: {path}")

    files = {
        str(path.relative_to(output_dir)): sha256(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "submission_package_manifest_v2.json"
    }
    receipt = {
        "schema": "eog.structural_submission_package.v3",
        "source_commit": manifest["source_commit"],
        "scientific_evidence_rebuilt_by_v1_builder": True,
        "presentation_only_v2_figures": ["figure_1", "figure_2"],
        "canonical_submission_figures": canonical,
        "metrics_share_axis_in_aislands_figure": False,
        "eog_wf_empirical_denominator_included": False,
        "structural_paper_boundary": "manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json",
        "aislands_strong_reference_result_fingerprint": manifest["aislands_strong_reference"]["result_fingerprint"],
        "tanzania_result_fingerprint": manifest["tanzania"]["result_fingerprint"],
        "files": files,
    }
    receipt_path = output_dir / "submission_package_manifest_v2.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    receipt = build(args.output_dir)
    print(json.dumps({
        "schema": receipt["schema"],
        "source_commit": receipt["source_commit"],
        "file_count": len(receipt["files"]),
        "figure_1": receipt["canonical_submission_figures"]["figure_1"],
        "figure_2": receipt["canonical_submission_figures"]["figure_2"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
