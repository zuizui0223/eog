from pathlib import Path

from independent_multilandscape_bam_generator_v4 import (
    LANDSCAPE_PANEL,
    candidate_parameter_grid,
    make_landscape,
    truth_scenarios,
)


def test_v4_generator_is_eog_independent():
    source = Path(
        "benchmarks/independent_multilandscape_bam_generator_v4.py"
    ).read_text(encoding="utf-8")
    for token in (
        "import eog",
        "from eog",
        "dynamic_island_reachability",
        "world_reconstruction",
    ):
        assert token not in source


def test_v4_frozen_panel_and_world_universe_sizes():
    assert len(LANDSCAPE_PANEL) == 8
    assert len({row.landscape_id for row in LANDSCAPE_PANEL}) == 8
    assert len(candidate_parameter_grid()) == 32
    assert len(truth_scenarios()) == 6


def test_each_v4_landscape_has_96_unique_nodes():
    for spec in LANDSCAPE_PANEL:
        landscape = make_landscape(spec)
        assert len(landscape.node_ids) == 96
        assert len(set(landscape.node_ids)) == 96
        assert landscape.environment.shape == (96, 2)
