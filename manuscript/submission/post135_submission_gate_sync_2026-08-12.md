# Post-PR #135 submission-gate sync

Date: 2026-08-12

PR #135 merged the single prospectively authorized A-Islands island-isolation adequacy outcome into `main` and selected the Ecological Informatics submission route under the predeclared decision rule.

## Frozen scientific state

The following results are separate estimands and must remain separate in the manuscript and release package.

- Original A-Islands conditional-ordering benchmark: mean conditional concordance `0.6177465917820878`, 845 estimable taxa, species-bootstrap 95% interval `0.6086806094469824–0.626944450492123`.
- Prospective A-Islands strong-reference predictive benchmark: `C - R3` species-macro held-out log-loss difference `+0.003485181598265469`, 95% species-bootstrap interval `+0.0024664225728659645 to +0.004508216483355693`; 341 species favourable, 545 adverse; 886/886 species estimable; 4231/4430 species-folds evaluable; 712,515 held-out predictions.
- Frozen A-Islands strong-reference result fingerprint: `5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a`.
- Tanzania primary LOSO remains adverse beyond its strong matrix-aware current-flow reference: log-loss difference `+0.032113119`; result fingerprint `6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`; spatial-block sensitivity remains uncertain.

## Already incorporated on main

The merged #135 state already contains all of the following and they should not remain described as pending scientific work:

- complete-manuscript Abstract, Introduction, Methods, Results and Discussion rewritten around reference-conditioned structural adequacy;
- explicit separation of the original A-Islands conditional-ordering estimand from the prospective `C - R3` predictive estimand;
- the adverse A-Islands strong-reference result in the manuscript, highlights and cover letter;
- verified closest-prior island and general connectivity references, including the post-outcome bibliographic correction log;
- machine-readable Table 3 / Table S1 and their metadata regenerated from the frozen strong-reference result;
- Figure 5 audit provenance regenerated for the updated result-table contract;
- offline submission-package builder/tests updated to require the new A-Islands result fingerprint;
- main Package checks green after merge commit `41b3d449c4a2cfe05162e742d197935ba1568ae2`.

## Remaining machine/editorial work

The remaining repository-controlled work is primarily presentation rather than analysis:

1. revise Figure 1 so the visual lead is `declared reference → held-out structural probe → residual / adverse-or-redundant / indeterminate`;
2. revise the A-Islands result figure so the original conditional-ordering result and strong-reference predictive result are both visible but never placed on a common effect-size axis;
3. add a reference-tier panel for R0/R1/R2/R3/C as explanatory context, explicitly marking `C - R3` as the only primary prospective extension contrast;
4. retain Tanzania as the external strong-reference boundary and keep the spatial-block uncertainty visible;
5. run final automated figure sync/fingerprint tests and then human journal-size/grayscale/colour-vision QA.

No further biological outcome analysis is authorized for novelty rescue.

## Remaining human/release gates

Still genuinely unresolved:

- final author order, affiliations, corresponding author and CRediT roles;
- funding, competing interests, ethics/permit applicability and originality confirmations;
- author approval of the generative-AI disclosure;
- live Ecological Informatics Guide-for-Authors verification on submission day;
- final human visual QA;
- Zenodo DOI reservation, identifier-only release PR, tag `v0.1.0`, GitHub Release and public archive verification.
