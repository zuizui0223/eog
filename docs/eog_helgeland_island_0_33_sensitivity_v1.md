# Helgeland: robustness to author-excluded literal Island codes 0/33

## Why this is needed

The original, pinned author code in \`R scripts/Main model of metapopulation dynamics.R\` excludes \`Island == 33\` and \`Island == 0\` from its demographic modeling table. The EOG PR #646 exploratory positive-only seasonal comparison did **not** exclude either raw Island CODE. Its frozen original paired result was 1,313 directly observed next-calendar-year May–August IDs with 1,074 first-same→next-same, 124 first-same→next-different, 1 first-different→next-same and 114 first-different→next-different (125 total paired discrepancies).

The code exclusion is a comparability risk. **Nothing in the author's two R filters by itself establishes how 0/33 map to named islands, nor that simply deleting those rows recreates the author's recruitment/CMR analysis.**

This new check is a **post-exposure descriptive sensitivity**, not new independent biological evidence. The explicit protocol was committed first at \`a8b7a145e4c24f5bc026cd6981122ad990cdfffa\`, before 0/33 real-source aggregate inspection.

## Exactly what is compared

Use exactly the **same 1,313 ID/endpoint pairs and all frozen first-versus-next positive classes** as PR #646. Keep its original result unchanged. Do not delete observation rows and reassign source, first positive or next-year detection dates.

Three matrices are generated:

1. **Baseline exact:** All original 1,313 pairs and all nine same/different/ambiguous combinations. Must exactly reproduce the mainline PR #646 frozen receipt.
2. **Primary, pre-target clean:** Same pairs after excluding IDs that have any literal raw \`Island\` 0 or 33 in their directly observed 1994–2014 \`nest/capt/obs\` history **up to and including the first next-year May–August positive date**. This does not use site observations after that endpoint to decide inclusion.
3. **Secondary, full-period clean:** Same pairs after excluding IDs that ever have raw Island 0 or 33 anywhere in their permissible 1994–2014 direct record. This is a more conservative *retrospective* screen and may depend on observation after the target date.

We also distinguish excluded source codes, first-raw-followup date codes and next-year-positive date codes, and count 0/33 rows without exporting any ID, island name or individual's trajectory. The original all-records cohort denominator must remain 10,073 eligible nest IDs and 1,313 paired directly reobserved IDs; no 2015–2022 ID/site/stage values may be inspected.

## Scientific inference boundary

The question is **whether the 125 disagreements survive a strict source-code exclusion**, not whether 0 and 33 represent unusual habitat or successful colonization. Any surviving discrepancy is still an *observation-time effect among directly detected records*, not an unbiased dispersal rate. The primary screen is endpoint-timed to avoid changing membership from post-target observations; the full-history screen makes that later-information sensitivity explicit.

Neither restricted result is necessarily the Ranke et al. (2021) 11-island recruit population. A true cross-archive Island-code dictionary, recruitment-event definition and island/year observation-effort table remain unverified. The already exposed 2026 source is not a 2014-public predictor. All ecological forecasting/causal claims remain HOLD.

## Source and execution

Read only the previously SHA256-verified 2026 Dryad v6 presence file via fixed author revision \`a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5\`. First rerun the merged #646 source/physical-header and full exact frozen receipt verification. Then read the same file with \`date\` as the **first and sole field inspected** on pre-1994 or post-2014 rows. Other consulted source fields are \`ID\`, \`Island\`, \`stage\`; never \`Year\`, \`Least_age\`, \`Location\`, filled/inferred sites, genotypes or later outcome fields.

The dedicated workflow runs synthetic contradictory event histories and original-source aggregate reconciliation. It emits only an aggregate JSON receipt. Before merging a successful PR, independently inspect the actual CI artifact, freeze the complete JSON and make reruns compare the entire receipt. Stop on baseline drift or output-contract mismatch.

The core EOG-WF fresh predictive programme stays at 3 scored endpoints, 31 scientific STOPs and 3 administrative exclusions.

Run:

\`\`\`bash
python -m pytest -q tests/test_helgeland_island_0_33_sensitivity_v1.py
python scripts/audit_helgeland_island_0_33_sensitivity_v1.py \
  --upstream-checkout upstream_public \
  --output build/helgeland-island-0-33-sensitivity-v1.json
\`\`\`
