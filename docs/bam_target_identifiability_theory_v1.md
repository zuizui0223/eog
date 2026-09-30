# Target-specific identifiability over finite BAM survivor fibers

## Purpose

The frozen BAM inverse-identifiability paper studies whether evidence identifies the
underlying BAM state.  The counterfactual successor requires a more general object:
whether evidence identifies a **declared target function of the surviving BAM worlds**.

This distinction formalizes why mechanism nonidentification need not imply forecast or
decision nonidentification.

## 1. Survivor fiber

Let the declared finite world universe be (W), and let evidence (e) leave the exact
survivor fiber

[
S(e) subseteq W.
]

No member of (S(e)) is promoted to historical truth merely because it survives.

## 2. Target equivalence

Let

[
T:Wightarrowmathcal Y
]

be any declared inferential target.

Examples include:

- the complete BAM state;
- an exact counterfactual occupied map after releasing one mechanism axis;
- a binary statement such as whether the released system expands beyond current (G);
- later, any preregistered management-relevant loss or action class.

Define target equivalence by

[
w sim_T v
quadLongleftrightarrowquad
T(w)=T(v).
]

The target-equivalence class of truth (w_*) is

[
[w_*]_T
=
{win W:T(w)=T(w_*)}.
]

## T1 — Target-identification criterion

The target (T) is identified by current evidence if and only if

[
S(e)subseteq[w_*]_T.
]

Equivalently,

[
|T(S(e))|=1.
]

Therefore the survivor fiber itself may be non-singleton while the target is exactly
identified.

### Consequence

Full BAM-state identification is sufficient for identification of any deterministic
function of BAM state, but it is not necessary.

The frozen counterfactual benchmark provides direct examples of the converse failure:
many truth cases retain multiple BAM states while their counterfactual or decision
target is already invariant.

## 3. Target refinement

Let (U) and (T) be two targets.  Say that (U) is finer than (T) when there exists
a deterministic mapping (f) such that

[
T=fcirc U.
]

Then

[
U(w)=U(v)Longrightarrow T(w)=T(v).
]

Hence every (U)-equivalence class is contained in a (T)-equivalence class.

For the frozen BAM successor,

[
	ext{BAM state}
ightarrow
	ext{exact counterfactual map}
ightarrow
	ext{binary release decision}
]

is precisely such a refinement chain.

## T2 — Identification monotonicity under target coarsening

If (U) is finer than (T), then identification of (U) implies identification of
(T).

Proof: if (U) is constant on (S(e)), then (T=f(U)) is also constant on (S(e)).

The converse need not hold.

This yields three distinct inferential states:

1. **mechanism identified** — the survivor fiber lies in one BAM-state class;
2. **mechanism unresolved but target identified** — multiple BAM states survive but
   all lie in one (T)-class;
3. **target unresolved** — the survivor fiber intersects multiple (T)-classes.

## 4. Truth-relative evidence burden

Fix a truth (w_*), current survivor fiber (S), and a finite direct-measurement
library (mathcal M).

Each truth-consistent measurement (m) eliminates a set

[
D_msubseteq S
]

of survivor worlds that disagree with the observed truth value.

For target (T), only worlds with the wrong target need to be removed:

[
N_T
=
{win S:T(w)
eq T(w_*)}.
]

A measurement set (Qsubseteqmathcal M) is target-sufficient when

[
N_T
subseteq
igcup_{min Q}D_m.
]

Define the exact target burden

[
b(T)
=
min
left{
|Q|:
N_Tsubseteqigcup_{min Q}D_m
ight},
]

when such a set exists.

This is a finite set-cover/hitting-set problem.  The optimization algorithm itself is
not claimed as novel.

## T3 — Evidence-burden monotonicity under target coarsening

If (U) is finer than (T), then

[
N_Tsubseteq N_U.
]

Therefore, under the same truth-consistent measurement library,

[
oxed{b(T)leq b(U)}.
]

Any measurement set sufficient to eliminate all (U)-discordant worlds is
automatically sufficient to eliminate the subset of (T)-discordant worlds.

For the frozen counterfactual hierarchy,

[
oxed{
b(	ext{binary decision})
leq
b(	ext{exact counterfactual map})
leq
b(	ext{full BAM state})
}.
]

The 12-system / 768-truth benchmark audited this relation with **0 violations**.

## 5. Decision-sufficient survivor fibers

Call a current survivor fiber **decision-sufficient for (T)** when

[
S(e)subseteq[w_*]_T
]

even if the full BAM state is unresolved.

This is not a statement that mechanism uncertainty is unimportant in general.
It states only that the remaining mechanism uncertainty is irrelevant to the
**declared target**.

A survivor fiber may therefore be:

- BAM-state unresolved but exact-counterfactual invariant;
- exact-counterfactual unresolved but binary-decision invariant;
- binary-decision unresolved.

The frozen benchmark observed all three states.

## 6. Why this matters for evidence design

If the scientific decision concerns (T), designing observations to identify the
entire BAM state can collect information that cannot change (T).

Target-specific evidence design instead asks:

> Which surviving worlds disagree about the target, and what is the smallest admissible
> evidence set that can eliminate those target-discordant worlds?

This gives a formal stopping rule:

> **stop collecting mechanism-discriminating evidence when the surviving world fiber is
> already contained within one equivalence class of the declared decision target.**

This stopping rule is conditional on the declared finite universe, target and
measurement library.

## 7. Frozen empirical-theory correspondence

In the preregistered 768-truth counterfactual benchmark:

- full BAM state was identified in 25/768 truths;
- the joint exact three-probe counterfactual signature was identified in 174/768;
- all three binary release decisions were identified in 636/768;
- among the 743 BAM-state-nonidentified truths, 149 were exact-counterfactually
  invariant across all three probes, 462 retained exact-map disagreement but no binary
  decision disagreement, and 132 retained at least one binary decision disagreement.

Thus mechanism, counterfactual-map and decision identifiability are empirically distinct
partitions of the same frozen BAM survivor fibers.

## Claim boundary

These identities are generic finite-set consequences once (W), (S(e)), (T) and
the evidence library are declared.  Novelty is not claimed for equivalence relations,
set cover, target coarsening, value of information or optimal experiment design.

The ecological contribution under investigation is the use of these target-specific
identifiability layers inside an occurrence-conditioned BAM inverse problem, where
different ecological mechanisms can generate the same current distribution but need
not imply the same counterfactual ecological conclusion.
