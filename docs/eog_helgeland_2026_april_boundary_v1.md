# Helgeland 2026: Is `Year` exactly an April–March reporting label?

**Status:** exploratory hypothesis generated *after* seeing the Year/date discrepancy. No independent validation or biological inference.

## Established sources and finding

Previous real-data audit (merged [PR #631](https://github.com/zuizui0223/eog/pull/631)) on the **original byte-and-header-pinned** Dryad v6 file `presence_data_1994_2022_ECY25-1341.txt` observed **73,593 rows**, including **3,517** with `Year = date.year - 1`. Every offset was confined to January (1,007), February (1,180), or March (1,330); April–December produced no mismatches. These are raw exposed diagnostic observations, not a blinded prediction.

External supporting field protocol: **Husby et al. (2006)**, [Journal of Animal Ecology, doi:10.1111/j.1365-2656.2006.01132.x](https://doi.org/10.1111/j.1365-2656.2006.01132.x), classifies a nestling as a recruit when subsequently captured or observed **after April 1 of the following year** in Helgeland. This is supporting context for a **season boundary**, but **does not confirm how the specific 2026 `Year` column was encoded**.

The 2026 Dryad README [doi:10.5061/dryad.rr4xgxdnq](https://doi.org/10.5061/dryad.rr4xgxdnq) defines `Year` as the observation year and `date` as the observation date, without an explicit April 1 mapping. Biological membership in a recruitment cohort is **not** identical to the timestamp labeling of field observations.

## Actual result — exact fit on all 73,593 records (after exposure)

The first pinned-source GitHub Actions run **37804577337** completed successfully. Its aggregate-only artifact **11562470956**, ZIP SHA256 `3026186d8bd0d1c866e8ad7f681cf47a72e6772ac82b9e42ed45b0928f2ad11c`, was independently opened.

- All **3,517** observations dated January–March have `Year = calendar_year(date) - 1`. **None** has the same calendar year or any other year offset.
- All **70,076** observations dated April–December have `Year = calendar_year(date)`; zero exceptions.
- Thus the deterministic April–March mapping fits **73,593 / 73,593**, without changing the underlying data.
- The 12 monthly totals, first-run artifact identity and NO-SCORING controls are frozen in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_april_year_mapping_frozen_v1.json`. The repeat CI requires an exact match.

**What changed:** The rule is no longer merely plausible from the *discordant subset*; it is an exact **property of the observed file**. **What did not change:** Its intended semantics or whether it applies to other Helgeland datasets remain **not author-confirmed**. The 2006 post-April-1 recruitment criterion is a separate methodological precedent, not direct documentation of the source database's Year-field transformation.

## One remaining sharp diagnostic

The prior audit establishes that **all *discordant* records occur in January–March**, but does not answer whether *other* January–March records instead have `Year = date.year`. A universal April–March rule requires **both**:
1. Every January–March row has `Year = date.year - 1`.
2. Every April–December row has `Year = date.year`.

This PR measures those conditions for *all* months, not only mismatches. The source remains exactly GitHub commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5`, Dryad version 421942, file ID 4576411, after whole-file SHA-256 and physical-header check. It reads only the **Year and date** fields out of the CSV parser and outputs 12 monthly row totals plus five coarse mapping-count categories. Other physical fields are parsed as tokens by CSV but never accessed, retained, or exported.

The analysis contract `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_april_boundary_postexposure_contract_v1.json` was frozen before this *follow-up*, while explicitly preserving that the underlying result was already exposed. Synthetic tests include a January–March exception that must prevent claiming universal mathematical fit.

**Even a perfect deterministic match is not an author-confirmed meaning.** This workflow does not rewrite `Year`, change the cutoff for field observation eligibility, reconstruct site colonization, estimate dispersal, qualify surveyed-zero years or produce EOG model scores. Those gates remain HOLD.

The next *external* evidence needed is the database field-definition or data custodian's written statement confirming the season assignment rule, and whether it is consistent across nestlings, recaptures, resightings, and population-size tables.
