from __future__ import annotations

from pathlib import Path
import cairosvg


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "manuscript" / "neon_small_mammal_continuity" / "generated"

FIGURES = (
    "figure_1_conceptual_outcomes",
    "figure_2_community_vs_species",
    "figure_3_exploratory_redundancy",
    "figure_4_ornl_weakest_link",
)


def main() -> None:
    for stem in FIGURES:
        source = OUT / f"{stem}.svg"
        target = OUT / f"{stem}_1961px.png"
        if not source.is_file():
            raise FileNotFoundError(source)
        cairosvg.svg2png(
            url=str(source),
            write_to=str(target),
            output_width=1961,
        )
        if target.stat().st_size <= 0:
            raise RuntimeError(f"empty exported figure: {target}")


if __name__ == "__main__":
    main()
