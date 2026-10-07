# History-storage manuscript — submission readiness v1

Updated: 2026-10-07

## Overall status

**Scientific analysis line: CLOSED at v38.**

**Manuscript line: SUBMISSION-READY. Remaining blockers are author-supplied metadata,
final conflict screening and the exact submission-release DOI.**

Do **not** add a v39 derived endpoint before submission.

---

## 1. Scientific evidence — complete

Merged evidence chain:

- v28: target-specific history retention in the plant microbiome;
- v30: independent target-specific history retention in grassland;
- v31: universal identity-storage hypothesis prospectively refuted;
- v33: first-arriver-role mechanism prospectively falsified by complete placebo mapping;
- v34: Alternaria has the largest history-level leverage on identity-free architecture;
- v35: that leverage is dominance-centered, not dominance-exclusive;
- v36: direct Alternaria-vs-rest contrast confirms dominance-centered storage;
- v37: dominance shift positive in 11/12 host genotypes and primarily genotype shared;
- v38: mechanistic ceiling fixed; current archive cannot distinguish interaction mechanism.

Current structural conclusion:

> **Assembly history is not stored in one universal feature of the present. Different
> communities can retain the same kind of past perturbation in different components of
> present organization, and identifying that storage channel is logically prior to
> assigning a mechanism.**

Microbiome refinement:

> **Alternaria arrival history leaves a broadly host-genotype-shared,
> dominance-centered structural legacy, but the current archive cannot identify why.**

---

## 2. Main manuscript — complete

Merged files:

- `MANUSCRIPT_DRAFT_V1.md`
- `MANUSCRIPT_ECOLOGY_LETTERS_V1.md`
- `MANUSCRIPT_SPINE_V1.md`
- `ABSTRACT_RESULTS_DRAFT_V1.md`

Ecology Letters version:

- article type: Letter;
- abstract: **139 words**;
- main text: approximately **4,000 words**;
- figures planned: **4**;
- tables: **0**;
- text boxes: **0**;
- running title candidate: **Structural storage of assembly history** (38 characters).

Current source-data citations:

- microbiome Dryad: `10.5061/dryad.7p2cv`;
- grassland Zenodo: `10.5281/zenodo.5713397`.

Citation regression guard:

- Alonso-Crespo version-of-record year is **2023** in both generic and Ecology Letters
  manuscript variants;
- CI test prevents reintroduction of the stale 2022 in-text citation.

---

## 3. Submission-facing materials — complete

Merged:

- `SUBMISSION_STRATEGY_V1.md`
- `NOVELTY_STATEMENT_ECOLOGY_LETTERS_V1.md`
- `GRAPHICAL_ABSTRACT_TEXT_V1.md`
- `COVER_LETTER_ECOLOGY_LETTERS_V1.md`
- `ECOLOGY_LETTERS_SUBMISSION_CHECKLIST_V1.md`
- `LITERATURE_POSITIONING_V1.md`
- `FIGURE_PLAN_V1.md`

Journal order:

1. **Ecology Letters** — one reach attempt;
2. **Ecology** — strongest fit / rapid fallback;
3. **Oikos** — conceptual backup.

Do not submit the current two-system reanalysis to Nature Ecology & Evolution without new
independent process-level/generalization evidence.

---

## 4. Figure package — visual QA complete

Figure architecture:

1. storage problem;
2. target-specific retention in both systems;
3. identity stripping / contrasting storage channels;
4. placebo-mapping falsification + Alternaria localization.

Initial figure workflow:

- run `37481142599`;
- status: success;
- artifact `11425177411`;
- digest:
  `sha256:78616e077291557373767469e4a70e1760798b5a36e1d9832ab8c5e920088c60`.

Manual visual QA found and corrected:

- Figure 3 previously shifted E values vertically for display;
  - fixed: y-values now remain exact, with x-jitter only;
- Figure 3 Shannon markers now match their corresponding systems;
- Figure 4 mapping audit changed to a horizontal correct-vs-placebo representation;
- mapping rank and exact finite `p_map` are now shown;
- Figure 2 annotation placement improved.

Manual preview after the fixes was judged readable for Figures 2–4.

