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
