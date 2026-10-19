# EOG / Helgeland — physical Island CODE to Location LABEL crosswalk

**Status:** Post-exposure exploratory *source-internal* dictionary audit. No biological model score or dispersal inference.

## Primary question

Does the immutable source file underlying the 1994–2014 positive-observation analysis use a consistent literal numeric \`Island\` code ↔ raw string \`Location\` label relationship? In particular, what literal labels accompany model-excluded codes \`0\` and \`33\`, and which labels exactly match the eleven named study populations in Ranke et al. (2021)?

This is important because [merged PR #647](https://github.com/zuizui0223/eog/pull/647) retained 112 of 125 first-vs-next-season code-classification disagreements after conservative exclusion of records involving 0/33. That remains an **observation-process result among directly detected bird IDs**. Establishing labels may help diagnose category handling, but it cannot turn this into a geographic movement path.

## Source and chronology

- The relevant author-source commit is **\`a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5\`**, from \`torhanssonfrank/DensityRegulationHouseSparrows\`.
- 2026 Dryad \`10.5061/dryad.rr4xgxdnq\`, version \`421942\`, file \`4576411\` already has a frozen, independently SHA256-/header-attested byte counterpart.
- Exactly the original **1994-01-01 through 2014-12-31** physical \`date\` records can contribute to this mapping. The script must read \`date\` first and never consult any other field on records outside the window.
- The new mapping pass reads \`Island\`, \`Location\`, and physical \`stage\` (\`nest/capt/obs\`) only for eligible dated rows. **It never reads any \`ID\`**, source reporting \`Year\`, inferred age, genotype, individual history or post-2014 code/name.
- This is a **2026-published retrospective source**; data availability by a 2014 forecasting cutoff has **not** been established.

Protocol freeze is committed at:
\`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_island_location_crosswalk_protocol_v1.json\`.
The contract is committed before the new code/name-value aggregation is run.

## Fixed interpretation contract

The primary output is an **aggregate literal-code/label dictionary** with time-window row counts. It preserves raw spelling variants, and compares names using only Unicode NFKC, outer/inner whitespace normalization and casefolding—**no invented transliterations or inferred synonyms**.

Each code is marked as having a unique normalized label, multiple labels, or insufficient observation in one of the two date bins to check stability. The converse is tested too: a normalized name may map to multiple raw codes. Both cases must be explicitly reported rather than silently choosing a winner.

The eleven Ranke 2021 named populations are frozen in advance as:
Aldra, Gjerøy, Hestmannøy, Indre Kvarøy, Lurøy-Onøy, Lovund, Myken, Nesøy, Selvær, Sleneset and Træna.

\`Ytre Kvarøy\` and \`Sundøy\` are NOT substituted for \`Indre Kvarøy\` or an unnamed population. Unknown labels remain unknown. Matching source-internal text to one of these names is **not** a certificate that its coordinates, survey effort or the independently published 2020 numeric code system match.

Two count-guarding periods: **1994–2003** and **2004–2014**. An unobserved code in a period is not evidence the location was absent or unsurveyed. Codes \`0\` and \`33\` retain their raw row-count provenance (2,613 and 1,738 previously verified source-positive rows, respectively) and no meaning is assumed from the code values alone.

Expected pre-exposure total/source counts: 73,593 raw file rows, 51,162 eligible through 2014, 1,070 before 1994, 21,361 after 2014, plus the two code counts. Any drift fails closed.

## What this can resolve—and what it cannot

The strongest possible output is a **source-internal 1994–2014 observational name dictionary**, potentially a partial one if some codes have multiple names or some named sites were not recorded. This is a valid technical prerequisite for geographic analysis, not a novel ecological result by itself.

Even a perfect source-internal bijection would not validate:
- source-published pre-2021 Niskanen v8 files and their numeric coding;
- geographic coordinates or site-specific geographic distances;
- coverage, surveyed-zero effort, detectability or true island-year occupancy;
- verified second-calendar-year **breeding recruitment**, true natal dispersal, founders, or colonization;
- retrospective biological observations as available at a historical forecast date;
- a fourth EOG-WF held-out endpoint (the original 3/31/3 scientific conclusion stays fixed).

### Execution

\`\`\`bash
python -m pytest -q tests/test_helgeland_pre2015_island_location_crosswalk_v1.py
python scripts/audit_helgeland_pre2015_island_location_crosswalk_v1.py \
  --upstream-checkout upstream_public \
  --output build/helgeland-pre2015-island-location-crosswalk-v1.json
\`\`\`

The dedicated CI authenticates source SHA256/header through the already-merged original-source checker, compares the exposed 0/33 counts, runs the new aggregate-only pass, rejects schema drift and exports one auditable JSON. On completion, independently inspect the result, freeze the full JSON and make reruns compare against the entire frozen artifact before merging.

Further biological progress requires a truly independent study-island geography dictionary and an observation-effort/breeding-recruitment source, not more row-level reclassification of the same positive observations.
