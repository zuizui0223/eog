# Figure 2 reproducibility note

The committed Figure 2 builder is a presentation layer over frozen A-Islands benchmark outputs; it does not refit or alter the benchmark.

After the Figure 2 source projection was finalized, the builder was explicitly compiled with CPython 3.10.20 and `tests/test_structural_figure_2.py` passed all five contract tests under that interpreter. The compatibility correction only normalizes SVG-building f-string delimiters so that the same source is valid on the repository's Python 3.10–3.12 support range; it does not change the frozen numerical inputs, estimability accounting, or scientific interpretation.

The ordinary repository CI remains the authoritative cross-version check for the pull request.
