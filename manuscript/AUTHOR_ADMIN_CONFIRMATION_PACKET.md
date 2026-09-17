# Shared author/admin confirmation packet

This file consolidates the remaining **author-controlled** submission gates for the two scientifically closed EOG manuscripts. It is a completion interface only; it does not authorize any new analysis, endpoint, model change, claim expansion, release, DOI minting, or journal submission.

Current manuscript lanes:

- **EOG-WF** — target: *Methods in Ecology and Evolution*; science closed; remaining blockers are final title-page/author metadata, review archive or DOI/private-review link, and author-approved AI/LLM disclosure.
- **Structural/island paper** — target: *Ecological Informatics*; science, presentation-v2 figures, deterministic rebuild/fingerprints, and repository-side visual QA closed; remaining gates are author approvals, release/archive, and submission-day live-policy/publisher-preview checks.

Do not infer author-controlled fields from Git history, affiliations, repository ownership, or prior drafts. Complete them only from explicit author confirmation.

## A. Shared author identity and order

Provide the final author order exactly as it should appear on both manuscripts, or explicitly state where the two manuscripts differ.

For each author:

- Full publication name:
- ORCID, or `none`:
- Affiliation ID(s):
- CRediT roles approved by that author:
- Corresponding author: `yes` / `no`:

For each affiliation:

- Affiliation ID:
- Institution:
- Department/unit, if applicable:
- City:
- Country:
- Postal address if required for the corresponding author:

Corresponding-author contact:

- Name:
- Email:
- Postal address if required:

## B. Funding

List every grant, fellowship, institutional award, or other financial support that contributed to either manuscript. If there was none, explicitly state `No external or dedicated funding to declare` only if all authors agree that this is accurate.

For each source:

- Funder:
- Grant/award number, or `none`:
- Recipient:
- Applies to: `both` / `EOG-WF only` / `structural-island only`:

## C. Competing interests

Approve one of the following:

- `The authors declare no competing interests.`
- Replacement disclosure: [AUTHOR-APPROVED TEXT]

All authors must confirm the selected statement.

## D. Ethics, permits, and directly contributed field data

The structural manuscript currently states that it analyses archived occurrence, environmental, landscape, and derived computational data and does not report a new human-participant experiment. Authors must still confirm whether any directly contributed field data require animal-use, collection-permit, institutional ethics, or other permit language.

Choose one:

- `No additional ethics or permit statement is required for directly contributed data.`
- Required statement: [AUTHOR-APPROVED TEXT]

For EOG-WF, provide any separate ethics/permit statement if required by the underlying contributed data; otherwise state `none required` after author review.

## E. Originality and simultaneous submission

Confirm whether all authors approve the following statement for each manuscript at submission time:

> This manuscript is original, has not been published previously, and is not under consideration for publication elsewhere.

- EOG-WF: `approved` / replacement text
- Structural/island: `approved` / replacement text

## F. Generative-AI / LLM disclosure

### Structural/island draft to approve or correct

Current repository draft:

> During the preparation of this work, the authors used ChatGPT (OpenAI) to assist with code review, reproducibility checks, literature triage, manuscript organization, and language editing. After using this service, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.

Choose one:

- `approve structural draft as written`
- `replace with:` [AUTHOR-APPROVED TEXT]

Also confirm that the submitted figures remain deterministic code-generated figures rather than generative-AI artwork.

### EOG-WF disclosure inputs

The EOG-WF readiness gate additionally requires explicit author confirmation of the actual AI/LLM applications and versions used and the extent of assistance. Do not reconstruct this from repository history.

Provide:

- Application/provider:
- Model/version if known:
- Approximate period of use:
- Assistance categories: code review / code generation / reproducibility checks / literature triage / manuscript organization / language editing / other:
- Any manuscript or code portions requiring specific annotation:
- Responsible author who accepts accountability for review of AI-assisted code/text:

If multiple applications/models were used, provide one entry per application/model.

## G. Structural/island release metadata

Confirm before the tagged `v0.1.0` release and archive record are created:

- Creator order for software/archive metadata:
- Software citation metadata approved by all authors: `yes` / `no`:
- Any authors who should not appear as software/archive creators:

The release and DOI remain on HOLD until the author gates in this packet are complete.

## H. EOG-WF title-page-only items

Provide:

- Running headline, maximum 45 characters:
- Acknowledgements:
- MEE inclusion statement required at submission stage, or author instruction to draft it after the live journal-policy check:
- Any author/affiliation difference from the structural/island paper:

The final `manuscript/EOG_WF_TITLE_PAGE.md` must not be created until all required author-controlled fields are confirmed.

## I. One-response completion block

Authors may return the following block in one response. Preserve `UNKNOWN` where a coauthor still needs to approve something; do not guess.

```text
AUTHOR ORDER:
1. ...
2. ...

AFFILIATIONS:
A1. ...
A2. ...

CORRESPONDING AUTHOR:
Name: ...
Email: ...
Postal address: ...

CREDIT ROLES:
Author 1: ...
Author 2: ...

FUNDING:
...

COMPETING INTERESTS:
...

ETHICS / PERMITS:
EOG-WF: ...
Structural/island: ...

ORIGINALITY / SIMULTANEOUS SUBMISSION:
EOG-WF: approved / ...
Structural/island: approved / ...

AI / LLM:
Structural draft: approve as written / replace with ...
EOG-WF applications/models/versions and extent: ...
Responsible author: ...
Figures are not generative-AI artwork: yes / no

STRUCTURAL RELEASE METADATA:
Creator order: ...
Software citation metadata approved: yes / no

EOG-WF TITLE-PAGE ITEMS:
Running headline: ...
Acknowledgements: ...
Inclusion statement: ...
Author/affiliation differences: none / ...
```

## After author confirmation

Repository-side sequence is fixed:

1. write the final author metadata/title-page/declaration files without changing scientific content;
2. run package/readiness checks;
3. create the tagged `v0.1.0` release after author gates clear;
4. reproduce the canonical release fingerprints from the final package;
5. create/fix the review archive or DOI and replace release placeholders;
6. perform submission-day live journal-policy and publisher-preview checks;
7. build the final submission packages.
