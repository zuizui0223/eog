# Independent Danish Arctic Tern source evidence: breeding-field and coordinate-quality gate v2

**Status:** precommitted historical DOFbasen GBIF field-presence audit; no original Danish Tern Group dispersal event rows reopened, and no original 115 candidate source sites matched yet.

## Why we are not treating 18,456 sightings as 18,456 breeding colonies

The [source-only GBIF gate v1](tern_independent_dofbasen_breeding_source_gate_v1.md) verified the independent [DOF/BirdLife Denmark DOFbasen observation archive](https://www.gbif.org/dataset/95db4db8-f762-11e1-a439-00145eb45e9a) DOI `10.15468/tww7cj`: **4,203** coordinate-bearing Sterna paradisaea records dated 1960–1975, and **18,456** dated 1976–2005 across the original tern movement target era.

However, most DOFbasen observations are opportunistic, archived records may have been entered retrospectively, and the GBIF dataset explicitly warns that some sensitive breeding locations have coordinates rounded to **25 km** uncertainty. Therefore:
- A positive species observation at a site is not automatically a breeding/nesting source.
- A GBIF observation year is not proof the record was available as of that historical year.
- A coordinate value with missing uncertainty or >2 km uncertainty cannot support an unqualified ≤2-km source match.
- The source can be institutionally independent of the Danish Tern Group ringing records while some individual observations may still overlap; independence at the record level must eventually be assessed.

The original tern data remain intact: [source-specific v1](tern_known_origin_geographic_minrelax_v1.md) had **198/224** known-origin-infeasible events rendered ≤20 km under a broad retrospective alternative-source catalogue; [v2 sensitivity](tern_source_catalogue_rounding_sensitivity_v2.md) leaves **171** after excluding exactly coincident rounded coordinates. These are **candidate-geometry results**, not historically verified alternative colonies.

## Protocol-first v2 record-field sample

Before opening any external DOF occurrence row, the first v2 branch commit froze [the v2 field sampling protocol](../validation/tern_independent_dofbasen_breeding_field_gate_v2/protocol_v2.json), binding the original stage0 source receipt, accepted species key `5229230`, GBIF DOF dataset UUID, original year-window counts, and 15 deterministic pages (first/middle/last 100 rows from each of five windows). Total **1,500 ephemeral records**, with **all 15 query URLs, page offsets and pre-observed denominators declared**. This is a deliberately nonrandom **schema diagnostic**, not a representative sample of breeding records.

The [source-field gate](../scripts/eog_tern_independent_dofbasen_breeding_field_gate_v2.py) reads only capped public official GBIF `/v1/occurrence/search` pages and computes **aggregate field-presence and coordinate-uncertainty bins**. Public raw GBIF records, `gbifID`, observer names, site coordinates, exact dates, `occurrenceRemarks` text and breeding field string values are never saved or printed. The [synthetic tests](../tests/test_eog_tern_independent_dofbasen_breeding_field_gate_v2.py) check adverse source/taxon substitution, count drift since stage0, malformed uncertainty, protocol/page tampering and suppression of original values. [Dedicated CI](../.github/workflows/eog-tern-external-dofbasen-breeding-fields-v2.yml) uploads only aggregate schema counts.

The sample counts presence of `reproductiveCondition`, `behavior`, `occurrenceRemarks`, `eventDate`, species/country identity, `coordinateUncertaintyInMeters` and spatial quality flags. Uncertainty is grouped into `MISSING`, ≤1 km, (1,2] km, (2,5] km, (5,20] km, >20 km, or invalid. **No text keywords are used to promote breeding claims at this stage.**

## What a v2 PASS would *not* establish

A pass means that an independent *candidate data source* retains fields potentially needed to verify breeding evidence and spatial accuracy. A nonempty `behavior` or `reproductiveCondition` field is **not** automatically a confirmed breeding pair, because source-coded values and negations require separate interpretation. Similarly, any source record with 25-km-generalized coordinates does not support source matching within 20 km.

A future **separately frozen v3 semantic gate** must establish which publisher source categories mean secure `Ynglepar` (breeding pairs), nests, eggs, or chicks, and how much original breeding-site coordinate precision can be independently verified. Only then can a planned v4 *site/year proximity crosswalk* to the original 115 candidate departure points be evaluated. Even a positive independent matched breeding observation would not prove the actual alternative origin of a **marked individual** or the site's source availability at the exact original date.

No new EOG-WF predictive result. Original closed **3 scored /31 scientific STOP /3 administrative exclusions** remains.
