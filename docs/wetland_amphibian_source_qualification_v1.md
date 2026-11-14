# Wetland amphibian real source: structural qualification, not occupancy readiness

## Source

Existing user research repository
`zuizui0223/frogcs`, fixed commit
`5e2f0a87c639df373fa2700b29403d2ab417a1cc`,
external source folder `research/external/zenodo_15044115`.
Two native CSVs:
`wetland_amp_site_data.csv` and `wetland_amp_surv_data.csv`.

Original source SHA256:
- Sites: `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`
- Surveys: `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`

## Source-exact qualification

Canonical CI:
https://github.com/zuizui0223/eog/actions/runs/43577318683

| Field | Observed |
|---|---:|
| Site rows | 29 |
| Survey rows | 381 |
| Unique survey identifiers | 379 |
| Duplicate survey IDs beyond first occurrence | **2** |
| Sites with >=2 dates | 29 |
| Site × method groups with >=2 dates | 105 |
| Acoustic surveys | 129 |
| Visual surveys | 129 |
| Bottle-trap surveys | 64 |
| Dipnet surveys | 59 |
| Native species count columns | 9 |

All 29 site records have the audited depth, submerged
vegetation, emergent vegetation, plant species count,
fish and site-treatment fields. The 381 survey rows
have no missing values in the audited `num`, temperature,
humidity and precipitation columns.

This is **genuinely richer than the deer example**:
repeat surveys, multiple methods, measured local
weather and site habitat variables coexist in the same
native source. However, the survey IDs are not fully
unique, and the field `num` is not verified as
standardized effort duration.

## Fail-closed boundary

Status: `SOURCE_STRUCTURE_ONLY_NOT_OCCUPANCY_READY`.
Before occupancy or causal analysis:
1. Diagnose the two duplicate survey identifiers at row level.
2. Verify that survey counts of zero are true standardized
   nondetections, not unsampled species/methods.
3. Establish effort comparability and species-appropriate
   within-season closure intervals.
4. Distinguish measured site habitat covariates from
   independently identified abiotic/biotic/movement constraints.

Passing this source audit does not identify EOG geometry,
independent A/B/M, causal constraint release or a new
EOG-WF endpoint.

Receipt:
`validation/wetland_amphibian_source_qualification_v1/result_receipt.json`.
