from pathlib import Path

import numpy as np

from benchmarks.independent_stochastic_bam_generator import (
    candidate_parameter_grid,
    make_landscape,
    simulate_associates,
    simulate_focal,
    truth_scenarios,
)


def test_generator_source_has_no_eog_imports():
    source = Path("benchmarks/independent_stochastic_bam_generator.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "import eog",
        "from eog",
        "dynamic_island_reachability",
        "world_reconstruction",
    )
    assert all(token not in source for token in forbidden)


def test_frozen_candidate_grid_and_truth_ids_are_declared():
    grid = candidate_parameter_grid()
    ids = {row.scenario_id for row in grid}

    assert len(grid) == 32
    assert len(ids) == 32
    assert set(truth_scenarios().values()).issubset(ids)


def test_associates_are_generated_before_focal_and_keep_partner_source():
    landscape = make_landscape()
    associates = simulate_associates(landscape)
    source = landscape.node_ids.index("r4c0")

    assert associates.partner_history.shape == (31, 96)
    assert associates.antagonist_history.shape == (31, 96)
    assert associates.partner_mask[source]
    assert not np.array_equal(
        associates.partner_mask,
        associates.antagonist_mask,
    )


def test_stochastic_occurrences_never_leave_truth_structural_support():
    landscape = make_landscape()
    associates = simulate_associates(landscape)
    grid = {row.scenario_id: row for row in candidate_parameter_grid()}
    truth_id = truth_scenarios()["joint_ABM"]
    realization = simulate_focal(
        landscape,
        associates,
        grid[truth_id],
        replicate=0,
    )

    reachable = set(realization.structural_reachable_ids)
    previous = set()
    for _, ids in realization.accumulated_occurrence_ids_by_horizon:
        observed = set(ids)
        assert previous.issubset(observed)
        assert observed.issubset(reachable)
        previous = observed
