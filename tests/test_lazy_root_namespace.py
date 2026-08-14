import subprocess
import sys


def test_root_package_is_lazy_and_preserves_public_exports():
    code = """
import sys
import eog

assert eog.__version__ == '0.1.0'
assert 'eog.geometry' not in sys.modules
assert 'eog.bridge' not in sys.modules
assert 'eog.support_topology' not in sys.modules
assert 'eog.island_reachability' not in sys.modules

_ = eog.infer_occupancy_geometry
assert 'eog.geometry' in sys.modules
assert 'eog.bridge' not in sys.modules
assert 'eog.support_topology' not in sys.modules
assert 'eog.island_reachability' not in sys.modules

for name in eog.__all__:
    getattr(eog, name)
"""
    subprocess.run([sys.executable, "-c", code], check=True)
