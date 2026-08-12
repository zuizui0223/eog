# EOG core sell and novelty-maximization path

Date: 2026-08-12

## Central repositioning

Connectivity itself is not the novelty target. Existing work already establishes that accessibility, source proximity, habitat-network topology, resistance, current flow, and habitat-patch context can matter for occurrence and distribution.

The strongest defensible EOG sell is instead:

> **EOG is a reference-conditioned structural adequacy diagnostic: it asks whether occurrence-conditioned landscape configuration retains held-out information after the reference model has already represented local support, direct source proximity, and—where available—a stronger landscape-specific connectivity model.**

A shorter editorial form is:

> **Does the reference model know enough landscape geometry?**

EOG therefore should not be presented primarily as another connectivity index or dispersal proxy. It is a model-checking / incremental-information framework for structural information.

## Three diagnostic states already represented by the frozen empirical evidence

The framework should explicitly allow three outcomes.

1. **Residual structural information** — a declared structural feature adds held-out ordering or predictive information beyond the reference. The A-Islands benchmark currently provides this state relative to frozen climatic support plus nearest outer-training source distance.
2. **No added structural information / adverse increment** — the structural feature is redundant, too coarse, or variance-increasing relative to the tested reference. Tanzania primary LOSO currently provides this state after matrix-aware current flow, patch area, the area×current-flow interaction, and nearest-source distance.
3. **Indeterminate under the evaluation design** — the data or partition do not support a stable incremental conclusion. Tanzania spatial-block sensitivity currently provides this state.

This trichotomy is preferable to a universal-improvement claim because a negative result becomes a valid output of the diagnostic rather than a failure of the method.

## What must be distinguished from established spatial diagnostics

Residual spatial autocorrelation, CAR/SAR models, barrier spatial fields, and habitat-network occurrence models already address important classes of residual or network structure. EOG must therefore be described more narrowly as testing **source-conditioned, graph-mediated structural information under a held-out boundary**.

The distinctive combination is:

- occurrence anchors rebuilt from outer-training presences only;
- target rows never act as their own sources;
- intermediate nodes can create transitive connection differences even when local support and endpoint distance are similar;
- graph scenarios are predeclared rather than selected from held-out outcomes;
- the structural increment is evaluated relative to an explicit reference model;
- stronger reference content is allowed to remove the EOG increment;
- non-estimability and adverse results remain visible;
- source-to-manuscript provenance is auditable.

No individual item above should be called unprecedented. The claim is about the combined diagnostic architecture.

## Highest-return novelty additions

### Priority A — controlled simulation benchmark

Add a simulation study with known data-generating truth. This is the safest way to strengthen the method without reopening or tuning the frozen empirical outcomes.

Predeclare generative regimes such as:

- local support only;
- local support plus direct nearest-source effect;
- local support plus multi-source kernel / incidence-function-style source pressure;
- local support plus genuinely transitive stepping-stone structure;
- local support plus matrix-resistance/current-flow structure;
- graph misspecification / no structural signal.

For each regime compare a correctly cross-fitted EOG construction (outer-training anchors only) against a deliberately naive construction that allows held-out occurrence information to influence source-conditioned features. The simulation should estimate false-positive structural gain, power under transitive structure, redundancy when the reference already contains the generating connectivity process, and sensitivity to graph misspecification.

The main methodological question becomes not whether EOG can improve prediction, but whether EOG is **calibrated to detect missing structural information without manufacturing it from the held-out response**.

### Priority B — stronger A-Islands structural baselines

The most important empirical reviewer challenge is that A-Islands connected frequency may be acting as a proxy for ordinary source pressure or local network density rather than specifically for intermediate-patch configuration.

A new comparator analysis should therefore be prospectively contracted before execution and reported regardless of direction. Candidate baselines should be simple, literature-recognisable, and computed strictly from outer-training information:

- nearest occupied source distance (already controlled);
- occupied-source count or density within fixed distance bands;
- an incidence-function-style or exponential all-source pressure term with a predeclared scale rule;
- unanchored local topology such as degree / k-hop neighbourhood size / component size, where scientifically interpretable.

