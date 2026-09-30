# BAM counterfactual identifiability v1 — frozen result

## Result

The preregistered 12-system / 768-truth benchmark completed successfully.

Authoritative evidence:

- protocol commit: `fad0a6e931bac9012fb978d293dadac4d041d012`;
- workflow run: `36668189863`;
- artifact: `11076812787`;
- artifact digest: `sha256:af45c87a8c49f7dd56f8c78bb17e974c2d64c8c51d56092479e3d9a4451d0a44`;
- result fingerprint: `77314699090fd3b0a19066363eab0589c3a0c89ac41aabbce49873c84b468172`.

All four preregistered hypotheses were **SUPPORTED**.  The target-coarsening burden
contract had **0 violations**.

## The main biological-inference result

Complete current presence/absence identified the full BAM state in only **25/768
(3.3%)** truth cases.

But full mechanism identification was usually unnecessary for the declared
counterfactual target:

- the joint exact signature of all three release probes was identified in
  **174/768 (22.7%)** truths;
- all three binary release decisions were identified in **636/768 (82.8%)** truths;
- only **132/768 (17.2%)** truths retained ambiguity in at least one binary decision.

Thus the three targets form a sharply different identifiability hierarchy:

```text
full BAM mechanism             25 / 768    3.3%
exact three-probe effects     174 / 768   22.7%
three binary decisions        636 / 768   82.8%
```

## What happened inside the 743 mechanism-nonidentified truths

The nonidentified set was not homogeneous.

1. **149/743 (20.1%) — counterfactually harmless even at exact-map level.**
   The full BAM state was unresolved, but all three exact release maps were already
   invariant across the survivor fiber.

2. **462/743 (62.2%) — map uncertainty without decision uncertainty.**
   At least one exact counterfactual map differed among surviving BAM worlds, but all
   three yes/no release-expansion decisions were identical.

3. **132/743 (17.8%) — decision-relevant ambiguity.**
   At least one frozen binary release decision changed across the survivor fiber.

This separation is the main successor result.  Mechanism ambiguity, forecast-map
ambiguity and decision ambiguity are distinct states.

## Which axis produced unresolved counterfactuals?

Exact-map divergence among the 743 BAM-nonidentified truths:

| divergent release probes | truth cases |
|---|---:|
| none | 149 |
| A only | 15 |
| B only | 201 |
| M only | 202 |
| A+B | 51 |
| A+M | 24 |
| B+M | 36 |
| A+B+M | 65 |

Binary-decision divergence was much rarer:

| divergent binary decisions | truth cases |
|---|---:|
| none | 611 |
| A only | 33 |
| M only | 16 |
| A+B | 63 |
| A+M | 20 |

These pattern frequencies are properties of the frozen generator panel and must not be
treated as universal ecological frequencies.

## Evidence burden

Full BAM-state identification required a median of **2** direct node measurements and
up to **4** in the frozen programme.

By contrast, many target-specific questions required no additional measurement at all.

### Release A

- exact map already identified: 613/768;
- binary decision already identified: 652/768;
- binary decision required at most 2 direct measurements;
- strict binary-decision saving versus full BAM-state recovery: 730/768 truths.

### Release B

- exact map already identified: 415/768;
- binary decision already identified: 705/768;
- every unresolved binary decision was resolved by exactly 1 direct measurement;
- strict binary-decision saving versus full BAM-state recovery: 738/768 truths.

### Release M

- exact map already identified: 441/768;
- binary decision already identified: 732/768;
- binary decision required at most 2 direct measurements;
- strict binary-decision saving versus full BAM-state recovery: 741/768 truths.

Across every truth and probe,

```text
binary-decision evidence burden
    <= exact counterfactual-map burden
    <= full BAM-state burden
```

with **0 violations**.

## Interpretation

The earlier BAM inverse-identifiability result showed that complete occurrence data can
leave the generating A/B/M mechanism unresolved.

The new result adds an important qualification:

> **Not every mechanism ambiguity is decision-relevant.**

If all surviving worlds agree on the target being acted on, resolving the remaining
mechanism aliases adds no information for that declared target.

Conversely, if survivor worlds agree on current G but diverge under a declared
counterfactual, the ambiguity is consequential and additional evidence can be targeted
specifically at the worlds that disagree about that target.

The appropriate inferential endpoint is therefore not always “recover the true
mechanism.”  It can instead be:

> **establish that the current survivor fiber lies inside one equivalence class of the
> ecological target that matters.**

## Boundary

The release-A/B/M probes are idealised mechanism interventions.  They do not establish
the effect of a literal climate manipulation, partner removal, antagonist control,
corridor restoration or translocation.

The numerical frequencies and measurement bounds are conditional on the frozen 12
finite BAM systems and their declared evidence library.

This result is a successor programme.  It does not modify the frozen JBI BAM manuscript
or the EOG-WF empirical denominator.
