# EOG v2.1 Thalassia exact genetic validation — frozen result

## Status

**`indeterminate_selector_reference_failure` — `promotion_go = false`.**

This is the first response-capable execution of the prospectively frozen `Thalassia hemprichii` microsatellite validation. The outcome is retained as-is. No conventional reference, graph, EOG definition, clone rule, FST estimator, response transform, bootstrap rule, or GO criterion may be changed to rescue this result.

## Authoritative execution

- workflow: `Thalassia one-time exact genetic validation`
- authoritative response-capable run: `31670695990` (workflow run number 4)
- head: `246bbec9d121948a36a9921d822cee071e321416`
- artifact: `9169570228`
- artifact digest: `sha256:0eb23b3a1f7798f40a4bf8e9c1ee881f1729467a1b2d447125a13dcfb6cdad85`
- result fingerprint: `6165e361e10ee692801f67d4580f431a598e428aa3e0312444a5270d70dbe76f`
- nested-result fingerprint: `ef8a77f3f05828e8a02938a9b606a528bc113ff3806b3a5572d3f0f973d365c7`

Runs 1–3 did not produce a genetic response. Run 1 preceded the harmonized pre-FST manifest. Run 2 passed manifest/raw-byte gates but failed on Python import before workbook parsing (`ModuleNotFoundError: benchmarks`). Run 3 was a duplicate queued under the same pre-response launch state. The only execution-path change before run 4 was `PYTHONPATH=.` plus a job guard restricting response-capable execution to workflow run number 4; frozen scientific code was unchanged.

## Frozen parent identities

- Stage-2 predictor fingerprint: `ef119675a596fe2044aca97b43efc618cfb7b00aee1dc3a1663ff5736c0a94ea`
- Stage-3A schema fingerprint: `a0b2c6bb0755f1d09f9aa88fbe4bfa645c5a4c8f011907fe4ceb93f64ff674de`
- pre-FST harmonization fingerprint: `91c3be6023d7cfe8778270950aa5463735ebb852bfafa68a7cc8d75004f9a63c`
- candidate family: `gabriel_current_flow`, `gabriel_shortest_path`, `geographic`
- EOG excluded from candidate selection
- bootstrap: 10,000 held-population resamples, seed `20260813`

## Raw genetic source identity

Zenodo record `4937634`, `Genalex_Th3all_IAA.xlsx`:

- size: `118400` bytes
- MD5: `ec25c053161d4d62b86c860193475784`
- SHA-256: `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`
- released Zenodo checksum matched the MD5

The raw workbook was deleted before workflow-artifact upload.

## Primary genetic response

The frozen primary response used complete 16-locus samples followed by exact within-population multilocus-genotype collapse.

- raw samples: `806`
- incomplete samples dropped: `0`
- exact within-population clonemates removed: `166`
- retained unique complete MLGs: `640`
- populations: `17`
- pairwise responses: `136`
- loci: `16`
- estimator: multilocus Weir–Cockerham theta, no clipping
- theta range: `0.14763190068206627` to `0.7086475782921913`
- transform: `theta / (1 - theta)`
- primary response CSV SHA-256: `e37cc82e4620e22cc5ab21ffaad35131369f661d37d206afce74038ca10befdc`

All-complete-ramet FST was computed only as a non-promotional descriptive sensitivity.

## Nested conventional-reference validation

Outer held-population nested selection chose:

- `geographic`: `14/17` populations
- `gabriel_shortest_path`: `3/17`
- `gabriel_current_flow`: `0/17`

Pooled MSE:

- fixed geographic reference: `0.1410802986208657`
- nested-selected conventional baseline: `0.14209054584817615`
- same selected baseline + frozen EOG: `0.13871588688746944`

Thus:

- nested-selected baseline minus fixed geography = `+0.0010102472273104401` (selector failed the predeclared competitiveness gate)
- selected + EOG minus selected baseline = `-0.0033746589607067112`
- selected + EOG minus fixed geography = `-0.002364411733396271`

EOG reduced MSE in `10/17` held-population folds.

## Bootstrap uncertainty

Equal-weight population-level delta MSE (`selected + EOG - selected`):

- mean: `-0.0033746589607067316`
- median: `-0.002125618979927177`
- fraction negative: `0.5882352941176471` (`10/17`)
- fixed 95% percentile interval: `[-0.0150470081208439, 0.010516385360070631]`

The interval crosses zero, so the predeclared EOG added-information uncertainty gate also fails.

## Promotion checks

- all 17 populations / 136 pairs aligned: **PASS**
- nested-selected conventional baseline pooled MSE <= fixed geographic pooled MSE: **FAIL**
- mean population EOG delta MSE < 0: **PASS**
- bootstrap upper 95% bound < 0: **FAIL**

Therefore `promotion_go = false` and the frozen status is `indeterminate_selector_reference_failure`.

## Interpretation boundary

This result does **not** establish independent empirical added information for EOG genetics. It contains a weak favourable EOG signal after augmentation, but the conventional selector failed its own fixed-geography competitiveness condition and the population bootstrap did not exclude zero. The correct interpretation is therefore indeterminate/no promotion, not a rescued positive result.

Symmetric pairwise FST remains incapable of validating migration directionality.
