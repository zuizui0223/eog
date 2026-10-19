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


## Empirical execution of the frozen **synthetic** protocol (2026-10-19)

The first complete source-independent [GitHub Actions run 39248967844](https://github.com/zuizui0223/eog/actions/runs/39248967844) passed all simulated known-truth v23–v40 parent checks, v26 state mappings, independent conditional Bayes computation, and original v39 information regression. The original aggregate-only artifact **12184367871** was independently downloaded and inspected. Artifact ZIP SHA256: \`9d98a1cc1704954f9c9f8f9487f85748a1368f6422fbd3125b6ee964647f4527\`. The full canonical result JSON SHA256 is \`34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d\`. The complete JSON exists as that Actions artifact, and its **full hash** and key numerical results are frozen in \`validation/eog_original_idea_provenance_ecological_state_v41/result_frozen_v41.json\`; all future runs must reproduce the complete digest.

The first two CI tries stopped on **test/output scaffolding** issues before a valid final gate: a fabricated test supplied a partial target dictionary where the alias helper expected all targets; and a zero-valued history-blind counter was omitted from the serialized dictionary. Neither issue changed the frozen protocol, any latent landscape, Bayes likelihood, process state function or original v39 ecological conclusion. Both were repaired, and the full run completed successfully.

### New result — historical information often has no marginal value for the chosen present state

The primary stratum contains **189/768** original v23 design rows whose complete four-time occupancy observations did not distinguish all three activation histories. Under the unchanged assumed synthetic provenance assay (coverage q=0.60, miscall e=0.10), and at most three potential source-confluence sites:

| Target inferred from the same noisy source-tag observations | Mean additional information, bits | Number of 189 designs with positive information | Mean expected correct-target accuracy gain |
| --- | ---: | ---: | ---: |
| **Exact activation history** | **0.404169** | **120** | **0.204100** |
| Present state: persistent lag-2 mature/not mature | 0.140648 | 48 | 0.062300 |
| Present state: transient age-1-to-2 state | 0.177515 | 64 | 0.082885 |
| Present state: saturated age 0/1/2/3+ state | 0.208385 | 64 | 0.101649 |
| History-blind current occupancy (negative control) | 0 | 0 | 0 |

**The key contrast is 120 versus 48:** in **72/189** designs, provenance observations reduced uncertainty about the *exact history* while providing **zero additional information about the lag-2 mature-state map** beyond the four complete occupancy snapshots. These 72 cases make up **60%** of the 120 designs in which the observation informed exact history at all. Conversely, all 48 with maturity-target improvement also had exact-history information; this is consistent with the frozen data-processing constraint.

Why does this matter? An ecologist who wants to infer a specific current state, rather than historical labels for their own sake, can obtain information about past routes without improving the state prediction they care about. More knowledge about the past is not identical to more ecologically relevant knowledge.

The exact *mean* information ratio 0.140648 / 0.404169 ≈ 35% is **not** a measured biological cost-benefit ratio. It is a ratio across one frozen synthetic ensemble, with a specific age mapping and assumed observation channel.

### The information loss depends on the ecological target mapping

Under the same fixed 189 design worlds and same source tags, the transient target had **0.177515 bit**, exceeding persistent lag-2 maturity's **0.140648 bit**. The richer saturated age target had **0.208385 bit**. This confirmed the preregistered V3 direction **under the fixed synthetic process family**; it does not establish biological superiority of transient phenotyping or more categories in general.

Among the stricter **88** designs with three available potential confluence assay sites, exact-history information was 0.655816 bit, whereas persistent maturity information was 0.197241 bit, transient 0.244573 bit, saturated age 0.250572 bit. Do not confuse the 88 matched assay-coverage stratum with the full 189 occupancy-aliased worlds.

Source geometry also conditioned the target-specific result among the 189 occupancy-aliased worlds: in clustered-source designs (n=153), confluence provenance supplied **0.173741 bit** about lag-2 maturation; in dispersed-source designs (n=36), **0.000000 bit**, despite small residual exact-history information (0.011631 bit). These groups are not matched ecological treatment allocations, and synthetic source geometry is not a causal observed property of the Helgeland islands.

### A harder inferential ceiling

The original v23/v25/v26 **81 perfect-library exact-history aliases** reproduced exactly. In **12** of those, even full perfect earliest-source observations could not distinguish histories that implied different persistent lag-2 mature-state maps; the transient and saturating state targets each had **45** such residual designs. Thus replacing imperfect tag measurement with an arbitrarily complete set of *the same source-tag observation class* is insufficient to close those target distinctions. A new temporal/source-age measurement, or other independently discriminating evidence, is required within this known-truth world set.

The 726 design rows with any age-sensitive state memory were also exactly reproduced for all three target processes, as was the history-blind memory count zero.

### Verdicts and integrity

All five predeclared v41 predictions V1–V5 were **SUPPORTED**, with zero discrepancies against the independent v39 exact-history information calculator, zero target-information data-processing violations, and zero negative-control violations.

V4 (reproducing the original 12 historical aliases with different current mature-state targets) and V5 (information cannot increase after target compression) are **parent-consistency/theoretical invariants**, not two independent discoveries of ecological effects. The more useful v41 observation is the **existence and frequency of historical information with no incremental value for a declared ecological state target**.

No real biological maturation, genetic origin, colonization, ecological fitness, sampling cost or field survey effort was estimated. A 2021 individual-level genetic/recruitment archive remains inaccessible through the official URL tested in EOG #652. There is **no fourth EOG-WF predictive endpoint** and no alteration of the Methods in Ecology and Evolution submission claim.
