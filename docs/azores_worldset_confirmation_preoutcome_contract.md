# Azores world-set independent confirmation — pre-outcome source contract

## Purpose

This branch starts a second independent confirmation attempt after the SIVFLORA design stopped pre-outcome because the frozen climate representation did not cover all frozen nodes. The ecological question is unchanged:

> Does retaining the exact identities of declared alternative geographic/environmental connectivity worlds add held-out ecological information beyond strong compressed summaries of those same worlds?

This document freezes **source identity only**. It does not freeze coordinates, climate values, world construction, species eligibility, predictive models or outcome statistics.

## Why this system was selected

Selection used public dataset metadata only. GBIF describes the Azores checklist as a nine-island archipelago dataset, gives island-level distributions whenever possible for terrestrial organisms, and explicitly includes vascular plants among the terrestrial taxonomic groups. No EOG species-by-island predictive result from this dataset was inspected before this contract.

## Frozen source identity

- GBIF dataset UUID: `ec1a0bfb-7d8e-4c6b-bc4d-dfd68a1e844f`
- preferred DOI: `10.15468/hyvwxi`
- title: `A list of the terrestrial and marine biota from the Azores`
- publisher: `Universidade dos Açores`
- licence: `CC BY 4.0`
- GBIF metadata API: `https://api.gbif.org/v1/dataset/ec1a0bfb-7d8e-4c6b-bc4d-dfd68a1e844f`
- Darwin Core Archive endpoint: `https://ipt.gbif.pt/ipt/archive.do?r=uac_checklist_acores`

## Candidate node scope from metadata only

The later node-freeze gate may proceed only if a response-blind rule resolves exactly these nine islands:

1. Corvo
2. Flores
3. Faial
4. Pico
5. Graciosa
6. São Jorge
7. Terceira
8. São Miguel
9. Santa Maria

No coordinates are frozen here. A coordinate source/rule must be declared before climate coverage is tested, and it may not be changed in response to climate results.

## Strict staged firewall

### Gate 1 — source bytes

The dedicated workflow may:

- query GBIF metadata;
- verify the frozen UUID / DOI / title / publisher / licence;
- download the DwC-A as opaque bytes;
- compute byte count and SHA-256;
- upload the archive and source-freeze manifest as CI artifacts.

It must **not** open the archive or inspect taxon/distribution rows.

### Gate 2 — response-blind node freeze

Only after the exact archive hash is committed may a new amendment define and execute a response-blind rule for the nine island nodes. If exactly nine nodes cannot be resolved without reading species-incidence outcomes, stop.

### Gate 3 — climate coverage

Only after coordinates are frozen may climate products, variables and resolution be declared and sampled. Any nodata at a frozen node is a hard block under that declared representation. Do not rescue it by snapping, moving coordinates, changing resolution, imputing values or dropping islands after the climate contract is frozen.

### Gate 4 — world universe

Only if complete climate coverage succeeds may the exact analyst-choice / ecological world universe be frozen and fingerprinted.

### Gate 5 — outcome

Species-island incidence and predictive outcomes may be opened only after Gates 1–4 are committed. A failed pre-outcome gate is preserved as non-estimable design evidence and is not repaired after outcome inspection.

## Cleanup boundary

This source-freeze branch intentionally contains no EOG production API, no new scientific operator, no outcome model, no system-specific package module, and no large climate runner. If Gate 1 fails, the branch is closed without adding downstream confirmation machinery.
