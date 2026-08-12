# Live journal-policy verification — 2026-08-12

Target: **Ecological Informatics** (Elsevier / ScienceDirect)

## Verified from current official sources

The current official journal page describes *Ecological Informatics* as an international journal on computational ecology and ecological data science. Its stated scope includes modelling of ecological data, uncertainty analysis, biogeography and ecosystem analysis. This supports the current manuscript positioning as a tested computational ecological framework with explicit uncertainty and reproducibility contracts.

The official journal page currently identifies the journal as open access. Publishing charges and institutional arrangements can change and must be checked at submission time rather than embedded as a scientific manuscript claim.

Elsevier's current journal-wide generative-AI policy was independently accessible on 2026-08-12 and establishes the following submission-facing requirements:

- substantive generative-AI use in manuscript preparation must be disclosed;
- the declaration should be a separate section at the end of the manuscript immediately before the references;
- the declaration should identify the tool/service, explain its purpose, and state that the authors reviewed/edited the output and take responsibility for the publication;
- basic spelling, grammar and punctuation checking does not require disclosure;
- AI use as part of the research process should be described reproducibly in Methods when relevant;
- generative-AI creation or alteration of manuscript figures/images is not permitted except when the AI use itself is part of the research design and is described reproducibly;
- AI tools cannot be listed as authors.

`manuscript/submission/declarations.md` has been aligned with this current journal-wide Elsevier policy while retaining **AUTHOR CONFIRMATION REQUIRED** status.

The EOG manuscript figures are deterministic code-generated SVGs from frozen scientific inputs and contracts; they are not generative-AI artwork. No generative-AI image editing should be applied to the final submission figures.

## Could not be independently machine-verified in this session

The journal page exposes a “Guide for authors” link, but automated retrieval of the journal-specific guide itself still returned HTTP 403 during this verification. Therefore the following remain **submission-day verification items** rather than machine-verified current rules:

- accepted article type and exact naming;
- exact manuscript word limit;
- exact abstract word limit;
- whether Highlights are required and their exact bullet/character limit;
- keyword count;
- graphical-abstract status;
- reference style;
- figure file types and minimum resolution;
- data/code statement requirements;
- anonymisation / peer-review model;
- journal-specific declaration placement beyond the verified Elsevier-wide AI requirement.

## Current internal working contract

Until the live guide is opened manually in the submission browser, the repository retains conservative package guards already enforced by CI:

- abstract <= 250 words;
- 3–5 Highlights;
- each Highlight <= 85 characters including spaces;
- complete manuscript includes Data/Code Availability drafts, declarations, cover letter, references and supplementary-material inventory.

These limits are packaging guards, not a claim that the inaccessible journal-specific guide was machine-verified on 2026-08-12.

## Submission-day gate

Before upload, an author must open the live Guide for Authors in a normal browser, compare every journal-specific requirement against `manuscript/structural_submission_checklist.md`, and record the verification date. Any formatting or policy correction may update the submission package, but it must not alter the original A-Islands conditional-ordering result, the prospective A-Islands strong-reference result, or the Tanzania strong-reference result/fingerprints.