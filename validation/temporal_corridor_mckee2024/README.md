# EOG temporal path certificate: McKee 2024 sparse/dense GPS source qualification

**Stage: Gate0 — source metadata only. Not an empirical result.**

The source was selected on 2026-11-22, before the repository source-metadata workflow was executed. The frozen gate is [source_gate0_protocol_v1.json](source_gate0_protocol_v1.json). This programme is separate from the closed EOG-WF three-endpoint manuscript.

## Gate0 observed result (publisher metadata, not GPS data)

Source-only GitHub Actions run [45029127610](https://github.com/zuizui0223/eog/actions/runs/45029127610) returned `SOURCE_METADATA_IDENTITY_QUALIFIED__NO_TRACK_ROWS`, with the source receipt and its verified artifact ZIP digest `17adc8def2b3354759aacf7715b9b08f8152888fcc21c94bc9cc6e1669dd209c`. The full publisher-declared file roster is now [frozen here](gate0_publisher_metadata_frozen_v1.json); protocol-first commit was `144bb8fdeaf6cbae1ef09c82b48ddbf821732f4b` before the source API request.

- Public dataset ID 134688, numeric version ID 305836, version number 2.
- Sparse 12-hour ZIP: file 3334125; 1,539,661 bytes; SHA-256 declared.
- Dense 2-hour ZIP (sealed): file 3334126; 8,938,302 bytes; SHA-256 declared.
- README: file 3334129; 4,915 bytes; SHA-256 declared.

The source-files' SHA-256 values remain **declarations, not independently checked against downloaded file bytes**. No location record or binary source file was accessed. Subsequent Gate0 execution rejects any drift from this frozen receipt; it does not authorize Gate1.

## Publisher and stated source structure

- DOI: https://doi.org/10.5061/dryad.15dv41p51
- Source: McKee et al. (2024), *Estimating ungulate migration corridors from sparse movement data*. Dryad, published July 18, 2024.
- Available files according to the official landing page: GPS12hrs_Locs.zip (sparse), GPS2hrs_Locs.zip (dense), README.md.
- The accompanying README identifies two shapefiles, animal ID (AID), herd, season/year, timestamp (Mountain Time), and UTM coordinates (EPSG:3742). These descriptions have not yet been validated against actual file headers.
- Four herds reported in the publicly shared subset: Atlantic Rim, Clarks Fork and Dubois mule deer; Jackson elk. Additional herds mentioned by the study are not included in the publicly shared files and must not be silently substituted.

The authors used 2-hour GPS data as the reference for 12-hour sparse Brownian-bridge corridor estimation. This source offers a within-track held-out observation design but not a new independent animal cohort.

## Gate0: exact frozen metadata-only procedure

On the PR containing this file, the source workflow:
1. Runs offline source-contract tests with fake API responses.
2. Performs at most one GET of the official Dryad dataset metadata JSON.
3. Performs at most one GET of its canonical numeric-version file-inventory JSON.
4. Checks DOI, version, pagination, three exact filenames, file IDs, positive byte sizes and the form of the source-declared digests.
5. Produces a JSON receipt with publisher-declared metadata and explicit negative flags for source-file/GPS access.

No archive, README payload, shapefile header, location fix, animal ID or 2-hour holdout observation is downloaded or inspected at Gate0. Publisher-reported hashes are not independently verified file-byte hashes. The script does not follow redirects or access unapproved endpoints.

The file-ID constraints were frozen from the landing-page file links. Changing them after reading the API result requires a separately identified source protocol revision, not a silent correction.

## Next experiment (not yet authorized)

Only after Gate0 passes, freeze a separate Gate1 protocol to authorize sparse **12-hour file bytes only**, safe archive validation, coordinate/time schema examination, and response-blind eligibility. Before the withheld 2-hour file may be opened, freeze the state grid, time steps, independent support layers, finite model-world family, baselines, GPS uncertainty buffer, grouped validation unit, candidate-domain area and STOP criteria.

The primary candidate endpoint is false exclusion of held-out intermediate positive GPS fixes under the declared possible-world envelope, paired with a footprint-area penalty to prevent declaring the whole map reachable. Strong baseline comparisons must be predeclared. A necessary corridor inferred by graph logic cannot be treated as a confirmed animal transit route from intermittent telemetry: no fix at a node is not proof it was never crossed.

Individual-season and herd are dependence clusters; GPS points within an animal path are not independent study replications. The fixed-motion-variance benchmark published on the same 2-hour GPS reference is not an independent test of variance calibration.

## Stop boundaries

- Gate0 DOI, public version, file list, source hash or transport mismatch: HOLD_SOURCE_METADATA_UNVERIFIED, no source substitution.
- Gate1 missing schema, accurate time conversion, independent environmental/corridor graph or viable comparator: STOP before dense-GPS opening.
- No heldout 2-hour within-interval tracks, inadequate independent units or post-outcome world/threshold selection: STOP or descriptive-only under later predeclared rules.

**Frozen EOG-WF unchanged:** exactly 3 scored (2 favorable, 1 adverse), 31 scientific STOPs and 3 administrative exclusions. No fourth endpoint, no biological migration history inferred.

## Reproduction

- [Source freeze](source_gate0_protocol_v1.json)
- [Public JSON-only auditor](qualify_gate0.py)
- [Offline tests](../../tests/test_temporal_corridor_mckee_source_gate0.py)
- [Metadata-only GitHub Actions workflow](../../.github/workflows/eog-mckee2024-dryad-metadata-gate0.yml)
- [Time-coherent EOG path API](../../src/eog/v2/temporal_path_certificates.py)


## Uploaded original sparse GPS: exact source matching and source-QC STOP (2026-11-22)

The user-supplied 12-hour ZIP was independently verified at **1,539,661 bytes / SHA-256 `556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4`**, matching frozen official Dryad file ID 3334125. The original ZIP is NOT committed. This resolves file acquisition after the earlier HEAD/GET 403 transport STOPs, **not** source schema correctness.

All source inspection stages were precommitted as separate protocols before examining archive members, DBF record values, alternative time/CRS assumptions and SHP Point geometries. Detailed evidence and the decision boundary: [SPARSE_SOURCE_QA_20261122.md](SPARSE_SOURCE_QA_20261122.md).

Key limitations: 28,953 sparse points / 144 herd–animal ID combinations; 10,835 date-only timestamp strings; and source `.prj`/README declares EPSG:3742 although all 28,953 physical coordinates are geographically plausible under candidate EPSG:5070 and zero under the declared projection. These are **input-data QC findings**, not an EOG performance result. Unverified time-zone semantics and the authoritative intended CRS block confirmatory path prediction. All 2-hour dense GPS records remain unopened.

Optional reproducibility CLIs (require local user-supplied sparse ZIP, never raw-data uploads): [schema/geometry replay](replay_sparse_schema_and_geometry.py) and [time/QC replay](replay_sparse_time_qc.py). Existing EOG-WF denominator 3 scored /31 scientific STOP/3 admin exclusions is unchanged.

## November 24 cross-sourced WGFD Baggs geolocation diagnostic (no 2h data)

The [official-WGFD locator note](POST_STOP_WGFD_CRS_LOCATOR_20261124.md) and [frozen aggregate receipt](post_stop_official_baggs_locator_receipt_v1.json) add an independent **source of published geography** (not independent biological animals) to the existing CRS STOP. Among 17,248 AtlanticRim sparse fixes, 16,533 lie within the official WGFD Baggs corridor **bounding rectangle** under either EPSG:5070 or EPSG:5071, but zero under the publisher-declared EPSG:3742. Both Albers CRS alternatives have the same counts, so author CRS identity remains unresolved. The source SHA was checked again; 2-hour holdout and ecological scores remain unopened. A [12h-only aggregate replay script](replay_official_baggs_bbox_locator.py) is included, and the precomparison extent and hypotheses were frozen in the [protocol](post_stop_official_baggs_locator_protocol_v1.json) before running this new cross-source comparison.

## 2026-11-24: conditional 5070/5071 grid sensitivity and missing datum grids

The [new datum/Grid note](POST_STOP_5070_5071_DATUM_SENSITIVITY_20261124.md) and [aggregate receipt](post_stop_5070_5071_datum_grid_sensitivity_receipt_v1.json) establish an important limit. Using the original-SHA 12h GPS and installed **offline fall-back** datum transforms, EPSG:5070 and 5071 differ by a median 1.156 m geodesically, with 602 /28,953 distinct 100m-grid cell labels versus 62 /28,953 distinct 1km-grid labels under one predeclared WGFD-origin grid. The preferred NAD83/HARN datum transformation grid is **not installed** (TransformerGroup.best_available=false), so these results are not a bound on actual geodetic uncertainty. All original CRS/date-only source STOPs remain; 2h GPS not opened, no ecological prediction computed. [Local 12h-only producer](replay_post_stop_5070_5071_grid_sensitivity.py) does not read animal identities.

## November 24: date-only time intervals and globally coherent pair/triplet paths

The [interval-valued time audit](POST_STOP_TIME_INTERVAL_COHERENCE_20261124.md) preserves original date-only timestamps as **uncertainty**, rather than imputing midnight. A 12.5h maximum BBMM gap from the source publication was applied to the same original-SHA 12-hour GPS's 28,532 within-group adjacent pairs. With unknown full-day clock time, 6,327 pairs robustly pass, 21,412 are contingent and 793 fail the interval rule; under a purely **hypothetical 00–01 local-clock window**, 17,034 pass robustly, 10,640 remain contingent and 858 fail. For 28,111 three-fix windows, **64** three-record windows with two individually possible links cannot share one globally coherent middle time under full-day uncertainty (affecting 41 dependent animal-season groups); zero under the stronger 00–01 assumption. These are source-data conditional clock tests, not biological route, BBMM or EOG predictive validation. The [pair](post_stop_time_interval_pair_receipt_v1.json) and [triplet](post_stop_triplet_time_coherence_receipt_v1.json) receipts and [replay script](replay_post_stop_time_interval_qc.py) do not export any timestamps or individuals; 2h dense GPS remains sealed, and source time/CRS STOPs remain unchanged.
