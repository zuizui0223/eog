# Observation-process routing for future BAM targets

## Joint world

Let the current ecological survivor set be (S_E) and the admitted assay-process
universe be (W_O).

The relevant joint hypotheses are

[
S_J = S_E \times W_O.
]

A future decision target depends on ecological world (	heta),

[
T(\theta,o)=T(\theta),
]

while an assay action (a) produces an outcome determined by both:

[
Y_a = g_{a,o}(\theta).
]

The observation process is therefore nuisance uncertainty, but it can change whether
ecological hypotheses are distinguishable.

## T1 — Repetition under fixed deterministic systematic bias

For one assay (a), suppose the same observation world (o) applies to repeated
measurements and outcomes are deterministic.

One assay returns

[
g_{a,o}(\theta).
]

Two repeats return

[
(g_{a,o}(\theta),g_{a,o}(\theta)).
]

The map (y\mapsto(y,y)) is one-to-one.  Therefore the induced partition of joint
hypotheses is unchanged, and so is every robust target-discordant pair split.

The Phase-VII audit found **0 violations**.

This identity does not apply to independent random error.

## T2 — Target identification does not require observation-world identification

Let (Q) be a selected set of assay actions.  Define the joint observed signature

[
\sigma_Q(\theta,o)
=
(g_{a,o}(\theta))_{a\in Q}.
]

The future target is robustly identified by (Q) exactly when

[
\sigma_Q(\theta_1,o_1)
=
\sigma_Q(\theta_2,o_2)
\Longrightarrow
T(\theta_1)=T(\theta_2)
]

for all active joint hypotheses.

Nothing in this condition requires (o_1=o_2) to be inferable.

Therefore multiple assays can be **target-self-calibrating**: their joint pattern can
identify the future target even while assay-process identity remains unresolved.

The S11 climate fiber is a frozen example.  `A_level + antagonist_excluded` robustly
identifies the climate decision across both admitted assay worlds without explicit
calibration.

## T3 — When explicit calibration is necessary

Let (Q_A) denote the complete assay-only library.

If there exists a target-discordant joint pair

[
(\theta_1,o_1),(\theta_2,o_2)
]

whose observed signature is equal under **all** assay-only channels, then no assay-only
subset can identify the target.

An observation-process calibration action (c(o)) can separate such a pair when
(o_1\neq o_2).  It is useful only together with ecological assays sufficient to
separate remaining same-observation-world target disagreement.

Phase VII found assay-only impossibility followed by calibration rescue in 2 climate,
2 biotic-stress and 3 barrier-restoration unique fibers.

## Evidence-routing consequence

The full routing logic is now:

1. Is the future target already invariant over the current ecological survivor fiber?
2. If not, can present-state evidence separate target-discordant ecological aliases?
3. If not, which latent parameter/challenge channels are required?
4. Under the admitted observation-process universe, are those channels robustly
   interpretable?
5. If not, can multiple assays self-calibrate the target?
6. If not, explicit observation-process calibration is required.

This hierarchy avoids the default assumption that more repetitions of the same
measurement type will solve a structural ambiguity.

## Boundary

The identities above are finite-partition logic.

The BAM-specific contribution is their use inside an occurrence-conditioned
A/B/M survivor fiber whose scientific target is a prospectively frozen ecological
counterfactual.

The observation worlds remain synthetic and finite.
