# Known-truth EOG development mainline

## Current position

This programme is a **separate post-closure simulation line**. It does not reopen or alter the frozen EOG-WF empirical 3/31/3 denominator.

The scientific center is now:

> **EOG does not need to recover one “true” process from occurrence data. It should eliminate finite declared worlds only when the available evidence contains a valid witness against them, preserve observationally equivalent worlds as unresolved, and use the remaining ambiguity to design the next discriminating observation, calibration, or intervention.**

## 1. What was directly refuted

The first large known-truth factorial falsified the strong recovery idea.

Across 64 virtual truth cases, even complete positive-occurrence coverage uniquely recovered the generating process in **0/64** cases.

This was not a software failure. Every truth had at least one alternative world whose positive reachable state was equal to or a superset of the truth.

For truth-positive set (R_*), false-world set (R_w), and observed positives (O), a false world is eliminated only when

[
O\cap(R_*\setminus R_w)\neq\varnothing.
]

If (R_*\subseteq R_w), no amount of positive-only sampling can eliminate that world.

Therefore the claim

> enough occurrence records should eventually recover the generating process

is rejected for the frozen known-truth universe.

## 2. BAM was made explicit rather than used as a covariate bundle

The focal realised state is generated as

[
G=A\cap B\cap M.
]

- **A** — abiotic niche support.
- **B** — explicit biotic permissibility from independently generated partner and antagonist distributions.
- **M** — source-conditioned movement accessibility from distance, barrier permeability and finite horizon.

v2.1 passed preregistered activation gates for all axes:

- A-only witness pairs: 16
- partner-B-only: 11
- antagonist-B-only: 6
- M-distance-only: 7
- M-barrier-only: 12

Across all ordered world contrasts, A-only, B-only, M-only and all overlap categories were observed.

Yet unique truth recovery remained:

- complete positives: **0/64**
- + perfect surveyed negatives: **2/64**
- + exact occupied-node arrival times: **6/64**

So the non-identification is not a failure to include B or M.

## 3. Direct mechanism evidence still has a ceiling

v2.2 supplied idealized complete A, B and M state information.

Unique parameter-world recovery became:

- baseline: 6/64
- + A: 8/64
- + B: 7/64
- + M: 9/64
- + A+B: 9/64
- + A+M: 18/64
- + B+M: 16/64
- + A+B+M: **32/64**

The remaining 32 worlds belonged to duplicate complete-state classes.

The alias audit showed that all residual duplicates differed only in inactive M parameters:

- 8 duplicate classes varied only barrier permeability (P);
- 8 varied only movement horizon (H).

Thus state identification and parameter identification are distinct targets.

## 4. Targeted interventions activated dormant parameters

v2.3 preregistered two mechanism-specific challenges.

**Barrier-permeability challenge**:
standardized source immediately left of the barrier, one-step crossing outcome.

**Horizon challenge**:
standardized source at one end of a long barrier-free corridor, distal reachability outcome.

Results:

- P-only alias classes split: 8/8
- H-only alias classes split: 8/8
- axis-specificity violations: 0
- passive classes: 48
- intervention-augmented classes: **64 singletons**

Within the frozen finite parameter universe, intervention therefore changed non-identifiable passive parameters into identifiable active parameters.

## 5. Ambiguity became an experimental-design object

v2.4 represented the 16 remaining passive alias pairs explicitly.

A preregistered evidence library contained:

- P barrier challenge
- H long-corridor challenge
- repeated passive observation as a negative control

Pair discrimination:

- P challenge: 8/16
- H challenge: 8/16
- repeated passive state: 0/16

The exact minimum separating set was the two useful interventions.

v2.5 generalized this to a domain-agnostic API taking only:

- world IDs;
- current evidence signature by world;
- predicted outcome by evidence channel;
- optional active-world subset.

It reproduced the BAM result exactly, failed closed when an evidence library was insufficient, and reduced the required design from two interventions to one after the compatible world set contracted.

## 6. Observation process is part of the world universe

v2.6 showed that low probability is not impossibility.

For finite repeated surveys and detection probability (p<1),

[
P(0\text{ detections}\mid Z=1)=(1-p)^n>0.
]

For example, at (p=0.75,n=8), the value is (1.5259\times10^{-5}): very small, but not zero.

Therefore finite nondetection cannot be promoted to exact absence without an observation contract that makes it impossible under presence.

Similarly, if any admissible observation world allows false positives (q>0), one detection does not robustly falsify absence.

## 7. Ecological worlds and observation worlds must be audited jointly

v2.7 formed an explicit Cartesian product:

[
W_E\times W_O.
]

At the response-independent maximally discriminating BAM node `r1c3`:

- 16 ecological worlds predict presence;
- 48 predict absence.

After four nondetections:

- with perfect detection only, ecological projection = **48/64**;
- after admitting an imperfect (p=0.75) observation world, ecological projection = **64/64**.

All 16 presence worlds were “resurrected” because at least one admissible observation world could miss the species.

