# Competitor comparison benchmark

## Question

Does shared-reference EOG span merely duplicate established multivariate summaries, or does it occupy a narrower estimand with identifiable advantages and failure modes?

## Design

Seven frozen scenarios were evaluated with 20 independently generated datasets and 20 matched-size subsamples per dataset. All directional extent summaries were computed after one external median–MAD reference transformation. The known dilation target was `log(2) = 0.6931`.

Comparators were:

| Comparator | Estimand | Directional? | Main limitation |
|---|---|---:|---|
| EOG 0.90 span | upper pairwise-distance extent | yes | sensitive to irrelevant dimensions and declared reference |
| Mean centroid distance | average radial dispersion | yes | influenced by tails and centroid placement |
| Median centroid distance | robust radial dispersion | yes | can ignore sparse tail expansion |
| Gaussian linear extent | covariance-volume scale | yes | assumes covariance is a useful shape summary |
| 2-D convex hull | linearized enclosing area | yes | dimension-specific and strongly outlier-sensitive |
| Energy distance | whole-distribution difference | no | does not identify an extent direction |

## Main results

### Known two-fold dilation

All directional extent comparators recovered the target under a common reference. Median absolute error from `log(2)` was 0.057 for EOG span, 0.062 for mean centroid distance, 0.087 for median centroid distance, 0.053 for Gaussian linear extent, and 0.076 for linearized hull area. EOG is therefore not uniquely capable of recovering simple global dilation.

### Outlier contamination

Four extreme observations inflated linearized convex-hull area most strongly (median log contrast 0.902), followed by Gaussian extent (0.630). EOG span and mean centroid distance were moderately affected (0.302 and 0.322), while median centroid distance changed little (0.076). The benchmark supports comparator-specific robustness claims rather than a universal ranking.

### Irrelevant dimensions

When six irrelevant features were appended to a two-feature dilation, every multivariate extent contrast was attenuated. EOG span fell to 0.354 and Gaussian linear extent to 0.166. Two-dimensional hull area was undefined. This confirms that ecological feature preselection is required and that a frozen reference does not make arbitrary dimensions harmless.

### Curved versus straight support

The curved and straight generators had different support geometry, so extent statistics produced different positive contrasts. Gaussian extent and hull area were especially large. This scenario is not evidence that one comparator measures path shape better; it shows why support-family mismatch must not be interpreted as generic continuity or extent.

### Multimodal versus connected distributions

The connected and multimodal generators were constructed with approximately matched covariance extent. Median EOG span (-0.056) and Gaussian linear extent (-0.002) were near zero, whereas energy distance remained positive (0.205). Radial and hull summaries disagreed. This is the key estimand-separation result: distributional difference, radial dispersion, enclosing area, and upper-distance extent answer different questions.

### Null scenarios

Matched-size resampling removed systematic direction under unequal sample sizes: median directional contrasts remained near zero for all extent summaries. Under the equal-distribution null, however, a sign-stability rule alone produced directional-support rates of 0.55–0.65. Therefore subsampling direction stability must not be interpreted as confirmatory evidence by itself. A design-valid permutation diagnostic or hierarchical sampling design remains necessary.

## Consequences for the manuscript

1. EOG should not be marketed as universally superior to established dispersion measures.
2. Its distinctive contribution is the executable comparison contract: frozen reference, matched-size sampling, support declarations, fingerprints, and claim limits.
3. Mean/median centroid distance and covariance extent are legitimate alternatives for different estimands.
4. Energy distance is a useful comparator when the question is any distributional difference rather than directional extent.
5. Convex hull is informative only in low dimension and is highly tail-sensitive.
6. Direction stability must remain separate from inferential support.

The machine-readable frozen output is `benchmarks/expected/competitor_comparison.json`.
