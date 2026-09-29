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

## 10. Computational language decision

The original witness factorial required **75.865 s** in the straightforward Python implementation, crossing the provisional 60 s threshold for considering C++.

A preregistered Python integer-bitset replay then reproduced the **exact same scientific fingerprint** in **1.437 s**, a **52.8× speedup**.

Therefore:

> **C++ is not currently needed.**

Python remains the scientific reference implementation. C++ should be reconsidered only if later finite-world universes exceed the optimized Python/bitset envelope.

## Current product definition

The post-closure known-truth line now supports the following workflow:

[
\text{declare finite worlds}
\rightarrow
\text{observe}
\rightarrow
\text{falsify incompatible worlds}
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
