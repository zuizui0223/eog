# Helgeland: why near-identical marginal fractions do not validate natal dispersal

**Status:** 2021 published-result and official source-metadata comparison. The 2021 original file bodies remain inaccessible in this runtime; **no new published-recruit event or raw file body was scored or parsed**. Original EOG-WF outcomes are frozen.

## The usable empirical contrast

The new [EOG #649 all-named-eleven-island receipt](../validation/eog_virtual_world_ecology_synthesis_v1/helgeland_11island_habitat_paired_observed_frozen_v1.json) is based on 2026-published source data restricted by raw physical observation date through 2014. Exactly **1,272** source-ID positive pairs had an observed next-calendar-year May–August `capt/obs`; of these **219** were observed on a different literal `Island` code from an unambiguous nest code. Another **118** had a different **first-followup-vs-next-calendar-year** same/different classification. The latter two numbers concern different outcomes and must not be conflated.

Ranke et al. (2021), [Journal of Animal Ecology, DOI 10.1111/1365-2656.13580](https://doi.org/10.1111/1365-2656.13580), reports **2,192 recruits** that were ringed as nestlings/juveniles and later recorded as potential second-calendar-year breeders; **376** were established as inter-island *recruit* dispersers. Critically, **357 of the 376** dispersers were recorded in the recruitment year while **19 were documented using later-year capture/resighting**. This is a biological study-specific endpoint and observation-history construction, *not* the raw first/next `capt/obs` rule in EOG.

### Numerical agreement—and its inferential boundary

| Distinct observational estimand | EOG 2026-vintage directly observed positive sample | Ranke et al. 2021 published recruit sample |
| --- | ---: | ---: |
| Different island code / study-dispersed recruit | 219 / 1,272 = **17.21698%** | 376 / 2,192 = **17.15328%** |
| Different-code/distance-positive within same farm/nonfarm habitat class | 191 / 219 = **87.21461%** | 326 / 376 = **86.70213%** |
| Farm→farm among different-island positives | 62 | 99 |
| Farm→nonfarm | 7 | 19 |
| Nonfarm→farm | 21 | 31 |
| Nonfarm→nonfarm | 129 | 227 |

The apparent difference is **+0.06370 percentage points** in the marginal different-island fraction, **+0.51248 percentage points** for same-habitat among different-island positives, and **0.03325 total-variation distance** between normalized four-category habitat distributions.

**These are descriptive comparisons of overlapping, not independent, data.** The almost-matching numbers do **NOT** show that the same bird IDs entered the numerator, that direct positive detections meet verified recruitment criteria, or that the implied movement rates are unbiased. No file-level linkage to the 2021 recruit records is possible from the verified published aggregates. Comparing unpaired count ratios cannot identify false positive/negative classifications, detection probabilities, true settlement timing or biological pathwise reachability.

A sharper example of the underlying risk is already verified *within the same* EOG-positive cohort: **118/1,272 (9.28%)** changed the assigned same/different nest-code class when the target changed from first direct positive to next-year breeding-season direct positive. Thus near agreement of two distinct *marginal* proportions can coexist with material sensitivity to event definitions. **This is an observational-estimand warning, not an EOG predictive success or new dispersal ecology.**

Published methods also report incomplete nest-search coverage on Lurøy-Onøy and on nonfarm islands before the improved surveys (nonfarm nest monitoring for recruit production from 2004), so calendar eligibility alone is not an independently verified survey-effort denominator. The paper's adult counts and 0-valued annual recruits are analysis-derived quantities, not automatically field-observed surveyed absences.

## Original 2021 aggregate data source: genuine external comparator but body gated

Official [Dryad dataset](https://datadryad.org/dataset/doi:10.5061/dryad.v41ns1rx1), published 2021-08-24: dataset ID `74465`, version ID `136299`; [official file-list endpoint](https://datadryad.org/api/v2/versions/136299/files) lists exactly **four files**. We froze **names, IDs, sizes and source-declared SHA-256 digests** in [the source inventory](../validation/eog_virtual_world_ecology_synthesis_v1/helgeland_ranke2021_published_recruit_comparator_source_v1.json). These digests are claims from Dryad's public metadata, not locally checked 2021 bytes.

The landing page says `emigration.txt`, `immigration.txt` and `island-pairs.txt` contain island-year numbers of emigrants, immigrants, recruits and adult population size, plus pairwise aggregation. `description.txt` is the description/data dictionary. **We have not accessed any of their actual physical headers or data rows.**

Attempted public download routes returned **HTTP 401** on the official file API and an anti-bot-only `Validating...` page on the web stream. Do not attempt authentication circumvention or silently replace them with the 2026 source.

### Source-qualified offline continuation, already implemented

The read-only script [`scripts/audit_helgeland_ranke2021_published_comparator_v1.py`](../scripts/audit_helgeland_ranke2021_published_comparator_v1.py) does two completely separate actions.

- With only the repository's frozen JSON, calculate and test the *published* aggregates side by side. **No 2021 files are read.**
- **Only if the four original 2021 files have been obtained legitimately** into a local folder, pass `--authorized-source-dir <directory>`. It checks *every* file's exact declared byte size and SHA-256 in streaming binary mode, refusing missing/mismatched/symlink/renamed files. This gate still reads no biological rows or columns and never commits file bodies. Hashing authenticates the original source; further grain/year/recruitment/effort checks would need a new frozen extraction contract and independent inspection.

```bash
python scripts/audit_helgeland_ranke2021_published_comparator_v1.py \
  --output build/helgeland-ranke2021-published-only-v1.json

# When an authorized official source copy exists:
python scripts/audit_helgeland_ranke2021_published_comparator_v1.py \
  --authorized-source-dir path/to/legitimate_originals \
  --output build/helgeland-ranke2021-byte-verified-v1.json
```

The default package/CI tests use **invented** byte strings only for the SHA256 checker. The reproducible published-only aggregate receipt is frozen after inspection and checked field-for-field against future runs.

## Scientific decision

The current Helgeland observational-discrepancy result is real as a *positive-record, observation-time comparison*, but **it is not a new biological reachability, recruitment, or dispersal result**. Stop serially reclassifying the same 2026 positive sample. The next meaningful biological experiment requires **a different independently collected system**, or legitimately obtained original 2021 recruit **and field survey effort** files with a separate, predeclared analysis that asks a novel ecological question instead of rediscovering the 2021 article.

This independent source was public in 2021, **not** at a retrospective 2014 prediction cutoff. No independent EOG forecast scored, no fourth EOG-WF endpoint, no new 2014 as-of-time source proven.
