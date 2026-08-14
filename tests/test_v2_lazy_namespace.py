import subprocess
import sys


def test_v2_package_root_does_not_eagerly_import_operator_facades():
    code = """
import sys
import eog.v2 as v2

assert 'eog.v2.reachability' not in sys.modules
assert 'eog.v2.traversability' not in sys.modules
assert 'eog.v2.validation' not in sys.modules
assert v2.API_STATUS == 'prospective-v2-development'
assert v2.DEVELOPMENT_DIRECTION == 'distributional-watershed-world-reconstruction'

_ = v2.build_dynamic_transition_operator
assert 'eog.v2.reachability' in sys.modules
assert 'eog.v2.traversability' not in sys.modules
assert 'eog.v2.validation' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", code], check=True)
