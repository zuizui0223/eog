# Audited real-taxon held-out validation

## Purpose

`eog-support-topology-validate` applies the five predeclared support-topology comparators to an externally prepared support grid and held-out candidate set. It does not fit an SDM, choose thresholds, move occurrence anchors, or tune scores against held-out outcomes.

## Required inputs

### `support.npy`

A two-dimensional NumPy array containing the frozen pointwise support field produced from training-only data.

### `mask.npy`

A matching boolean NumPy array. `True` means unavailable or outside the analysis graph. Sea, excluded substrate, or cells outside the declared domain belong here rather than being encoded as merely low support.

### `anchors.csv`

```csv
anchor_id,row,column
historical_population_1,120,340
```

Anchor cells must be explicit. The adapter does not silently snap coordinates.

### `candidates.csv`

```csv
candidate_id,row,column,detected
site_001,125,350,1
site_002,130,360,0
```

The file must contain at least one detection and one non-detection. These labels are used only after all five scores have been calculated from the frozen inputs.

### `declaration.json`

```json
{
  "analysis_id": "campanula_island_holdout_v1",
  "thresholds": [0.8, 0.7, 0.6],
  "single_threshold": 0.7,
  "neighbourhood": 4,
  "minimum_persistence_steps": 3,
  "unresolved_below": 0.55,
  "support_distance_weight": 0.5,
  "frozen_before_outcomes": true
}
```

The declaration is rejected when `frozen_before_outcomes` is false. This is an auditable assertion, not proof that freezing actually occurred; the study protocol and archive must establish that independently.

## Command

```bash
eog-support-topology-validate \
  --support support.npy \
  --mask mask.npy \
  --anchors anchors.csv \
  --candidates candidates.csv \
  --declaration declaration.json \
  --output-dir results/topology_validation
```

## Outputs

- `validation_bundle.json`: declaration, SHA-256 hashes for all five inputs, topology fingerprint, ROC AUC, Brier score, candidate-level records, and bundle fingerprint;
- `candidate_scores.csv`: flattened candidate-level support, nearest-anchor distance, component classes, labels, and five scores.

The compared rules are local support, nearest-anchor distance, equal-weight support plus distance, one-threshold detached membership, and multi-threshold persistent detached membership.

## Interpretation limits

The 0-1 component scores are decision rules, not calibrated probabilities. Brier score is retained only as a common label-error diagnostic. The output does not establish occupancy probability, colonisation, dispersal connectivity, historical routes, causal barriers, or confirmatory evidence when the support field, thresholds, anchors, candidates, or outcomes influenced method development.

For the シマホタルブクロ case, the first use remains exploratory because prior field outcomes influenced development. A confirmatory analysis requires a new independently frozen holdout or another taxon-region pair.
