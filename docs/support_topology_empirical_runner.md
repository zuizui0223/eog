# Support topology held-out runner

`eog-support-topology-compare` compares five frozen scores on one declared candidate set: local support, nearest-anchor distance, their weighted mean, single-threshold detached membership, and multi-threshold persistent membership.

Inputs are a 2D `support.npy`, a matching Boolean `mask.npy`, `anchors.csv` with `anchor_id,row,column`, and `candidates.csv` with `candidate_id,row,column,detected`. Thresholds, adjacency, persistence steps, and support weight are command-line arguments.

The JSON output records ROC AUC, Brier score, candidate-level scores and topology classes, the complete configuration, a SHA-256 fingerprint, and the interpretation limit. The runner does not fit scores to held-out labels or silently snap coordinates.

Example:

```bash
eog-support-topology-compare \
  --support support.npy \
  --mask mask.npy \
  --anchors anchors.csv \
  --candidates candidates.csv \
  --thresholds 0.8 0.7 0.6 \
  --single-threshold 0.7 \
  --minimum-persistence-steps 3 \
  --output results/comparison.json
```

Results apply only to the frozen input bundle. They do not establish occupancy, colonisation, dispersal connectivity, causal isolation, or general superiority.