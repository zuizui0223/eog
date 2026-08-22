# Yale–Myers wood-frog fresh paired complementarity attempt

This directory freezes one fresh temporal test of EOG Layer B in the 64-pond
*Rana sylvatica* monitoring system of Rowland et al. (2022). It is
candidate-specific validation infrastructure, not a new ecological operator and
not an API/CLI change.

Dryad version `162105` contains four independently stored objects. The preflight
uses the official version redirect and tokenized file manifest, keeps all signed
URLs in memory, and downloads only `distance.mat.csv`, `pondinfo.csv`, and
`README_file.rtf`. It verifies the physical `woodfrogdata.csv` header with 138
one-byte Range requests and stops at the first CR. No response row or value is
opened. The dynamically assembled whole-version ZIP is never downloaded.

The endpoint is observed annual breeding-count reappearance: a pond has released
finite `Avg.RASY.Count == 0` at year *t* and either remains zero or becomes
positive at the consecutive observed year *t+1*. This is not latent occupancy,
physical immigration, parentage, or a reconstructed colonization history. The
source claim is explicitly conditional on current positive ponds inside the
closed 64-pond registry; external sources are not added or inferred.

The first 11 transitions (2000→2001 through 2010→2011) are calibration; the last
nine are held out and scored by target year. Published materials do not provide
split-specific endpoint counts, so preflight preserves `uncertain_pre_response`
and authorizes only an exact-count-first once-only run. Count failure means zero
model fits and zero heldout scores.

The primary contrast is a frozen strong random forest with conventional static
pond, annual environmental, distance, and lagged source-state predictors versus
the identical learner plus the unchanged ten-column
`symmetric_world_support_summary_v1` Layer-B block. Exact pond IDs and exact
world IDs are never supervised features. Favorable, null, and adverse results are
all terminally acceptable.

Outcome access requires a second commit adding only
`OUTCOME_AUTHORIZED_ONCE.json`. That marker binds the already-green parent commit,
contract, runner, preflight fingerprint, and 16-key authorization result. The
outcome workflow then performs one full response download, never retries, and
never redesigns after opening.
