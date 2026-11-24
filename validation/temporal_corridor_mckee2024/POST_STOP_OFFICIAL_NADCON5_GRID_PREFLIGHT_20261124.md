# McKee 2024: NOAA NADCON5 grid-backed EPSG5070/5071 comparison — acquisition preflight

**2026-11-24. Status: NOT RUN with the official datum shift. Source and model validation STOPs remain.**

## What the prior CRS test could and could not establish

The original source declares [NAD83(HARN)/UTM zone 12N EPSG:3742](https://doi.org/10.5061/dryad.15dv41p51), yet source XY transforms to the Wyoming study area under candidate [NAD83/Conus Albers EPSG:5070](https://epsg.io/5070) and [NAD83(HARN)/Conus Albers EPSG:5071](https://epsg.io/5071). A separate official WGFD Atlantic Rim geographic check was compatible with both candidate Albers definitions. **Neither candidate is certified as the data author's intended original CRS**.

The previous [source-only datum comparison](POST_STOP_5070_5071_DATUM_SENSITIVITY_20261124.md) used offline pyproj 3.7.2 / PROJ 9.5.1, which lacked the preferred NAD83→NAD83(HARN) grid. It explicitly reported fallback results rather than claiming the preferred datum operation had been used. That original result described **two independently constructed candidate→WGS84/EPSG3857 transformations**:

- Geodesic difference median **1.155895 m**, max **1.200898 m**.
- Cell flips on one frozen EPSG3857 grid anchored at WGFD's lower-left x/y: **602** at 100m, **233** at 250m, **114** at 500m, **62** at 1km, **8** at 5km, among all **28,953** original sparse Point records.

In this follow-up, the original 1,539,661-byte SHA-verified 12h ZIP was **independently reopened and these old fallback quantiles and every flip count were exactly reproduced** (see the [aggregate preflight receipt](post_stop_official_nadcon5_integrity_and_blocker_receipt_v1.json)). This is a useful reproducibility check, **not** a validated physical datum-offset bound or proof of the source coordinate system.

## A concrete new advance: primary-source grid fingerprint pinned

The [official OSGeo PROJ-data catalogue at files.geojson](https://github.com/OSGeo/PROJ-data/blob/master/files.geojson) identifies the datum correction file required by the local EPSG5070→5071 best operation:

| Attribute | Verified official metadata |
|---|---|
| NOAA / OSGeo grid filename | us_noaa_nadcon5_nad83_1986_nad83_harn_conus.tif |
| Official origin | https://cdn.proj.org/us_noaa_nadcon5_nad83_1986_nad83_harn_conus.tif |
| Exact file size | **3,522,682 bytes** |
| Exact SHA-256 | **e12ac2e886edafe616e0994c610ad3daa01db17c00d0e9938145d956f249fc2f** |
| Geographic transformation | EPSG:4269 NAD83 → EPSG:4152 NAD83(HARN), CONUS |
| File catalogue source | OSGeo/PROJ-data files.geojson, master blob de494d5669d976abb650c4d730fa893964e3fdc0 |
| Local previous grid status | Unavailable / best_available=False |
| Preferred operation's reported accuracy metadata | 0.05m for NAD83→HARN operation 47, **if** appropriate and grid present |

The exact [pre-acquisition protocol](post_stop_official_nadcon5_5070_5071_protocol_v1.json) was committed at **28352d5a0aafc5404d1a3652b632b98b9889d4fa** before attempting to retrieve this public datum grid or recalculate source positions.

## What happened in this environment

- A direct retrieval attempt of the official datum GeoTIFF failed.
- The container could not resolve the host: curl reported a DNS failure for cdn.proj.org.
- A search of the installed filesystem found **no copy of the specific required grid**, and pyproj TransformerGroup(EPSG5070, EPSG5071) still reports **best_available=False**. The only locally available operation is a **ballpark geographic offset**, with accuracy=-1 (unknown).
- The **official GeoTIFF bytes were NOT retrieved** and their pinned SHA has NOT been matched against a downloaded file. Therefore **NO official-grid-backed displacement values, grid cell flips, measurement error bound, or source-CRS certification are reported**.

The official grid catalogue's SHA is a verified *expected digest*, not evidence the grid exists in the sandbox. Downloading the grid would remove one computational dependency but **would not independently identify the source's true original CRS**.

## Reproduction once official grid bytes are available

The [fail-closed source-only replay](replay_post_stop_official_nadcon5_grid.py) is ready but does **not** run a pretend best transformation when the grid is absent:

1. Supply the public NOAA GeoTIFF under its exact filename from a trusted copy of the above official CDN.
2. Verify its byte size equals **3,522,682** and SHA-256 equals **e12ac2e886edafe616e0994c610ad3daa01db17c00d0e9938145d956f249fc2f**. The script rejects the wrong name, size, symlinks, non-TIFF headers or unexpected digest **before reading any sparse GPS Point coordinates**.
3. Append the verified grid's private directory to the PROJ data paths, explicitly turn PROJ network **off**, and require TransformerGroup(5070,5071).best_available=True and the selected non-ballpark operation to **reference this exact NOAA grid** with reported accuracy <=0.1m. If not, stop.
4. Only then read the exact publisher-hash-matched **12h sparse Point geometry**, transform source-as-5070 XY to a common EPSG5071 target frame and compare against the same raw XY interpreted as EPSG5071. Report aggregate geodesic and WebMercator offsets and the pre-frozen grid origin/width cell flips. Never report raw coordinates, dates or individual tracks.
5. Keep the **previous ~1.156m ballpark result as a separate numerical estimand**, not a quantity for direct subtraction from the direct EPSG5070→5071 official grid-backed offset. Different transformation pathways cannot be silently conflated.

The [offline regression tests](../../tests/test_mckee2024_official_nadcon5_grid_preflight.py) pin exact publisher/source and NOAA/OSGeo grid fingerprints, assert failure for missing or tampered GeoTIFFs, check the previous baseline's exact numeric reproducibility, and exercise the geographic/grid output math using synthetic nonanimal Point arrays.

**Command once the grid is available locally on an environment with a PROJ installation**:

\`\`\`bash
python validation/temporal_corridor_mckee2024/replay_post_stop_official_nadcon5_grid.py \
  --source-zip /path/to/GPS12hrs_Locs.zip \
  --official-grid /private/trusted/us_noaa_nadcon5_nad83_1986_nad83_harn_conus.tif \
  --output /private/output/mckee_verified_grid_sensitivity.json
\`\`\`

## Scientific STOP remains

The original file's WKT and Dryad README continue to declare EPSG:3742 despite Albers-family coordinate/geography consistency; precise author-intended CRS cannot be inferred from NOAA grid availability. The earlier **10,835 date-only timestamp** issue now has a credible R4.3 exact-midnight serialization mechanism, but original exporter version and Mountain fixed-MST versus DST-aware clock encoding remain uncertified. Both are required before formal 2h holdout scoring.

No dense 2h GPS was opened, no DBF record rows or animal identifiers were read for this follow-up, no EOG model was fit or scored, and EOG-WF remains **3 scored /31 scientific STOP /3 administrative exclusions**. The controlling provenance issue is [#745](https://github.com/zuizui0223/eog/issues/745). The official NOAA data grid is **neither a biological validation nor an accuracy bound on raw GPS collars**.
