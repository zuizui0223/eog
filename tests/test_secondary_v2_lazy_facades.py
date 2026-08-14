import subprocess
import sys


def test_traversability_facade_loads_only_requested_owner():
    code = r'''
import sys
import eog.v2.traversability as traversability

assert 'eog.ecological_traversability' not in sys.modules
assert 'eog.v2.occurrence_constraints' not in sys.modules

_ = traversability.EcologicalTransitionEdge
assert 'eog.ecological_traversability' in sys.modules
assert 'eog.v2.occurrence_constraints' not in sys.modules
'''
    subprocess.run([sys.executable, "-c", code], check=True)


def test_validation_facade_loads_only_requested_evidence_tree():
    code = r'''
import sys
import eog.v2.validation as validation

for name in (
    'eog.eventual_genetic_connectivity',
    'eog.genetic_validation',
    'eog.v2_empirical_occurrence_validation',
    'eog.v2.evidence_discrimination',
):
    assert name not in sys.modules, name

_ = validation.DirectionalOrderConstraint
assert 'eog.v2.evidence_discrimination' in sys.modules
assert 'eog.genetic_validation' not in sys.modules
assert 'eog.v2_empirical_occurrence_validation' not in sys.modules
'''
    subprocess.run([sys.executable, "-c", code], check=True)


def test_all_secondary_facade_public_names_resolve():
    code = r'''
import eog.v2.traversability as traversability
import eog.v2.validation as validation
for module in (traversability, validation):
    for name in module.__all__:
        getattr(module, name)
'''
    subprocess.run([sys.executable, "-c", code], check=True)
