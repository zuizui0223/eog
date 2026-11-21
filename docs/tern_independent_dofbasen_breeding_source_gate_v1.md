# Arctic tern 1976–2005: independent colony source availability gate (DOFbasen/GBIF) v1

**Scientific status:** SOURCE DISCOVERY / EXTERNAL DATA COUNT GATE ONLY. No original Li et al. 2026 tern movement event reopened, no third-party DOF occurrence record downloaded, no contemporary occupancy inferred, and no EOG-WF predictive endpoint.

## Actual research question after v2 source-catalogue sensitivity

[Known-departure Arctic tern v1](tern_known_origin_geographic_minrelax_v1.md) found **198** events at a 20-km geographic threshold that appear feasible if one chooses any of 115 retrospectively indexed earlier departure coordinates, although their *marked departure* is more than 20 km away. [Frozen v2 10-condition source sensitivity](tern_source_catalogue_rounding_sensitivity_v2.md) found **171** cases remain without exact co-located rounded source coordinates and **78** remain when only six sources from years through 1965 are allowed.

This means **neither 198 nor 171 counts as independently established feasible ecological sources**. A valid assessment needs independently documented **same-species breeding activity at each candidate colony near the relevant target year**. More tautological catalog filters will not produce that evidence.

## Relevant external Danish breeding evidence, independently sourced

| Record source | Species/site/year provenance | Can it verify that 115 original candidate colonies were actually breeding sources? |
| --- | --- | --- |
| [DOF/BirdLife DOFbasen observations on GBIF](https://www.gbif.org/dataset/95db4db8-f762-11e1-a439-00145eb45e9a), DOI `10.15468/tww7cj` | Independent volunteer observations with dated locations, historical observations included, dataset updated weekly | **Potentially**, but only specific records explicitly coded as breeding/nesting and with sufficient positional precision; not all species-presence records. Historical digitization coverage varies by region |
| [DOFbasen example, Mandø, 1992-07-04](https://dofbasen.dk/ypobs.php?obsid=17701) | **Sterna paradisaea**, historical breeding-pair observation (48–52 pairs) at named site and year | **Yes, an independent existence example** at that time/place; **no match** to any original tern source or target has yet been established |
| [DOF breeding observation guideline](https://dofbasen.dk/IBA/printartsvejledninger.php?lokid=53) | Distinguishes secure breeding pairs/nesting and timing of counts for Arctic Tern | Useful for future behavioral evidence code; general observation or flying bird does not prove colony source |
| [DOFbasen legacy observation conversion notes](https://dofbasen.dk/vejledning/arkivmateriale.php) | Older records entered unevenly across Danish regions/years (for example, some 1983–1993 records converted but gaps remain) | **No**: a missing observation cannot be taken as a source colony's absence |
| [NOVANA Arctic Tern historical trend and monitoring](https://novana.au.dk/fugle/fugle-2012-2017/ynglefugle/ynglefuglearter/havterne) | Systematic modern site counts **from 2006**; earlier population-wide estimates go back to 1970s | **No direct same-year site support** for the 1976–2005 original event range |
| [DOF Bird Atlas maps (Atlas I, II, III)](https://dofbasen.dk/danmarksfugle/art/06160) | Breeding distribution grids 1971–1974, 1993–1998, 2014–2017 | **Coarse regional corroboration only**; not precise breeding-confirmed candidate site-year at original 0.01° locations |
| [Original Li et al. tern paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13612375/) and [associated public Dryad data](https://doi.org/10.5061/dryad.x69p8czxh) | Source banding project 15,015 selected ringing/return records from 242 colonies, 1931–2005, but shared Dryad contains only 890+200 derived dispersal events | Same underlying ringing source, **not independent**; original non-disperse observations and ring IDs are not shared. The 15,015 archived originals may be needed for detailed history but cannot be created from derived rows |

**GBIF/DOF caution:** The original DOF dataset is predominantly opportunistic sightings, not a designed systematic survey. Some sensitive breeding bird observations are generalized to approximately **25 km** uncertainty; such records are **not safe** for 2–20-km source-specific comparisons. DOF itself documents uneven historic archive digitization. DOF/GBIF occurrence `year` is observation year but does not prove the record was **available to an analyst by that date**.

## What stage 0 can and cannot do

The first commit in this branch [froze the official GBIF source count protocol](../validation/tern_independent_dofbasen_breeding_gate_v1/protocol_v1.json) before any API count was requested:

- GBIF dataset UUID `95db4db8-f762-11e1-a439-00145eb45e9a`; DOI `10.15468/tww7cj`; **exact target species** `Sterna paradisaea` (not Common Tern `Sterna hirundo`).
- Fixed five nonoverlapping source search windows: **1960–1975, 1976–1985, 1986–1995, 1996–2005, 2006–2012**.
- One official dataset metadata call, one accepted GBIF species match, then only **five `limit=0` count queries** with `datasetKey`, `taxonKey`, `country=DK`, `hasCoordinate=true`, `year` fixed.
- Only aggregate counts, source metadata/version hashes and exact normalized query URLs can leave the workflow. **No coordinate or observation rows or IDs**, and no original tern movement rows reopened.
- Count `N` means `N` target-species occurrence *records* with coordinates, **not** `N` independent nesting colonies or breeding site-years. Missingness is not reliable nonbreeding evidence.

Reproducibility: [metadata/count script](../scripts/eog_tern_independent_dofbasen_source_count_gate_v1.py), [offline scientific STOP regression tests](../tests/test_eog_tern_independent_dofbasen_source_count_gate_v1.py), [source-only Actions workflow](../.github/workflows/eog-tern-external-dofbasen-source-gate-v1.yml).

## Stage 1/2 eligibility (not yet authorized)

If stage0 shows that the correct species has coordinate-bearing observations in relevant years, **separately freeze** a bounded field-schema sample and test whether the *publisher* explicitly exposes `behavior`, `reproductiveCondition`, `occurrenceRemarks` or other appropriate evidence of `Ynglepar`/nest/chicks, and `coordinateUncertaintyInMeters`. Don't infer breeding from `occurrenceStatus=PRESENT` or `eventDate` alone. Restrict to same-year or declared previous-year breeding-positive, not five-year interpolated presence. Reject spatial uncertainty exceeding the target threshold, especially DOF's 25-km-generalized points.

Before spatial linking, independently freeze location resolution, reproduction evidence, time window, source-to-candidate matcher tolerance and expected negative controls. Compare to 115 original tern historical source coordinates *only after those checks pass*. The original GBIF 2026 publication and retrospected records never establish a truly prospective `as of 1975` source roster.

The EOG-WF frozen **3 scored /31 scientific STOP /3 administrative exclusions** remains unchanged. Even a successful DOF breeding source match would establish **historical breeding evidence**, not that a matched bird actually originated at that colony or that a 20-km move was possible through environmental/biotic/barrier constraints.
