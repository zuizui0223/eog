# EOG v2 Ryukyu published-binary FST connectivity result

## Status

**Retrospective published-response sensitivity — COMPLETED.**

This result does **not** satisfy the independent prospective/raw-genetic promotion gate. It uses only the published Figure 2 binary encoding `FST < 0.1` from Thomas, Nakajima & Mitarai (2022), DOI `10.3389/fmars.2022.827590`, under the frozen contract in `docs/eog_v2_ryukyu_published_binary_connectivity_contract.md`.

Continuous FST values are not digitized from heatmap colours, raw genotypes are not reconstructed, and migration direction is not evaluated.

## Frozen response-free predictor provenance

The predictors were created before the published genetic response was attached and were restored byte-for-byte from the original successful workflow artifact rather than regenerated after response visibility:

- source workflow run: `31610691970`;
- source workflow head: `5a8449f51480dd127311a1befe0cae98e1272ce7`;
- source artifact ID: `9147048185`;
- source artifact digest: `sha256:23725655494ff7ba09fd764186a675e4f13190d92f0605e601d9b3cc4737a681`;
- populations CSV SHA-256: `6de60475209e49927c68d2467bdac253a0e2777c39a9f4df49dde4832ee3495e`;
- predictors CSV SHA-256: `b5485e42c8c884bf31f3d8b76fd71db04a93c377bc9836f085a4c65b6f62aa7f`;
- predictor-manifest fingerprint: `8bef3ea33d24f1f124aab5e023cbfac087f74b2e5584546b9da50adaf2de7d31`;
- operator fingerprint: `61b4794914976bd1ac5687fd814a2d2878d397a2feac02314031feb68c249e35`;
- exact-eventual connectivity fingerprint: `d0261069e634cb21068a45ff59c5bb891ce573ec9a6d01e75308b7b8e2215c38`.

The one-time published-response sensitivity was then run on CI run `31653840406`. Every provenance, Figure-2, extraction, LOPO and result-contract step passed.

## Published response

Official Frontiers Figure 2 asset SHA-256:

`70d35809ac5e6408b647a920366703aff02b99cab5888ce10744ed3f7b6e9ad1`

The article caption states that exactly 25 population pairs have pairwise `FST < 0.1` and are indicated with bold grids. The frozen image extraction recovered exactly 25 positive pairs and included all four article-identified low-differentiation integrity pairs:

- `IRMe–IRMf`;
- `ISGa–ISGc`;
- `MYKb–MYKd`;
- `MYKc–IRMd`.

No continuous FST value was inferred from cell colour.

## Leave-one-population-out results

All 15 genetic pairs involving one population were held out together. Lower log loss and Brier score are better.

| Model | LOPO log loss | Brier | AUC |
|---|---:|---:|---:|
| IBD | `0.5222093035` | `0.1708419354` | `0.4231578947` |
| IBD + EOG | `0.5227274879` | `0.1711313856` | `0.4307368421` |
| Gabriel current flow | `0.5474059795` | `0.1764516039` | `0.2023157895` |
| Gabriel current flow + EOG | `0.5207157319` | `0.1717402824` | `0.3482105263` |

Frozen primary contrast:

`currentflow + EOG − currentflow = -0.02669024763` held-out log loss.

Frozen secondary contrast:

`IBD + EOG − IBD = +0.00051818443` held-out log loss.

Current-flow + EOG improved over current flow in `10/16` population-held-out folds. IBD + EOG improved over IBD in `7/16` folds.

Result fingerprint:

`8469cfe848327cefb984c9cac35c521b1603b01161648341c2f53dbd2dcc5d5b`

CI artifact:

- workflow run: `31653840406`;
- artifact ID: `9163578699`;
- artifact digest: `sha256:e994d2c3fe4fc4c610c06006c0a50aad530ea953c1b02bdfae970964d2b9d675`.

## Interpretation

The frozen interpretation is `retrospective_binary_added_information` **only relative to the predeclared Gabriel current-flow reference**.

The result does not support a universal genetic-superiority claim:

1. current flow alone was worse than straight-line IBD on this binary endpoint;
2. adding EOG to current flow materially reduced held-out log loss;
3. adding EOG to IBD was effectively null/slightly adverse;
4. the effect was heterogeneous across held-out populations;
5. the response is a published thresholded FST classification rather than raw continuous FST.

The useful scientific boundary is therefore narrower: the frozen exact-eventual EOG construction can contain information that is absent from a graph-aware current-flow representation, but that added information is reference-dependent and is not demonstrated beyond simple IBD in this retrospective endpoint.

This result justifies continuing to seek a genuinely prospectively frozen/raw independent genetic dataset. It does **not** close that promotion gate, and symmetric FST remains invalid for testing migration direction.
