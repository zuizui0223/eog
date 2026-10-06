#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "manuscript" / "history_storage" / "figures"

FILES = {
    "v28": ROOT / "validation/eog_original_idea_leopold_history_retention_v28/result_summary_v28.json",
    "v30": ROOT / "validation/eog_grassland_above_below_history_retention_v30/result_summary_v30.json",
    "v31": ROOT / "validation/eog_identity_storage_rank_abundance_v31/result_summary_v31.json",
    "v33": ROOT / "validation/eog_role_mapping_specificity_v33/result_summary_v33.json",
    "v34": ROOT / "validation/eog_history_level_leverage_v34/result_summary_v34.json",
    "v36": ROOT / "validation/eog_alternaria_binary_components_v36/result_summary_v36.json",
    "v37": ROOT / "validation/eog_alternaria_genotype_generality_v37/result_summary_v37.json",
}


def load():
    return {key: json.loads(path.read_text()) for key, path in FILES.items()}


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def box(ax, xy, text, width=0.25, height=0.13):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        facecolor="white",
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=10)
    return patch


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=12, linewidth=1.2))


def figure1():
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box(ax, (0.06, 0.43), "Manipulated\nassembly history", 0.20, 0.16)
    box(ax, (0.40, 0.70), "Ecological identity\nWho is abundant?", 0.25, 0.15)
    box(ax, (0.40, 0.43), "Abundance architecture\nHow unequal are ranks?", 0.25, 0.15)
    box(ax, (0.40, 0.16), "Downstream state\nHost / spatial / aggregate", 0.25, 0.15)

    arrow(ax, (0.26, 0.51), (0.40, 0.775))
    arrow(ax, (0.26, 0.51), (0.40, 0.505))
    arrow(ax, (0.26, 0.51), (0.40, 0.235))

    box(ax, (0.73, 0.66), "Microbiome\ncomposition → rust", 0.21, 0.16)
    box(ax, (0.73, 0.28), "Grassland\nshoot → roots", 0.21, 0.16)
    arrow(ax, (0.65, 0.51), (0.73, 0.74))
    arrow(ax, (0.65, 0.51), (0.73, 0.36))

    ax.text(0.06, 0.91, "Where is assembly history stored in the present?", fontsize=15, weight="bold")
    ax.text(
        0.06, 0.06,
        "Storage is descriptive: a target retains history when randomized assembly histories remain distinguishable.",
        fontsize=9,
    )
    save(fig, "Figure1_storage_problem")


def interval_panel(ax, items, title):
    y = list(range(len(items)))[::-1]
    labels = []
    for yi, item in zip(y, items):
        labels.append(item["label"])
        ax.hlines(yi, item["q025"], item["q975"], linewidth=4, alpha=0.35)
        ax.plot(item["median"], yi, marker="|", markersize=13)
        ax.plot(item["observed"], yi, marker="o", markersize=6)
        annotation_x = min(max(item["q975"], item["observed"]) + 0.025, 1.04)
        ax.text(
            annotation_x, yi,
            f"E={item['E']:+.3f}\np={item['p']:.4f}",
            va="center", fontsize=8,
        )
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("Partial history $R^2$")
    ax.set_title(title, loc="left", fontsize=11, weight="bold")
    ax.spines[["top", "right"]].set_visible(False)


