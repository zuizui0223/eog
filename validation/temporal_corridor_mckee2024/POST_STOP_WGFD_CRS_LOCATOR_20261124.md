# McKee 2024 12-hour GPS: cross-sourced WGFD geography check

**Source-QC diagnosis only — not a scored EOG method result.** Frozen November 24, 2026.

## Question

Does the apparent source CRS mismatch persist when compared against a
specific externally published Wyoming herd geography rather than a broad state
bounding box? Prior EOG audit found an exact Dryad-source SHA-256 match, 28,953
sparse Point records, a publisher README/.prj declaring EPSG:3742, and coordinates
geographically plausible under candidate EPSG:5070. The underlying timestamp
precision and CRS-semantic STOP remain unchanged.

## Pre-comparison freeze

The numeric full extent of the Wyoming Game and Fish Department (WGFD)
[Baggs mule deer migration corridor service](https://services6.arcgis.com/cWzdqIyxbijuhPLw/ArcGIS/rest/services/MuleDeerMigrationBaggsWGFDCorridor/FeatureServer)
was fixed in protocol commit 4c1d19db6567e34e949fdc98359c36fca5b4b63a,
**before this new cross-source point/rectangle comparison**.

The public WGFD service explicitly describes a northern Dad/Atlantic Rim
component (38 mule deer, 90 migration sequences) and southern Wild Horse
component, with source records 2005–2016, edited to create management polygons.
The service's full rectangle is in EPSG:3857, X from -12021622.7691 to
-11916202.5626 m, Y from 5012625.0685 to 5110144.4915 m. We also froze a
5,000-m rectangle expansion as an untuned sensitivity check.

Only AtlanticRim from the exact original 12h GPS ZIP is evaluated, with the
predeclared competing input interpretations EPSG:3742, EPSG:5070, EPSG:5071,
ESRI:102003 and EPSG:3857. No heldout 2h data or new herd/corridor/buffer
could be selected after inspecting the results.

## Results: 17,248 Atlantic Rim points

| Coordinate interpretation | WGFD full rectangle | +5,000 m rectangle |
|---|---:|---:|
| Publisher's EPSG:3742 | 0 (0%) | 0 (0%) |
| Candidate EPSG:5070 | 16,533 (95.85%) | 16,812 (97.47%) |
| Candidate EPSG:5071 | 16,533 (95.85%) | 16,812 (97.47%) |
| ESRI:102003 control | 0 | 0 |
| EPSG:3857 control | 0 | 0 |

The exact 12h source digest remains
556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4.
No raw coordinates, herd IDs, exact timestamps or paths were exported. The
aggregate receipt is
[post_stop_official_baggs_locator_receipt_v1.json](post_stop_official_baggs_locator_receipt_v1.json);
the opt-in SHA-locked local replay is
[replay_official_baggs_bbox_locator.py](replay_official_baggs_bbox_locator.py).

## Claim limitations and independent checks

This is **stronger evidence that the supplied coordinate *label* is
inconsistent with the positions** than a generic Wyoming-range test, because
the external official geography explicitly covers the named Atlantic Rim herd.

It is NOT evidence of the precise intended original CRS: EPSG:5070 and
EPSG:5071 yield indistinguishable aggregate counts. It is also NOT an
independent ecological replication; the official corridor may derive from
overlapping collared deer and observation years. A fix inside a corridor's
**bounding rectangle** does not establish overlap with its polygon or a
true path, and no movement outcome has been predicted.

The [Dryad README](https://doi.org/10.5061/dryad.15dv41p51) still explicitly
declares EPSG:3742 and Mountain Time. The
[published McKee et al. paper](https://doi.org/10.1002/ecs2.4983)
documents sparse fixes around 00/01 and 12/13 Mountain Time, supporting
the previous midnight diagnostic but not resolving timezone/DST semantics.
The [Migration Mapper CalcBBMM.R code](https://github.com/jmerkle1/Migration-Mapper/blob/main/app4_uds/wmiScripts/CalcBBMM.R)
transforms supplied points to the population grid CRS; it does not specify
that EPSG:5070 or 5071 is the original source CRS.

**Decision:** Retain source-QC STOP until original processing metadata or
data-author confirmation resolves intended CRS (and timing semantics).
Only conditional input-method experimentation is justified. Dense 2h is
sealed, no ecology scores were computed, and frozen EOG-WF remains
3 scored /31 scientific STOPs /3 administrative exclusions.
