# Genetic-assignment origin evidence: source-only feasibility gate v1

## Direct next question from EOG minimum-relaxation

Merged PR #701 showed that a recorded-positive distribution can be reconciled either by a wider allowable one-hop distance or by hypothetically reopening a few `t−1` recorded-zero source sites. Both are **post-outcome conditional explanations**; none reconstructs realized dispersal, true colonization, or detection error.

A useful external measurement is a **source → destination → year** assignment from independently recorded dispersal evidence, rather than another re-weighting of the same observed-positive targets. DiLeo et al. (2022; DOI `10.1098/rspb.2022.0322`) used genetic assignment tests over **five years and 232 patches** of the same Åland Glanville fritillary metapopulation. Published reconstruction is not direct movement observation, and source assignment itself may be uncertain.

The published paper cites an empirical data deposit (`10.5061/dryad.7h44j0zws`) and a connected software deposit is catalogued at Zenodo record `6610910` (`10.5281/zenodo.6610910`). The latter is explicitly **software**, not assumed to contain the original movement events. The original Dryad bytes and source-to-destination keys have NOT been inspected as part of this gate yet.

## Qualification — no ecological response opened

Freeze the following protocol before network access:
`validation/glanville_genetic_origin_source_preflight_v1/protocol_v1.json`.

One metadata GET each to `https://zenodo.org/api/records/6610910` and to `https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.7h44j0zws`. Report HTTP status, metadata hash, publication identity, individual file names, file sizes and checksums. If the Zenodo record exposes a deterministic small eligible file, obtain **only one** bounded file and verify its publisher checksum; inspect **only** the table header or a safe archive member path list, not any records.

Retain an explicit source-qualification STOP for access 403, absent metadata, too-large files, unknown schema, checksum mismatch or a dataset that only publishes code and no source/destination table. A green CI process **does not** override a scientific STOP or make missing data an ecological result.

The key independent evidence needed for further work is not the article's *overall* movement distance distribution alone. We need:
- verifiable `source_patch` and `destination_patch` **per assignment**, with provenance and ambiguity;
- year/date of assignment aligned to a `t−1 → t` period;
- overlap of those patch IDs with the SHA-frozen 2019 Åland survey network or a published exact crosswalk;
- detection histories that can distinguish a true previously empty destination from a missed occupied patch.

The 2022 inferred movement data may overlap the study period and individual source samples already used in EOG development. It is **an independent evidence type**, not necessarily an independent population/sample or a new prospective validation endpoint.

## Scientific decision gate

`SOURCE_METADATA_PREFLIGHT_COMPLETED_EVENT_JOIN_NOT_VERIFIED` means only a published source is described and possibly a header/manifest can be inspected. Neither true source identity, source/destination joinability, nor time-ordered dispersal validation are known.

If the published record offers no comparable event IDs, the correct result is **source-only structure qualified or source unavailable**. Do not fill in inferred directional assignments from mean distances, genetic kinship or site proximity.

The EOG-WF prospective empirical study remains closed at 3 scored / 31 scientific STOP / 3 administrative exclusions. This source-only audit is exploratory background for the separate minimal-relaxation research line.

## Execution

```bash
python -m pytest -q tests/test_glanville_genetic_origin_source_preflight_v1.py
python scripts/glanville_genetic_origin_source_preflight_v1.py \
  --protocol validation/glanville_genetic_origin_source_preflight_v1/protocol_v1.json \
  --output results/glanville_genetic_origin_source_preflight_v1/receipt.json
```