def figure2(d):
    v28 = d["v28"]["primary"]
    v30 = d["v30"]["primary"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharex=True)

    interval_panel(
        axes[0],
        [
            {
                "label": "Fungal composition",
                "observed": v28["fungal_community_composition"]["partial_r2"],
                "median": v28["fungal_community_composition"]["null_median"],
                "q025": v28["fungal_community_composition"]["null_q025"],
                "q975": v28["fungal_community_composition"]["null_q975"],
                "E": v28["fungal_community_composition"]["excess_over_null_median"],
                "p": v28["fungal_community_composition"]["permutation_p"],
            },
            {
                "label": "Rust lesion state",
                "observed": v28["rust_lesion_fraction"]["partial_r2"],
                "median": v28["rust_lesion_fraction"]["null_median"],
                "q025": v28["rust_lesion_fraction"]["null_q025"],
                "q975": v28["rust_lesion_fraction"]["null_q975"],
                "E": v28["rust_lesion_fraction"]["excess_over_null_median"],
                "p": v28["rust_lesion_fraction"]["permutation_p"],
            },
        ],
        "A  Plant microbiome",
    )

    interval_panel(
        axes[1],
        [
            {
                "label": "Shoot composition",
                "observed": v30["shoot_functional_group_composition"]["partial_r2"],
                "median": v30["shoot_functional_group_composition"]["null_median"],
                "q025": v30["shoot_functional_group_composition"]["null_q025"],
                "q975": v30["shoot_functional_group_composition"]["null_q975"],
                "E": v30["shoot_functional_group_composition"]["excess_over_null_median"],
                "p": v30["shoot_functional_group_composition"]["permutation_p"],
            },
            {
                "label": "Root distribution",
                "observed": v30["root_vertical_distribution"]["partial_r2"],
                "median": v30["root_vertical_distribution"]["null_median"],
                "q025": v30["root_vertical_distribution"]["null_q025"],
                "q975": v30["root_vertical_distribution"]["null_q975"],
                "E": v30["root_vertical_distribution"]["excess_over_null_median"],
                "p": v30["root_vertical_distribution"]["permutation_p"],
            },
        ],
        "B  Grassland",
    )

    fig.suptitle("Assembly history is retained unevenly across present-state targets", fontsize=14, weight="bold")
    fig.tight_layout()
    save(fig, "Figure2_target_specific_retention")


def figure3(d):
    s = d["v31"]["systems"]
    systems = ["v28_microbiome", "v30_grassland"]
    labels = ["Microbiome", "Grassland"]
    fig, ax = plt.subplots(figsize=(7.4, 4.8))

    x_labeled, x_rank, x_shannon = 0, 1, 1.28
    x_offsets = [-0.025, 0.025]
    for sys, label, off in zip(systems, labels, x_offsets):
        row = s[sys]
        line, = ax.plot(
            [x_labeled + off, x_rank + off],
            [row["labeled_E"], row["rank_abundance_E"]],
            marker="o", linewidth=1.6, label=label,
        )
        ax.plot(
            x_shannon + off,
            row["shannon_E"],
            marker="o",
            fillstyle="none",
            color=line.get_color(),
        )
        ax.text(
            x_rank + off + 0.04,
            row["rank_abundance_E"],
            f"{row['rank_fraction_of_labeled_E']*100:.1f}% retained",
            va="center", fontsize=8,
        )

    ax.set_xticks([x_labeled, x_rank, x_shannon], ["Labeled\ncomposition", "Identity-stripped\nrank abundance", "Shannon"])
    ax.set_ylabel("Retained-history excess, E")
    ax.set_title("Removing identity reveals different structural storage channels", loc="left", fontsize=12, weight="bold")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "Figure3_identity_stripping")


