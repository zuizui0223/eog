# BAM decision robustness margin v1 — frozen result

## Result

The preregistered same-G completion audit completed with all theorem checks passing.

- protocol commit: `85c8034bd89b80657e34d2b3d3c04a1d9bdaceac`;
- workflow run: `36669307476`;
- artifact: `11077279261`;
- artifact digest: `sha256:38163eafd3438c575c31473511b3f24d261697d68d41e5779ada7e1da805c0c4`;
- result fingerprint: `ffd0d11bbe75d4e27cc8918ab77a95e991ab52b43bd39ee83ce81b8a3bd52050`;
- exhaustive small-universe theorem violations: **0**;
- 12-system / 768-truth theorem violations: **0**.

There were **129 unique E1 same-G survivor fibers** in the frozen deterministic panel.

## The first correction to Phase II

Phase II showed high binary decision identifiability inside the declared BAM candidate
universes:

- release A: 652/768;
- release B: 705/768;
- release M: 732/768.

The new theorem shows that this is a **finite-universe certificate**, not a property of
current (G) alone.

For any proper (G\subset X), the unrestricted set of all BAM decompositions satisfying

[
A\cap B\cap M=G
]

contains both binary outcomes for every single-axis release.

Therefore every declared-universe identified decision with proper (G) can be made
unresolved by expanding the universe far enough.

The relevant question becomes not whether an opposite world exists in principle, but:

> **How far outside the declared world family is the nearest same-G world that reverses
> the decision?**

## Exact completion margins

Among proper-G decisions that were identified inside the frozen candidate universe:

| release | identified proper-G truths | margin 1 | median margin | mean | maximum |
|---|---:|---:|---:|---:|---:|
| A | 618 | 439 (71.0%) | 1 | 1.54 | 13 |
| B | 671 | 263 (39.2%) | 2 | 4.19 | 29 |
| M | 698 | 281 (40.3%) | 2 | 3.61 | 31 |

Thus many apparently resolved decisions were only one axis-node state change away from
an undeclared same-G reversal.

But the distribution also had a substantial upper tail, especially for B and M.

## A strong asymmetry: no expansion versus expansion

The direction of the current decision explains much of the margin structure.

### Current decision: no expansion

Excluding the 34 full-(G) truth cases where no outside node exists:

- release A: all 482 finite margins were 1 or 2; median 1;
- release B: all 277 finite margins were 1 or 2; median 1;
- release M: all 321 finite margins were 1 or 2; median 1.

A no-expansion conclusion is reversed as soon as one outside-(G) node becomes a
release witness.  Only the local BAM state at that one node must be changed.

### Current decision: expansion

Expansion can be much harder to reverse:

- A: median 1, maximum 13;
- B: median 5, maximum 29;
- M: median 4, maximum 31.

For an expansion conclusion, every outside-(G) node already supported by both retained
axes is a witness.  Reversing the decision requires destroying **all** such witnesses.

This is an exact set-theoretic asymmetry:

[
\rho_{\mathrm{true}\rightarrow\mathrm{false}}
=
|R\setminus G|,
]

where (R) is the released map, whereas

[
\rho_{\mathrm{false}\rightarrow\mathrm{true}}
]

requires only the cheapest construction of one new outside-(G) witness.

The first quantity can scale with landscape size; the second is locally bounded by the
three BAM axis states at one node.

## New interpretation

The finite-BAM programme now has three distinct levels of robustness:

1. **evidence robustness** — which worlds survive the observations?;
2. **target robustness inside the declared universe** — do all survivors agree on the
   counterfactual decision?;
3. **universe-boundary robustness** — how far must the BAM world family be expanded
   before an opposite decision becomes possible?

A decision should therefore not be described simply as “identified” without also
specifying the declared world universe.

## What this does not mean

The unrestricted completion envelope intentionally includes biologically implausible
decompositions.  It is a logical stress test, not a proposed ecological prior.

A margin of one means only that one binary A/B/M node state separates the declared
fiber from a same-G counterexample.  It does not mean that state change is likely or
biologically defensible.

The next scientific step is therefore to replace unrestricted Hamming completion by
**prospectively declared ecological expansion operators**: additional plausible niche
states, interaction states and movement states.  Only then can universe-boundary
robustness be interpreted ecologically rather than logically.
