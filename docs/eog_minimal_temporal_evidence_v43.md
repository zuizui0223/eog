# EOG v43 — which additional time/site observations distinguish the 12 maturity aliases?

**Status:** Exact finite-world synthetic identifiability experiment, post-v42 exploratory. Source was frozen at protocol commit \`49d41d17df5495200a0e1faa0ed4ffb81e7d4eea\` before any new site×time readout was scored.

## What problem is actually unresolved?

The original [v42 evidence decomposition](./eog_provenance_uncertainty_v42.md) showed that complete original occupancy already determines a lag-2 maturity target in **141/189** history-ambiguous worlds. Among the **48** where maturity is genuinely uncertain, full perfect source labels at existing measurement sites distinguish maturity in **36**; the remaining **12** still have differing maturity targets under identical four occupancy snapshots and identical *complete* perfect earliest-source labels. In the independently reviewed v42 scenario CSV, all twelve were **clustered-source, rook-adjacency** worlds; this was already exposed and is not a new blind ecological result.

The target is the exact original synthetic condition *mature at Tstar iff earliest non-source arrival time ≤ Tstar−2*. It is **not** a real-world measurement of fitness, birth, persistence or survival.

## New question

Can a **time-resolved presence observation**, rather than adding more perfect source-identity tags, separate the remaining twelve *in this fixed original source model*? How many spatially localized binary presence measurements are needed, and which measurement options are fundamentally tautological?

We compare three **perfect** candidate measurement modes: a full non-source census at one clock time, a single binary node×clock-time presence readout, and the shortest exact set of at most 3 binary readouts needed to distinguish all candidate history pairs that have the same original occupancy+source label signature but a different mature-state target. The minimal set is a finite exact bit-mask set-cover computation (≤3 history pairs), not a fitted machine learner.

## Data and design: frozen before outcome

- Same **768** original source worlds from v23/v41/v42, identical sources, graph, barriers, three activation histories, original four full occupancy snapshots at **t=4,5,6,8**, and the same common synthetic present horizon Tstar. Recompute the original 768 / 189 / 141 / 36 / 12 count partition before extracting any new 12-world results.
- Parent v41 entire canonical result SHA256 \`34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d\` must reproduce on rerun; v42 frozen source-digest and 11,520-row CSV signatures must be read and reconciled.
- At baseline the analyst is granted **all** perfect earliest-source tags for **all** non-source nodes, plus the four existing perfect occupancy snapshots. The experiment is limited to target differences still unresolved under this optimistic information.
- Candidate new observation times are **integers 0 through Tstar inclusive**. Original t=4,5,6,8 are excluded from the new design (repeat exposure control) and t>Tstar is forbidden (future look-ahead).
- **Mandatory tautology exclusion:** t=Tstar−2 is **not** an independent test of prediction. A perfect *full* occupancy census at that time is exactly the definition of the binary lag-2 maturity state at Tstar. It is scored *only* as a named positive control, not included in the main rescue count or time/site optimization.
- Candidate schedule selection may inspect the three **model-predicted** history/readout signatures and the target-equivalence classes, but may not see which of the three is actually true. It is explicitly an optimistic, model-aided **oracle design**, not a response-blind field sampling recommendation.
- For sensitivity, also score each of the frozen calendar times 0,1,2,3,7,9,10,11,12 when it is ≤Tstar, not one of the existing four, and not equal to Tstar−2. Denominators are the number of the 12 original cases in which that **specific time was applicable**; do not silently divide by 12 for a time that would be in the future or would directly measure the target.

## Falsifiable statements

**T1** (definition, positive control): a complete census at t=Tstar−2 distinguishes the lag-2 maturity targets in every one of the twelve residual worlds.

**T2** (may be refuted): at least one residual case admits a single extra complete census at a *non-tautological* time that fully distinguishes the mature-state target among baseline-observationally equivalent candidate histories.

**T3** (may be refuted): at least one residual case can be distinguished with **one** non-tautological binary node×time presence readout.

**T4** (may be refuted): at least one residual case requires **two or more** binary node×time readouts for full mature-state discrimination.

**T5** (structural negative control): repeating any original occupancy census time, while conditioning on its already observed four-time signature, contributes exactly **zero** new conditional information. A positive result would indicate a broken observation contract.

Original v25/v26 maturation map or the three histories cannot be changed to make any prediction pass. Cases with no non-tautological solution must remain labelled **unresolved**; refutations of T2/T3/T4 must not be tuned away. Report each world's selected time/node, where mathematically possible, without any real geographic/bird identifiers.

## Important inference boundary

A successful new time measurement in this known-truth world is **not** proof that source-identity evidence is useless, that a real field survey would detect an immigrant, or that actual genetic ancestry is equivalent to first arrival. The full-census positive control *literally observes the maturity target used by this simulation*, so it cannot constitute independent ecological predictive success.

If other times resolve a case, that shows only that **time information separates histories left equivalent by a particular source-label observation channel**. Costs, observation errors, seasonal timing, occupancy censoring and genuine biological maturation are outside this fixed world. The v43 panel contains only twelve already-exposed synthetic rook/clustered cases and is not independently representative of natural islands.

No 2021 Dryad authentication retries, no real genotype/individual site data, and **no fourth EOG-WF predictive endpoint**. Original EOG-WF 3 scored / 31 scientific STOP / 3 administrative exclusions remains frozen.

## Reproduce

\`\`\`bash
python -m pytest -q tests/test_eog_temporal_evidence_v43.py
python benchmarks/run_eog_temporal_evidence_v43.py \
  --output-dir build/eog-v43-timing
\`\`\`

The dedicated CI must execute from the full parent v41 source and compare original v41 canonical hash, original v42 world partitions, original t=4/5/6/8 zero-information controls and each predetermined prediction verdict. Independently inspect and freeze both full aggregate result JSON and twelve-scenario diagnostics by canonical SHA256 before merge.
