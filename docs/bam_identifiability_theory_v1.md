# Finite BAM identifiability — exact survivor-set theorems

## Setup

Let (X) be a finite node universe. Each declared candidate world is

[
w=(A_w,B_w,M_w,	au_w,	heta_w),
]

where:

- (A_wsubseteq X): abiotic viability;
- (B_wsubseteq X): biotic permissibility;
- (M_wsubseteq X): source-conditioned movement accessibility;
- (	au_w): first-arrival state over (X);
- (	heta_w): optional parameter labels.

The realised distribution is

[
G_w=A_wcap B_wcap M_w.
]

Let (w_*) denote the generating truth.

Two worlds are **BAM-state equivalent** when

[
A_w=A_*,
quad
B_w=B_*,
quad
M_w=M_*,
quad
	au_w=	au_*.
]

Parameter labels are not part of BAM-state identity.

---

## T1 — positive-only survivor characterization

With complete positive occurrence evidence (G_*), a candidate survives iff every observed positive is contained in its realised distribution:

[
S_0(w_*)=
{w:G_*subseteq G_w}.
]

### Proof

Positive-only compatibility requires

[
xin G_w
]

for every observed positive (xin G_*). This is exactly the set-inclusion statement

[
G_*subseteq G_w.
]

No information about (Xsetminus G_*) is supplied. Therefore no candidate can be rejected for predicting extra occupied nodes outside (G_*). QED.

### Corollary — positive-superset ceiling

If

[
G_*subseteq G_w,
]

then no amount of valid positive-occurrence sampling drawn from (G_*) can eliminate (w).

This is not a sampling-size limitation. It remains true under complete observation of all positives.

---

## T2 — complete-map fiber

Suppose every node is surveyed perfectly, so the evidence contains:

- positives (G_*);
- negatives (Xsetminus G_*).

Then

[
S_1(w_*)=
{w:G_w=G_*}.
]

### Proof

Positive evidence gives

[
G_*subseteq G_w.
]

Perfect negatives require

[
G_wcap(Xsetminus G_*)=arnothing,
]

which is equivalent to

[
G_wsubseteq G_*.
]

Both inclusions together imply

[
G_w=G_*.
]

QED.

### Consequence

A complete distribution map identifies (G), not necessarily the decomposition

[
G=Acap Bcap M.
]

The intersection map is generally many-to-one.

---

## T3 — progressive evidence fibers

Add evidence in the frozen order.

### E2 — occupied-node arrival state

[
S_2=
left{
win S_1:
	au_w|_{G_*}=	au_*|_{G_*}
ight}.
]

### E3 — direct abiotic state

[
S_3=
{win S_2:A_w=A_*}.
]

### E4 — direct biotic state

[
S_4=
{win S_3:B_w=B_*}.
]

### E5 — direct movement-accessibility state

[
S_5=
{win S_4:M_w=M_*}.
]

### E6 — complete arrival state

[
S_6=
{win S_5:	au_w=	au_*}.
]

Each step is simply an intersection between the previous survivor set and a newly observed equality constraint.

---

## T4 — monotone contraction

Therefore

[
S_6subseteq
S_5subseteq
S_4subseteq
S_3subseteq
S_2subseteq
S_1subseteq
S_0.
]

Adding valid evidence cannot restore a previously contradicted world.

This monotonicity is structural and does not depend on the simulation parameter values.

---

## T5 — complete BAM-state fiber

At E6, a candidate survives iff:

[
A_w=A_*,
quad
B_w=B_*,
quad
M_w=M_*,
quad
	au_w=	au_*.
]

Hence

[
S_6=[w_*]_{m BAM},
]

the exact BAM-state equivalence class of truth.

Parameter aliases with identical finite BAM state remain unresolved, correctly.

This explains why v2.3 reached 100% BAM-state identification while parameter-label identification remained below 100%.

---

## T6 — exact identifiability criterion

At any evidence level (E), BAM state is identified iff every surviving world lies in one BAM-state equivalence class:

[
left|
{
[w]_{m BAM}:win S_E
}
ight|=1.
]

A single surviving parameter label is unnecessary. Conversely, multiple surviving parameter labels do not imply mechanistic ambiguity when they encode the same BAM state.

---

## T7 — diagnostic measurement as a hitting-set problem

Let:

- (S) be the current survivor set;
- (Tsubseteq S) be the target fiber to retain;
- each possible direct measurement (m) eliminate the candidate subset (D_msubseteq S).

A measurement set (Q) reproduces the target fiber exactly iff:

[
D_mcap T=arnothing
quad	ext{for all }min Q,
]

and

[
Ssetminus T
subseteq
igcup_{min Q}D_m.
]

Thus diagnostic measurement design is a finite hitting/set-cover problem over nuisance worlds.

The exact minimum diagnostic design is

[
Q^*=
argmin_Q |Q|
]

subject to the coverage condition above.

### Important correction

The earlier BAM simulation code used deterministic greedy split-maximizing measurement selection. Those counts are valid **constructive upper bounds** on the number of measurements needed, but are not automatically exact minima.

The theory line therefore uses an exact bit-mask dynamic-programming solver and will only use the word *minimum* when equality with the exact solver has been verified.

---

# Interpretation of the simulations

The v3 simulation result is now explained by these identities rather than by an empirical coincidence.

Across 12 activation-qualified virtual systems and 768 truths:

- E0 identified 0 BAM states uniquely;
- E1 identified 25;
- E2 identified 159;
- E3 identified 275;
- E4 identified 565;
- E5 identified all 768;
- E6 retained the same complete BAM-state identification.

These numbers are contingent on the declared virtual universes.

The **ordering and survivor-set characterizations** above are exact under the evidence contracts.

The scientifically important distinction is therefore:

> The finite-world theorem states what information each evidence type can possibly remove. The simulations show how often those information differences actually occur in heterogeneous BAM landscapes.

---

# Claim boundary

These theorems do not show that real ecological A, B, M or movement arrival are perfectly observed.

They establish a conditional identifiability result:

> Given a declared finite BAM world universe and explicit evidence semantics, EOG's survivor set is exactly the fiber of worlds that agree with the observed information.

A surviving world is not thereby established as historical truth.
