#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manuscript" / "bam_identifiability" / "figure_data"


def read_csv(name: str):
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save(fig, output_dir: Path, stem: str):
    fig.tight_layout()
    fig.savefig(output_dir / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(output_dir / f"{stem}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def figure2(output_dir: Path):
    rows = read_csv("F2_restrictiveness_scenarios.csv")
    x = [int(row["support_size"]) for row in rows]
    y = [int(row["compatible_world_count"]) for row in rows]
    labels = [row["scenario"] for row in rows]

    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    ax.scatter(x, y, s=70)
    for xi, yi, label in zip(x, y, labels):
        ax.annotate(label, (xi, yi), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Complete positive support size")
    ax.set_ylabel("Compatible candidate worlds")
    ax.set_title("Stronger restriction can increase positive-only ambiguity")
    ax.text(
        0.02,
        0.98,
        "Exact audit: 304/304 strict support-inclusion pairs obeyed\n"
        "R1 ⊂ R2 ⇒ C(R1) ⊇ C(R2); violations = 0",
        transform=ax.transAxes,
        va="top",
        fontsize=9,
    )
    save(fig, output_dir, "Figure2_restrictiveness_ambiguity")


def figure3(output_dir: Path):
    rows = read_csv("F3_evidence_ladder.csv")
    labels = [row["stage"] for row in rows]
    counts = [int(row["unique_count"]) for row in rows]

    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.plot(labels, counts, marker="o")
    ax.set_ylim(0, 810)
    ax.set_ylabel("Uniquely identified BAM states (of 768)")
    ax.set_xlabel("Evidence stage")
    ax.set_title("Progressive evidence contracts BAM survivor fibers")
    for x, y in zip(labels, counts):
        ax.annotate(str(y), (x, y), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8)
    ax.text(
        0.02,
        0.95,
        "Predeclared 'M always last' claim: REFUTED",
        transform=ax.transAxes,
        va="top",
        fontsize=9,
    )
    save(fig, output_dir, "Figure3_evidence_ladder")


def figure4(output_dir: Path):
    rows = read_csv("F4_stochastic_challenge.csv")
    labels = [row["scenario"] for row in rows]
    compatible = [int(row["median_compatible_world_count_h40"]) for row in rows]

    fig, ax = plt.subplots(figsize=(8.4, 4.9))
    bars = ax.bar(labels, compatible)
    ax.set_ylabel("Median compatible worlds at horizon 40")
    ax.set_xlabel("Known-truth stochastic scenario")
    ax.set_title("Independent stochastic challenge preserves non-identification")
    ax.tick_params(axis="x", rotation=30)
    for bar, value in zip(bars, compatible):
        ax.annotate(
            str(value),
            (bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    ax.text(
        0.02,
        0.97,
        "384/384 eligible runs; truth-retention failures = 0; API parity mismatches = 0\n"
        "unordered-history strict improvements = 0/384; unique truth recovery = 0",
        transform=ax.transAxes,
        va="top",
        fontsize=8.5,
    )
    save(fig, output_dir, "Figure4_independent_stochastic")


def figure5(output_dir: Path):
    rows = read_csv("F5_temporal_scenarios.csv")
    labels = [row["scenario"] for row in rows]
    static = [int(row["static_median_compatible"]) for row in rows]
    temporal = [int(row["temporal_median_compatible"]) for row in rows]

    positions = list(range(len(labels)))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.bar([x - width / 2 for x in positions], static, width, label="Static support")
    ax.bar([x + width / 2 for x in positions], temporal, width, label="First-occurrence time")
    ax.set_xticks(positions, labels, rotation=30, ha="right")
    ax.set_ylabel("Median compatible worlds at horizon 40")
    ax.set_title("Time-stamped occurrence history refines static support")
    ax.legend()
    ax.text(
        0.02,
        0.97,
        "8 static classes → 20 temporal classes; 19/48 static M-equivalent pairs split\n"
        "strict temporal contraction in 256/384 runs; unique truth recovery remained 0",
        transform=ax.transAxes,
        va="top",
        fontsize=8.5,
    )
    save(fig, output_dir, "Figure5_temporal_information")


def figure6(output_dir: Path):
    rows = read_csv("F6_exact_measurement_distribution.csv")
    axes = ["A", "B", "AB_joint", "M"]
    max_measure = max(int(row["measurement_count"]) for row in rows)
    lookup = {
        (row["evidence_axis"], int(row["measurement_count"])): int(row["truth_cases"])
        for row in rows
    }

    positions = list(range(len(axes)))
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    bottoms = [0] * len(axes)
    for count in range(max_measure + 1):
        values = [lookup.get((axis, count), 0) for axis in axes]
        ax.bar(positions, values, bottom=bottoms, label=f"{count} nodes")
        bottoms = [a + b for a, b in zip(bottoms, values)]
    ax.set_xticks(positions, ["A", "B", "A+B jointly", "M accessibility"])
    ax.set_ylabel("Truth cases (of 768)")
    ax.set_title("Exact targeted diagnostic-measurement requirements")
    ax.legend(title="Exact minimum")
    ax.text(
        0.02,
        0.97,
        "Programme-wide maxima: A=1, B=2, A+B=3, M=2 nodes\n"
        "Exact hitting-set audit failures = 0/768",
        transform=ax.transAxes,
        va="top",
        fontsize=8.5,
    )
    save(fig, output_dir, "Figure6_diagnostic_measurements")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    figure2(args.output_dir)
    figure3(args.output_dir)
    figure4(args.output_dir)
    figure5(args.output_dir)
    figure6(args.output_dir)


if __name__ == "__main__":
    main()
