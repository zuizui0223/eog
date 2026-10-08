# Helgeland 2026: Is `Year` exactly an April–March reporting label?

**Status:** exploratory hypothesis generated *after* seeing the Year/date discrepancy. No independent validation or biological inference.

## Established sources and finding

Previous real-data audit (merged [PR #631](https://github.com/zuizui0223/eog/pull/631)) on the **original byte-and-header-pinned** Dryad v6 file `presence_data_1994_2022_ECY25-1341.txt` observed **73,593 rows**, including **3,517** with `Year = date.year - 1`. Every offset was confined to January (1,007), February (1,180), or March (1,330); April–December produced no mismatches. These are raw exposed diagnostic observations, not a blinded prediction.

External supporting field protocol: **Husby et al. (2006)**, [Journal of Animal Ecology, doi:10.1111/j.1365-2656.2006.01132.x](https://doi.org/10.1111/j.1365-2656.2006.01132.x), classifies a nestling as a recruit when subsequently captured or observed **after April 1 of the following year** in Helgeland. This is supporting context for a **season boundary**, but **does not confirm how the specific 2026 `Year` column was encoded**.

The 2026 Dryad README [doi:10.5061/dryad.rr4xgxdnq](https://doi.org/10.5061/dryad.rr4xgxdnq) defines `Year` as the observation year and `date` as the observation date, without an explicit April 1 mapping. Biological membership in a recruitment cohort is **not** identical to the timestamp labeling of field observations.

## One remaining sharp diagnostic

The prior audit establishes that **all *discordant* records occur in January–March**, but does not answer whether *other* January–March records instead have `Year = date.year`. A universal April–March rule requires **both**:
1. Every January–March row has `Year = date.year - 1`.
2. Every April–December row has `Year = date.year`.

This PR measures those conditions for *all* months, not only mismatches. The source remains exactly GitHub commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5`, Dryad version 421942, file ID 4576411, after whole-file SHA-256 and physical-header check. It reads only the **Year and date** fields out of the CSV parser and outputs 12 monthly row totals plus five coarse mapping-count categories. Other physical fields are parsed as tokens by CSV but never accessed, retained, or exported.

The analysis contract `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_april_boundary_postexposure_contract_v1.json` was frozen before this *follow-up*, while explicitly preserving that the underlying result was already exposed. Synthetic tests include a January–March exception that must prevent claiming universal mathematical fit.

**Even a perfect deterministic match is not an author-confirmed meaning.** This workflow does not rewrite `Year`, change the cutoff for field observation eligibility, reconstruct site colonization, estimate dispersal, qualify surveyed-zero years or produce EOG model scores. Those gates remain HOLD.

The next *external* evidence needed is the database field-definition or data custodian's written statement confirming the season assignment rule, and whether it is consistent across nestlings, recaptures, resightings, and population-size tables.
