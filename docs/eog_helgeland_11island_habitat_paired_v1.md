# EOG: 11 named Helgeland islands — observation-time and habitat-type sensitivity

## Scientific focus

**Question:** In the published 2026 positive observation file, does retaining **all eleven named Ranke 2021 island population labels** (especially Lurøy-Onøy, source code \`33\`) alter the previously frozen classification difference between the first post-nest capture/observation and the first *next-calendar-year May–August* direct detection?

**Not the question:** Is movement biologically proven, does Lurøy-Onøy cause immigration, do farm-island birds prefer non-farm islands, or does EOG predict an unobserved colonization event?

Earlier work is already exposed and fixed:

- PR #646: 1,313 matched directly reobserved ID pairs, **125** discordances (124 first-same→next-different, 1 reverse).
- PR #647: after excluding ID histories involving *both* original model-excluded codes \`0\` and \`33\` by the target date: 1,260 positive ID pairs, **112** discordances. This is not the complete named-11-island roster.
- PR #648: exact 2026 source-internal raw code/label mapping; \`0=other helgeland\` and \`33=lurøy-onøy\`. The latter is **Lurøy-Onøy**, a named, **farm** population in Ranke et al. (2021).

The original [Ranke et al. (2021)](https://doi.org/10.1111/1365-2656.13580) already established higher inter-island dispersal among *non-farm* populations, more exchange within habitat type and only modest farm/non-farm cross-type movement **among its recruited birds**. An exploratory comparison of positive detections to those descriptions would **not** be an independent discovery or a method-equivalent replication.

## Frozen protocol and estimand

The new contract at \`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_11island_habitat_paired_protocol_v1.json\` was committed at \`fd18c40e521e14c982164e3b132ff81320c4b8be\` **before** reading the new 0-only/farm-type outcomes.

The same *entire* original 1,313 ID pairs are reconstructed from the author-fixed source using the previously verified 1994–2014 physical date mask. The origin remains each eligible ID's unique directly observed \`nest\` code, the raw-first classification remains its first physically dated post-nest \`capt/obs\`, and the next-calendar-year target remains its first May–August \`capt/obs\`. No codes/dates are inferred from the author R script's retrospective \`Least_age\`, filled island trajectories, \`Year\` or posterior population sizes.

The nested comparisons are:

1. **Original, unchanged:** all 1,313 positive-observation pairs.
2. **Named eleven, primary:** remove an ID only if a literal \`0=other helgeland\` positive record was physically observed **on/before its qualifying next-year positive date**. Keep \`33=Lurøy-Onøy\`. Do **not** delete rows and re-pick or reclassify events.
3. **Named eleven, retrospective sensitivity:** remove an ID if any literal \`0\` appears **anywhere in original pre-2015 observations**, even *after* the target date. This is a hindsight-only subset for bounding membership sensitivity.
4. **Author-model-filtered comparator:** remove an ID for any literal \`0\` **or** \`33\` before/by target, and demand exact reproduction of the PR #647 **1,260 / 112** previously reviewed result. This conservative ID exclusion is not a reproduction of the original author's row-level model filter or inferred demography.

### Habitat-specific descriptive pattern

Among the 0-only-primary positive IDs, use the immutable, published eleven-island dictionary to classify the unique source and directly observed next-season location as **farm** or **non-farm**.

The six farm populations are Aldra, Gjerøy, Hestmannøy, Indre Kvarøy, **Lurøy-Onøy**, Nesøy. Five non-farm populations are Lovund, Myken, Selvær, Sleneset and Træna.

Report separately:
- all next-year direct-positive encounters, in a 2×2 origin-type→observed-type table;
- the subset whose next direct-positive code differs from their unique nest code, in the same 2×2 table;
- first-same→next-different discrepancies by **source habitat type**;
- aggregate origin-code counts for the eleven already public population names, with no ring IDs or individual event histories.

This is **positive-detection geography conditioned on next-year reobservation**, not population rates, calibrated movement kernels, dispersal, habitat preference or seasonal survey effort.

## Controls and provenance

Source: Hansson Frank et al. (2026), Dryad \`10.5061/dryad.rr4xgxdnq\`, v6 version \`421942\`, file ID \`4576411\`, author fixed commit \`a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5\`.

The new runner:
- independently recalculates SHA256-attested source/header and matches the **complete frozen PR #646 receipt**;
- reconstructs all PR #647 both-code pre-target counts and matrix exactly, from the same source;
- verifies 11 named codes and the six/five habitat assignments against the **complete PR #648 source-internal code/name dictionary** and independent literature label table;
- reads **only date** outside 1994–2014. Post-2014 ID, stage, code, and destination are never read. Within the window only \`date\`, \`ID\`, \`Island\`, \`stage\` are consulted;
- fails on new codes, conflicting same-day source/destination codes in a habitat contrast, incomplete cohort partitions or attempts to expand ecological claims;
- emits aggregate counts and site-label categories only; no individual-level data.

The original 2026 archive was **not** publicly available as a 2014 real-time predictor source, and the above observational comparisons are explicitly post-exposure exploratory.

### Strongest scientifically supportable conclusion

Whether the previously seen **first-detection versus next-breeding-season spatial classification** persists when all eleven named populations are kept, and how the selected positive records distribute among the two already established habitat types. Do **not** infer movement probabilities, first settlement, source–sink flow, causal habitat effects, or EOG forecast improvements from these counts.

The frozen EOG-WF independent endpoint denominator stays **3 scored / 31 scientific STOP / 3 administrative exclusions**, with favorable/favorable/adverse outcome pattern unchanged.

## Reproduce

\`\`\`bash
python -m pytest -q tests/test_helgeland_11island_habitat_paired_v1.py
python scripts/audit_helgeland_11island_habitat_paired_v1.py \
  --upstream-checkout upstream_public \
  --output build/helgeland-11island-habitat-paired-v1.json
\`\`\`

The dedicated GitHub Actions runs this against the immutable upstream commit, uploads only aggregates, and must reproduce its independently reviewed frozen complete JSON before merge.


## Authenticated real-source result — 2026-10-19

The first original-source [GitHub Actions run 39208937959](https://github.com/zuizui0223/eog/actions/runs/39208937959) succeeded. Its aggregate-only artifact ID is \`12166747729\`, ZIP SHA-256 \`c9c6c9fcf4d11d4f007227fd9c265c7d15f06cfc1c197d30a0763302f03744f8\`. The ZIP and complete included JSON were independently inspected. The entire exact aggregate receipt is now fixed at \`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_11island_habitat_paired_observed_frozen_v1.json\`, and all dedicated reruns must equal it field-for-field.

Original Dryad-v6 SHA256/physical header, 51,162 physical pre-2015 positive rows, 10,737 unique-nest-origin IDs, and **all original PR #646/#647 paired matrices** were reproduced exactly. No bird ID or observation-date trajectory was exported.

### Same original 1,313 ID pairs; different membership rules

| Matched original same-ID comparison | Paired IDs with next-year direct positive | First/next classification discordant | Discordance conditional on observed target |
| --- | ---: | ---: | ---: |
| Original all raw codes (PR #646) | 1,313 | 125 | 9.52% |
| **All 11 named islands**: remove only \`0=other helgeland\` through target | **1,272** | **118** | **9.28%** |
| Named 11, even if \`0\` appears anywhere through 2014 | 1,268 | 118 | 9.31% |
| Exclude \`0\` and \`33\` through target (PR #647 comparator) | 1,260 | 112 | 8.89% |

The frozen 11-population named-source primary paired table is:

| First directly observed post-nest code | Next-calendar-year May–August: same as nest | Next-calendar-year May–August: different from nest |
| --- | ---: | ---: |
| Same as nest | 1,052 | **117** |
| Different from nest | **1** | 102 |

Thus **117 of the 118** disagreements are first-same→next-year-different; the reverse is observed once. All are direct site-code detection changes or changes in which observation is selected, NOT proof of true migration timing or breeding recruitment.

Only **41** of the original 1,313 positive-pair IDs showed raw \`0\` on/before the endpoint, while **14** showed \`33\`; **2** showed both. Keeping the named-island \`33\` instead of excluding it adds **12** matched IDs and six first-same→next-different discrepancies (117 rather than 111). Among the named-11 retained 1,272, \`33=Lurøy-Onøy\` is an origin for six ID pairs, the observed next-year positive destination for eleven ID pairs, and appears as origin and/or next destination in twelve unique pairs. These are positive-detection category counts, not source/sink flux.

### Habitat-type pattern among directly reobserved named-11 positive IDs

| Source named population habitat | Next observed farm | Next observed nonfarm | Original-nest-code different at next-year positive |
| --- | ---: | ---: | ---: |
| Farm (6 named populations; 813 positive pairs) | 806 | 7 | **69** |
| Nonfarm (5 named populations; 459 positive pairs) | 21 | 438 | **150** |

Within those **219** next-year different-*island-code* positive pairs, 62 are farm→farm, 129 nonfarm→nonfarm, seven farm→nonfarm and 21 nonfarm→farm. That is **191/219 (87.2%) within habitat type**. The selected positive-detection same-versus-different fraction is 69/813 (8.5%) among farm-origin IDs versus 150/459 (32.7%) among nonfarm-origin IDs, **not** exposure- or detection-adjusted dispersal probabilities.

Among the temporal first-same→next-different discrepancies, 39 have farm origins and 78 nonfarm origins. The original Ranke 2021 paper already reports nonfarm-biased dispersal and strong within-habitat exchange using a separately defined breeding-recruit denominator. Similarity to that established pattern is not a discovery, validation of recruitment identity or an independent replication.

**Numerical trap:** 219/1,272 ≈17.2% among this selected *next-year directly observed ID subset* happens to be close to the published **376/2,192 =17.2%** actual study recruits reported by Ranke et al. (2021). The two estimands and observation filters differ materially; they overlap in place, people, study years and underlying observation archive. Their agreement when rounded is NOT evidence they measure the same biological quantity, nor a confirmation of EOG.

### Hard conclusion and ecological STOP

It is justified to conclude the **observation-time classification disagreement survives full named-11 island inclusion**, and its recorded positives are heterogeneous by the known published habitat types. It is **not** justified to conclude causal habitat-dependent movement, an unbiased dispersal or survival probability, island colonization, true recruitment, 2014 as-of-time forecast access, or improvement from EOG model predictions.

This same observational file has now passed several descriptive sensitivity checks; further repeated filtering on the same positive sample has diminishing scientific returns. A biological next experiment should require an independent **individual recruitment-at-breeding record and island-year survey opportunity/detection denominator**, or a different prospective multi-taxon data source. Do not redefine these positive detections as another held-out EOG-WF endpoint.
