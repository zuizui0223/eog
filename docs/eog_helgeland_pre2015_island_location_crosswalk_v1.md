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


## Independently inspected real-source mapping (2026-10-19)

Original-source dedicated [Actions run 39202831125](https://github.com/zuizui0223/eog/actions/runs/39202831125) succeeded with source SHA256/header, the prior first-positive denominator, and the separately frozen #647 0/33 counts all matched. Its aggregate-only artifact ID **12165010358** was downloaded and independently opened (ZIP SHA-256 \`34e54b9781b8afadc823ccf3f27e6c825c1a12afc3a1bb3de9b2834ffe9fcade\`). Every field of that receipt is now frozen at [\`helgeland_pre2015_island_location_crosswalk_observed_frozen_v1.json\`](../validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_island_location_crosswalk_observed_frozen_v1.json) and rechecked by the dedicated CI.

**Actual result:** All **51,162** directly observed pre-2015 records resolve to **12 unique literal Island-code / Location-label pairs**, with **no code associated with two normalized labels and no normalized label associated with two codes**. All 12 mappings appear in *both* the 1994–2003 (15,864 records) and 2004–2014 (35,298 records) periods without name changes.

| Literal Island code | Raw Location label | Direct physical observation rows, 1994–2014 | Exact 2021 11-name text match |
| --- | --- | ---: | --- |
| 0 | other helgeland | 2,613 | No, extra geographic category |
| 20 | nesøy | 1,839 | Nesøy |
| 22 | myken | 1,523 | Myken |
| 23 | træna | 5,572 | Træna |
| 24 | selvær | 3,986 | Selvær |
| 26 | gjerøy | 8,536 | Gjerøy |
| 27 | hestmannøy | 13,514 | Hestmannøy |
| 28 | indre kvarøy | 4,546 | Indre Kvarøy |
| **33** | **lurøy-onøy** | **1,738** | **Lurøy-Onøy** |
| 34 | lovund | 2,453 | Lovund |
| 35 | sleneset | 2,984 | Sleneset |
| 38 | aldra | 1,858 | Aldra |

The names of **all eleven populations in Ranke et al. 2021 are represented** by exact normalized label matches. No unmatched 2021 study name was found in the source-internal label universe. This refines the earlier source \`stage_location_summary.txt\` table, which showed only ten names and lacked numeric \`Island\` codes.

### Scientific consequence of decoding 0 and 33

The two original-model-excluded codes are **not scientifically equivalent**:
- \`0\` = \`other helgeland\`: an umbrella label outside the named eleven-study-population roster.
- \`33\` = **\`Lurøy-Onøy\`**, **one of the named eleven study populations**. It is not an unknown island or a generic data-entry error merely because this *particular* author's demographic modeling script filtered the code.

The earlier #647 sensitivity **112/1,260** excluded any ID having either code through the target date. It is valid as a conservative **model-filter-aligned** observation-subset analysis, but cannot be characterized as an *eleven-population-inclusive* analysis. A distinct hypothetical \`0\`-only screen could retain the named Lurøy-Onøy category, but would be **post-exposure exploratory** and must not be silently substituted for the frozen #647 result.

### Scientific HOLDs unchanged

This is a **within-one-2026-file observed category dictionary**, not an independently verified map-coordinate lookup, a pre-2021 Niskanen numeric cross-archive key, or a longitudinal complete island-year census. It does not establish surveyed-zero effort, undetected birds, correct breeding/recruit status, population founding, actual movements between named islands, or out-of-time EOG added predictive value. The 2026 data source remains retrospective with respect to 2014.
