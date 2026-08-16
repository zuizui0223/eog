# SIVFLORA confirmation pre-outcome amendment 001

## Status

This amendment was fixed **after source identity and workbook schema audit, but before any SIVFLORA world set, held-out feature, predictive model, or validation result was computed**.

It resolves two implementation ambiguities exposed by the frozen schema and public climate-file feasibility. It does not change the scientific question, response rule, world count, thresholds, comparator hierarchy, primary metric, or favourable/no-added-value gate.

## 1. Island coordinates supersede locality aggregation

The original contract already stated that an explicit island-level coordinate pair has priority for node geometry. The frozen workbook schema audit confirmed that the `islands_data` sheet contains exactly 22 primary island/archipelago rows with explicit latitude and longitude values.

Therefore the same 22 declared island coordinates are now used for:

- great-circle geographic distances;
- CHELSA sampling;
- WorldClim sampling.

The earlier environmental text proposing an equal-weight mean across unique locality climate values is superseded. No occurrence/locality row count can therefore weight environmental node values.

This is a **schema-driven clarification**, not an outcome-driven change.

## 2. WorldClim resolution is fixed at 2.5 arc-minutes

WorldClim v2.1 is fixed to the official `2.5m` bioclimatic archive:

`https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip`

Reason fixed before outcome modelling:

- the confirmation contains very small oceanic islands, so the coarser 5m/10m products are not preferred when a finer globally consistent product is available;
- the 30-second global bioclimatic archive is unnecessarily large for a 22-node point-sampling confirmation;
- 2.5m is a pre-outcome computational/resolution compromise, not a tuned biological scale.

Only BIO1, BIO5, BIO6, BIO12 and BIO15 are used.

If any of the 22 declared island coordinates returns missing/nodata for any selected variable in either climate product, the climate freeze is **blocked/non-estimable**. Do not move the coordinate, snap to a nearby cell, substitute a locality, change resolution, or impute after inspecting incidence outcomes.

## 3. Climate product symmetry

CHELSA v2.1 and WorldClim v2.1 2.5m are both sampled at the same 22 frozen node coordinates. Each five-variable product is standardized independently across those 22 nodes, then used only to construct its own environmental-distance family.

The two products remain alternative analyst-choice representations; they are not averaged into one climate surface.

## Unchanged rules

Still frozen unchanged:

- 22 nodes;
- species-rank Native/Endemic catalogue-incidence target;
- 4 geographic thresholds q25/q50/q75/q90;
- environmental q50/q75 per product;
- exactly 20 worlds = 4 geography-only + 8 CHELSA + 8 WorldClim;
- LOIO validation;
- nested self/held-out leakage firewall;
- R0/R1/R2/C comparator hierarchy;
- C minus R2 island-macro log-loss primary contrast;
- 10,000 paired-island bootstrap replicates, seed 20260816;
- all five favourable-gate conditions;
- no retuning after outcome inspection.