The strongest possible A-Islands claim would be that EOG retains held-out information after local climatic support, nearest source, **multi-source pressure, and simple unanchored topology** are represented. If it does not, the result should narrow the EOG claim rather than trigger post-hoc retuning.

### Priority C — same-system Tanzania reference ablation

The current cross-system contrast cannot establish that the stronger Tanzania reference *causes* the EOG increment to disappear because system, taxon, sample size, graph, and endpoint all differ.

A prospectively frozen explanatory ablation within Tanzania could compare, on identical outer folds and rows:

- patch area + nearest source;
- the same reference + EOG;
- patch area + nearest source + selected current flow (+ the predeclared interaction);
- the same strong reference + EOG.

If EOG helps under the weaker reference but not after current flow, the paper gains a direct within-system demonstration of **structural information saturation / substitutability**. Because the primary strong-reference Tanzania outcome is already known, this must be labelled a post-primary explanatory ablation rather than confirmatory evidence and must be reported whatever its direction.

### Priority D — constrained topological null, only if needed

A more demanding extension would test whether the A-Islands signal survives a null that preserves simpler structural summaries while disrupting multi-step configuration. Possible designs include constrained edge rewiring or other graph randomisations that preserve degree/local density as far as possible.

This should not be added unless the null can be justified clearly. A poorly chosen graph null could create more reviewer objections than it resolves.

## Reference-conditioned structural increment

The manuscript can formalise a family of estimands rather than force both benchmarks onto one numerical scale.

Let `R` denote the declared reference information and `G` an EOG structural feature. The target is the held-out information in `G` conditional on `R`:

`structural increment = held-out evidence contributed by G after R is fixed`.

A-Islands instantiates this through conditional concordance after matching on local support and nearest-source distance. Tanzania instantiates it through paired held-out loss between `R + G` and `R`.

The endpoints need not be numerically comparable. The unifying object is the **reference-conditioned question**, not a universal effect-size formula.

## Manuscript-level novelty sentence

Preferred form:

> Existing ecological models already represent habitat accessibility, occupied-source proximity, network topology and resistance-based connectivity. The unresolved question addressed here is therefore not whether connectivity matters, but whether a declared reference model has already captured the structural information available from the observed landscape. EOG provides a leakage-safe, source-conditioned held-out test of that remaining structural increment.

Avoid:

- first integration of suitability and connectivity;
- first source-conditioned connectivity model;
- first threshold-robust connectivity framework;
- first network-based occurrence model;
- dispersal or colonisation probability claims.

## Figure and story redesign

Figure 1 should lead with the reference-conditioned diagnostic, not with a new connectivity cartoon. The visual logic should be `reference information -> held-out structural probe -> three possible outcomes: residual / no gain or adverse / indeterminate`.

The cross-system figure should show A-Islands and Tanzania as **different reference tests**, not as evidence that EOG is biologically stronger in islands. The strongest editorial message is that the framework was constructed to be falsifiable and the empirical data occupied more than one diagnostic state.

## What not to do for novelty

Do not add another empirical system merely to obtain another positive result. Do not tune species-specific radii, directed edges, graph thresholds, or trait rules after seeing current outcomes. Do not convert connected frequency into a pseudo-probability of movement. Do not hide the Tanzania adverse result. These moves would increase apparent novelty at the cost of credibility.

## Decision rule

For the current paper, the highest-return path is:

1. reframe EOG as a reference-conditioned structural adequacy diagnostic;
2. add a controlled simulation benchmark if method-development scope is expanded;
3. if adding new empirical work, prioritise the A-Islands multi-source/topology comparator before any new dataset;
4. consider the Tanzania reference ablation only as explicitly post-primary explanatory evidence;
5. report all added analyses regardless of direction and preserve the existing frozen outcomes unchanged.

If the simulation establishes calibration/specificity and A-Islands retains an increment beyond multi-source pressure and simple topology, the methodological novelty becomes substantially stronger than a standard connectivity-plus-SDM paper. If those tests absorb the A-Islands signal, the paper should retain the narrower but still useful audit/reproducibility contribution rather than manufacture a stronger claim.