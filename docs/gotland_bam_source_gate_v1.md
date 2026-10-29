# Gotland 2020 butterfly × host-plant BAM external bridge — source-only preflight

## Decision, 2026-10-29

The completed known-truth **EOG × BAM** integration was already checked
against 12 original heterogeneous synthetic systems / 768 worlds (PR #669).
This source-only gate asks whether a genuinely independent, publicly
documented **patch × host × environment × connectivity** dataset exists
for a *retrospective* external ecological demonstration.

**No species-response rows have been accessed in this PR.**

## Candidate and prior-art boundaries

Johansson et al. (2020), *Journal of Applied Ecology*
DOI `10.1111/1365-2664.13611`, reports a 256-patch marsh fritillary
(`Euphydryas aurinia`) network on Gotland with 2018–2019
colonization/extinction and `Succisa pratensis` host-plant observations.
Dryad dataset DOI `10.5061/dryad.s1rn8pk4k` lists:

- `Butterfly_occurrence_data.xlsx` (stream file 264459)
- `Host_plant_data.xlsx` (stream file 264460)

Published study results are **already known**. The source cannot be called
a fresh independent predictive replication. Published analysis already
used patch area, connectivity, moisture and grazing. EOG cannot claim
novelty by repeating those associations.

## BAM qualification criteria

- **A**: independent abiotic ground moisture or physical habitat at
  exactly the patch scale; no environmental outcome-derived thresholds.
- **B**: observed host plant `Succisa pratensis`, with a documented
  plot/grid-to-**same**-patch join. Similar words in headers are
  insufficient. **No verified join = B_UNQUALIFIED.**
- **M**: an independently calculated landscape-connectivity measure,
  not a data-driven EOG predictor or actual animal dispersal rate.
- **G**: a butterfly occupancy observation with distinct years, known
  survey opportunity and careful treatment of nondetection.
- **Reference**: shared frozen environmental feature scale; no
  outcome-dependent refitting.
- **Comparator**: baseline patch area + moisture + published connectivity;
  B addition must be separately justified by the join and independent host
  measurement.

Even if all are present, the source supports only a **retrospective
proxy-level illustration**. It cannot prove causal A/B/M mechanisms or
colonization history.

## Frozen source gate

Protocol was committed before Excel sheet/physical-header inspection:
`validation/gotland_bam_preflight_v1/protocol_v1.json`, commit
`7d77af98d6c0ecf7fcdc9f99897c173bfb219028`.

The gate downloads **exactly once** each of the two stated Dryad stream
URLs. It requires a legitimate XLSX and reads only first physical row
headers/sheet metadata, not any biological response rows. It records
SHA256, physical names, workbook dimensions, response-row-access=0, and
candidate column labels. A common `PatchID`-like string **does not
certify spatial correspondence**. Crosswalk qualification is a separate
scientific gate.

The runner's HTTP/schema failure is a **terminal SOURCE_STOP**, not a
reason to try an alternate file, replace a candidate or silently infer
variable mapping. Only a separate source protocol would permit a future
independently justified alternative.

## Outcome of this PR

The only permitted current outputs are:

- `SCHEMA_GATE_STARTED` before acquisition;
- `HEADER_ONLY_SUCCESS__BIOLOGICAL_JOIN_NOT_YET_QUALIFIED`;
- `SOURCE_STOP_HTTP_*` / `SOURCE_STOP_SCHEMA_*` / transport STOP.

There is no species-level estimate, heldout score or new empirical
EOG-WF endpoint. Existing frozen numerical results and manuscripts
are untouched.

Next scientific action is dictated by the archive receipt, not by
a desire to obtain a positive A/B/M result.

## Terminal source result (verified 2026-10-29; post-protocol)

The first and only authorized GitHub Actions source attempt terminated:

- GitHub Actions run: https://github.com/zuizui0223/eog/actions/runs/40855899932
- Artifact: `gotland-bam-source-schema-only`, artifact ID `12889541851`
- Archive ZIP SHA256: `9a7bb75ad4ba93174fe8af90067896b87f86da5d2797b531134e6f23508e36fe`
- Exact source-result JSON SHA256: `964b876dadbbfca7adeaa4c538665c8647ed3590b3768c3dba38cdb6f3eab195`
- Result fingerprint: `b179a8d3d20f75406910799246ebac86ecf54711d36de8948933141807319377`
- Status: **`SOURCE_STOP_HTTP_403`**
- Stopped at first file: `Butterfly_occurrence_data.xlsx`, file ID `264459`
- Verified workbooks: **0 of 2**
- Biological response rows opened: **0**
- Ecological model fits and endpoints scored: **0**

No spreadsheet schema and no patch-level B join were verified. There is no
ecological result or valid independent EOG/BAM empirical score in this programme.
The GitHub Actions job itself succeeded because it correctly emitted a
*terminal STOP receipt*; that infrastructure success is not source-admission success.

This is one fixed failed source acquisition, not permission to retry,
switch to another archive, use mirrors, or substitute different coordinates.
The workflow was changed to **manual-only** after the terminal stop so PR
updates cannot accidentally re-acquire source data. Do not dispatch it
without a separately reviewed scientific source contract.

Canonical committed receipt:
`validation/gotland_bam_preflight_v1/schema_receipt_v1.json`.
