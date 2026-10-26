from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    ROOT
    / "manuscript"
    / "neon_small_mammal_continuity"
    / "build_paper_assets.py"
)

spec = importlib.util.spec_from_file_location(
    "neon_small_mammal_continuity_assets",
    BUILDER_PATH,
)
assert spec is not None and spec.loader is not None
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_continuity_paper_assets_match_frozen_closure(tmp_path):
    builder.OUT = tmp_path
    rows = builder.load_csv(builder.SITE_DATA)
    best_rows = builder.load_csv(builder.BEST_DATA)
    lock = json.loads(builder.LOCK.read_text(encoding="utf-8"))
    closure = json.loads(builder.CLOSURE.read_text(encoding="utf-8"))

    builder.validate(rows, best_rows, lock, closure)
    builder.main()

    manifest = json.loads(
        (tmp_path / "asset_manifest_v1.json").read_text(encoding="utf-8")
    )
    values = manifest["frozen_values"]

    assert values["fixed_sites"] == 16
    assert values["scored_sites"] == 16
    assert values["positive_emergent_gain_sites"] == 0
    assert values["community_survival_one_sites"] == 15
    assert values["best_species_survival_one_sites"] == 16
    assert values["strict_emergent_world_positive_sites"] == 0
    assert values["ORNL_community_survival_fraction"] == 0.25
    assert values["ORNL_best_species_survival_fraction"] == 1.0

    for name in (
        "figure_1_conceptual_outcomes.svg",
        "figure_2_community_vs_species.svg",
        "figure_3_exploratory_redundancy.svg",
        "figure_4_ornl_weakest_link.svg",
        "table_s1_site_metrics.csv",
        "table_s2_best_species_frequency.csv",
        "table_s3_response_integrity.txt",
    ):
        assert (tmp_path / name).is_file()


def test_identity_redundancy_audit_is_consistent_with_site_metrics():
    audit = json.loads(
        (
            ROOT
            / "manuscript"
            / "neon_small_mammal_continuity"
            / "IDENTITY_REDUNDANCY_AUDIT_V1.json"
        ).read_text(encoding="utf-8")
    )
    rows = builder.load_csv(builder.SITE_DATA)

    assert audit["sites_with_at_least_two_individually_continuous_species"] == sum(
        int(row["best_species_count"]) >= 2 for row in rows
    )
    assert audit["unique_individually_continuous_species_across_sites"] == 32
    assert audit["maximum_site_recurrence_of_any_species"] == 3
    assert audit["individually_continuous_species_count_median"] == 2
