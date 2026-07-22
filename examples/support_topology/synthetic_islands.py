"""Synthetic islands: identical local support, different spatial structure.

Run with:
    python examples/support_topology/synthetic_islands.py
"""
import numpy as np

from eog import SupportTopologyConfig, infer_support_topology


support = np.array(
    [
        [0.92, 0.88, 0.00, 0.91, 0.87],
        [0.90, 0.84, 0.00, 0.89, 0.86],
    ]
)

# The middle column is unavailable sea, not low-support habitat.
sea_mask = np.array(
    [
        [False, False, True, False, False],
        [False, False, True, False, False],
    ]
)

result = infer_support_topology(
    support,
    {"historical_west_island": (0, 0)},
    SupportTopologyConfig(
        thresholds=(0.90, 0.85, 0.80),
        neighbourhood=4,
        minimum_persistence_steps=2,
    ),
    missing_mask=sea_mask,
)

print("fingerprint", result.fingerprint)
for component in result.components:
    print(
        component.component_id,
        component.component_class,
        "birth=", component.first_threshold,
        "persistence=", round(component.persistence, 3),
        "cells=", component.member_cell_count,
        "anchors=", component.anchor_ids,
    )

# Both islands contain cells near 0.9 support. The west island is occurrence
# anchored; the east island is a persistent detached component because sea is a
# hard mask. This structural difference is absent from cellwise support alone.
