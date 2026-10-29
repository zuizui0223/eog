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
