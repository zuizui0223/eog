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



def figure1_conceptual():
    from matplotlib.patches import FancyArrowPatch, Rectangle

    fig, ax = plt.subplots(figsize=(11.8, 5.2))
    ax.set_xlim(0, 11.8)
    ax.set_ylim(0, 5.0)
    ax.axis("off")

    # Panel A: forward BAM.
    ax.text(0.4, 4.55, "A  Forward BAM", fontweight="bold")
    forward_boxes = [
        (0.5, 3.1, 1.2, 0.7, "A"),
        (0.5, 2.1, 1.2, 0.7, "B"),
        (0.5, 1.1, 1.2, 0.7, "M"),
    ]
    for x, y, w, h, label in forward_boxes:
        ax.add_patch(Rectangle((x, y), w, h, fill=False, linewidth=1.5))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=12)
    ax.text(2.05, 2.45, "intersection", ha="center", va="center", fontsize=9)
    ax.add_patch(FancyArrowPatch((1.75, 2.45), (2.75, 2.45), arrowstyle="->", mutation_scale=12))
    ax.add_patch(Rectangle((2.8, 2.05), 1.2, 0.8, fill=False, linewidth=1.5))
    ax.text(3.4, 2.45, "G", ha="center", va="center", fontsize=12)
    ax.text(0.55, 0.45, "mechanisms  →  realised distribution", fontsize=9)

    # Panel B: inverse ambiguity.
    ax.text(4.35, 4.55, "B  Inverse BAM", fontweight="bold")
    ax.add_patch(Rectangle((4.55, 2.05), 1.2, 0.8, fill=False, linewidth=1.5))
    ax.text(5.15, 2.45, "observed G", ha="center", va="center", fontsize=11)
    ax.add_patch(FancyArrowPatch((5.8, 2.45), (6.55, 2.45), arrowstyle="->", mutation_scale=12))
    worlds = [
        (6.65, 3.2, "w1: A1,B1,M1"),
        (6.65, 2.3, "w2: A2,B1,M2"),
        (6.65, 1.4, "w3: A1,B2,M3"),
    ]
    for x, y, label in worlds:
        ax.add_patch(Rectangle((x, y), 1.75, 0.55, fill=False, linewidth=1.2))
        ax.text(x + 0.875, y + 0.275, label, ha="center", va="center", fontsize=8)
    ax.text(4.55, 0.45, "one distribution  →  a survivor fiber", fontsize=9)

    # Panel C: evidence contracts the fiber.
    ax.text(8.75, 4.55, "C  Evidence fibers", fontweight="bold")
    stages = [
        (8.9, 3.55, 1.65, "S0  positives"),
        (9.05, 2.70, 1.35, "S1  complete G"),
        (9.20, 1.85, 1.05, "S2+  time / A / B / M"),
        (9.35, 1.00, 0.75, "target fiber"),
    ]
    for x, y, width, label in stages:
        ax.add_patch(Rectangle((x, y), width, 0.55, fill=False, linewidth=1.2))
        ax.text(x + width / 2, y + 0.275, label, ha="center", va="center", fontsize=7.5)
    for (x1, y1, w1, _), (x2, y2, w2, _) in zip(stages, stages[1:]):
        ax.add_patch(
            FancyArrowPatch(
                (x1 + w1 / 2, y1),
                (x2 + w2 / 2, y2 + 0.55),
                arrowstyle="->",
                mutation_scale=10,
            )
        )
    ax.text(8.9, 0.42, "valid evidence contracts or preserves the fiber", fontsize=8.5)

    fig.suptitle(
        "Forward BAM generates distributions; inverse BAM returns evidence-compatible worlds",
        y=0.99,
    )
    _save(fig, "F1_forward_inverse_bam")

def figure2_restrictiveness():
    rows = _read_csv("F2_restrictiveness_scenarios.csv")
    x = [int(row["support_size"]) for row in rows]
    y = [int(row["compatible_world_count"]) for row in rows]
    labels = [row["scenario"] for row in rows]

    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    ax.scatter(x, y)

    # Several frozen truth scenarios have exactly identical coordinates.
    # Combine those labels rather than jittering data values.
    grouped = {}
    for xi, yi, label in zip(x, y, labels, strict=True):
        grouped.setdefault((xi, yi), []).append(label)

    offsets = {
        (33, 32): (8, -18),
        (40, 8): (8, 8),
        (67, 8): (8, 8),
        (96, 4): (-128, 10),
    }
    for (xi, yi), group in sorted(grouped.items()):
        clean = [value.replace("_", " ") for value in group]
        label = " / ".join(clean)
        dx, dy = offsets.get((xi, yi), (6, 6))
        ax.annotate(
            label,
            (xi, yi),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8.5,
            ha="left",
            va="center",
        )

    ax.set_xlabel("Complete positive support size")
    ax.set_ylabel("Compatible candidate worlds")
    ax.set_ylim(2, 35)
    ax.set_title("Stronger restriction can increase positive-only ambiguity", pad=28)
    ax.text(
        0.5,
        1.015,
        "304/304 strict support inclusions obeyed the inverse survivor ordering",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.5,
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
    ax.set_title("Progressive evidence contracts the BAM survivor fiber", pad=28)
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
        0.5,
        1.015,
        "Predeclared claim 'M is always the final bottleneck' was REFUTED",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.5,
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
    ax.set_title("Independent stochastic BAM challenge", pad=42)
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
        0.5,
        1.015,
        "Truth-retention failures = 0; API parity mismatches = 0\n"
        "Positive-witness universality and unordered-history strict gain were REFUTED",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.2,
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
    ax.set_title("Time-stamped positive evidence recovers movement information", pad=42)
    ax.legend()
    ax.text(
        0.5,
        1.015,
        "Static classes 8 → temporal classes 20\n"
        "19/48 static M-equivalent pairs split; strict gain in 256/384 runs",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.2,
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
    figure1_conceptual()
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
