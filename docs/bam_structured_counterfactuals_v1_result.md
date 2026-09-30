# BAM structured counterfactuals v1 — frozen result

## Result

The preregistered Phase-V audit completed successfully.

- initial protocol freeze: `d776e013be4dff11e4380ef8d59a09ee893031f3`;
- pre-implementation amendment: `aba42db77c7135d9f7bfba85b30e42920c5cffdb`;
- workflow run: `36671298135`;
- artifact: `11078605793`;
- artifact digest: `sha256:6ffd073329e8c4656ee3061ba976517798e6d637be941386da4f3c60bdd5c0a0`;
- result fingerprint: `f502fb647ba4666f5c40ddbd5639123f3e0296fe492dd97a1ec19ec246531cb1`.

All amended preregistered hypotheses were supported and the guaranteed
parameter-world → exact-map → binary-decision hierarchy had **0 violations**.

## Structured counterfactuals preserve the main hierarchy

### W0 — original 64-world universe

Only **13/768** truth cases had a singleton parameter world after complete current
(G).

Only **25/768** identified the complete current BAM state.

Yet target identification was much higher.

| transformation | exact future map | binary decision |
|---|---:|---:|
| climate shift | **622/768** | **646/768** |
| biotic stress | **558/768** | **603/768** |
| barrier restoration | **604/768** | **744/768** |

Parameter-world nonidentification therefore coexisted with binary decision
identification in:

- climate: **633** truth cases;
- biotic stress: **590**;
- barrier restoration: **731**.

This reproduces the target-specific identifiability principle without using axis
deletion as the target.

## W1 — expanded ecological universe

Under the 2,592-world ecological lattice, no truth case had a singleton parameter world.

Current BAM state was identified in only **8/768** truth cases.

Yet binary decisions remained identified in:

- climate: **636/768**;
- biotic stress: **498/768**;
- barrier restoration: **700/768**.

So a unique parameter-world explanation is clearly not necessary for these frozen
decision targets.

## World-universe expansion removes real decision certificates

From W0 to W1:

| transformation | W0 binary identified | retained in W1 | lost |
|---|---:|---:|---:|
| climate shift | 646 | **636** | **10** |
| biotic stress | 603 | **498** | **105** |
| barrier restoration | 744 | **700** | **44** |

Retention fractions:

- climate: **98.5%**;
- biotic stress: **82.6%**;
- barrier restoration: **94.1%**.

Thus H3 was supported for all three transformations, not merely one.

In this frozen design the biotic-stress target was substantially more sensitive to
world-universe expansion than the climate or barrier-restoration targets.

This is a system-specific result, not a universal ranking of A, B and M uncertainty.

## Exact-map certificates show a different pattern

Exact future-map identification changed:

| transformation | W0 | W1 |
|---|---:|---:|
| climate shift | 622 | 610 |
| biotic stress | 558 | 442 |
| barrier restoration | 604 | 604 |

Barrier restoration lost 44 binary certificates without losing any of the 604 exact-map
certificates that were already exact in W0.

That is possible because many W0 fibers were already exact-map unresolved but happened
to agree on the coarser gain/no-gain decision.  W1 introduced the opposite binary
decision inside some of those already map-ambiguous fibers.

## Dormant parameter alias activation

The pre-implementation protocol amendment anticipated that a transformation could
activate parameter information absent from the current BAM-state projection.

One frozen W1 fiber did exactly that.

- system: **S11_9x5_gap**;
- current (G): **29 nodes**;
- truth multiplicity: 2;
- same-G W1 parameter worlds: **36**;
- current A/B/M/tau state classes: **1**;
- climate-shift exact-map classes: **2**;
- climate net-loss decision classes: **2**.

So all 36 worlds are observationally identical at the complete current BAM-state level,
yet the frozen climate transformation separates them into both loss and no-loss
outcomes.

This is an important correction to a simple “identify the current mechanism state,
then forecast” picture.

The more accurate diagram is

[
\theta
\rightarrow
C_{current}(\theta)
]

and separately

[
\theta
\rightarrow
F_{counterfactual}(\theta)
\rightarrow
D(\theta).
]

If the current-state projection collapses parameter distinctions that the
counterfactual transformation uses, current-state identification need not imply future
decision identification.

## Scientific interpretation

The finite BAM programme now separates four questions:

1. Which parameter worlds remain possible?
2. Which current BAM states remain possible?
3. Which exact future distributions remain possible under a declared transformation?
4. Which decision-relevant outcome classes remain possible?

These form neither a single universal ranking nor a requirement to identify every
upstream object.

Parameter-world identity is the finest representation and therefore guarantees every
deterministic downstream target.

Current BAM-state identity is different: it is a projection optimized for describing
the current realized mechanism state, and can omit dormant parameter distinctions that
matter under a future intervention.

## Boundary

The three transformations remain synthetic fixtures.

The climate delta is not an emissions pathway, associate shell changes are not
population-dynamic forecasts, and forced barrier permeability is not a calibrated
restoration project.

The robust conclusion is structural:

> **target identifiability must be evaluated under the transformation and world universe
> actually relevant to the decision; current-state identifiability is not a universal
> substitute for that calculation.**
