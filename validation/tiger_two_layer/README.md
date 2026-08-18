# India tiger two-layer EOG-WF validation screen

## Final status

> **`gate0_stop_no_separate_response_free_grid_registry`**

The candidate stopped before any tiger presence, absence, occupancy, sign, abundance or later worksheet row was opened.

This is not evidence for or against the post-Glanville label-invariant Layer-B predictor.

## Why the candidate was screened

Public study reporting made this a strong transition-feasibility candidate:

- constant national 10 × 10 km sampling framework;
- four survey cycles: 2006, 2010, 2014 and 2018;
- repeated tiger-sign surveys with model-based occupancy interpretation;
- approximately 30% occupied-area expansion over the study;
- approximately 138,200 km² occupied extent by 2018;
- stable Zenodo XLSX transport.

These published aggregates were used only to establish endpoint plausibility. They did not tune EOG worlds, Layer-B features, blocks, comparators, metrics or decisions.

## Frozen source

- Zenodo record `13856111`, version 2;
- DOI `10.5281/zenodo.13856111`;
- workbook `data28sep24.xlsx`;
- size `24,630,077` bytes;
- MD5 `ac4fd29ab1f7ea1045ac279885c72a11`;
- SHA-256 `8e9b5269b2c946200ce8bf1df36fd0da6f6e378dece69125025a7e9cd7bb9b0d`;
- publication DOI `10.1126/science.adk4827`.

## Response-firewalled XLSX inventory

The workbook was inspected as a ZIP/XML package, not loaded with pandas or openpyxl.

Authoritative workflow:

- run `32097349646`;
- artifact `9310384905`;
- artifact ZIP SHA-256 `4073f367ab3a06a6fa64be3d8542769c58c17b62268f4d6c05ebe41ad708c21f`;
- inventory fingerprint `f51e74ae4dfc281e6464c6a3dd3b26aaa45f568f18be8943d9bb2cdd14d41a7f`.

The inventory read only:

- ZIP/member metadata;
- workbook and relationship metadata;
- worksheet dimensions;
- exactly the first logical worksheet row;
- no row after the first logical row.

Firewall state:

- response rows opened: **false**;
- response values parsed: **false**;
- rows after first logical row opened: **false**;
- general workbook library used: **false**.

## Technical correction before the authoritative run

The first workflow stopped while parsing the first row because Excel attached a namespaced extension attribute (`x14ac:*`) whose namespace declaration existed only on the enclosing worksheet element.

The correction removed extension attributes from the isolated header fragment before parsing ordinary spreadsheet cells. It did not read farther, change a sheet, decode a response, or alter a scientific gate.

A second vocabulary correction excluded generic `State` and `count` from provisional response-keyword matching because `State` is an expected Indian administrative field. Explicit tiger, presence, absence, occupancy and detection terms remained protected.

## Decisive workbook inventory

The workbook has exactly two visible worksheets:

| sheet | dimension | role visible from metadata |
|---|---:|---|
| `occupancy` | `A1:AR7184` | response/result worksheet |
| `cooccurrence` | `A1:FD29878` | response/result worksheet |

There are:

- no Excel table definitions;
- no separate geometry worksheet;
- no separate grid registry;
- no separate survey-effort or availability worksheet.

Both header rows reference noncontiguous shared-string indices. The frozen Gate 0 contract allowed shared-string decoding only when header references formed a contiguous prefix from zero. Reading through indices 83 or 242 would also read intervening unique strings that may be data values, so the candidate was not rescued by weakening that rule.

## Gate decision

A conceptual constant 10 × 10 km sampling frame is not the same as a released deterministic node registry. The workbook does not expose grid IDs and geometry separately from occupancy/cooccurrence data.

Therefore:

- canonical response-free grid universe frozen: **false**;
- complete response-free geometry frozen: **false**;
- survey-negative semantics adjudicated: **false**;
- structural LCC Gate 1 run: **false**;
- EOG worlds constructed: **false**;
- Layer-B representation evaluated: **false**;
- predictive model fit: **false**.

Role-adjudication fingerprint:

`714937030869fa3313a9e4635a241669db9bb04b29d371c6337d06476b938787`

## No-rescue boundary

Do not:

- open occupancy/cooccurrence rows to recover grid IDs or centroids;
- decode additional shared strings after seeing the noncontiguous header indices;
- infer geometry from maps or occupied-area figures;
- assume a national 10 × 10 km frame uniquely specifies the released cells;
- rerun a weakened-firewall design and call it fresh independent confirmation.

The candidate closes unmerged so no system-specific machinery expands production `main`.
