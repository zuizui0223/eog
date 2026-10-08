# Helgeland historical public-data vintages: 2014 and 2020 source availability

## Question

The merged [PR #633](https://github.com/zuizui0223/eog/pull/633) synthetically proved a date-only information firewall for the **2026** public observation file, but this file was not itself publicly available back in 2014 or 2020. Treating it as a 2020-available historical model input is unqualified unless an earlier source snapshot proves those values and methods were available.

The fixed authors' GitHub repository `torhanssonfrank/DensityRegulationHouseSparrows` was created in 2024, and its `Data/presence_data_1994_2022.txt` has one GitHub commit history entry on **26 November 2025**, not a public 2020 source snapshot. This does **not** show that the field team lacked the data earlier; it only shows this public GitHub archive cannot independently certify what was accessible to an outside analyst in 2020.

## Contemporary alternatives genuinely published by old cutoffs

1. **Baalsrud et al. (2014)**, Dryad [10.5061/dryad.nb260](https://doi.org/10.5061/dryad.nb260), **24 April 2014**: archived population/genetic/demographic datasets including `DemographicNe-Datafile.csv` and `README_for_DemographicNe-Datafile.txt`.
2. **Niskanen et al. (2020)**, Dryad [10.5061/dryad.m0cfxpp10](https://doi.org/10.5061/dryad.m0cfxpp10), **2020 original published version** (public page lists a July 15, 2020 version): contains `Pop_size_1997_2012.csv`, `Pop_size_1998_2013.csv` and `Dryad_readme.txt`. Public page shows it was substantially revised **19 January 2023**, with many additional files. **Using the latest 2023 version as if it were public in 2020 is forbidden.**
3. **Hansson Frank et al. (2026)**, Dryad [10.5061/dryad.rr4xgxdnq](https://doi.org/10.5061/dryad.rr4xgxdnq), exact v6/421942, includes full 1994–2022 presence and derived abundance. Potential **later evaluation source**, not a valid pre-2020 public training snapshot.

The 2020 study focused on **8 islands** while the 2026 source concerns **11 islands**. Never assume exact island IDs, survey effort, same estimand, or equivalent year labels without independent code/variable concordance.

## Task of this PR — no bird data rows

`scripts/audit_helgeland_historical_dryad_vintages_v1.py` uses a **strict API GET allowlist** for only the two specific historical DOIs:
- `/api/v2/datasets/<DOI>/versions`, to enumerate published versions, including original release dates
- `/api/v2/versions/<numeric-id>/files`, for **only the latest historically published version before each predeclared cutoff** (2014-12-31 or 2020-12-31)

No `/download`, raw files, headers, biological rows or genetic records may be fetched. Pagination, missing version publication timestamps, missing exact requisite files or unexpected version link formats must fail closed. Even a metadata PASS verifies **public version/file inventory only**: it does not independently verify whole-file bytes, metadata completeness for modeling, island-code alignment, negatives or ecological effects.

Dedicated tests contain fabricated metadata. GitHub Actions outputs a single source-metadata-only JSON receipt. After a successful live run, manually freeze IDs/dates/source-declared digests in a separate source-evidence record before any actual biological analysis.

## Which scientific question this would enable *later*

Potential honest retrospective simulation:
- Model inputs from an **actually published pre-2021 historical file version**, never full 2026 data.
- Forecast 2021–2022 outcomes from 2026 sources while **blindly** freezing model, island denominator, date convention and comparator before reading 2021/22 outcome rows.
- Compare reachability/observation-model information against distance-only or fixed-connectivity baselines.

**This does not yet authorize such a forecast.** It requires verified historical physical source files, compatible island roster/year index, a defensible held-out response/observation process and rigorous control for public manuscript outcome exposure. Outcomes for 1998/2000 already discussed are **not blind** and cannot be recycled as an independent result. Observation dates are not proof of contemporaneous public availability.

Tracked at [EOG Issue #626](https://github.com/zuizui0223/eog/issues/626). Do not alter EOG-WF's frozen 3/31/3 evidence or claim a new paper.
