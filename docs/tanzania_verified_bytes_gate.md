# Tanzania verified-byte structural gate

The Tanzania forest-fragment benchmark is the frozen primary full non-island structural validation. Dryad DOI `10.5061/dryad.p042h0c` exposes the file inventory and integrity metadata publicly, but anonymous binary download is blocked from the current hosted runners.

`benchmarks/audit_tanzania_verified_bytes.py` is therefore the mandatory bridge between source acquisition and any species-level EOG analysis.

## Required sequence

1. Generate or retrieve the frozen Dryad `source_manifest.json` with `benchmarks/fetch_tanzania_dryad.py`.
2. Obtain the six analysis files from the official Dryad record in an environment where download is permitted:
   - `Sites.csv`
   - `spp_occur.csv`
   - `Nodes_E.csv`
   - `Nodes_W.csv`
   - `raster_east3.tif`
   - `raster_west3.tif`
3. Run the verified-byte audit. Every file must exactly match Dryad's declared byte size and digest before schema inspection.
4. CSV dimensions/headers and TIFF identity are audited. With `rasterio` installed, raster CRS, bounds, dimensions, transform and nodata are also frozen.
5. Only after this gate passes may a later PR freeze column semantics, site-node-raster alignment and the 10-presence/10-absence species eligibility cohort.
6. Species-level EOG results remain prohibited until those later pre-outcome gates are frozen.

Example:

```bash
python benchmarks/audit_tanzania_verified_bytes.py \
  --source-dir /path/to/official-dryad-files \
  --manifest results/tanzania_source/source_manifest.json \
  --output results/tanzania_source/verified_schema.json
```

## Scientific boundary

The gate does not inspect which bird species perform well, does not choose a connectivity model, and does not compute occurrence discrimination. It exists to make it impossible to substitute mirrored, modified, partially downloaded, or bot-challenge content for the frozen Dryad source.
