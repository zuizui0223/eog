# Persistent split benchmark results

## Reproducibility

- GitHub Actions run: `29635750141`
- Artifact: `persistent-split-benchmark`
- Artifact digest: `sha256:5323d2a54cc68c9fc21403b4fed86381885a9b6811752d41aac9be01001da4d8`
- Repeats: 12 per cell
- Subsamples: 20 per cloud

## Frozen decision

The persistent-split score failed the frozen gate and is not added to the EOG public API.

- minimum raw gap-strength AUC: 0.0938;
- minimum persistent-split-score AUC: 0.5017;
- minimum-AUC improvement: 0.4080;
- maximum connected strong-evidence rate: 0.0000;
- minimum fragmented strong-evidence rate: 0.0000.

## AUC results

| n | fragmented structure | raw gap AUC | persistent score AUC |
|---:|---|---:|---:|
| 60 | two modes | 0.488 | 0.594 |
| 60 | missing bridge | 0.188 | 0.635 |
| 120 | two modes | 0.432 | 0.634 |
| 120 | missing bridge | 0.193 | 0.507 |
| 240 | two modes | 0.365 | 0.661 |
| 240 | missing bridge | 0.094 | 0.502 |

## Interpretation

Partition persistence, balance, and gap stability removed false strong-evidence calls in the connected generators and improved the worst-case ranking substantially. However, the score remained only slightly above chance in the hardest missing-bridge cells. The candidate split can be reproducible without being uniquely separated from curved or heterogeneous connected geometry.

The next improvement should normalize the candidate bridge edge by local neighbour scales at its endpoints. A true bridge between dense occupied regions should be long relative to both local scales; a long edge caused by a sparse tail or outlier should not. This local bridge contrast should be evaluated before any API change.