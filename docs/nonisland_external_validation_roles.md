# Non-island external validation roles

This document freezes the roles of the two non-island external systems after the Czech PLOS S4 schema audit and before any non-island EOG species-level outcome is calculated.

## Czech dry-grassland patches: plant conceptual replication

The public PLOS S4 table for the 272-patch Czech dry-grassland system was retrieved and structurally audited before any EOG outcome. The table contains exactly 272 data rows and 15 columns, including:

- patch identifier;
- local abiotic variables (`TWI`, `slope`, `Elevation`, `PDSI.June`);
- patch area / present-day and historical isolation-area variables (`LogA`, `Ia2000`, `Ia1843`, `Ia1980`, `A1843`, `A1980`, `Age`);
- diversity outcomes (`SD`, `MPD`, `MFD`).

The public S4 table contains **no coordinates and no explicit pairwise distance/adjacency representation**. Therefore it fails the preregistered full-EOG geometry gate.

Consequences:

1. scalar isolation variables are retained only as conventional landscape baselines/covariates;
2. no graph, stepping-stone chain, connected frequency or bottleneck is reconstructed from those scalars;
3. the Czech system is retained as a plant-specific conceptual replication of the separation between local abiotic support and landscape/dispersal filtering;
4. it may be promoted to a full structural EOG benchmark only if independently verifiable coordinates, patch boundaries or pairwise geometry linked to the same patch IDs become available.

Frozen PLOS S4 source fingerprint from the pre-outcome audit:

- DOI: `10.1371/journal.pone.0223826.s011`;
- bytes: `38631`;
- SHA-256: `e647fefcf3814d681ebeb7d599b9e2679626949dadff07c6f7d444ebf8ea04dd`.

## Tanzania forest fragments: primary full non-island structural benchmark

The Brodie & Newmark fragmented-landscape dataset remains the primary full non-island structural benchmark because its public archive explicitly contains:

- site table (`Sites.csv`);
- species occurrence table (`spp_occur.csv`);
- explicit node coordinate tables (`Nodes_E.csv`, `Nodes_W.csv`);
- landscape matrix rasters (`raster_east3.tif`, `raster_west3.tif`);
- original analysis scripts.

This dataset therefore satisfies the **source-level geometry requirement** in a way the public Czech tables do not.

The Dryad public page reports 43 bird species and provides the full file inventory. Hosted GitHub runners currently cannot retrieve the binary file streams because Dryad returns access/challenge responses. That is an infrastructure gate, not a scientific exclusion criterion. No Tanzania EOG species outcome is permitted until the retrieved bytes match the frozen Dryad size/checksum inventory from the existing source audit.

## Claim boundary

The two systems serve different purposes and are not interchangeable:

- **Czech plants:** ecological replication of the local-environment versus landscape-filtering distinction;
- **Tanzania forest fragments:** test of whether occurrence-anchored structural reachability generalizes beyond islands when true non-island graph geometry is available.

The A-Islands result remains the confirmatory island benchmark. Neither non-island system may be retrospectively reassigned based on whether EOG performs well or poorly.
