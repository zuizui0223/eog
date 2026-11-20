# Toad coordinate–published-distance quality diagnosis: preserving the original STOP

**Status:** Post-exposure **source-quality diagnosis only**. Original external experimental geographic MRR source-anchor test [PR #721](https://github.com/zuizui0223/eog/pull/721), [source-gated CI run #44756566395](https://github.com/zuizui0223/eog/actions/runs/44756566395) failed the scientific **`STOP_GEO_UNIT_CONCORDANCE`** gate. The original pre-score H1 directional test remains **NOT SCORED**. This document and diagnostic cannot change that status.

## Frozen failure and scope

The original toad publisher dataset is still [Jreidini & Green, Dryad `10.5061/dryad.x3ffbg7ms`](https://doi.org/10.5061/dryad.x3ffbg7ms), version **198534**, CSV **18,702 bytes/165 source rows**, SHA256 `c8ee049eb807af31660ffa28e11f6a66b07a85a5dda4e756bb1b06610edb3f17`. It has original `Initial`, `Released`, and `Final` Easting/Northing pairs plus published columns `Distance release-final (m)` and `Distance capture-final (m)`.

Before its first outcome calculation, [the original strict protocol](../validation/independent_toad_source_anchor_geography_v1/protocol_v1.json) required **each** of those two archived distance columns to match Euclidean coordinate recomputation within `max(2 m, 5% of recomputed)` for **at least 95%** of comparable rows. Source SHA and software regression tests passed, but the distance-unit/definition concordance threshold did not. The original scientific result is **not** a positive/negative homing test; it is an unanswered source-quality question.

## New restricted quality task

The separate [quality-only protocol](../validation/independent_toad_coordinate_diagnosis_v1/protocol_v1.json) was committed first, before any diagnostic re-reading of source rows. It fixes this one source, these two distance fields, the three possible coordinate-pair geometries (`release→final`, `capture→final`, `capture→release`), and exactly three exploratory scale factors `0.001, 1, 1000`. The role of alternate scales is **diagnosis**, not retrospective scientific correction.

The [restricted diagnostic script](../scripts/eog_toad_source_coordinate_quality_diagnosis_v1.py) reads only the necessary coordinate and published-distance fields, and produces **aggregated quality counters**: coordinate/field missingness, valid numeric denominators, original strict match fractions, and matches/quantile ratios against each of the nine frozen pair×scale candidates. The original H1 denominator is reproduced exactly by requiring an eligible Toad ID, a nonempty recapture date, and all six numeric coordinates after removal of byte-identical raw-row duplicates.

Output explicitly forbids computing the source-anchor contrast `d_RF-d_IF`, its sign, individual-level statistics, recapture success, EOG-WF predictive skill or any new biological effect.

## Expected honest outcomes

- **Quality diagnosis succeeded, original STOP retained**: reports which field lacks values or is inconsistent with the proposed UTM coordinate geometry. Does not grant permission to score H1 on this already-opened data.
- **Source SHA or column failure**: retains a scientific STOP; do not use an alternate source version.
- **Contradiction to original STOP**: fail-closed `STOP_REPRODUCED_QUALITY_GATE_CONTRADICTS_FROZEN_PRIMARY_STOP` for independent investigation, not automatic promotion.
- **No ecological conclusion**: even if a plausible unit conversion is found, the candidate source is **experimental release**, not a natural founder. This experiment is only individual-level geographic calibration, and has no independent environment/barrier candidate graph.

The original empirical EOG-WF denominator remains **3 scored / 31 scientific STOP / 3 administrative exclusions**, with zero new endpoints.

## Reproducibility

- [Pre-score frozen quality diagnostic protocol](../validation/independent_toad_coordinate_diagnosis_v1/protocol_v1.json)
- [Post-STOP quality-only script](../scripts/eog_toad_source_coordinate_quality_diagnosis_v1.py)
- [Synthetic no-rescoring/STOP tests](../tests/test_eog_toad_source_coordinate_quality_diagnosis_v1.py)
- [Dedicated source-only Actions workflow](../.github/workflows/eog-toad-source-geo-quality-diagnosis-v1.yml)

Only aggregate checksum, missingness and consistency results may be archived. Raw ID, individual coordinates, individual dates, original data bytes, movement directions, or computed H1 contrasts are never uploaded.
