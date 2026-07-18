# Core local bridge development results

## Reproducibility

- GitHub Actions run: `29635928563`
- Artifact: `core-local-bridge-benchmark`
- Artifact digest: `sha256:9c0faea2995c17c03cedc01ab7e8655e35eefbfc6daeb07108c53202c59be769`
- Repeats: 30 per cell
- Seed: `20260830`

## Development decision

The density-trimmed core local bridge score passed the frozen development gate.

- minimum raw gap AUC: 0.1725;
- minimum core local bridge score AUC: 0.8272;
- minimum-AUC improvement: 0.6547;
- minimum two-mode AUC: 0.9744.

## AUC results

| n | fragmented structure | raw gap | core gap | local bridge | balanced local bridge score |
|---:|---|---:|---:|---:|---:|
| 60 | two modes | 0.496 | 0.963 | 0.989 | 0.994 |
| 60 | missing bridge | 0.198 | 0.611 | 0.781 | 0.827 |
| 120 | two modes | 0.451 | 0.951 | 0.969 | 0.974 |
| 120 | missing bridge | 0.210 | 0.706 | 0.872 | 0.882 |
| 240 | two modes | 0.391 | 0.962 | 0.981 | 1.000 |
| 240 | missing bridge | 0.173 | 0.683 | 0.901 | 0.953 |

## Interpretation

The result supports the proposed mechanism: sparse-tail points were responsible for much of the failure of global largest-edge statistics. Removing the 10% sparsest points and normalizing the remaining bridge by endpoint local scales preserved balanced internal gaps while suppressing fringe-driven edges.

This is a development result, not confirmation. The exact definition is now frozen for an independent-seed benchmark with altered generator parameters, contamination, unequal mode weights, and dimensions beyond two. No public API or real-taxon manuscript claim changes until that confirmation passes.