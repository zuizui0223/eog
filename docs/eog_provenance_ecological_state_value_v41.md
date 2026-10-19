# EOG v41 — does noisy source-origin evidence predict ecological states, not just historical labels?

## Main research question

The frozen v39–v40 EOG benchmark established that noisy or missing **idealized earliest-source-of-arrival tags** can contain information about which of three activation schedules generated spatial observations. The strength of a static-confluence-site heuristic was very small after 64 response-blind placement-seed trials.

But exact latent **history** is not automatically the scientific target. Earlier original EOG **v24–v26** already demonstrated that two distinct histories can retain the same final occupancy and complete earliest-source tags while producing a different *present ecological state* through colonization age. Specifically, under the fixed v25 lag-2 mature/not-yet-mature mapping, **12/81** cases with histories aliased by complete occupancy and complete ideal source tags still had differences in mature state. For the v26 transient age-1-to-2 and saturating age-class targets, **45/81** had residual present-state differences.

**New question:** *Under the identical v39 noisy/missing provenance observation channel, how much of that evidence helps infer an age-dependent present state, rather than only the identity of an otherwise consequential or inconsequential activation history?*

The ecological interpretation is **abstract only**: \`mature\` is a two-step synthetic colonization-age status, **not** reproductive success, demographic recruitment, fungal succession or true local occupancy viability in a species.

## Pre-result fixed design

v41 source, target definitions, predictions and hard stop rules were frozen before new results in commit \`a812771a2d033b634dc95aceac0dc311a842a1e0\`, file \`validation/eog_original_idea_provenance_ecological_state_v41/protocol_v41.json\`.

- Exactly the original **768** v23 three-activation-history / two-source-geometry design rows. Original 579 occupancy-identifiable and 189 occupancy-aliased histories, 687 exactly identifiable under *complete perfect* occupancy+provenance, leaving 81 exact aliases. Among the 189, 88 support the v39 three-confluence-site fair comparison. **Every design row is retained**; the 189 occupancy-aliased rows are the principal statistical denominator for new information.
- Exact original v25/v26 **common present T\***: latest non-source first-arrival date among all three histories for that design, before declaring any age-dependent state. Do not change horizon or choose it after results.
- Four fixed present-state targets from v26: history-blind occupancy (negative control), binary persistent mature age≥2, binary transient state age 1–2, four-level saturating age 0, 1, 2, 3+. Compare these with the exact activation-history identity (the v39 target).
- Exactly the unchanged v39 response-blind source-confluence top-three, fixed SHA256 random top-three and unique-source-site negative-control sampling policies. At every measured synthetic site, \`q=0.60\` probability of being observed, \`e=0.10\` conditional probability of a wrong ideal source label; independent missingness/miscalls with the **known synthetic likelihood**. No real genetic data or estimated SNP error rates.
- Uniform prior on the three frozen latent histories. Exactly enumerate all missing/categorical report combinations to calculate each target's **conditional mutual information** \(I(T; \text{noisy source tags} \mid \text{all four occupancy snapshots})\) in bits and expected Bayes-optimal **correct target-state classification gain** relative to the occupancy-only baseline. Target accuracy and entropy depend on target granularity, so different targets' raw classification accuracy are not compared as though they shared the same label set.

This is a target-specific **value of information** calculation on finite known-truth worlds, not a new benchmark of real species' fitness or genetic prediction.

## Five falsifiable predictions

- **V1:** some of the 189 occupancy-aliased designs gain positive information about the frozen lag-2 maturity target from noisy confluence-site source tags.
- **V2:** some occupancy-aliased designs gain information about exact history while gaining **zero** about lag-2 maturity under the same observations; this would expose historical detail with no additional value for that declared present-state target.
- **V3:** averaged over the same 189 occupancy-aliased designs, the noisy confluence readout carries *strictly more* information about the v26 transient age-1-to-2 state than about the persistent lag-2 maturity state. Failure is a genuine refutation of this predeclared directional target prediction.
- **V4:** the original **12** complete-source observational aliases differ on the lag-2 mature state. These remain non-identifiable even with ideal complete source-tag observations; this is a **parent reproduction/integrity** check, not new biology.
- **V5:** for each target and world, the data-processing bound \(I(T;Y\mid O)\le I(H;Y\mid O)\) holds. This is a mathematical integrity check, not a novel biological hypothesis.

Other must-pass controls: the entire independent target-specific posterior calculator reproduces the original v39 history information **for every selected policy/world** within 1e-8 bit, the history-blind target and unique-source-tag site control both gain zero information/accuracy, and the original v26 present-state-memory counts remain **726 design rows** for each age-sensitive process (0 for history-blind).

## What counts as scientific progress?

A positive result would show that **imperfect source-origin measurements can help distinguish relevant synthetic present-state consequences** beyond spatial occupancy, with their information value depending on the ecological target. A mixed or negative result is also useful: a method can reconstruct *historical labels* without narrowing uncertainty about the state the ecologist actually cares about.

It would **not** validate that a molecular assignment is the first colonist at a site, that the v25 maturation lag is biologically accurate, that an actual source event changes phenotype, or that this method improves heldout field prediction. The original Dryad 2021 source containing Helgeland genetic/recruitment records could not be accessed on the tested public route (HTTP 403 in #652); no bird-level evidence is used.

Frozen EOG-WF remains **3 fresh scored endpoints / 31 scientific STOPs / 3 administrative exclusions**, with Methods in Ecology and Evolution submission boundary unchanged.

## Reproduction

\`\`\`bash
python -m pytest -q tests/test_eog_provenance_ecological_state_v41.py
python benchmarks/run_eog_provenance_ecological_state_v41.py \
  --output build/eog-v41-provenance-ecological-state.json
\`\`\`

After an independently inspected real GitHub Actions artifact is produced, freeze its **complete canonical JSON hash**, preregistered verdicts and original source evidence receipts. Dedicated and full package CI must match before merging.
