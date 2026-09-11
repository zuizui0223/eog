# EOG-WF — Methods in Ecology and Evolution desk-fit audit v2

Date: 2026-09-11

## Decision

**Scientific desk-fit: PASS.**

Keep **Methods in Ecology and Evolution** as the primary submission route and submit EOG-WF as a **Research Article describing a new methodological approach**, not as a Workflow article.

This audit does not reopen the empirical denominator. The EOG-WF paper remains frozen at **3 scored fresh endpoints / 31 scientific-protocol STOPs / 3 administrative exclusions**, with endpoint pattern **favorable / favorable / adverse**. The post-closure Layer-B v2 NCRN programme is separate repository evidence and must not be added as endpoint 4 or used to alter the paper synthesis.

## Current MEE fit

Official Author Guidelines checked on 2026-09-11:

- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/policyonpublishingcode.html

The current Research Article guidance favors new ecological/evolutionary methods that are broadly applicable across systems, normally asks computational methods to be demonstrated first with simulations or benchmark data when empirical applications are also used, and uses a standard structure of Abstract, Data/Code for peer review, Keywords, Introduction, Materials and Methods, Results and Discussion.

The current EOG-WF draft now matches the important scientific presentation requirements:

1. a deterministic known-truth method benchmark appears before the empirical Results;
2. Layer A and Layer B are defined as distinct estimands rather than one prediction score;
3. Layer B is tested only as paired added information beyond the same unchanged strong learner;
4. failed prospective candidates remain visible in the denominator;
5. the empirical series preserves both favorable and adverse outcomes and is hard-stopped after three scored endpoints;
6. the novelty section explicitly concedes existing accessibility, occupied-source proximity, habitat-network and threshold-sensitivity precedents rather than claiming those ingredients as new.

## Automated manuscript audit

Reference-closure workflow evidence:

- workflow run: `34563881236`
- artifact: `10185289291`
- artifact digest: `sha256:00680d0309bb5f96c644d79a81cd387ce661d103eff040cacca8e51d33334d7d`

Current read-only readiness audit:

- workflow run: `34575325740`
- job: `103186366597`
- artifact: `10189400010`
- artifact digest: `sha256:13206b5d90119fa7169086a9d6b31061616d7e22d8aa37006488ecb48e6afd5e`
- schema: `eog.eogwf_mee_submission_readiness.v3`
- workflow conclusion: **success**

Measured state:

- Abstract word count: **343**;
- complete Markdown manuscript word count under the repository checker: **3685**;
- numbered Abstract 1–4: PASS;
- Data/Code → Keywords → Introduction order: PASS;
- keywords: 7, alphabetical: PASS;
- `Materials and Methods` heading: PASS;
- known-truth benchmark before empirical Results: PASS;
- unresolved literature placeholders: **0**;
- References section present: PASS;
- manuscript under 8000 words: PASS;
- scientific desk-fit ready: **true**;
- submission ready: **false**, because author/release/legal gates remain unresolved.

The 3685 count is deliberately conservative because it includes the complete Markdown manuscript, including references and the submission-boundary checklist.

## What changed since audit v1

Audit v1 correctly identified a desk-reject risk: the method could be read as a prospective-validation workflow wrapped around existing ingredients because the method properties were not sufficiently visible before the empirical applications.

That risk has now been materially reduced without adding biological evidence:

- the deterministic known-truth benchmark is in Materials and Methods before empirical Results;
- the Abstract is numbered 1–4;
- Data/Code and Keywords are in current MEE order;
- Keywords are alphabetized and remain below eight;
- `Materials and Methods` is the section heading;
- the three literature-positioning placeholders have been replaced with verified references;
- the Discussion explicitly states that EOG does not claim novelty for accessibility, source-conditioned proximity, generic network occurrence modelling, thresholded connectivity, model combination or schema validation.

No empirical endpoint, score, direction or denominator was changed by these edits.

## Remaining blockers are administrative/release/legal, not scientific

The manuscript is **not submission-ready yet** because four items require author/external completion:

1. **Final title page.** Authors, affiliations, corresponding-author details, running headline, acknowledgements, author contributions, funding, competing interests and inclusion statement require author confirmation. The repository contains `manuscript/EOG_WF_TITLE_PAGE_TEMPLATE.md`; it must not be promoted to the final title page until confirmed.
2. **Review-ready archive / DOI.** `[FINAL ARCHIVE/DOI TO ADD]` remains in the Data/Code statement. A release/archive or a suitable private peer-review repository must be fixed before upload.
3. **AI/LLM disclosure.** Current MEE guidance requires transparent disclosure when LLMs are used in manuscript/code production, including the application/version and extent of use and author responsibility. The exact historical applications, versions and assisted portions must be confirmed by the authors before inserting the Methods disclosure and corresponding contribution statement.
4. **Open-source license file.** `pyproject.toml` currently declares `MIT`, but no root `LICENSE`, `LICENSE.txt` or `LICENSE.md` file is present. MEE's code policy requires an accompanying open-source license. Authors must confirm the intended license before the repository release package is fixed; this audit does not create a legal license grant on their behalf.

The repository readiness checker tracks these as author/release/legal gates. None justify additional ecological analyses or another fresh endpoint.

## Submission boundary

Do not:

- add a fourth EOG-WF fresh endpoint;
- move the post-closure NCRN Layer-B v2 attempt into the paper denominator;
- repair or rerun opened STOP systems as independent evidence;
- pool endpoint rows into a common-effect claim;
- market Layer B as a generally beneficial prediction product;
- identify a surviving finite world as historical truth;
- add mechanistic explanations for Tampa degradation without a separately preregistered study.

## Final desk-fit conclusion

The editor-facing answer to “what is the method?” is now concrete:

> **EOG-WF is a two-layer ecological inference architecture that retains exact finite-world identities for auditable sequential compatibility and falsification, exposes only a label-invariant projection to prediction, and prospectively tests that projection as added information beyond an unchanged strong learner while retaining failed candidates in the validation denominator.**

The next work is therefore **submission administration and reproducibility packaging**, not further scientific model development.
