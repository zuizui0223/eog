# NEON small mammal data: source qualification before EOG×BAM field tests

## Concrete external data candidate

**NSF NEON Small mammal box trapping**, product **DP1.10072.001**:
https://data.neonscience.org/data-products/DP1.10072.001

NEON's native tables are `mam_perplotnight` (plot-level trapping
night and effort) and `mam_pertrapnight` (individual trap/night
outcomes). Join using `nightuid`, checking duplicates and cardinality.
NEON's official design includes **three consecutive trapping nights**
on pathogen grids and **one night** on diversity grids. Only verified
multi-night trap histories are candidates for within-bout detection
estimation. The product includes both captured animals and trap
opportunities, so a properly qualified noncapture can be retained
rather than invented from absence of a capture record.

Source: NEON product and documentation (see URL above);
NEON user guide:
https://data.neonscience.org/api/v0/documents/NEON_smammal_userGuide_vE1?inline=true

NEON also notes known individual-trap geolocation errors in 18
mammal grids. Plot-level locations are less affected; exact
individual-trap spatial coordinates require separate qualification.
Sampling schedules changed in 2024, and traps that were not deployed
or could not be sampled must not be treated as valid nondetections.

## What was and was not accomplished

This PR freezes a source qualification contract and implements a
fail-closed structural gate for **native** perplotnight and
pertrapnight CSVs. It checks required join keys, duplicate plot
nightuids, orphan trap records, same trap in multiple nights of
the same bout, and hashes original source files.

**No original NEON CSV bytes were acquired or analyzed in this
commit.** The source is a documented *candidate*, not an already
qualified real detection history. The machine gate's
`PASS_SOURCE_STRUCTURE_ONLY` is not sufficient for a valid
occupancy model.

Before any ecological model, additionally inspect trapStatus
capture/no-capture coding, trap deployment, samplingImpractical,
quality flags, species identity, duplicates/recaptures, closure
and time-varying effort. Missing rows are not certified negative
traps. Species selection and geographic unit must be frozen before
fitting.

## Why this is a better empirical starting point

The previously verified Charaxes reduced CSV has trap capture
records but not independent repeat-visit and effort histories.
NEON's *native* small-mammal product explicitly contains
per-trap-night data and effort information, so its design can
potentially support detection models. It does **not** provide
independently measured full abiotic A, biotic B and dispersal M
constraints, so no causal BAM or EOG response intervention
claim follows.

## Run after downloading source data

```bash
python benchmarks/neon_mammal_source_gate_v1.py \
  --perplotnight mam_perplotnight.csv \
  --pertrapnight mam_pertrapnight.csv \
  --output neon_source_gate_result.json
```

Source provenance must include NEON release, site, month,
download URL, SHA256, and any documented issues. If no verified
source files exist, status remains **STOP: not ingested**.

The synthetic EOG×BAM 768-world series and EOG-WF endpoints
are unchanged.
