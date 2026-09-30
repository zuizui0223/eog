# BAM future-target evidence under assay-process uncertainty v1

## Phase VII question

Phase VI used exact parameter assays.  Phase VII admits uncertainty in how the same
parameter assay is coded.

The ecological W1 world and the assay-observation process are separate axes:

[
W_J = W_E \times W_O.
]

The future decision depends only on the ecological world.  Observation-world identity
is nuisance uncertainty.

## Frozen assay worlds

Two deterministic global assay worlds are admitted:

1. calibrated;
2. systematically miscalibrated.

Ordinal fields are shifted by +1 under miscalibration. Binary fields are flipped.

This is a synthetic observation-process stress test, not a laboratory error model.

## Why repetition is not calibration

Under one fixed systematic observation world, repeating the same deterministic assay
twice gives the same coded result twice.  It does not reveal whether the code is
calibrated or systematically transformed.

Therefore repeat assays are explicitly audited as a negative control.

## Robust target design

For every W1 same-G fiber whose structured future binary target is unresolved:

1. form ecological-world x assay-world joint hypotheses;
2. retain only pairs with different future target values;
3. compute which action robustly separates each target-discordant pair;
4. solve the exact minimum action cover.

Same-target joint hypotheses do not need to be separated.

The action library contains:

- one assay per W1 parameter field;
- one repeated version of each assay;
- one idealized assay-process calibration action.

## Claim boundary

Robust separation here is support-based guarantee logic. It is not expected information
gain or probabilistic optimal experiment design.

Repeated-assay equivalence applies to fixed systematic bias only. Independent random
measurement error would be a different observation universe.
