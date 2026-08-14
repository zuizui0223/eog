import subprocess
import sys


def test_reachability_facade_does_not_eagerly_import_owned_implementations():
    code = r'''
import sys
import eog.v2.reachability as reachability

for name in (
    'eog.dynamic_island_reachability',
    'eog.island_state_layers',
    'eog.reachability_network_diagnostics',
    'eog.reachability_visualization',
    'eog.reachability_html',
    'eog.synthetic_archipelago',
    'eog.v2.world_reconstruction',
    'eog.v2.relaxation_family',
    'eog.v2.temporal_reachability',
    'eog.v2.temporal_reconstruction',
    'eog.v2.temporal_survey',
    'eog.v2.temporal_transition_landscape',
):
    assert name not in sys.modules, name

_ = reachability.TemporalTransitionLandscape
assert 'eog.v2.temporal_transition_landscape' in sys.modules
assert 'eog.reachability_html' not in sys.modules
assert 'eog.synthetic_archipelago' not in sys.modules
assert 'eog.v2.world_reconstruction' not in sys.modules
'''
    subprocess.run([sys.executable, "-c", code], check=True)


def test_all_reachability_public_names_resolve_after_lazy_refactor():
    code = r'''
import eog.v2.reachability as reachability
for name in reachability.__all__:
    getattr(reachability, name)
'''
    subprocess.run([sys.executable, "-c", code], check=True)