Even eight nondetections left all 16 presence worlds compatible.

Direct calibration to (p=1), without a new focal ecological observation, restored the 48-world strict projection.

Thus calibration of how data were observed can be more discriminating than collecting more of the same ecological observation.

## 8. Future observations can be stochastic

v2.8 extended evidence design from deterministic outcomes to finite sets of possible outcomes.

An action robustly separates two hypotheses only if their possible outcome sets are disjoint.

For the three active joint hypotheses:

- `absent::p1`
- `absent::p075`
- `present::p075`

the robust split counts were:

- repeat one survey: 0/3 pairs
- repeat four surveys: 0/3
- direct detection calibration: 2/3
- direct biological-state assay: 2/3

The minimum worst-case robust nonadaptive design was the two direct channels.

## 9. Evidence collection is naturally adaptive

v2.9 solved the finite decision tree exactly.

- minimum worst-case depth: **2**
- optimal first actions: detection calibration or state assay
- repeat-survey-first worst-case depth: **3**
- known truth `absent::p1`: calibration outcome (p=1) resolves in **1 action**
- remove calibration: worst-case exact resolution impossible
- remove state assay: worst-case exact resolution impossible

The first CI run failed because child-node replanning incorrectly required action mappings to contain *exactly* the reduced active hypothesis set. This was corrected to allow parent-universe mappings while reading only active hypotheses. The rerun passed the independent brute-force depth check.

## 10. Independent stochastic generator: restriction can increase ambiguity

The deterministic BAM results were then challenged with an **independent stochastic
metapopulation generator** implemented outside the EOG reconstruction modules.

Across 384/384 eligible stochastic runs:

- true-world retention failures: **0**;
- EOG API parity mismatches: **0**;
- positive-superset ceiling violations: **0**;
- omitted-truth witness-criterion mismatches: **0**;
- unique truth recovery at horizon 40: **0 in every truth scenario**.

Two stronger hypotheses were refuted.

First, the preregistered expectation that every structurally distinct truth would
realize a positive witness failed for the joint A+B+M truth. Its complete positive
support contained only 33 nodes and was a subset of every candidate reachable set, so
even complete positive observation eliminated **0/32** candidates.

Second, unordered accumulated positive history was never strictly more discriminating
than the final snapshot in any of the 384 runs.

This exposed an exact set-theoretic principle. If complete positive supports satisfy

[
R_1 subset R_2,
]

then the compatible-world sets obey

[
C(R_1) supseteq C(R_2).
]

The restrictiveness audit checked **304/304** strict support-inclusion pairs with zero
violations. The most jointly constrained A+B+M support was therefore also the most
ambiguous in the frozen universe.

So stronger ecological restriction does **not** imply easier mechanism identification
from positive occurrences. It can do the opposite.

## 11. Time-stamped occurrence history recovers information that unordered history loses

The failure of unordered accumulated history did not imply that temporal information
was useless.

When first-occurrence time was retained:

- static support classes: **8**;
- temporal signature classes: **20**;
- static M-equivalent pairs: **48**;
- pairs split by temporal signatures: **19**;
- stochastic runs with strict temporal contraction: **256/384**.

Truth retention remained exact, but unique truth recovery was still **0** in every
scenario.

Thus the relevant distinction is:

> unordered occurrence accumulation can be redundant, while time-stamped occurrence
> history is a genuinely different evidence class that can recover movement
> distinctions.

## 12. The stochastic principles generalize across preregistered landscapes

A later frozen panel contained eight landscapes spanning open-smooth, barrier-gap,
environmental-bottleneck and joint-fragmented structures.

Two joint-fragmented landscapes failed response-free activation gates and remained
**DESIGN_STOP**. They were not repaired or replaced.

The remaining six landscapes contributed **1,152** eligible stochastic runs.

Across every eligible landscape:

- truth retention failures: **0**;
- restrictiveness-nesting violations: **0**;
- static compatible-set expansion violations: **0**;
- independent evaluator parity mismatches: **0/72 audits**;
- joint A+B+M limitation remained maximally ambiguous;
- temporal signatures refined static support classes;
- at least one realized temporal strict-gain run occurred;
- non-identification persisted at horizon 40.

All frozen U1-U8 claims were supported in the eligible panel.

The two DESIGN_STOP landscapes remain part of the denominator and are evidence that
the validation protocol can reject a virtual system before outcome scoring.

## 13. Deterministic BAM generality and exact evidence bounds

A separate deterministic panel used **12/12 activation-qualified systems** and
**768 truth cases**.

Unique BAM-state recovery across the frozen evidence ladder was:

| evidence level | unique truths |
|---|---:|
| complete positives | **0 / 768** |
| complete realized G | 25 / 768 |
| + occupied-node arrival | 159 / 768 |
| + direct A | 275 / 768 |
| + direct B | 565 / 768 |
| + direct M accessibility | **768 / 768** |
| + full M arrival | **768 / 768** |

