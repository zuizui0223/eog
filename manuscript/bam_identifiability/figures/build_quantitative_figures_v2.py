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

    fig, ax = plt.subplots(figsize=(13.2, 5.4))
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 5.1)
    ax.axis("off")

    # Panel A: forward BAM.
    ax.text(0.35, 4.55, "A  Forward BAM", fontweight="bold")
    forward_boxes = [
        (0.45, 3.10, 1.35, 0.72, "A"),
        (0.45, 2.05, 1.35, 0.72, "B"),
        (0.45, 1.00, 1.35, 0.72, "M"),
    ]
    for x, y, w, h, label in forward_boxes:
        ax.add_patch(Rectangle((x, y), w, h, fill=False, linewidth=1.5))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=12)

    # Keep the intersection label above the arrow so it does not collide with B.
    ax.text(2.48, 2.80, "intersection", ha="center", va="center", fontsize=9)
    ax.add_patch(
        FancyArrowPatch(
            (1.95, 2.42),
            (2.95, 2.42),
            arrowstyle="->",
            mutation_scale=12,
        )
    )
    ax.add_patch(Rectangle((3.00, 2.02), 1.25, 0.80, fill=False, linewidth=1.5))
    ax.text(3.625, 2.42, "G", ha="center", va="center", fontsize=12)
    ax.text(0.55, 0.35, "mechanisms  →  realised distribution", fontsize=9)

    # Panel B: inverse ambiguity.
    ax.text(4.55, 4.55, "B  Inverse BAM", fontweight="bold")
    ax.add_patch(Rectangle((4.75, 2.02), 1.40, 0.80, fill=False, linewidth=1.5))
    ax.text(5.45, 2.42, "observed G", ha="center", va="center", fontsize=11)
    ax.add_patch(
        FancyArrowPatch(
            (6.28, 2.42),
            (7.03, 2.42),
            arrowstyle="->",
            mutation_scale=12,
        )
    )
    worlds = [
        (7.12, 3.18, "w1: A1,B1,M1"),
        (7.12, 2.18, "w2: A2,B1,M2"),
        (7.12, 1.18, "w3: A1,B2,M3"),
    ]
    for x, y, label in worlds:
        ax.add_patch(Rectangle((x, y), 2.05, 0.58, fill=False, linewidth=1.2))
        ax.text(x + 1.025, y + 0.29, label, ha="center", va="center", fontsize=8.3)
    ax.text(4.75, 0.35, "one distribution  →  a survivor fiber", fontsize=9)

    # Panel C: evidence contracts the fiber.
    ax.text(9.55, 4.55, "C  Evidence fibers", fontweight="bold")
    stages = [
        (9.72, 3.54, 2.35, 0.62, "S0  positives", 8.5),
        (9.92, 2.61, 1.95, 0.62, "S1  complete G", 8.3),
        (10.07, 1.64, 1.65, 0.70, "S2+  time\nA / B / M", 7.6),
        (10.30, 0.70, 1.20, 0.68, "target\nfiber", 7.6),
    ]
    for x, y, width, height, label, fontsize in stages:
        ax.add_patch(Rectangle((x, y), width, height, fill=False, linewidth=1.2))
        ax.text(
            x + width / 2,
            y + height / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            linespacing=1.05,
        )
    for current, nxt in zip(stages, stages[1:]):
        x1, y1, w1, h1, _, _ = current
        x2, y2, w2, h2, _, _ = nxt
        ax.add_patch(
            FancyArrowPatch(
                (x1 + w1 / 2, y1 - 0.03),
                (x2 + w2 / 2, y2 + h2 + 0.03),
                arrowstyle="->",
                mutation_scale=10,
            )
        )
    ax.text(
        9.55,
        0.20,
        "valid evidence contracts or preserves the fiber",
        fontsize=8.5,
    )

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
    ax.set_title("Programme-specific diagnostic measurement bounds", pad=34)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.08,
            str(value),
            ha="center",
            va="bottom",
        )
    ax.text(
        0.5,
        1.015,
        "12 systems · 768 truths · exact hitting-set audit · 0 failures",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.2,
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
