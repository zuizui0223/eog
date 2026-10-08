# Helgeland 2025-only parent–recruit route: source-documentation qualification

**Result: `HOLD_PARENT_RECRUIT_TIME_ORIENTATION_UNVERIFIED`.**

This is a response-blind, same-archive alternative to the 2024 genotype/pedigree ↔ 2025 lifetime-fitness key-join protocol. It does not replace the original protocol or change its HOLD. No physical data file, bird row, genotype, reproductive response or survival value has been read under this proposal.

## What the public 2025 v2 README actually describes

Source: Saatoglu et al. (2025) [Dryad 10.5061/dryad.qfttdz0sx](https://datadryad.org/dataset/doi%3A10.5061/dryad.qfttdz0sx), version ID 354268. These are **public README variable descriptions**, not attested physical headers.

| 2025 file | Relevant described variables | What it might support | What it does **not** prove |
|---|---|---|---|
| `LRS.txt` | `ID`, `natal.island`, `adult.island`, `year` | Individual lifetime natal/adult island proxy | Parent's breeding island at offspring birth, or first settlement |
| `ARS_Survival.txt` | `ID`, `obs.year`, `year`, `fiflok`, `laflok` | Individual-year record and first/last observed islands | A unique location for every breeding year |
| `Rectype_LRS.txt` | `dam`, `sire`, `recruit`, `lastobs.island`, `year` | Candidate parent/offspring IDs and recruit observation island | Birth island or first-ever settlement island |
| `Rectype_ARS_Survival.txt` | `dam`, `sire`, `recruit`, `lastobs.island`, `obs.year`, `year`, `flok.year` | Candidate year-indexed recruit observation records | Parent's location at offspring birth; `flok.year` is described for the recruit's breeding island-year, not a proven parent origin |

These four files are **already in the frozen 2025 Dryad v2 five-file inventory**. The archived source metadata pins their Dryad file IDs, sizes, and source-declared SHA-256 strings. The 2024 SNP/pedigree dataset is **not** required to state these candidate relationships, but its independence must not be silently borrowed.

## Why this is a different scientific candidate

A within-archive link `Rectype_LRS:dam/sire → LRS:ID`, or `Rectype_ARS_Survival:dam/sire → ARS_Survival:ID`, might support a directed parent–offspring observation-history hypothesis *after values and timing are qualified*. It avoids assuming `SNPpedigree:individual` from 2024 and `LRS:ID` from 2025 are the same key domain.

It does **not** eliminate the central temporal problem. A mother or father with retrospective `adult.island=A` and an offspring with `lastobs.island=B` does not establish `A → B` at the time of dispersal: the parent's breeding-year island could differ, the recruit might move again, and `lastobs.island` can require later observation. Even correct parentage is not proof of the source of a previously empty island.

## Preregistered stop conditions

1. Verify exact physical headers and file-byte identities for **all four 2025 source files**. Original 2024+2025 four-file header contract remains separate.
2. Examine parent–recruit ID-domain correspondence, duplicates, missing parents and whether `dam/sire` are observed or genetically inferred; use a time-free qualification before any ecological scores.
3. Verify an **independent parental breeding-island-at-offspring-birth** observation and an **offspring island/time at a specified detection window**. Do not substitute lifetime or final observation islands silently.
4. Establish which records and location/origin assignments were available at forecast cutoff `t`. Derivations using later recapture or parentage cannot be predictors at `t`.
5. Independently qualify island-wide sampling effort, non-detection and settlement/founding status. Without these the strongest target is **directional parent–recruit observation proxy**, not first-island colonization or source-loss/recolonization.

No new held-out test is defined from the observed biological outcomes. No ecological results, population founding claims, or third paper are authorized. Existing Helgeland `HOLD_DIRECTIONAL_INDIVIDUAL_PROXY_ONLY` and EOG-WF 3/31/3 remain unchanged.

## Inspectable frozen contract

`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_parent_recruit_2025_sourceonly_v1.json`

Read-only offline audit:

```bash
python -m pytest -q tests/test_helgeland_2025_parent_recruit_sourceonly_v1.py
python scripts/audit_helgeland_2025_parent_recruit_contract_v1.py \
  --output build/helgeland-2025-parent-recruit-sourceonly-receipt.json
```

The receipt is an explicit HOLD; the code reads the frozen **metadata JSON** only, not the source biological files. This is a feasible source-path refinement, **not** a verified ecological finding.