def figure4(d):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.2))

    # A: placebo mapping specificity
    ax = axes[0, 0]
    rows = [
        ("Microbiome", d["v33"]["v28_microbiome"]),
        ("Grassland", d["v33"]["v30_grassland"]),
    ]
    y_positions = [1, 0]
    for idx, ((label, row), yi) in enumerate(zip(rows, y_positions)):
        correct_label = "Correct mapping" if idx == 0 else None
        median_label = "Incorrect median" if idx == 0 else None
        max_label = "Incorrect maximum" if idx == 0 else None
        ax.plot(
            row["correct_partial_r2"], yi,
            marker="o", markersize=7, linestyle="None", label=correct_label,
        )
        ax.plot(
            row["incorrect_mapping_median_r2"], yi,
            marker="s", markersize=6, fillstyle="none", linestyle="None", label=median_label,
        )
        ax.plot(
            row["incorrect_mapping_max_r2"], yi,
            marker="^", markersize=6, fillstyle="none", linestyle="None", label=max_label,
        )
        text_x = max(0.27, row["correct_partial_r2"] - 0.18)
        ax.text(
            text_x, yi - 0.19,
            (
                f"rank {row['correct_rank_descending']}/{row['mapping_count']}; "
                f"p_map={row['exact_upper_tail_mapping_probability']:.3f}"
            ),
            fontsize=8,
        )
    ax.set_yticks(y_positions, [row[0] for row in rows])
    ax.set_xlim(0.25, 1.0)
    ax.set_ylim(-0.35, 1.25)
    ax.set_xlabel("Role-aligned partial $R^2$")
    ax.set_title("A  Correct role mapping is not specific", loc="left", fontsize=10, weight="bold")
    ax.legend(frameon=False, fontsize=7, loc="center", bbox_to_anchor=(0.58, 0.50))
    ax.spines[["top", "right"]].set_visible(False)

    # B: deletion leverage
    ax = axes[0, 1]
    lev = d["v34"]["leave_one_history_out"]
    order = d["v34"]["leverage_order_descending"]
    values = [lev[name]["leverage_D"] for name in order]
    ax.barh(range(len(order)), values)
    ax.axvline(0, linewidth=1)
    ax.set_yticks(range(len(order)), order)
    ax.invert_yaxis()
    ax.set_xlabel("Deletion leverage, $D_h$")
    ax.set_title("B  History-level leverage is uneven", loc="left", fontsize=10, weight="bold")
    ax.spines[["top", "right"]].set_visible(False)

    # C: direct dominance vs tail
    ax = axes[1, 0]
    comp = [
        ("Rank-1\ndominance", d["v36"]["dominance"]["E"], d["v36"]["dominance"]["permutation_p"]),
        ("Lower-rank\ntail", d["v36"]["lower_rank_tail"]["E"], d["v36"]["lower_rank_tail"]["permutation_p"]),
    ]
    xs = range(len(comp))
    vals = [x[1] for x in comp]
    ax.bar(xs, vals)
    for i, (_, val, p) in enumerate(comp):
        ax.text(i, val + 0.006, f"p={p:.4f}", ha="center", fontsize=8)
    ax.set_xticks(list(xs), [x[0] for x in comp])
    ax.set_ylabel("Alternaria-vs-rest E")
    ax.set_title("C  Alternaria legacy is dominance-centered", loc="left", fontsize=10, weight="bold")
    ax.spines[["top", "right"]].set_visible(False)

    # D: genotype deltas
    ax = axes[1, 1]
    deltas = d["v37"]["genotype_deltas"]
    ordered = sorted(deltas.items(), key=lambda kv: kv[1])
    y = range(len(ordered))
    ax.scatter([v for _, v in ordered], list(y))
    ax.axvline(0, linewidth=1)
    ax.axvline(d["v37"]["genotype_delta_summary"]["equal_weight_mean_delta"], linestyle="--", linewidth=1)
    ax.set_yticks(list(y), [k for k, _ in ordered], fontsize=8)
    ax.set_xlabel("Alternaria − Other rank-1 dominance")
    ax.set_title(
        f"D  Shared across host genotypes ({d['v37']['genotype_delta_summary']['positive_count']}/12 positive)",
        loc="left", fontsize=10, weight="bold",
    )
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Falsification and localization of the microbiome structural legacy", fontsize=14, weight="bold")
    fig.tight_layout()
    save(fig, "Figure4_audit_and_localization")


def main():
    data = load()
    figure1()
    figure2(data)
    figure3(data)
    figure4(data)
    manifest = {
        "figures": [
            "Figure1_storage_problem",
            "Figure2_target_specific_retention",
            "Figure3_identity_stripping",
            "Figure4_audit_and_localization",
        ],
        "source_files": {key: str(path.relative_to(ROOT)) for key, path in FILES.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
