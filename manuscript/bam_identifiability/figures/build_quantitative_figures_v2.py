#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
FIG_DATA = ROOT / "manuscript" / "bam_identifiability" / "figure_data"
OUT = ROOT / "build" / "bam_identifiability_figures"


def _read_csv(name: str):
    with (FIG_DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _save(fig, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def figure2_restrictiveness():
    rows = _read_csv("F2_restrictiveness_scenarios.csv")
    x = [int(row["support_size"]) for row in rows]
    y = [int(row["compatible_world_count"]) for row in rows]
    labels = [row["scenario"] for row in rows]

    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.scatter(x, y)
    for xi, yi, label in zip(x, y, labels, strict=True):
        ax.annotate(label, (xi, yi), xytext=(5, 5), textcoords="offset points")
    ax.set_xlabel("Complete positive support size")
    ax.set_ylabel("Compatible candidate worlds")
    ax.set_title("Stronger restriction can increase positive-only ambiguity")
    ax.text(
        0.02,
        0.97,
        "304/304 strict support inclusions obeyed inverse survivor ordering",
        transform=ax.transAxes,
        va="top",
    )
    _save(fig, "F2_restrictiveness_ambiguity")


def figure3_evidence_ladder():
    rows = _read_csv("F3_evidence_ladder.csv")
    stages = [row["stage"] for row in rows]
    counts = [int(row["unique_count"]) for row in rows]
    total = int(rows[0]["total"])

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bars = ax.bar(stages, counts)
    ax.set_ylim(0, total * 1.08)
    ax.set_xlabel("Evidence stage")
    ax.set_ylabel("Uniquely identified BAM states")
    ax.set_title("Progressive evidence contracts the BAM survivor fiber")
    for bar, count in zip(bars, counts, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + total * 0.015,
            f"{count}/{total}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.text(
        0.02,
        0.96,
        "Predeclared claim 'M is always the final bottleneck' was REFUTED",
        transform=ax.transAxes,
        va="top",
    )
    _save(fig, "F3_evidence_ladder")


def figure4_stochastic_challenge():
    result = _read_json(
        "validation/independent_stochastic_bam_v3/result_summary_v3.json"
    )
    scenario_order = [
        "A_limited",
        "partner_limited",
        "antagonist_limited",
        "distance_limited",
        "barrier_limited",
        "joint_ABM",
    ]
    medians = [
        int(result["median_compatible_world_count_h40"][scenario])
        for scenario in scenario_order
    ]
    supports = [
        int(result["truth_structural_reachable_count"][scenario])
        for scenario in scenario_order
    ]

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    bars = ax.bar(range(len(scenario_order)), medians)
    ax.set_xticks(range(len(scenario_order)))
    ax.set_xticklabels(
        [value.replace("_", "\n") for value in scenario_order],
        fontsize=8,
    )
    ax.set_ylabel("Median compatible worlds at horizon 40")
    ax.set_title("Independent stochastic BAM challenge")
    for bar, support in zip(bars, supports, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"support={support}",
            ha="center",
            va="bottom",
            fontsize=7,
        )
    ax.text(
        0.02,
        0.96,
        "Truth-retention failures = 0; API parity mismatches = 0\n"
        "Positive-witness universality REFUTED; unordered-history strict gain REFUTED",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
    )
    _save(fig, "F4_independent_stochastic_challenge")


def figure5_temporal():
    rows = _read_csv("F5_temporal_scenarios.csv")
    labels = [row["scenario"] for row in rows]
    static = [int(row["static_median_compatible"]) for row in rows]
    temporal = [int(row["temporal_median_compatible"]) for row in rows]

    positions = list(range(len(labels)))
    width = 0.38
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    ax.bar([x - width / 2 for x in positions], static, width, label="Static support")
    ax.bar([x + width / 2 for x in positions], temporal, width, label="First-occurrence time")
    ax.set_xticks(positions)
    ax.set_xticklabels([value.replace("_", "\n") for value in labels], fontsize=8)
    ax.set_ylabel("Median compatible worlds at horizon 40")
    ax.set_title("Time-stamped positive evidence recovers movement information")
    ax.legend()
    ax.text(
        0.02,
        0.96,
        "Static classes 8 → temporal classes 20\n"
        "19/48 static M-equivalent pairs split; strict gain in 256/384 runs",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
    )
    _save(fig, "F5_temporal_information")


def figure6_measurement_bounds():
    result = _read_json(
        "validation/bam_identifiability_theory_v1/"
        "targeted_measurement_exact_audit_summary_v1.json"
    )
    bounds = result["exact_maximum_measurements"]
    axes = ["A", "B", "AB_joint", "M"]
    values = [int(bounds[key]) for key in axes]
    labels = ["A", "B", "A+B", "M"]

    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    bars = ax.bar(labels, values)
    ax.set_ylim(0, max(values) + 1)
    ax.set_ylabel("Maximum exact targeted measurements")
    ax.set_title("Programme-specific diagnostic measurement bounds")
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.08,
            str(value),
            ha="center",
            va="bottom",
        )
    ax.text(
        0.02,
        0.96,
        "12 systems · 768 truths · exact hitting-set audit · 0 failures",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
    )
    _save(fig, "F6_targeted_measurement_bounds")


def main() -> int:
    figure2_restrictiveness()
    figure3_evidence_ladder()
    figure4_stochastic_challenge()
    figure5_temporal()
    figure6_measurement_bounds()
    outputs = sorted(path.name for path in OUT.iterdir())
    print(json.dumps({"output_dir": str(OUT), "files": outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
