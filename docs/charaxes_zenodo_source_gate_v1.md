# Charaxes jasius — single-record non-Dryad source preflight

## Mainline role

The prior EOG × BAM analyses established shared-reference environmental geometry
and static geographic topology across 12 deterministic known-truth landscapes.
The Gotland and Pyrgus Dryad payloads ended in HTTP 403 **transport stops**;
no field A/B/M result was obtained. These are not evidence about the biological
hypotheses, and they do not authorize retries of those frozen source contracts.

**This is a distinct Zenodo dataset**, not an alternative delivery route for
either previously stopped dataset.

## Publicly described system

Zenodo DOI `10.5281/zenodo.20525795`, record ID `20525795`:
Torres-Vila & Kőrösi (2026), `Charaxes jasius`, southwest Iberia,
1666 bait-trap placements spanning 2018–2024.

Two publicly listed files:

- `C_jasius_readme.csv`, indexed MD5 `296db7fac71b138ec6d84f99391388e0`;
- `C_jasius_reduced_dataset.csv`, indexed MD5 `6f9f638a1c6966f567c4b7b783a5a47d`.

The published study already reports positive occupancy association with
`Arbutus unedo` host cover and negative association with distance to
nearest host patch, as well as abundance association with host-patch
connectivity. These headline relationships are **prior art**, not EOG
discoveries.

## BAM interpretation boundary

- **B candidate**: host-patch cover `Arbutus unedo` at eight landscape
  scales. Availability/host patch abundance is not proof of a realized
  biotic interaction at every trap.
- **M candidate**: host-patch-based geographical connectivity under a
  specified dispersal kernel; it is **dependent on B source geometry**.
  Do not treat B and M as independent experimental axes or assert actual
  dispersal rates from an index alone.
- **A candidate**: forest habitat type. It is habitat/context rather
  than measured physiological abiotic tolerance. A true climatic or
  microclimatic axis remains unverified.
- **G candidate**: focal butterfly capture/detection data, not guaranteed
  to be occupied-population state. Detection and trap effort need explicit
  modeling or a limited positive-only contract.

**The data are not yet qualified for a complete independent A/B/M
mechanism identification.** Independent EOG geometry results can only
be interpreted after actual file/schema and measurement gates.

## Frozen Gate0 (this PR)

Protocol committed first at
`81f360249b48d9ebff539367911dae0331b27225`:
`validation/charaxes_zenodo_metadata_v1/protocol_v1.json`.

The only permitted access now is a **single**
`GET https://zenodo.org/api/records/20525795`.
The response must be a JSON object with the exact record ID and DOI,
two exact filenames, expected MD5 identities and bounded file sizes.

It does **not** download the README or biological table. It can return
`SOURCE_METADATA_QUALIFIED_NO_RESPONSE_ROWS` or a terminal
`SOURCE_STOP_*`. Retry, fallback or alternative host after 403/429
is forbidden under this protocol.

Next stage, only if source-qualified: separately freeze and verify exact
README/documentation semantics, file bytes and direct measured columns;
then decide whether an independently measured A/B/M design is possible.
Preserve all null, negative, unidentifiable or inaccessible outcomes.

## Successful fixed metadata result (2026-10-29)

GitHub Actions run https://github.com/zuizui0223/eog/actions/runs/40862054463
performed the one authorized official API request. It qualified the exact
record and **both** files against the precommitted roster and MD5 identities.

- README `C_jasius_readme.csv`: **1,068 bytes**.
- Data `C_jasius_reduced_dataset.csv`: **152,897 bytes**.
- API metadata result fingerprint:
  `b500ca1c05cb4ac591619ff4aee8b4513f78ff300d2a5674d9fe3b576eb95142`.
- Exact artifact id `12892061774`, original ZIP SHA-256
  `7d1a1a52743bde97050c779c5787624369c825036821d2a8f0783a224249e835`.
- **Zero biological bytes downloaded** and no ecological inference.

Canonical commit-bound receipt:
`validation/charaxes_zenodo_metadata_v1/result_receipt_v1.json`.
The metadata gate is now **manual-only** to avoid repeated API access.
This is source qualification, not an A/B/M science result.
