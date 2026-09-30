# BAM inverse-identifiability — reviewer attack / defense matrix v2

## Purpose

This document is a manuscript-development tool. It separates:

- criticisms already answered by frozen theory or simulations;
- criticisms that require wording changes;
- criticisms that remain genuine limitations.

Do not turn every criticism into a new analysis. The current paper should remain focused
on inverse BAM identifiability.

## Attack 1 — "The set theory is obvious"

### Likely criticism

The statements

- positive evidence leaves supersets compatible;
- complete presence/absence leaves equal realised supports;
- adding equality constraints contracts a set;

may be seen as mathematically elementary.

### Defense

Agree that the algebra is elementary.

The contribution is not mathematical difficulty. It is the ecological consequence of
writing the BAM inverse problem in this exact form and then testing how large the
resulting fibers remain in heterogeneous known-truth systems.

The paper must therefore pair each theorem with a non-obvious empirical consequence:

- complete positives: 0/768 unique BAM states;
- stronger ecological restriction can increase ambiguity;
- unordered history adds no strict gain in the frozen stochastic programme;
- first-occurrence timing does add information;
- direct A/B/M evidence contracts the fiber at sharply different rates.

### Writing rule

Do not call the set identities "deep" or "new mathematics".

Call them **exact finite identifiability statements** whose ecological consequence is
non-trivial.

## Attack 2 — "BAM confounding is already known"

### Likely criticism

Soberón & Osorio-Olvera already showed that movement and niche effects may be difficult
to disentangle.

### Defense

Acknowledge this directly.

The present paper does not claim first recognition of confounding.

The added object is the exact inverse evidence fiber:

- what positive evidence leaves;
- what complete G leaves;
- what direct A/B/M evidence removes;
- when BAM state versus parameter label is identified;
- how support nesting orders ambiguity;
- how diagnostic measurements hit the residual fiber.

### Writing rule

The Introduction must say:

> Our contribution is not to rediscover general equifinality or BAM confounding.

This sentence is already in manuscript V3.

## Attack 3 — "The simulations are constructed to produce non-identification"

### Likely criticism

The candidate universe may have been chosen so that supersets and aliases necessarily
exist.

### Defense already present

Three independent safeguards exist.

1. The first strong recovery claim was explicitly allowed to fail and did fail.
2. The deterministic generality panel used 12 frozen seeded systems with no
   post-result replacement.
3. The stochastic challenge used an independently implemented NumPy/stdlib generator
   forbidden from importing EOG reconstruction modules.

The 8-landscape extension also retained two DESIGN_STOP systems instead of replacing
them.

### Remaining limitation

The candidate universes are still finite and deliberately structured to span A/B/M
contrasts. They are not random samples from all plausible ecological process spaces.

### Writing rule

State the finite-universe boundary prominently. Do not generalize 0/768 to all real
ecological systems.

## Attack 4 — "0/768 is guaranteed by the way candidate worlds are nested"

### Likely criticism

If every truth has a positive-superset alternative, positive-only non-identification
is built into the candidate grid.

### Defense

This is partly true and should not be hidden.

The theorem explains exactly when positive-only identification is impossible. The
simulation question is therefore not whether the theorem can be violated, but how
often its premise occurs under heterogeneous BAM constructions.

The important empirical results are:

- positive-superset ambiguity occurred throughout the deterministic panel;
- support nesting produced zero violations in 304 strict inclusion pairs;
- independent stochastic generation reproduced the same ceiling;
- joint A+B+M restriction generated the smallest support and maximum ambiguity.

### Writing rule

Do not present 0/768 as a mysterious empirical discovery independent of the theorem.

Present it as **the prevalence of the theorem's non-identifiability condition in the
frozen BAM panels**.

## Attack 5 — "Why is stronger restriction causing more ambiguity surprising?"

### Likely criticism

Once set inclusion is written down, the inverse ordering is immediate.

### Defense

Yes, the proof is immediate.

The surprise is ecological, not algebraic: stronger joint limitation narrows the
realised distribution, which might intuitively seem more diagnostic, but positive-only
data provide fewer exclusion witnesses against permissive alternatives.

This is precisely why Figure 2 should combine:

- the exact inclusion identity;
- the 304/304 audit;
- the joint_ABM example with support 33 and 32 compatible worlds;
- distance/barrier-limited examples with support 96 and only 4 compatible worlds.

### Writing rule

Call this a **counterintuitive ecological consequence of an exact inclusion relation**.

## Attack 6 — "Complete presence/absence and direct A/B/M maps are unrealistic"

### Likely criticism

Perfect detection and direct mechanism-state maps are idealized.

### Defense

Agree.

These are information contracts used to locate identifiability boundaries. The paper
does not claim they are straightforward field measurements.

Their purpose is to answer:

> If this information were available perfectly, what ambiguity would remain?

This distinguishes information insufficiency from practical measurement difficulty.