Final post-QA push artifact:

- workflow run `37546022729`;
- status: **success**;
- artifact: `11450079490`;
- digest:
  `sha256:4949c953a1b04af693431d1bb4f76e14fe000a42a169349bba0498254464f930`.

The corrected Figures 1–4 passed manual visual QA. The figure code uses only committed
machine-readable result summaries.

---

## 5. Reproducibility / claim-control layer — complete

Merged / prepared:

- hard fingerprints for v28, v30, v31, v33-v37;
- frozen figure-data builder;
- manuscript integrity tests;
- Ecology Letters length checks;
- v38 mechanistic-ceiling claim guard;
- source DOI checks;
- 2023 grassland-citation regression guard.

Equivalent connector-side gate on the final hardening branch passed:

- all 8 authoritative result fingerprints;
- v31 rank-abundance figure value;
- v34 Alternaria leverage;
- v36 dominance value;
- v38 mechanistic-ceiling text;
- failed v32/v33 mechanism remains rejected;
- both source DOIs present;
- EL abstract <=150 words;
- EL main text <=5,000 words;
- EL title-page count fields present.

Final main push integrity workflow:

- run `37546159253`;
- status: **success**.

---

## 6. Explicitly closed scientific routes

Do not reopen before submission:

- v29 Dryad wood-decomposer transport lane;
- reef-fish third-system candidate;
- additional TP1 abundance transformations;
- TP1-vs-TP2 persistence analysis;
- first-arriver-role mechanism;
- mechanism inference from rust;
- extra third-system novelty rescue.

Why TP2 is closed:

The source analysis explicitly states that Timepoint 2 was collected during rust sampling
and the community data were overwhelmed by rust reads.

Why within-dataset mechanism is closed:

The archive lacks:

- absolute fungal abundance;
- pairwise interaction/growth matrix;
- clean pre-pathogen temporal trajectory;
- host-response measurements between inoculations.

---

## Final intake files

Use these two files for the remaining submission work:

- `AUTHOR_METADATA_INTAKE_V1.md` — one-place form for final author order, affiliations,
  corresponding-author contact, CRediT, funding, acknowledgements, competing interests,
  all-author approval and reviewer/editor conflict screening;
- `SUBMISSION_PACKAGE_MANIFEST_V1.json` — machine-readable record of the exact
  manuscript, figure artifact, integrity runs, source-data DOIs, scientific stop and
  proposed immutable submission release.

The reef-fish third-system candidate PR has been closed in accordance with the submission
stopping rule; it is not part of the current manuscript.

## 7. Remaining tasks that require external / author input

### Required before journal submission

- [ ] final author list and order;
- [ ] final affiliations;
- [ ] e-mail address for every author;
- [ ] corresponding author:
  - name;
  - full mailing address;
  - telephone;
  - e-mail;
- [ ] CRediT author contributions;
- [ ] funding statement;
- [ ] acknowledgements;
- [ ] competing-interest declaration;
- [ ] all-author approval of final manuscript;
- [x] reviewer/editor candidate pool prepared;
- [ ] final reviewer/editor conflict screen after the author list is fixed;
- [ ] opposed reviewers only for real conflicts.

### Repository/archive release

- [ ] reserve/mint a Zenodo DOI for the exact EOG submission release;
- [ ] insert that DOI into Data Accessibility;
- [ ] create immutable submission tag/release after final author approval;
- [ ] verify public archive after DOI minting.

The current GitHub repository has no published releases; release minting is intentionally
left until the manuscript/author gates are final.

---

## 8. Immediate next action

Do not run another biological analysis.

Next execution order:

1. insert final author metadata and declarations;
2. run the reviewer/editor conflict screen against that author list;
3. mint the exact submission archive DOI and immutable release;
4. insert the archive DOI into Data Accessibility;
5. final PDF/portal formatting;
6. submit to Ecology Letters;
7. if editorially rejected, move rapidly to Ecology without adding a novelty-rescue
   analysis.

## Stop condition

Both final workflows are green.

All remaining blockers are external or author-supplied. The EOG history-storage paper is
**analysis-complete and submission-ready**.
