# Azores independent-confirmation evidence

## Final status

`non_estimable_pre_model_taxon_scope_zero`

This directory preserves the staged Azores independent-confirmation attempt under the contracts that were frozen at the time. It is **not** a successful confirmation result, and the historical contract is not rewritten after the later EOG method audit.

For future validation rules see [`../../docs/method_validation_protocol.md`](../../docs/method_validation_protocol.md).

## Frozen sequence

1. exact GBIF/DwC-A source identity frozen before archive parsing;
2. nine GeoNames island nodes frozen response-blindly;
3. CHELSA v2.1 and WorldClim v2.1 BIO1/BIO5/BIO6/BIO12/BIO15 frozen at those nodes;
4. exact response-blind 20-world universe frozen and fingerprinted;
5. nine-island LOIO response/comparator/model contract frozen before Taxon/Distribution rows were read;
6. Taxon-core estimability gate run once.

## Final stop

The Taxon core contained:

- 15,256 canonical taxa;
- 8,078 canonical species;
- 2,455 canonical Plantae species;
- **0 species satisfying the frozen literal `Tracheophyta` rule**.

The source used vascular phylum vocabulary including `Magnoliophyta`, `Pteridophyta`, `Lycopodiophyta` and `Pinophyta`. Broadening the frozen rule after observing that vocabulary would change the predeclared population and is prohibited for this attempt.

Critically:

- Distribution rows read: **0**;
- species-island response scored: **false**;
- predictive models fitted: **false**;
- confirmation metric computed: **false**;
- contract changed after source rows: **false**.

The exact frozen stop is [`estimability_result.json`](estimability_result.json).

Azores therefore supplies **no favourable or null EOG result**. It is an independent but non-estimable process-integrity record.

## Prospective methodological lesson

The later method audit does not rescue Azores. It changes only future protocol:

- a generic response-blind eligibility screen may inspect taxonomic/rank/establishment vocabularies needed to define a deterministic **semantic** mapping before the EOG-specific outcome contract is frozen;
- future validation separates identity-preserving inferential value from predictive added value;
- future world families distinguish biological/process uncertainty from analyst-choice sensitivity worlds;
- confirmatory uncertainty respects the actual number of independent outer units.

## Preserved evidence

- `azores_nodes.csv` — immutable response-blind island nodes;
- `node_freeze_manifest.json` — node source/rule provenance;
- `azores_climate.csv` — frozen nine-node climate table;
- `climate_freeze_record.json` — climate product/transport/hash record;
- `world_freeze_record.json` — exact 20-world family fingerprint and thresholds;
- `dwca_schema_record.json` — schema-only record inspected before response-contract freeze;
- `estimability_result.json` — authoritative pre-model stop result.

The corresponding contracts and reproduction scripts remain under `benchmarks/`, with contract tests under `tests/`. Completed one-time GitHub Actions scaffolding is not part of the durable scientific surface.

## Claim boundary

This attempt is neither favourable nor null evidence for EOG predictive added value or identity-preserving inferential value. The integrated EOG claim remains **exploratory-supported but independently unconfirmed**.
