# Helgeland 2026 public presence file: preregistered aggregate-only data-quality audit

**This gate differs from prior metadata/header audits: it DOES parse the published individual observation rows in memory**, after authenticating the complete source bytes against Dryad 2026 v6 and matching the predeclared physical header. It exports **only aggregate diagnostics**, never individual identifiers, recorded dates, recorded islands or any source row.

## Preregistered BEFORE opening the observation rows

Source contract: `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2026_direct_observation_qc_protocol_v1.json`.

Input: exactly `Data/presence_data_1994_2022.txt` in authors' public GitHub commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5`, byte-identical to Dryad v6 version 421942 file ID 4576411 (matched in PR #628). Its *physical header* was attested in PR #629: `Year;date;scriptsex;Island;Location;stage;Least_age;Least_hatchyear;ID`.

**QC-only checks**:
- Row count, number of nonempty and distinct IDs; missing ID/date/year/island/location/stage fields.
- Date parseability (ISO `YYYY-MM-DD` only) and Year-vs-date consistency; records outside declared 1994–2022 interval.
- Distinguish the literal `nest` and directly observed `capt`/`obs` stage names; count records of other stages without guessing labels.
- Exact duplicate same-ID/date/stage/island/location observations.
- Individuals with nest observations attributed to more than one island (ambiguous natal source).
- Count **candidate IDs** with one documented nest island and any strictly later directly recorded `capt`/`obs` record. This is a structural *linkability* count **without comparing origin and destination islands**, and is **not** a dispersal rate, number of migrants or new ecological result.

The script does not use `Least_age` or `Least_hatchyear` as a historical predictor, never fills a missing island using later observations, and does not infer an island-year's unoccupied state from its absence in the occurrence table. No individual values can appear in the output.

## Proof and research boundary

Predeclared validation occurs in synthetic-only unit tests. Dedicated GitHub Actions checks out a fixed upstream revision, revalidates source-file size/SHA-256 against Dryad and first-header SHA, then runs the QC script and exports one **aggregate-only JSON** artifact.

Run:
```bash
python -m pytest -q tests/test_helgeland_2026_direct_observation_qc_v1.py
python scripts/audit_helgeland_2026_direct_observation_qc_v1.py \
  --upstream-checkout upstream_public \
  --output build/helgeland-2026-structural-encounter-qc-v1.json
```

**Mandatory scientific holds:** structural candidate linkage is not a time-of-prediction covariate; its direct observation dates and nest stage are not separately calibrated for detection. No survey-effort/true-absence denominator, colonization or source population identity, mechanistic movement effect, or independent held-out EOG performance is established.

No existing EOG-WF frozen 3/31/3 denominator or previously observed historical event list is modified. See [Issue #626](https://github.com/zuizui0223/eog/issues/626).

## Stop rules

If immutable source ID/whole-byte hash/physical header mismatch, reject before reading any data row. If data quality issues appear, report bounded **aggregate counts and HOLD**; do not edit thresholds or filter criteria after seeing outcomes to manufacture an ecological success. Aggregates themselves are descriptive data provenance evidence, not ecological parameter estimates.
