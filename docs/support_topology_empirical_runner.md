# Support topology held-out runner

`eog-support-topology-compare` compares five frozen scores on one declared candidate set: local support, nearest-anchor distance, their weighted mean, single-threshold detached membership, and multi-threshold persistent membership.

Inputs are a 2D `support.npy`, a matching Boolean `mask.npy`, `anchors.csv` with `anchor_id,row,column`, `candidates.csv` with `candidate_id,row,column,detected`, and a frozen JSON declaration. The declaration records the analysis ID, thresholds, adjacency, persistence steps, support weight, and the analyst assertion that these choices were frozen before outcomes were inspected.

Each held-out row must identify a unique raster cell, and held-out cells must be disjoint from historical anchor cells. Repeated visits, individuals, or records falling in one raster cell must be aggregated before this cell-level comparison rather than entered as independent candidates.

Example declaration:

```json
{
  "analysis_id": "independent_taxon_region_holdout_v1",
  "frozen_before_outcomes": true,
  "thresholds": [0.8, 0.7, 0.6],
  "single_threshold": 0.7,
  "minimum_persistence_steps": 3,
  "neighbourhood": 4,
  "support_weight": 0.5
}
```

The JSON output records ROC AUC, squared score error, candidate-level scores and topology classes, the complete configuration, SHA-256 hashes for all five input files, the comparison fingerprint, a bundle fingerprint, and the interpretation limit. The runner does not fit scores to held-out labels or silently snap coordinates.

Example:

```bash
eog-support-topology-compare \
  --support support.npy \
  --mask mask.npy \
  --anchors anchors.csv \
  --candidates candidates.csv \
  --declaration declaration.json \
  --output results/comparison.json
```

`frozen_before_outcomes: true` is an auditable analyst assertion, not independent evidence of temporal precedence. A confirmatory manuscript claim still requires a timestamped protocol or archive showing that the declaration and training-only support field existed before held-out outcomes were inspected.

Results apply only to the frozen input bundle. They do not establish occupancy, colonisation, dispersal connectivity, causal isolation, or general superiority.
