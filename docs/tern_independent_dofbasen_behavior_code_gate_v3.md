# Danish Arctic Tern historical breeding-source codes: official DOF vocabulary gate v3

**Status:** publisher-code semantic source audit, specifically **not** certification of historic colony source availability or fresh ecological validation. Pre-execution [protocol v3](../validation/tern_independent_dofbasen_behavior_semantics_v3/protocol_v3.json) committed first at `7d231fbc540a51ac045635a14654bad57978f61e`, with a **before-data** duplicate public-code correction `da711c1deb525db4a21c3498f84ea185ffcc6a4d`. Both occur before any GBIF `behavior` value was inspected in this stage.

## Why this test and not an immediate spatial crosswalk

The independent [DOFbasen source-count gate](tern_independent_dofbasen_breeding_source_gate_v1.md) confirmed 18,456 coordinate-bearing Arctic Tern observation records in 1976–2005, but not breeding. A [fixed 1,500-record source-field audit](tern_independent_dofbasen_breeding_field_gate_v2.md) found `behavior` present in every record and source-reported spatial uncertainty ≤2km for 1,001/1,500. However, `reproductiveCondition` and `occurrenceRemarks` were absent in that nonrandom sample. **Field presence alone proves neither nesting nor any of the original 115 source sites' active populations.**

