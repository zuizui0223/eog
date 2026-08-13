# EOG v2 Ryukyu published-FST binary connectivity sensitivity contract

## Status

**Retrospective published-response sensitivity; not raw-genotype replication and not confirmatory validation.**

Response-free IBD, Gabriel-current-flow and exact-eventual EOG predictors for the 16 `Rhizophora stylosa` populations were already frozen before this sensitivity. The official Frontiers Figure 2 asset is archived separately from the article DOI `10.3389/fmars.2022.827590`.

The article caption explicitly states that **25 site pairs have pairwise FST < 0.1 and are shown by bold grids**. This sensitivity uses only that published binary visual encoding. It does **not** infer continuous FST values from cell colours, does not use p-value stars as response values, and does not reconstruct migration direction.

## Frozen figure asset

Official asset URL:

`https://www.frontiersin.org/files/Articles/827590/xml-images/fmars-09-827590-g002.webp`

Expected SHA-256:

`70d35809ac5e6408b647a920366703aff02b99cab5888ce10744ed3f7b6e9ad1`

Expected image dimensions: `2047 x 2081` pixels.

## Population order and heatmap geometry

X-axis order:

`OKI, MYKa, MYKb, MYKc, MYKd, ISGa, ISGb, ISGc, ISGd, IRMa, IRMb, IRMc, IRMd, IRMe, IRMf, IRMg`.

Y-axis is the reverse of that order. Figure-cell boundaries are fixed from the official archived asset:

- X: `270, 380, 488, 598, 712, 819, 929, 1039, 1149, 1262, 1371, 1483, 1590, 1701, 1814, 1922, 2032`;
- Y: `163, 267, 372, 478, 584, 689, 795, 901, 1010, 1116, 1222, 1328, 1433, 1539, 1645, 1748, 1853`.

These coordinates are figure-layout metadata, not model tuning parameters.

## Bold-grid extraction

For every one of the 120 off-diagonal population-pair cells:

1. inspect only four narrow strips surrounding that cell boundary, extending 2 pixels outside to 5 pixels inside and excluding 8-pixel corners;
2. convert the official asset to grayscale;
3. pool border-strip pixels and compute the 20th percentile grayscale value;
4. lower values mean a darker/thicker border;
5. rank all 120 pair cells by this frozen border-darkness score and label exactly the darkest `25` as `published_FST_lt_0.1 = 1`, because the article caption states that exactly 25 grids are bold for FST < 0.1.

Ties at the 25th position are broken lexicographically by the frozen `(population_a, population_b)` order. The count `25` comes from the published caption, not from EOG performance.

The extraction is accepted only if all four pairs explicitly identified in the Results as very low/insignificant differentiation are included among the 25 published-connectivity pairs:

- `IRMe-IRMf`;
- `ISGa-ISGc`;
- `MYKb-MYKd`;
- `MYKc-IRMd`.

This is a figure-transcription integrity check, not an EOG validation gate.

## Validation models

Binary response: `1 = published FST < 0.1 bold grid`, `0 = other pair`.

Use leave-one-population-out validation: for each held-out population, all 15 pairs involving that population are held out together.

Common deterministic ridge-logistic penalty: `1.0`.

Models:

1. `IBD`: geographic distance;
2. `currentflow`: response-free Gabriel effective-resistance distance;
3. `IBD_EOG`: geographic distance + exact-eventual EOG continuous distance + disconnection indicator;
4. `currentflow_EOG`: current-flow reference + exact-eventual EOG continuous distance + disconnection indicator.

Primary retrospective contrast:

`currentflow_EOG - currentflow` held-out log loss; negative favours added EOG information.

Secondary metrics: Brier score and pooled AUC. No significance threshold or GO rule is imposed because the published response was known before this retrospective contract.

## Interpretation

- negative primary contrast: `retrospective_binary_added_information`;
- zero/adverse primary contrast: `retrospective_binary_no_added_information`;
- extraction/integrity failure: `non_estimable_published_figure`.

A favourable result motivates a genuinely independent raw-data or prospectively frozen genetic validation; it does not satisfy that promotion gate.

Symmetric FST threshold connectivity cannot validate migration direction.
