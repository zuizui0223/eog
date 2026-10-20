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


## First independent actual-source synthetic execution (2026-10-20), followed by chronology audit

The first full dedicated [GitHub Actions run 39416079181](https://github.com/zuizui0223/eog/actions/runs/39416079181) **SUCCESS** reran and SHA-verified the exact original v41 full known-truth result and matched every v42 world denominator. The original binary/census observations were then scored from the frozen graph histories. Independently downloaded aggregate artifact ID \`12261207341\`, initial ZIP SHA256 \`03390f9a62472ab49926fcc048c15bdd2cc0ac5a371e8327c7dbd3215045ae7e\`. Its complete original result had **12/12** non-tautological single-census rescues and **12/12** single node×time binary-observation rescues, with no two-site condition; the direct maturity-defining census t=Tstar−2 was separately counted **12/12 but only as a definitional positive control**. The original four census remeasurement information gain was exactly zero.

All five original v43 preregistered hypotheses were evaluated: **T1 SUPPORTED (definition), T2 SUPPORTED, T3 SUPPORTED, T4 REFUTED, T5 SUPPORTED (negative control)**. The average original source+occupancy posterior mature-target entropy in these twelve was exactly **2/3 bit per design**, all of which was removed by the best model-aided non-tautological perfect time census. This is not evidence that real detection cameras could achieve that success.

### Important result limiting generality: small domains and retrospective timing

Inspection of the independently produced **twelve world diagnostic table** established a much narrower interpretation than the headline \`12/12\` initially suggests:

| Previously unresolved twelve designs | Number |
| --- | ---: |
| Present horizon \`Tstar=4\` | **10** |
| Present horizon \`Tstar=3\` | **2** |
| Exactly one equilibrium non-source node | **8** |
| Exactly two equilibrium non-source nodes | **3** |
| Four equilibrium non-source nodes | **1** |
| All twelve source geometry and graph neighborhood | **clustered / rook** |

**Every single one of the twelve target times (\`Tstar=3\` or \`4\`) precedes the original final occupancy snapshot at \`t=8\`.** This is a **retrospective state-reconstruction** (smoothing) experiment conditioning on some observations made *after* the state being reconstructed, not an as-of-time ecological prediction. A claim of real prospective forecasting would leak future relative to the target. This chronology fact was noticed during independent review **after the initial v43 results had been exposed** and added only as a labelled post-exposure audit. The original ecological worlds, target definitions, all five hypotheses, readout times and source noise settings were **not changed**.

The original fixed universal calendar sensitivity shows how time applicability matters: census \`t=3\` was eligible in all twelve and resolved **10/12**; \`t=1\` was eligible in ten and resolved **3/10**, and \`t=2\` was eligible in only two (in the other ten it would be the maturity-defining time) and resolved **2/2**. One optimally selected binary time+node event resolved all twelve *given the three exact known candidate histories*. These are post-exposure mechanistic details, **not a field observation plan**.

**Scientific interpretation:** for these narrowly scoped original worlds, the unidentifiable mature-target state is hidden from **perfect source-of-first-arrival labels** but can be distinguished by an additional earlier occupancy timestamp. However, the toy equilibrium non-source region has at most four nodes and the original observation baseline includes future relative to the target. Thus \`12/12\` is a **synthetic identifiability counterexample**, not a strong generalizable ecological sampling recommendation.

This distinction reinforces the [v42 conclusion](./eog_provenance_uncertainty_v42.md): changing the *class* of observations can resolve an equivalence that endlessly perfecting the original source-tag class cannot—but whether it is usable for genuinely **prospective** ecological inference requires a separate as-of-time protocol, empirical detectability and a biologically justified target definition.

The **final reviewed v43 evidence artifact, posthoc chronology flags and exact checksum** are fixed separately on the v43 branch, and its dedicated rerun is required before merge. Do not quietly reuse the initial pre-audit result digest for the final receipt.


### Final independent evidence lock and retrospective status

The final dedicated [original-source known-truth run 39416634712](https://github.com/zuizui0223/eog/actions/runs/39416634712) independently reproduced the unchanged full v41 parent canonical digest and the complete original 768/189/141/36/12 population. Downloaded aggregate-only artifact **12261633054**; ZIP SHA256 \`4fc6fcc2a47377d61bfe6d518dca4f4944398568939d1dbe9acdad887188b394\`. The complete v43 final result canonical JSON SHA256 is \`04f24a88911b76da4c112a827dd4df4694152ff92dd350d413056f007ef05446\` and the **twelve-case diagnostic JSON** canonical SHA256 is \`2e5c00a3a596f70a522839702345316a6d024ef23f1793e639f9f6210560f939\`. All reviewed counts, all five predeclared verdicts and the separately labelled post-exposure chronology warning are fixed in \`validation/eog_original_idea_temporal_evidence_v43/result_locked_v43.json\`; CI must match both original full hashes.

**Practical conclusion in this simulation:** the original 12 hard cases are **tiny (1–4 non-source nodes), temporally early, and reconstructed using already available later observations**. An oracle-chosen earlier binary observation suffices under the exact assumed model, but does not supply genuine **as-of-time** validation. A stronger next experiment must restrict every input snapshot to t≤ the ecological target timestamp and recompute its denominator before scoring any proposed observation intervention. This is a **different prospective information problem**; results from the present retrospective twelve must not be reused as if they were forecast testing.
