from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "figures" / "build_figure_2_aislands.py"
SPEC = importlib.util.spec_from_file_location("build_figure_2_aislands", MODULE_PATH)
assert SPEC and SPEC.loader
fig2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fig2)


def test_archived_sources_and_post_outcome_provenance_are_gated():
    data = fig2.validate_inputs()
    expected = data["expected"]
    assert data["primary"]["n_islands"] == expected["islands"]
    assert data["primary"]["n_declared_taxa"] == expected["declared_taxa"]
    assert data["primary"]["n_species_estimable"] == expected["primary_estimable_taxa"]
    assert data["bottleneck"]["n_species_estimable"] == expected["bottleneck_estimable_taxa"]
    assert data["provenance"]["preregistered"] is False
    assert "not_preregistration" in data["provenance"]["status"]


def test_primary_species_projection_is_complete_and_retains_direction_counts():
    data = fig2.validate_inputs()
    rows = fig2._species_rows(data)
    expected = data["expected"]
    assert len(rows) == expected["primary_estimable_taxa"]
    assert data["direction_counts"] == {
        "above": expected["species_above_null"],
        "equal": expected["species_equal_null"],
        "below": expected["species_below_null"],
        "not_estimable": expected["species_not_estimable"],
    }
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))


def test_modes_and_applicability_are_derived_from_frozen_projections():
    data = fig2.validate_inputs()
    modes = fig2._mode_rows(data)
    assert [row["quantity"] for row in modes] == [
        "combined",
        "geography_only",
        "environmentally_constrained",
        "bottleneck_secondary",
    ]
    expected = data["expected"]
    app = {(r["analysis"], r["status"]): r["count"] for r in fig2._applicability_rows(data)}
    assert app[("primary_combined", "evaluable")] == expected["primary_evaluable_species_folds"]
    assert app[("primary_combined", "no_comparable_pairs_within_frozen_strata")] == expected["primary_no_comparable_pair_species_folds"]
    assert app[("bottleneck_secondary", "evaluable")] == expected["bottleneck_evaluable_species_folds"]
    assert app[("bottleneck_secondary", "no_finite_comparable_pairs_within_frozen_strata")] == expected["bottleneck_no_comparable_pair_species_folds"]
    for row in fig2._fold_rows(data):
        assert row["total"] == expected["declared_taxa"]


def test_builder_reproduces_every_committed_figure_2_asset_exactly():
    assets = fig2.build_assets()
    assert len(assets) == 12
    for relative, text in assets.items():
        assert (ROOT / relative).read_text(encoding="utf-8") == text
    assert (ROOT / "figures/output/aislands_species_concordance.csv").read_text() == (
        ROOT / "manuscript/figure_data/aislands_species_concordance.csv"
    ).read_text()


def test_sha_gate_rejects_modified_species_projection(tmp_path, monkeypatch):
    altered = tmp_path / "species.csv"
    altered.write_bytes(fig2.PRIMARY_SPECIES.read_bytes() + b"\n")
    monkeypatch.setattr(fig2, "PRIMARY_SPECIES", altered)
    with pytest.raises(ValueError, match="SHA mismatch"):
        fig2.validate_inputs()


def test_plotting_code_contains_no_frozen_outcome_or_sample_size_literals():
    source = MODULE_PATH.read_text(encoding="utf-8")
    data = fig2.validate_inputs()
    outcome_values = [
        data["primary"]["overall_conditional_concordance"],
        *data["primary"]["bootstrap_95_ci"],
        data["secondary"]["modes"]["geography_only"]["mean_conditional_concordance"],
        data["secondary"]["modes"]["environmentally_constrained"]["mean_conditional_concordance"],
        data["bottleneck"]["mean_conditional_concordance"],
        *data["bottleneck"]["bootstrap_95_ci"],
    ]
    for value in outcome_values:
        assert f"{value:.6f}" not in source
    for key in [
        "islands",
        "declared_taxa",
        "primary_estimable_taxa",
        "bottleneck_estimable_taxa",
        "species_above_null",
        "species_below_null",
        "primary_evaluable_species_folds",
        "primary_no_comparable_pair_species_folds",
        "bottleneck_evaluable_species_folds",
        "bottleneck_no_comparable_pair_species_folds",
    ]:
        assert str(data["expected"][key]) not in source

    caption = (ROOT / "manuscript/figure_2_caption.md").read_text(encoding="utf-8")
    assert "not dispersal or colonisation probabilities or realised pathways" in caption
    assert "no pairwise superiority test among the modes was predeclared" in caption