Official DOF original [adfærdskoder / behavior-code table](https://dofbasen.dk/opslag/behaviour.php) differentiates resting `R`, migration `T`, flying over `OF`, breeding-related `YF` and **specific** secondary evidence codes. The [DOF seabird/nesting guidance](https://dofbasen.dk/IBA/artsvejledninger.php?lokid=36) distinguishes direct nests/eggs/young from less secure territorial, mating and season-only presence. Thus “some `behavior` value exists” is not an evidentiary qualification.

## Frozen explicit public category mapping

The protocol freezes the 15 **identical** GBIF occurrence pages from v2, all 1,500 original records, original source DOI/UUID and speciesKey `5229230`, plus **31** fixed public-source behavior code labels. Values outside this exact white list are not printed or guessed into a breeding category; only their count under `UNRECOGNIZED_DO_NOT_CLASSIFY` is retained.

| Evidence tier | Exact example DOF codes | What can be inferred |
| --- | --- | --- |
| Nonbreeding behavior | `R`, `T`, `OF` | Sighting/activity only; cannot certify colony presence |
| General breeding-labeled | `YF` or `YNGLENDE` | Publisher may call it breeding, but a local active colony is **not yet independently verified** |
| Suggestive breeding-related behavior | `YF P` mating, `YF TH` territorial, `YF FU` carrying food, `YF UF` fledglings | Not enough to assert a specific nesting point or original source-site at 2km precision without further context |
| Potential direct nest evidence | **`YF B`** building nest, **`YF BR`** incubating/flying from/to nest, **`YF UR`** young inside nest | Stronger publisher-coded reproductive evidence; still requires date, location/coordinate uncertainty and linked specific source **before** claiming colony-year support |
| Unrecognized value | any code/string not exactly declared | Remains **unknown**; never silently promoted |

**Explicit negative control:** if none of the 1,500 official GBIF values agrees with the predeclared 31-code vocabulary, report `STOP_GBIF_ALL_BEHAVIOR_VALUES_OUTSIDE_FROZEN_CODEBOOK`. This means source normalization differs and requires a separate documented mapping, not that the birds were not breeding.

## What is actually collected

For each of 5 time windows, 3 fixed pages x100 records, the [v3 script](../scripts/eog_tern_dof_official_behavior_code_gate_v3.py) reads transiently: `behavior`, `coordinateUncertaintyInMeters`, source dataset and species keys. It outputs only exact **allowlisted public code frequencies**, code-tier counts, and tier counts with coordinate uncertainty ≤2km. Individual GBIF IDs, full source and arrival coordinates, observer/location names, remarks, dates, raw/unknown behavior field values, and original tern banding events are not uploaded or printed. Stage2 exact original field-presence counts and original uncertainty bins are independently rechecked; a changed underlying page is a **scientific STOP** rather than a silently different sample.

The [synthetic tests](../tests/test_eog_tern_dof_official_behavior_code_gate_v3.py) cover secure-source codebook, identity mismatch, altered sample, unknown labels, DOF positional uncertainty, no individual values escaping, and no EOG-WF scoring. [Dedicated CI](../.github/workflows/eog-tern-dof-official-behavior-codes-v3.yml) retains only source-category aggregates.

## Result: an independent source-vocabulary STOP, not evidence that birds did not breed

The original source-only [Actions run #44855176485](https://github.com/zuizui0223/eog/actions/runs/44855176485) succeeded in re-reading the same **15 frozen GBIF historical pages**. The results were **1,500/1,500 nonempty `behavior`** again, and the original positional-uncertainty distribution was reproduced; **1,001/1,500** records still report ≤2km uncertainty. Individual records, observation IDs, coordinates, notes and raw `behavior` values were not uploaded.

**However, not a single one of the 1,500 actual GBIF `behavior` strings was an exact match to any of the 31 prespecified original [DOF primary/secondary codes](https://dofbasen.dk/opslag/behaviour.php).**

| Frozen semantic comparison | DOF/GBIF count in source sample |
| --- | ---: |
| `behavior` field nonempty | **1,500 / 1,500** |
| Match to any of the 31 frozen DOF code/primary label strings | **0 / 1,500** |
| Unknown original GBIF behavior value format | **1,500 / 1,500** |
| Nest/incubation codes `YF B`, `YF BR`, `YF UR` recognized in the frozen mapping | **0** (not evidence the real breeding count is zero) |
| Original independent DOF breeding source colonies matched to 115 catalogue sites | **0 (not attempted)** |

**Scientific gate: `STOP_GBIF_ALL_BEHAVIOR_VALUES_OUTSIDE_FROZEN_CODEBOOK`.** The official DOF observation code table is not by itself a documented mapping to the **indexed GBIF `behavior` field serialization**. We cannot assume that an unrecognized string means rest, migration or breeding. Consequently, **the current source provides no certified historic breeding site-year despite the 18,456 coordinate-bearing occurrences**.

The recorded failure is on the source encoding/crosswalk, *not* the original 20km tern marked-origin geometry or the ecological presence of the population. Exact CI receipt SHA256 `9c9c1581a23359e5cfb12a3ba01227e445dfc5b9d00f0d415025597e3ce5f8b1`; artifact ID `14686788696`, ZIP SHA256 `d574de09377a8ffb081f8367608adc2b0eda8137e087c06a4e6afc690212bedf`. The [frozen explicit STOP certificate](../validation/tern_independent_dofbasen_behavior_semantics_v3/frozen_vocabulary_stop_v3.json) preserves source provenance, sample size, original mapping and missing evidence without exposing individual records.

**What could resolve it:** independent official DOF/GBIF mapping or publisher Darwin Core archive field dictionary describing exactly how the GBIF `behavior` field is exported from the original DOF primary/secondary `ADF` codes, combined with a separately frozen semantic source gate. This is a documentation/source qualification requirement, **not permission** to expand the 31-code whitelist after seeing an unknown result or to infer source-colony occupancy.

## Remaining boundary

Even if a large number of DOF observations have nesting-associated codes and ≤2km positional uncertainty, this is **not yet a matched colony-source**. Only a separately precommitted record-level spatial/temporal link from independently attested same-species breeding evidence to a particular original colony, with appropriate original historical date and source independence, could support the next ecological claim. Even then **observation year** is not guaranteed to be a database-as-of timestamp, and **marked bird source/route** would remain unchanged.

Original tern R=20km **198** source-agnostic false assurances (or **171** after removing exact rounded-coordinate aliases) remain **retrospective candidate geometry**, not verified alternative breeding sources. EOG-WF remains frozen at **3 scored /31 scientific STOP /3 administrative exclusions**, without new ecological predictive endpoints.
