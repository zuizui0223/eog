# EOG-WF — Methods in Ecology and Evolution desk-fit audit v1

Date: 2026-09-08

Purpose: one-time submission-fit audit after empirical closure. This document **does not reopen candidate search or authorize a fourth fresh endpoint**.

Official sources checked:

- MEE Author Guidelines: https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines
- MEE Aims and Scope: https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/aims-and-scope/read-full-aims-and-scope
- MEE Workflow guidance: https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/features/workflows

## Decision

**Keep Methods in Ecology and Evolution as the primary route, but submit EOG-WF as a Research Article / new methodological approach, not as a Workflow article.**

The paper is not desk-safe yet. The main remaining scientific presentation risk is not the closed empirical denominator; it is whether the manuscript demonstrates the *method itself* clearly enough, independently of the three ecological applications.

## Why the paper remains in scope

MEE states that its emphasis is the description and analysis of new methods and methodological approaches in ecology and evolution. Research Articles should describe new methods and how they may be used, and the journal favors methods that are broadly applicable across taxa or systems.

EOG-WF has a plausible methods-level contribution if framed narrowly as:

> **a two-layer ecological inference architecture in which exact finite-world identities remain an auditable sequential compatibility/falsification state, while a frozen world-label-invariant projection is exposed to an unchanged strong predictor and evaluated by prospectively paired added value.**

The three scored endpoints already span distinct ecological data types and systems:

- telemetry;
- passive acoustics;
- seagrass monitoring.

The manuscript therefore need not add another biological endpoint to demonstrate cross-system application.

## Why this should not be submitted as a Workflow article

MEE's Workflow category is aimed at novel, broadly useful assemblages of software/informatic tools for complex Big datasets and explicitly requires substantial quantitative improvement over existing workflows, detailed open-source code, error-propagation analysis, extensive sensitivity/ablation analysis, and benchmark/Big-data testing.

EOG-WF is not principally a Big-data processing pipeline and should not make workflow assembly its novelty claim. The candidate funnel, response firewall, schema gates and reproducibility machinery are supporting validation infrastructure, not the central article type.

## Main desk-reject risk

MEE's Research Article guidance says descriptions of new computational methods normally should include testing with simulations or benchmark datasets; when empirical datasets are used, simulations should normally be described first. It also states that workflows merely linking existing methods generally are not treated as new methods.

The current `EOG_WF_MANUSCRIPT_V1.md` moves directly from conceptual motivation into empirical-development history and the three fresh endpoints. That makes the method vulnerable to being read as:

> a careful prospective validation workflow around existing finite-world summaries and strong learners,

rather than:

> a new ecological inference architecture with independently demonstrated method properties.

### Required remedy

**Do not add a fourth empirical endpoint.**

Instead, before submission, recover from the existing repository evidence a compact response-independent method demonstration that establishes the properties needed for the paper's central claim, ideally before the empirical section:

1. exact Layer-A world identity preserves rule-specific contraction/falsification;
2. Layer-B projection is invariant to world renaming and member order;
3. Layer-B removes arbitrary identity while retaining declared support-set information;
4. a favorable Layer-B predictive result does not imply survival/truth of a specific Layer-A mechanism;
5. Layer-A falsification can coexist with Layer-B predictive complementarity.

If existing synthetic/known-truth tests already establish these properties, convert them into one manuscript-level benchmark figure/table. This is exposition of frozen method behavior, not a new fresh ecological endpoint and cannot change the favorable/favorable/adverse decision.

If the existing repository does **not** contain adequate known-truth evidence for these method properties, that becomes the only scientifically justified pre-submission benchmark gap. Any added synthetic benchmark must be response-independent, declared as method validation, and prohibited from modifying the empirical closure boundary.

## Framing corrections for the draft

### Keep central

- Layer A versus Layer B as distinct estimands;
- exact identity for audit/falsification, not supervised labels;
- paired complementarity against an unchanged strong learner;
- Louisiana decoupling as the clearest structural-versus-predictive example;
- Tampa adverse result as the reason the product boundary is context dependent;
- prospective hard stop as protection of the empirical denominator.

### Keep secondary

- physical response-header gate;
- token normalization;
- registry failures;
- individual STOP taxonomy details;
- candidate-by-candidate chronology.

These are important reproducibility/prospective-design evidence but should not dominate the Introduction or Discussion.

### Do not claim

- generic novelty for finite world sets, ensembles, permutation-invariant summaries, stacking, threshold graphs, reachability, least-cost connectivity or schema validation;
- universal predictive superiority;
- causal mechanism recovery;
- unique historical-route reconstruction;
- biological impossibility outside the declared finite universe.

## Manuscript-format gaps from current MEE guidance

Before submission the main article still needs:

- numbered 1–4 Abstract structure required by MEE;
- Data/Code for peer review statement immediately after the Abstract;
- Keywords;
- complete literature references replacing `[REF]` markers;
- title-page file with authors, affiliations, acknowledgements, contributions and data availability information;
- final word-count check against the standard-article limit;
- AI-use disclosure if applicable under the current MEE policy;
- review-ready code/data archive or private peer-review repository.

These are submission-preparation tasks and do not require new biological analysis.

## Final gate

MEE remains the first submission route **if and only if** the final manuscript can answer the editor's likely first question:

> *What is the new method here, independently of the unusually careful prospective validation process?*

The intended answer is:

> **EOG-WF separates exact rule-specific ecological falsification state from a label-invariant prediction interface and tests the latter only as paired added information on top of an unchanged strong predictor; the two layers are allowed to disagree, and the empirical program demonstrates that they do.**

If a compact method/known-truth benchmark cannot make that answer concrete without inventing a new method after outcome closure, MEE should be downgraded and Ecological Informatics reconsidered. Until that audit fails, the frozen primary route remains MEE.
