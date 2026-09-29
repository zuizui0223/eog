# EOG-WF MEE live-policy verification — 2026-09-29

This receipt records a submission-day-style policy check for the scientifically frozen EOG-WF manuscript. It does not reopen scientific development.

## Journal and article type

Target journal: **Methods in Ecology and Evolution**  
Article type: **Research Article**

Current author guidelines continue to describe Research Articles as new, broadly applicable ecological/evolutionary methods papers. Computational methods should normally be demonstrated first with simulations or benchmark datasets before empirical applications.

Source:
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines

## Initial-submission manuscript requirements

The current author guidelines state that initial submissions should:

- remain within the Research Article word-count range of 7,000–8,000 words including references/statements;
- use a numbered 1–4 abstract aiming not to exceed 350 words;
- include no more than eight alphabetically ordered keywords;
- provide a Data/Code for peer review statement beneath the abstract;
- follow the standard Introduction / Materials and Methods / Results / Discussion structure;
- make code/data available for peer review;
- use an open-source software licence for submitted code.

EOG-WF already has automated checks for these requirements and an MIT licence at repository root.

Sources:
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/policyonpublishingcode.html

## Separate title page

The title page must be uploaded separately as a Supplemental Document Not for Review. The current MEE guidance requires:

- manuscript title;
- all author full names;
- institutions and addresses;
- corresponding-author name, address and email;
- running headline of no more than 45 characters;
- acknowledgements;
- data availability;
- conflict-of-interest statement;
- author contribution statement.

The EOG-WF author-admin builder now requires institutional postal addresses and deterministically renders these fields only after explicit author approval.

Source:
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines

## Authorship, inclusion and third-party data

During submission, authors must confirm that:

- the manuscript is original and not under consideration elsewhere;
- all authors/institutions approve submission;
- all entitled authors are included;
- necessary acknowledgements have been made;
- legal and ethical requirements are satisfied;
- third-party datasets are publicly available for unrestricted reuse or permission for reuse has been obtained.

MEE also requires a statement on inclusion during submission; it may be incorporated into the Author Contributions statement in the published article.

The EOG-WF confirmation schema therefore keeps originality, inclusion and third-party-data reuse as explicit author-controlled fields rather than inferring them from repository history.

Source:
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines

## LLM / AI disclosure

Current MEE guidance requires a clear Methods statement when LLMs or comparable AI tools were used to produce work described in the manuscript. The statement should identify the application and version. The corresponding or senior author must take responsibility for AI-generated code/text, and AI-generated code should be annotated accordingly.

The EOG-WF admin workflow therefore requires explicit author confirmation of:

- application/provider;
- model/version;
- approximate use period;
- assistance categories;
- any required code/text annotations;
- responsible author;
- final Methods disclosure text;
- author accountability.

The builder inserts the approved disclosure into the final manuscript only after the author-admin confirmation receipt validates.

Source:
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines

## Ethics policy update

A March 2026 MEE editorial reiterates BES ethics requirements and asks authors to expand reporting for methods involving or affecting organisms, people/communities, or new technologies. EOG-WF analyses archived ecological datasets rather than reporting a new field experiment, but the final authors must still review whether any directly contributed fieldwork, permits, animal-use approvals, or other ethical statements need to be declared.

Sources:
- https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210x.70290
- https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines

## Current unresolved items

After this policy check, no new scientific or journal-format blocker was identified.

The only unresolved EOG-WF submission gates remain author-controlled:

1. final author/title-page metadata and declarations;
2. author-approved AI/LLM disclosure and accountability.

These are resolved only through the verified author-admin confirmation workflow; they must not be inferred or backfilled automatically.
