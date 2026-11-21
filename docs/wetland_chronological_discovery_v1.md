# Original wetland amphibian records: first-date nondetection and later recorded positivity

## Completed result and interpretation

**New source-authenticated retrospective observation-grain result, not a proof of biological first-visit false negatives.** The original 2024 Hungarian wetland amphibian CSV has real site-specific survey dates and multiple recorded methods. We preserve each native CSV row and reconstruct, for every site×species, the **earliest recorded date** and whether a recorded positive for that taxon first occurred on that day or at a **strictly later recorded calendar date**.

Under the source-observed, full four-recorded-method definition, **82/144 (56.9%) original Q1 positive site×species combinations** and **49/77 (63.6%) Q2 positives** were first positively recorded **later than the site's first survey date**. Those combinations were source-nondetections in every method row on the initial recorded date. Such later positives are *not proof that the species was present on the first date*: seasonal breeding, local movement, changing visibility/phenology and true temporal change cannot be separated from imperfect detection here.

This is the main reason the earlier EOG wetland information-gate study deliberately refused to equate first-date zeros, later zeros or acoustic/visual-only zeros with **confirmed ecological absence**.

**Source:** Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837); original CC BY 4.0 data and author R [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115). Pin `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`; survey CSV SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site CSV SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

## Exact site×species first-date classification

The first recorded site date is the earliest ISO date in that site's **original raw rows**; different methods recorded on the same day are pooled using Boolean **count > 0** and not treated as separate successive visits. The source supports **27 Q1 sites** (351 native rows, 117 site×dates), **13 Q2 intervention sites** (188 rows, 64 site×dates). Q2 is source-verified as an exact subset of Q1. There are **nine native taxa**. No resampling to 20 pseudo-occasions per site was performed.

Each original site×species belongs to exactly one of five mutually exclusive **recording categories**, not ecological state classes:

| Source-recording category | Q1 (27 × 9 = 243 slots) | Q2 (13 × 9 = 117 slots) |
| --- | ---: | ---: |
| First date: acoustic or visual positive | **50** | **26** |
| First date: acoustic+visual nonpositive, dipnet/bottletrap positive **on the same day** | **12** | **2** |
| First date: all methods nonpositive; **later date** positive via acoustic/visual | **54** | **35** |
| First date: all methods nonpositive; **later date** positive only via additional methods | **28** | **14** |
| No recorded positive across all source dates/methods — biological status **unknown** | **99** | **40** |
| **Total** | **243** | **117** |

The first two rows sum to source positives on the first recorded date: **62 Q1** and **28 Q2**. The next two sum to **82 Q1** and **49 Q2** site×species combinations that had a later positive but no first-date full-method positive. The first four together reconstruct the complete original site×species positive sets **144 Q1 / 77 Q2** exactly. Acoustic+visual source-positive site×species across **all** dates remain **104 Q1 / 61 Q2**.

### Time to the first later recorded positive

The following is the cumulative count of **originally full-method first-date nonpositive site×species with a later full-method source positive first seen within N calendar days** of that site's first recorded date. It is **not a detection probability, colonization rate, nor a longitudinal occupancy estimate**.

| Days after first recorded date | Q1: later-positive pairs | Q2: later-positive pairs |
| --- | ---: | ---: |
| 7 | **22/82** | **10/49** |
| 14 | **34/82** | **13/49** |
| 21 | 39/82 | 14/49 |
| 30 | **53/82** | **26/49** |
| 45 | **76/82** | **46/49** |
| 60 | 78/82 | 48/49 |
| 91 | **82/82** | **49/49** |

Among those first-full-nonpositive, later-full-positive combinations, the source-recorded lag from a site's earliest date to its first positive ranges from **1 to 67 days** in Q1 (median **27 days**) and **1 to 62 days** in Q2 (median **30 days**). These lags mix temporal biological activity, survey effort and detectability and cannot be interpreted as first-arrival or time-to-colonization measures.

### Species-specific source timing is heterogeneous

| Q1 native species | Ever source-positive sites | First full-method positive sites | First full-method nonpositive, positive later |
| --- | ---: | ---: | ---: |
| *Bombina bombina* | 18 | **1** | **17** |
| *Pelophylax ridibundus* | 18 | **3** | **15** |
| *Pelobates fuscus* | 14 | 3 | 11 |
| *Triturus dobrogicus* | 7 | 2 | 5 |
| *Lissotriton vulgaris* | 21 | 13 | 8 |
| *Hyla arborea* | 24 | 17 | 7 |
| *Rana dalmatina* | 17 | 10 | 7 |
| *Bufotes viridis* | 11 | 5 | 6 |
| *Bufo bufo* | 14 | 8 | 6 |