The positive-only zero bound generalized to all 12 systems.

However, the predeclared claim that **M must always be the final bottleneck** was
refuted: at least one system already reached complete BAM-state identification before
direct M evidence was added.

Exact targeted-measurement audits across all 768 truths found maximum requirements of:

- direct A: **1 node**;
- direct B: **2 nodes**;
- joint A+B: **3 nodes**;
- direct M accessibility: **2 nodes**;
- additional full-arrival timing after M state: **0 nodes**.

These are finite-universe existence bounds, not claims that those measurements are
always feasible in real field systems.

## 14. Formal identifiability boundary

The simulation sequence is now accompanied by finite-set identities rather than only
empirical benchmark results.

For a declared truth world, the verified theory separates:

1. **positive-only compatibility** — the survivor fiber is exactly the set of worlds
   whose realized support contains the observed truth support;
2. **complete perfect presence/absence** — survivors are exactly the worlds with the
   same realized support;
3. **direct A/B/M evidence** — later evidence levels are successive state-equality
   fibers;
4. **complete BAM-state evidence** — survivors are the BAM-state equivalence class,
   which need not be a unique parameter label;
5. **targeted measurement design** — finding a minimal direct-measurement set is an
   exact finite hitting-set problem.

The exact hitting-set audit passed all **768** truth cases with zero failures.

This is the central conceptual correction to “recover the true process”: the inferential
object is a sequence of **evidence fibers over a declared finite universe**, and a
singleton is justified only when the relevant fiber is actually unique.

## 15. Computational language decision

The original witness factorial required **75.865 s** in the straightforward Python implementation, crossing the provisional 60 s threshold for considering C++.

A preregistered Python integer-bitset replay then reproduced the **exact same scientific fingerprint** in **1.437 s**, a **52.8× speedup**.

Therefore:

> **C++ is not currently needed.**

Python remains the scientific reference implementation. C++ should be reconsidered only if later finite-world universes exceed the optimized Python/bitset envelope.

## 16. EOG v3 public joint-world engine

The validated post-closure algorithms are now exposed through one domain-agnostic
public surface rather than as separate benchmark-only modules.

EOG v3 represents

[
W_J = W_E 	imes W_O,
]

where (W_E) is the declared finite ecological-world universe and (W_O) is the
declared finite observation-process universe.

An evidence event removes a joint world only when its observed outcome lies outside
that joint world's declared support. Ecological and observation conclusions are then
projections of the surviving joint set.

The integrated v3 regression reproduces the canonical frozen results:

- strict perfect-detection case: **48 joint / 48 ecological survivors**;
- broad perfect + imperfect case: **112 joint / 64 ecological survivors**;
- perfect-detection calibration: **48 joint / 48 ecological survivors**;
- robust split counts on the three active joint hypotheses: **0, 0, 2, 2**;
- exact minimum robust evidence set: **calibration + direct state assay**, size **2**;
- minimum adaptive worst-case depth: **2**;
- repeat-survey-first worst-case depth: **3**;
- removing either direct channel: exact worst-case resolution **unavailable**.

The public commands are:

```text
eog-v3-joint-evaluate
eog-v3-plan-evidence
eog-v3-plan-adaptive
```

Their JSON examples are executed inside CI after package installation.

Integrated v3 result fingerprint:

`073bcdf0e0e1761e6b5af077f9ffbfc79aeadb59b1c5aee4dd4ab6c4bbc23dab`

The v3 API is a product consolidation of frozen post-closure results. It is **not** a
new EOG-WF empirical endpoint and does not modify the MEE manuscript result.

## Current product definition

The post-closure known-truth line now supports the following workflow:

[
\text{declare ecological + observation worlds}
\rightarrow
\text{observe}
\rightarrow
\text{contract the joint world set}
\rightarrow
\text{project ecological / observation uncertainty}
\rightarrow
\text{retain unresolved equivalence}
\rightarrow
\text{diagnose why unresolved}
\rightarrow
\text{rank admissible next evidence}
\rightarrow
\text{choose exact or robust minimum design}
\rightarrow
\text{adapt after each outcome}.
]

The product is therefore better described as a **falsification-driven evidence and experiment design framework** than as a conventional distribution predictor or true-process selector.

## Hard claim boundary

Do not claim:

- a surviving world is historical truth;
- positive occurrences generally identify the generating process;
- complete realised distributions identify BAM decomposition;
- complete A/B/M state maps necessarily identify generating parameters;
- finite nondetections are hard absences under imperfect detection;
- more data of the same observational type necessarily resolve ambiguity;
- the current finite-world results imply universal ecological identifiability.

Do claim, conditionally on the declared finite universes:

- exact world elimination when valid witnesses exist;
- explicit non-identification when worlds remain observationally equivalent;
- monotone weakening of robust exclusion when ecological or observation universes expand;
- exact finite evidence-library sufficiency/insufficiency;
- exact or robust minimum evidence designs;
- adaptive replanning after evidence outcomes.
