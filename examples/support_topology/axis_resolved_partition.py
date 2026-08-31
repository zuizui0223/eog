"""Synthetic example: identical 2D support, disjoint time-height use.

This is an illustrative tensor, not a natural-history claim about any named taxon.
"""
from __future__ import annotations

import json

import numpy as np

from eog.v2.axis_resolved_support import audit_axis_resolved_overlap


def main() -> None:
    # Tensor layout: y, x, vertical stratum, time bin.
    small_mammal = np.zeros((3, 4, 2, 4), dtype=float)
    snake_like_predator = np.zeros_like(small_mammal)

    # Both taxa use every horizontal cell. Their vertical/time states differ.
    small_mammal[:, :, 1, 2:] = 1.0
    snake_like_predator[:, :, 0, :2] = 1.0

    result = audit_axis_resolved_overlap(small_mammal, snake_like_predator)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
