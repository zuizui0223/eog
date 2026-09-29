# BAM inverse-identifiability — journal positioning v2

## Current recommendation

### Primary: Journal of Biogeography

The current manuscript is best positioned as a **biogeographic theory + known-truth
identifiability paper**.

Why it fits:

- the central object is geographic distribution under BAM;
- the paper asks how distributional evidence maps back to ecological mechanism;
- the strongest result is conceptual, not software engineering;
- the paper contains exact theory, deterministic and stochastic simulations,
  landscape generality and explicit biological interpretation;
- the current Journal of Biogeography scope explicitly welcomes theoretical approaches
  and papers that articulate conceptual advances in biogeography.

The title, abstract and discussion should therefore foreground:

1. BAM as a forward distribution theory;
2. inverse partial identification;
3. the restrictiveness–ambiguity result;
4. temporal and direct mechanism evidence;
5. diagnostic evidence design.

EOG v3 should remain the implementation, not the title-level novelty.

## Secondary: Methods in Ecology and Evolution

MEE remains plausible only under a different manuscript center.

Its current Research Article criteria emphasize:

- a new ecological/evolutionary method;
- broad applicability across taxa/systems;
- simulation or benchmark testing for computational methods;
- clear demonstration of what the method enables.

The current repository can satisfy much of that evidence base:

- deterministic benchmark panel;
- independent stochastic generator;
- multilandscape panel;
- exact finite theory;
- public v3 API;
- robust/adaptive evidence-design functions.

However, an MEE version would need to make the **method/API workflow** co-primary:

declare worlds -> condition on evidence -> retain fibers -> design next evidence.

That would be a different paper emphasis from the current BAM inverse-identifiability
draft.

## Why not mix both centers in one submission

Trying to write one paper simultaneously as:

- a BAM conceptual theory paper;
- a generic EOG software paper;
- a distribution-model comparison paper

would dilute the strongest contribution.

The current branch therefore uses this boundary:

> Main paper = BAM inverse identifiability.

> EOG v3 = implementation and reproducibility layer.

> EOG-WF predictive complementarity = separate closed manuscript.

## Current manuscript format target

For a Journal of Biogeography-facing draft:

- concise conceptual Introduction;
- formal Theory before simulation details;
- Methods centered on known-truth systems;
- Results ordered by inferential question rather than software version;
- Discussion centered on distribution-to-process inference;
- figures organized around identifiability rather than algorithm performance.

## Journal-switch trigger

Consider reframing for MEE only if one or more of the following becomes central:

1. a real empirical application demonstrates the complete evidence-design workflow;
2. EOG v3 becomes the primary reusable product;
3. the robust/adaptive planning algorithm is expanded as a broadly applicable method;
4. the manuscript question shifts from "what can distributions identify?" to
   "how should ecologists design evidence to discriminate process worlds?"

Until then, keep Journal of Biogeography as the primary manuscript route.

## Submission boundary

Do not add a weak empirical illustration only to satisfy a perceived journal norm.

A real-data illustration should be included only if it has a separately frozen
evidence contract and demonstrates the inverse-fiber logic without pretending to know
historical truth.
