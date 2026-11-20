# Independent marked-movement records: exact Dryad publisher transfer and schema gate v2

> **後続の生物学的適格性（2026-11-20）:** publisher SHA/CSV headerが適格でも動物移動効果が採点できたわけではない。ヒキガエルの[独立source-anchor試験](independent_toad_source_anchor_geography_v1.md)は `STOP_GEO_UNIT_CONCORDANCE` で未評価。診断結果は[事後source-QC](independent_toad_geocoordinate_diagnostic_v2.md)であり、元のSTOPを解除しない。


**Status:** source transport and CSV-header qualification only, **zero biological outcomes read or modeled**. No new scored EOG-WF endpoint, no reinterpretation of historical Glanville. This is a follow-up to the explicit transport STOP in [v1](independent_movement_source_gate_v1.md) and no-payload [HEAD redirect audit](independent_movement_redirect_host_v1.md).

## Why the first gate stopped, and what v2 changes

Original public Dryad metadata, version IDs, file names, byte sizes and SHA-256 digests were independently retrieved for two studies, but both version ZIP downloads returned `STOP_UNEXPECTED_SOURCE_REDIRECT`. A separate frozen and successful **HEAD-only** provenance audit established that the **first HTTP 302** sent by the two official version ZIP endpoints points to the same specific AWS Lambda function host:

```text
w27i4vubmmwkssdf6xpszafmhq0rffog.lambda-url.us-west-2.on.aws
```

This hostname is an **observed publisher redirect target**, not an unconditionally trusted domain. The [new pre-payload v2 protocol](../validation/independent_movement_source_gate_v2/protocol_v2.json) allows **only this exact first redirect**, not arbitrary `*.on.aws`. Later redirect sites are limited to explicit AWS S3/CloudFront host suffixes and only after passing the first-hop exact-match gate. No signed URLs or query parameters are logged.

The [source-only v2 script](../scripts/eog_independent_movement_source_gate_v2.py) reuses the original metadata/parser module and independently verifies each received file's **actual SHA-256 and byte size** against the publisher manifest already frozen *before* this second-stage transport.

## Frozen publisher versions, no after-the-fact source selection

| Source | DOI | Publication version | Frozen file requirements |
| --- | --- | ---: | --- |
| Heliconius experimental translocation / mark–release–recapture | [10.5061/dryad.34tmpg4m6](https://doi.org/10.5061/dryad.34tmpg4m6) | 148124 | `data_site_fidelity.csv` (8,099 bytes), `turning_data.csv` (4,459 bytes), `README.txt` (4,635 bytes) |
| Toad experimental displacement / recapture | [10.5061/dryad.x3ffbg7ms](https://doi.org/10.5061/dryad.x3ffbg7ms) | 198534 | `Jreidini_and_Green_homing_toads_2021.csv` (18,702 bytes), `README_file.rtf` (2,102 bytes) |

The file SHA256 digests are retained individually in the v2 protocol and were obtained from the first official publisher metadata receipt. A file is rejected if even one byte changes.

## Strict scientific STOP rule

A **PASS** means only that the official publisher transport, checksum identity, CSV headers, and basic row counts qualify. It **does not** imply that individual source, experimental release and later recapture locations are separable, that environmental/barrier metrics exist, or that a biological MRR response has been validated.

The gate preserves statuses including `STOP_FIRST_REDIRECT_HOST_NOT_PINNED`, `STOP_UNVERIFIED_LATER_REDIRECT_HOST`, `STOP_PINNED_PUBLISHER_SHA256_OR_SIZE_MISMATCH`, and `STOP_VERSION_ID_CHANGED`. Any STOP prevents further biological scoring. External ecological predictions require a **separate pre-target evidence contract** written only *after* verifying the source columns, and before opening any individual outcomes.

The exact-host URL is a publisher-issued download mechanism, not a statement of AWS ownership or a claim that the tool can infer natal origins. At best, these experiments may validate *individual-level observed geographic movement*; full geographic×environment×barrier EOG-MRR remains unqualified without a distinct candidate ecological graph and independently measured edge properties.

## Reproducibility

- [Official version + SHA pretransport contract](../validation/independent_movement_source_gate_v2/protocol_v2.json)
- [Source-only exact-host adapter](../scripts/eog_independent_movement_source_gate_v2.py)
- [Offline host/sha/STOP tests](../tests/test_eog_independent_movement_source_gate_v2.py)
- [GitHub Actions gate](../.github/workflows/eog-independent-movement-source-exact-host-v2.yml)

**Output is metadata only:** the original ZIPs, individual rows, coordinates or experimental outcomes are not committed or uploaded as artifacts. The EOG-WF scored denominator remains **3 / 31 / 3**.