The striking contrast between *Bombina*, *Pelophylax* and *Hyla* is a **source-record timing difference**, not evidence that the first two species biologically colonized the wetland later. An interpretation in terms of breeding-season phenology is plausible but cannot be established from these records alone, as method coverage, state, weather, effort and visibility are not experimentally separated.

## Counterfactual witness-site check

The previous conditional negative-witness design identified a unique two-site minimum-cover set: `rachaz_2` (intervention site, 5 actual recorded source dates) and `nyarfas-turjan-laperdo` (control site, 2 actual recorded dates). The target taxa were `Lissotriton vulgaris` and `Hyla arborea`.

This new chronology audit explicitly verifies **all four site×taxon target combinations remain without source positives even after including every date and method**. In Q1 they contribute four `never_source_positive` rows; Q2 contains just the two intervention rows for `rachaz_2`. They are **not** validated absences and this result does **not** turn the previous hypothetical two-site/four-negative-certificate set cover into an actionable or guaranteed field experiment.

The original Q1 source also illustrates why time matters at these sites: at `nyarfas-turjan-laperdo`, `Pelophylax ridibundus` first becomes source-positive **34 days after** the initial date. At `rachaz_2`, `Bufotes viridis` becomes source-positive **54 days after** the initial date (through an additional method). Such examples provide direct source-recorded changes, not demonstrations of first-date population absence, biology-specific false negatives or a mechanism.

## Ecological significance and limitations

The source establishes that recorded detectability **as expressed in the archived methods/dates** is strongly method-, species- and time-conditional. EOG inference that treats an observed zero as an ecological impossibility without an explicit observation model would risk contradicting the later source-recorded positives; however, later positives do not establish that a first-date zero was a false negative **for the true first-date biological state**.

The source has no independently authenticated physical bottletrap IDs, equal method effort, standardized observer time or verified closed-season occupancy state. The paper describes dipnet surveys in regular field sessions while the CSV includes dipnet method rows on only part of the recorded dates; absence of a method row cannot be equated with nondeployment. Native `surv` is a site×method×DOY grouping key with two repeated bottletrap groups, not a proven unique trap/sample ID.

**This is not an independent out-of-sample ecological test.** No original `unmarked` occupancy model was refit; no p-values, detection probabilities, historical movement M, biotic interaction B or abiotic suitability A were estimated. The earlier EOG-WF sealed denominator of three scored endpoints, 31 scientific STOPs and three administrative exclusions remains unchanged. PR #697 remains Draft/unmerged.

## Reproducibility and source evidence

- Fixed **post-exposure** analysis protocol: `validation/wetland_chronological_discovery_v1/protocol.json`, original protocol commit `d641ea8cc49b0f468ea0e9fa3d07330bc66fd2ea`.
- Source-check executable: `benchmarks/wetland_chronological_discovery_v1.py`.
- Synthetic chronology/failure controls: `tests/test_wetland_chronological_discovery_v1.py`.
- Machine result and SHA record: `validation/wetland_chronological_discovery_v1/result_receipt.json`.
- Native Q1/Q2 full chronological rows: `published_q1_site_species_chronology.csv` (**243 rows**) and `published_q2_site_species_chronology.csv` (**117**); each row includes exact first/later dates and original CSV line identities for first recorded positives.
- Source-positive recovery by each of seven calendar horizons: Q1 `published_q1_site_species_horizon.csv` (**1,701 rows**) and Q2 `published_q2_site_species_horizon.csv` (**819**).
- Candidate source site×species chronology: Q1 `published_q1_candidate_site_species_chronology.csv` (**4**) and Q2 `published_q2_candidate_site_species_chronology.csv` (**2**).

[Original-source authenticated CI #43889603841](https://github.com/zuizui0223/eog/actions/runs/43889603841) **SUCCESS**, result fingerprint `6e9c3a23f8410e5b6ec2ad10fc77e4edc6f30422e6f1ef86707792ed883eba75`, artifact ID **14236012097**, digest SHA256 `577a45906061cea20182dd9304c10afc8f6ba2850157bb2e33c7e3cd1a4be800`. The workflow verifies exact original survey/site SHA, all five chronology classes and both source cohorts. This is an original-source observation-quality analysis, not a new biological status adjudication.
