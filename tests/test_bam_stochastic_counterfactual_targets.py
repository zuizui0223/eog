from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path("benchmarks").resolve()))

from independent_stochastic_bam_generator import (
    candidate_parameter_grid,
    make_landscape,
    simulate_associates,
    simulate_focal,
)
from independent_stochastic_counterfactual_generator_v1 import (
    stochastic_counterfactual_forecast,
)


def _fixture():
    landscape = make_landscape()
    associates = simulate_associates(landscape)
    specs = {row.scenario_id: row for row in candidate_parameter_grid()}
    spec = specs["A_broad|B_partner_and_antagonist|M_long_closed"]
    realization = simulate_focal(landscape, associates, spec, replicate=0)
    current = realization.occupancy_history[-1]
    return landscape, associates, spec, current


def test_generator_has_no_eog_imports():
    source = Path(
        "benchmarks/independent_stochastic_counterfactual_generator_v1.py"
    ).read_text(encoding="utf-8")
    assert "from eog" not in source
    assert "import eog" not in source


def test_biotic_stress_probability_is_nodewise_nonincreasing():
    landscape, associates, spec, current = _fixture()
    out = stochastic_counterfactual_forecast(
        landscape,
        associates,
        spec,
        current_snapshot=current,
        transformation="biotic_stress",
    )
    baseline = np.asarray(out.baseline_probability)
    cf = np.asarray(out.counterfactual_probability)
    assert np.all(cf <= baseline + 1e-12)
    assert out.expected_count_delta <= 1e-12


def test_barrier_restoration_probability_is_nodewise_nondecreasing():
    landscape, associates, spec, current = _fixture()
    out = stochastic_counterfactual_forecast(
        landscape,
        associates,
        spec,
        current_snapshot=current,
        transformation="barrier_restoration",
    )
    baseline = np.asarray(out.baseline_probability)
    cf = np.asarray(out.counterfactual_probability)
    assert np.all(cf + 1e-12 >= baseline)
    assert out.expected_count_delta >= -1e-12


def test_probability_vector_is_deterministic_not_monte_carlo():
    landscape, associates, spec, current = _fixture()
    left = stochastic_counterfactual_forecast(
        landscape,
        associates,
        spec,
        current_snapshot=current,
        transformation="climate_shift",
    )
    right = stochastic_counterfactual_forecast(
        landscape,
        associates,
        spec,
        current_snapshot=current,
        transformation="climate_shift",
    )
    assert left == right
