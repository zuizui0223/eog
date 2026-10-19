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
