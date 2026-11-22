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
