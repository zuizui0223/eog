# Camissoniopsis two-layer EOG-WF validation screen

## Final status

> **`gate0_stop_response_inseparable_geometry`**

The candidate stopped before any 2019/2022 survey row, occupancy value, abundance value, colonization outcome or extinction outcome was opened.

This is not evidence for or against the post-Glanville label-invariant Layer-B predictor.

## Why the candidate was screened

Public study reporting made this an unusually strong event-feasibility candidate:

- 5,418 randomized coordinates across roughly 938 km of coastline;
- 3,485 surveyed plots in the two-period study;
- 232 colonizations and 195 extinctions from 2019 to 2022;
- colonization risk set 1,223 and extinction risk set 638;
- stable Zenodo v3 transport rather than a Dryad-only route.

These aggregate values were used only to establish that a prospectively frozen event gate was plausible. They were not used to tune EOG worlds, Layer-B features, spatial blocks, comparators, metrics or decisions.

## Frozen source

- Zenodo record `14860282`, version 3;
- DOI `10.5281/zenodo.14860282`;
- archive `MetapopulationsCode.zip`;
- size `17,670,844` bytes;
- MD5 `77f8047ce9fc908683824643a7ea7c0b`;
- SHA-256 `c28054f8393c0ea5f8b35efd23ab2d24db630c148503fcd1c65d25644a373e4e`;
- CC BY 4.0;
- publication DOI `10.1111/ele.70128`.

## Response-firewalled inventory

Authoritative workflow:

- run `32095779472`;
- artifact `9309878540`;
- artifact ZIP SHA-256 `c1b4fe1e93312d86f82f8f2b4d7a28d86ffc4d7d1d5cccbb2252d49a1494995f`;
- inventory fingerprint `4b400a5b29689b1d39755917d275b95c08303dfbdd42053336e6d1bd3641cd61`.

The workflow:

- verified the exact archive checksum;
- listed 230 archive members / 209 files;
- read full code and named documentation only;
- read the bounded first physical record of ten text-like data files;
- inventoried all other binary/spatial members without deserializing them.

Firewall state:

- response rows opened: **false**;
- response values parsed: **false**;
- serialized objects deserialized: **false**;
- spatial attribute tables opened: **false**.

## Decisive role adjudication

The actual survey plot coordinates are not released as a separate response-free registry.

### `survey_dat.csv`

Geometry columns:

- `plot_id`
- `plot_lat`
- `plot_long`

The same physical rows also contain:

- abundance (`cam_total`, `log10_cam_total`);
- occupancy (`occupancy_bn`);
- local abundance and neighbouring presence;
- `colonization`;
- `extinction`.

The archived analysis code reads this file directly as the primary analysis table.

### `metapopulations_data.csv` and `ext_plots_unsuit.csv`

Both also co-locate plot coordinates with occupancy/abundance information; the latter additionally contains colonization and extinction fields.

### Rejected alternatives

- `gbif_occurrencedata.csv` contains external GBIF occurrence coordinates, not the randomized 2019/2022 survey-plot universe.
- `occupancy_bootstraps.csv` is response-derived and does not define canonical plot geometry.
- `__MACOSX/**/._*` members are AppleDouble metadata sidecars, not scientific tables; their binary payload caused false keyword hits in the initial inventory.
- No independent coordinate table, point layer or complete pairwise-distance matrix exists in the archive.

## Gate decision

The full survey node universe cannot be frozen without reading rows that simultaneously contain the outcomes reserved for the once-only response gate.

Therefore:

- canonical geometry frozen: **false**;
- structural LCC Gate 1 run: **false**;
- EOG worlds constructed: **false**;
- Layer-B representation evaluated: **false**;
- prediction model fit: **false**.

Role-adjudication fingerprint:

`1e869b35027c3c95eab0a31f8bd0b8113d9340b5788eb716ac264a9fc33d8cce`

## No-rescue boundary

Do not:

- extract coordinates from `survey_dat.csv` and claim the response remained unopened;
- replace the randomized survey network with GBIF occurrences;
- reconstruct coordinates from figures;
- weaken the response firewall because the published event count is attractive;
- rerun a redesigned version and call it fresh independent confirmation.

The candidate closes unmerged so no system-specific code expands production `main`.