The separate EOG observation-world work shows why imperfect detection cannot simply be
treated as exact absence, but that material should remain supplementary/background in
this manuscript.

### Writing rule

Use "idealized evidence contract" consistently.

## Attack 7 — "The evidence ladder order is arbitrary"

### Likely criticism

A -> B -> M ordering could create the apparent importance of later variables.

### Defense

The manuscript does not infer causal importance from the sequential order alone.

The preregistered claim that M is always the final bottleneck was explicitly REFUTED.

The exact targeted-measurement audit also treats A, B and joint A+B as explicit
diagnostic design problems rather than relying only on the sequential ladder.

### Remaining possible improvement

A supplementary order-sensitivity table could be useful, but it is not required for
the main theorem because the exact fibers themselves are order-independent equality
constraints when all components are observed.

Do not add a large permutation analysis unless reviewers require it.

## Attack 8 — "Why not Bayesian model probabilities?"

### Likely criticism

A probabilistic model comparison could assign posterior weights rather than returning a
set of compatible worlds.

### Defense

The inferential target here is different.

The paper asks whether evidence logically distinguishes candidate mechanisms under
declared support/equality contracts. A posterior can still distribute probability over
non-identifiable alternatives, but weighting does not erase the structural fact that
multiple mechanisms are observationally equivalent under the evidence.

The survivor fiber is therefore a diagnostic object complementary to probabilistic
weighting, not a replacement for Bayesian inference.

### Writing rule

Avoid claiming superiority to Bayesian methods.

## Attack 9 — "Hitting-set design is standard"

### Likely criticism

Set cover / hitting set is not novel.

### Defense

Agree explicitly.

The novelty is not the optimizer. It is deriving the BAM-specific survivor fiber and
measurement disagreement sets, then showing exact finite programme-specific bounds.

### Writing rule

The manuscript V3 already states:

> Hitting-set optimization itself is not novel.

Keep that sentence.

## Attack 10 — "The direct measurement bounds are over-sold"

### Likely criticism

A=1, B=2, A+B=3, M=2 may look like universal ecological rules.

### Defense

They are not universal.

They are exact maxima inside the frozen 12-system / 768-truth finite programme.

### Writing rule

Always attach "within the frozen programme" or "programme-specific".

Do not put the raw numbers in the title.

## Attack 11 — "Temporal evidence still never identifies truth, so why emphasize it?"

### Likely criticism

If unique truth recovery remains zero, temporal evidence may appear weak.

### Defense

The goal is not forced singleton recovery.

Temporal evidence demonstrates the central principle that **evidence type matters more
than quantity of the same evidence**.

Unordered accumulated positives had no strict gain; first-occurrence timing refined
8 static classes into 20 temporal classes and strictly contracted 256/384 runs.

That is a clean movement-information result even though full identification remains
unavailable.

## Attack 12 — "No empirical species example"

### Likely criticism

Theory + simulations may feel detached from field ecology.

### Current status

This is the largest remaining manuscript-level vulnerability.

### Options

1. Submit as theory + principled known-truth method evaluation.
2. Add one real-data illustration only if it can be preregistered and interpreted as
   an illustration of survivor fibers, not as proof of true mechanism recovery.
3. Keep real data out of the main paper and make the concrete field implications
   explicit in Discussion.

### Current recommendation

Do **not** opportunistically add an empirical system merely to make the paper look more
complete.

The present paper already has:

- exact theory;
- deterministic generality;
- independent stochastic validation;
- multilandscape validation;
- explicit refutations;
- software implementation.

If a real example is added, it should be a separately frozen illustration with a clear
evidence contract.

## Attack 13 — "The EOG branding distracts from BAM theory"

### Likely criticism

The manuscript could look like software marketing.

### Defense

Keep EOG v3 secondary.

Main novelty sentence should mention BAM inverse identifiability, not EOG.

Software appears in Methods/Reproducibility and late Discussion as implementation.

## Attack 14 — "Why Journal of Biogeography rather than a methods journal?"

### Current assessment

The scientific center is:

- geographic distributions;
- BAM;
- movement and accessibility;
- distribution-to-process inference;
- biogeographic identifiability.

That supports a biogeography venue.

A methods venue becomes more natural only if:

- software workflow;
- empirical applications;
- robust/adaptive evidence planning

are made co-primary.

## Terminal manuscript weaknesses after current analyses

### Already defended

- generic BAM confounding prior art;
- finite-set monotonicity;
- independent generator concern;
- positive-superset ceiling;
- stochastic generality;
- temporal evidence distinction;
- hitting-set exactness;
- programme-specific measurement bounds.

### Genuine remaining limitations

1. finite candidate universes;
2. idealized direct evidence contracts;
3. no named-species empirical illustration;
4. finite landscape panel rather than a probabilistic sample of landscapes;
5. exact state compatibility rather than a fully probabilistic observation model in
   the main BAM theorem.

These should be stated, not hidden.
