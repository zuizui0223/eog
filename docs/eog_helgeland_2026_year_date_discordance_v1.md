# Helgeland v6 observation `Year` vs `date`: post-exposure diagnostic (EXPLORATORY)

## Source ambiguity identified

The first preregistered structural QC of the byte-verified 1994–2022 presence records (merged PR #630) parsed **73,593 rows**, and reported **3,517 cases** where `Year != calendar_year(date)`, plus **914 date-year-consistent records** outside its prespecified 1994–2022 year window. Its 6,299 structurally linkable nest→later directly observed IDs are **not** migrants or ecology results.

The official [Dryad 2026 README](https://datadryad.org/dataset/doi%3A10.5061/dryad.rr4xgxdnq) defines `Year` as "year of observation" and `date` as "date of observation". It does **not** certify that `Year` is a breeding year rather than a calendar year. Consequently, a blanket `Year := calendar_year(date)` or `date := Year` coercion is **not authorized**; it would alter the temporal observation contract and risk past/future leakage.

## What this bounded follow-up will measure

An explicitly **POST-OUTCOME-EXPOSURE** exploratory diagnostic is recorded *before this follow-up* at `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_year_date_exploratory_contract_v1.json`. The earlier mismatch totals are already known, so this cannot be described as a fresh unexposed preregistration.

After verifying the exact source file's complete SHA-256 against Dryad v6 (file ID 4576411) and the frozen physical first-line columns, the code only inspects **`Year` and `date`** from each CSV row. It records:
- `Year - calendar_year(date)` in five fixed bins (≤−2, −1, 0, +1, ≥+2).
- Twelve calendar-month mismatch counts and a 12×4 month-by-nonzero-year-offset matrix.
- Coarse before/after 1994–2022 counts for both `Year` and `date.year`, and the earlier 914 eligible-but-outside-window records.
- Source row count, invalid date and Year counts.

All row-level dates, individual IDs, island names/codes, life stages, sex and biological responses **stay out of the receipt**. No movement/colonization/absence scores or model fit is computed. The sum of all offsets must reconcile with exactly 73,593 rows, **3,517 discrepancies** and **914 consistent-year out-of-window records**, or the workflow must fail closed.

## First observed result (exploratory; not independent confirmation)

Dedicated GitHub Actions run **37801160828** succeeded; its aggregate-only JSON artifact ID **11560154008**, ZIP SHA256 `9a1f4ab9c511ecc7343cfd5eedcf3cf731a7336588b82310fdd9b3a89f661d02` was independently opened and verified. The observed pattern is unusually regular:

- Exactly **3,517** `Year != date.year` records, all with `Year = date.year - 1`. No positive offsets or offsets of magnitude two or more.
- Every discordance is dated **January (1,007)**, **February (1,180)** or **March (1,330)**; April–December have **zero** discordances.
- Overall rows **73,593**; matched Year/date **70,076**; the 914 previously ineligible but Year/date-consistent out-of-window rows remain exactly 914.
- Coarse out-of-range counts (not disjoint): `Year < 1994` is **1,268**, `date.year < 1994` is **1,070**, and neither field has rows later than 2022. All 73,593 values parse as calendar dates / integer Years.

The real receipt's aggregate fields and evidence chain are frozen at `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_year_date_discordance_frozen_v1.json`, and the repeat CI asserts the exact same counts.

**Possible explanation, NOT a verified source definition:** `Year` may encode an April–March field/monitoring year rather than a simple calendar year. The Dryad README still calls both columns observation dates; independent author confirmation is necessary. No date labels will be rewritten or temporal eligibility upgraded based only on this pattern.

## Interpretation limits

Concentration in a particular month or a one-year shift **could** reveal a regular date-convention or preprocessing discrepancy; it would not by itself establish which variable is correct. Resolution requires author documentation or original timestamp/season protocols. Any later temporal split must be explicitly reconsidered once that independent evidence exists. Source data were already used for QC before this step; no new held-out claim.

Statuses remain `NO_SURVEYED_ZERO_PANEL_VERIFIED`, `NO_AS_OF_T_PREPROCESSING_CERTIFIED`, `NO_INDEPENDENT_HELDOUT_EVENT_BENCHMARK`, and `ecological_endpoint_authorized=false`.

Track source identity and decision history in [Issue #626](https://github.com/zuizui0223/eog/issues/626).
