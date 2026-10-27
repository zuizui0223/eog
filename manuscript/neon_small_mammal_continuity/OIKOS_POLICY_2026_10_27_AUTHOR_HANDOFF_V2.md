# Oikos NEON small-mammal manuscript — October 27, 2026 policy reconciliation

**Scope:** source-preserving pre-submission administration, not ecological reanalysis. The 16-site once-only NEON result, 32 original manuscript/figure/report source files, older blinded PDF and reviewer bundle, and original EOG-WF 3/31/3 are **frozen**. This document does not imply author approval, a permanent archive DOI, ScholarOne account access or actual submission.

## Confirmed live official Oikos / NSO policy

Checked **2026-10-27** against:

- https://nso-journals.org/author-guidelines
- https://nso-journals.org/oikos-for-authors
- https://www.wiley.com/publishing/article/ai-guidelines

The Oikos-specific page names Research Paper as a valid type, requires the title file, anonymous main text, reviewer data/code and relevant ScholarOne statements, and describes ScholarOne submission. The NSO Author Guidelines explicitly require:

1. **Title page as a separate file** containing title, author list and affiliations; the main text must not disclose author names or affiliations. The corresponding author's ORCID must be entered in the ScholarOne user profile.
2. **Data Availability Statement entered in the submission form**, not included in the anonymous main-text file. Anonymous data/code or an anonymous-accessible repository must be supplied for peer review.
3. **Significance Statement entered in the submission form**, not the main text. The Oikos/NSO conflict, funding and acknowledgements statements are also entered in the submission system where applicable.
4. **AI Use Statement at the end of the anonymous main text** when AI-assisted tools were used beyond minor copyediting, including for research code, manuscript content, displays, analysis or literature tasks. State the **actual tool(s), purpose and extent** and how human authors checked and accepted the work; the exact wording requires author/coauthor confirmation. AI cannot be an author.
5. Anonymous main text: abstract ≤300 words, single column, double spaced, continuous page and line numbers; PDF is accepted at initial submission. Research data/code must remain available for anonymous review; permanent public archival DOI is required by the journal's eventual publication policy.

These instructions supersede the **initial-submission packaging assumptions** captured in historical files checked September 25–27. This is not a change to the scientific protocol, analysis or the original 16-site finding.

## Reconciled blocker in the historical nine-page PDF

The original source \`MANUSCRIPT_V1.md\` (Git blob SHA1
\`ada5a84d3b862e122b1d6895c47ed3511de05854\`) contains a complete section
\`## Data availability\` between Discussion and Figure captions, but **no**
\`## AI use statement\`. The original PDF generator renders every source
section, so its archived \`OIKOS_BLINDED_MAIN_V1.pdf\` does not meet those
two current NSO placement rules.

The separate historical \`AI_USE_STATEMENT_V1.md\` is expressly a **draft**:
the tool/model versions, actual uses and author accountability have not been
attested. Do **not** treat that file as verified permission to invent or
insert an AI disclosure.

**Therefore do not upload historical OIKOS_BLINDED_MAIN_V1.pdf as the
final anonymous main file**, despite its formatting/visual QA and valid
historical artifact receipt. Retain the historical PDF and associated
timestamps/hashes as a reproducibility record.

## New non-destructive v2 submission assembly

\`build_oikos_initial_submission_policy_v2.py\` checks all **32 archived
original Git blob SHA1s** and the 16-site once-only response fingerprint
before any output. It **never edits** \`MANUSCRIPT_V1.md\`,
\`build_oikos_blinded_pdf.py\`, prior paper figures/receipts, or a scientific
NEON observation.

With no author approval, it generates only **ScholarOne form-ready
science-grounded fields**, namely:

- \`OIKOS_SCHOLARONE_DATA_AVAILABILITY_V2.txt\` — copies the exact original
  manuscript data-availability statement for the **separate submission form**.
- \`OIKOS_SCHOLARONE_SIGNIFICANCE_V2.txt\` — copies the existing separate
  significance statement for the **form**.
- \`OIKOS_SUBMISSION_POLICY_PREFLIGHT_V2.json\` — explicitly records that the
  final anonymous PDF, title page, author/coauthor approval, conflict/funding
  information, publication archive DOI and ScholarOne submission remain
  incomplete.

Only after a completed **private** copy of the
\`OIKOS_AI_AUTHOR_APPROVAL_TEMPLATE_V2.json\` is affirmatively attested by
the human author(s), the builder may produce a **new**, distinctly named
\`OIKOS_ANONYMOUS_MAIN_AI_APPROVED_V2.md\` and
\`OIKOS_ANONYMOUS_MAIN_AI_APPROVED_V2.pdf\`. Those new documents:

- preserve the scientific original and references;
- remove only the **separate form-only** Data availability section;
- add exactly the author-approved AI use statement after Discussion and
  before Figure captions/References, which is the end of the main scientific
  prose;
- use the unchanged, SHA1-verified ReportLab renderer for the same blind
  layout, line numbers and page numbering;
- reject email, identity-bearing repository links, ORCID and unapproved
  placeholders in the **blinded** output.

The output is only an **approved AI-statement/anonymous-main-file assembly**.
It does **not** mark title page, author list/order, correspondence,
funding/acknowledgements/conflict, NEON data ethics, CRediT, permanent archive
DOI or ScholarOne metadata as finally approved. Original author accountability
cannot be inferred from automated tests.

## Commands

With no human approval, produce the source-only form fields and a
**not-ready-for-submission** status:

\`\`\`bash
python manuscript/neon_small_mammal_continuity/build_oikos_initial_submission_policy_v2.py \
  --output-dir build/oikos-policy-preflight-v2
\`\`\`

When the coauthors genuinely agree on precise AI-use wording, copy the
provided public **template** to an untracked location **outside the
repository**, fill the exact statement and all five true attestations, and
run:

\`\`\`bash
python manuscript/neon_small_mammal_continuity/build_oikos_initial_submission_policy_v2.py \
  --approval-json /secure/untracked/OIKOS_AUTHOR_APPROVAL.json \
  --output-dir build/oikos-author-approved-blinded-v2
\`\`\`

The output directory must not already exist. The private approval file is
read-only and **never** included in the generated anonymous PDF or outputs.
Do not commit a filled approval record containing personal author information.

CI runs the preflight path and *invented synthetic* approval fixtures to
test PDF generation. These fake fixtures are explicitly not human-approved
paper content and are not uploaded as journal submission PDFs.

## Actual remaining author-only decisions

- Final author order, affiliations, corresponding author email/contact and
  ORCID profile, all required coauthor assent.
- Actual AI model/tool name and version, dates, scope, human checks and
  jointly approved disclosure, or accurately justified non-use if applicable
  (the existing source draft says generative AI was used, so an empty
  disclosure cannot be assumed).
- True funding/acknowledgements, conflict-of-interest and applicable
  ethics/EDI statements for the ScholarOne fields.
- Final confidential title page and cover-letter authorization.
- Availability of the already-built anonymous peer-review data/code package;
  final DOI-based permanent archiving at the journal-required stage.
- Submission-system completion and review of ScholarOne's compiled proof.

**Stop:** No new NEON biological-response requests, site substitutions,
post hoc scientific positive-outcome hunting or EOG-WF endpoint changes
are permitted for Oikos formatting. The primary confirmatory result remains
0/16 emergent guild gain with 16/16 individually fully continuous species
and 13/16 occupancy-continuity redundancy (post hoc).
