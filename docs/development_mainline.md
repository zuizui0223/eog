# EOG development mainline

## Purpose

This is the **single active scientific/development direction** after the 2026-08 cleanup. It does not alter or rescue any frozen v0.1/v2 result, empirical benchmark, fingerprint, manifest or manuscript outcome.

The repository must not grow another parallel EOG story while this mainline remains active.

## Scientific center

EOG starts from:

> **Local possibility is not the same object as distributional realizability.**

Observed occurrences are realized states of an unknown distribution-forming process. They constrain which ecological/analytical worlds could have produced the observed configuration, but they do not identify one historical route.

The active question is:

> **What worlds could have made the observed distribution realizable, how tightly can observations reconstruct that world set, and which distributional flows remain robust, contingent or excluded across it?**

A local SDM/support surface may supply node viability. EOG is not defined by adding a movement covariate to an SDM; its main objects are relations, reachable configurations and world-set constraints.

## Integrated objects

### 1. Distributional realizability

For observations `O`, evaluate which declared worlds can realize the required occurrence configuration.

### 2. World-indexed flow sets

For each compatible world `w`, preserve its transition operator and support trajectory. Do not average away which world generated which flow.

Conceptually:

`K_t = { p_t^(w) : w in W(O) }`.

### 3. World reconstructability

The inverse object is:

`W(O) = { w : w is compatible with the observations }`.

New positive evidence may contract `W(O)`. If multiple worlds survive, the result remains underidentified.

### 4. Robust exclusion

A state/transition is `robustly_unreachable` only relative to the declared/certified world universe when no compatible world permits reachability. Claim strength must not exceed coverage strength.

## Distributional-watershed interpretation

Use watershed language only where there is an auditable structural definition:

- occurrence — realized state/anchor;
- basin — states reachable under declared constraints;
- channel/tributary — supported transition sequence;
- confluence — route reconvergence;
- bottleneck — transition/state whose loss strongly reduces reachability;
- divide — boundary between reachable basins;
- water level `lambda` — **predeclared monotone one-dimensional relaxation coordinate**;
- basin merge — first declared level at which occurrence groups become jointly realizable.

`lambda` must not be manufactured after outcomes by weighting unrelated axes.

## IBD, IBE and barriers stay separate

At minimum keep separately inspectable:

- geographic / IBD-like constraint;
- environmental / IBE-like constraint;
- explicit barrier/permeability constraint.

A long geographic jump and a large environmental crossing are different ecological explanations. Return a non-dominated relaxation frontier when more than one explanation survives.

## Implemented finite architecture

All current prospective names live on `eog.v2.reachability`, not on the `eog.v2` compatibility root.

### Static finite world layer

Implemented:

- exact finite forward reachability envelope;
- positive-occurrence inverse reconstruction `O -> W(O)`;
- world-indexed support-flow set and lower/upper envelopes;
- `reachable_in_all`, `contingent`, `robustly_unreachable` finite-universe classes;
- separate geographic/environmental/barrier relaxation axes;
- non-dominated minimum-relaxation frontier;
- compatible-world contraction after added positive evidence;
- positive static survey discrimination;
- declared monotone one-dimensional relaxation families;
- first-possible / first-robust basin merge across analytical variants.

### Finite temporal layer

Implemented:

- `TemporalWorld`: ordered sequence of existing transition operators;
- source mass injected once at the initial state;
- exact-time support trajectories and cumulative `reached by time` states;
- world-set robust/contingent/unreachable classes at each declared time;
- time-stamped positive occurrence reconstruction;
- compatible temporal-world contraction after additional timed positive evidence;
- positive `(node,time)` survey discrimination among still-compatible temporal worlds.

Time labels are ordered state labels, not calibrated dates/generations.

### Positive-only feedback loop

The finite temporal loop is now closed:

```text
declared worlds
  -> temporal flow
  -> positive timed observations
  -> compatible temporal worlds
  -> ranked positive (node,time) discriminator
  -> added positive evidence
  -> contracted world set
```

No non-detection evidence enters this loop.

## Known-truth falsification

The finite archetype matrix verifies one common core across:

- IBD-dominated rescue;
- IBE-dominated rescue;
- barrier-dominated rescue;
- environmental-crossing versus geographic-jump tradeoff through a niche desert;
- stepping-stone versus direct-route underidentification;
- rare low-support long-distance reachability;
- branching and reconvergence;
- analytical ambiguity in basin merge;
- robust exclusion under explicit finite-universe expansion.

Temporal tests verify:

- temporal order matters even with the same edge set;
- bridge opening order matters;
- source mass is not re-injected;
- exact-time mass differs from reached-by-time history;
- timed positive observations can eliminate worlds that arrive too late;
- candidate timed positive observations correctly predict which worlds would survive if observed.

These are known-truth structural validations, not empirical superiority claims.

## Scientific boundaries

Keep these explicit in code/docs/manuscripts:

- transition/reachability values are model support unless independently calibrated;
- low positive support is not impossibility;
- a time-stamped positive occurrence means the node must have been reachable **by** that time; it is not a persistence/occupancy likelihood;
- non-detection is not absence without a detection model;
- multiple compatible worlds are not replaced by a best history;
- `robustly_unreachable` is relative to the declared finite universe/certificate;
- one-dimensional `lambda` is valid only inside a declared monotone family;
- finite exact enumeration does not justify claims over an undeclared continuous universe.

## Repository roles

### Frozen evidence layer

Preserve:

- benchmark inputs/results;
- fingerprints/manifests;
- adverse/null/failed/indeterminate outcomes;
- claim/evidence ledgers;
- publication provenance.

A negative result is evidence, not dead code.

### Stable root API

Root `eog` remains frozen/stable compatibility for environmental geometry, comparative reference, support topology, bridge and survey tooling.

### Prospective v2 facades

- `eog.v2.reachability` — current finite/static/temporal world framework;
- `eog.v2.traversability` — IBD/IBE/barrier/pathwise transition constraints;
- `eog.v2.validation` — independent occurrence/genetic/directional validation.

### System-specific adapters

A-Islands, Tanzania, Finland, Ryukyu, Zhoushan and similar code remain adapters/evidence. They do not define generic APIs.

### Manuscript assets

`manuscript/` preserves the earlier structural empirical paper line. It is not the active package architecture and must not be silently rewritten into the newer method story.

## Cleanup rules

1. Reuse an existing facade before adding a namespace.
2. Do not duplicate transition, bottleneck, reconstruction or survey logic for narrative reasons.
3. Do not add prospective convenience exports to `eog.v2` root without a real compatibility obligation.
4. Package-wide regression belongs to Package checks; scientific workflows keep narrow path scopes.
5. Search frozen reproduction paths before physical deletion/moves.
6. Preserve frozen negative and indeterminate evidence.
7. Presentation/manuscript tooling must not become a scientific-core dependency.
8. Cleanup cannot change scientific outcomes merely to simplify the story.

## Current development gate

**Pause feature growth.** The positive-only finite temporal loop is complete enough for an end-to-end falsification checkpoint.

Before opening imperfect detection, calibrated time, continuous-world optimisation or large-raster forecasting:

1. keep README / package layout / progress ledger / manuscript provenance synchronized;
2. audit that no prospective API has leaked onto compatibility roots;
3. run one compact end-to-end temporal feedback benchmark in which a ranked positive `(node,time)` observation is applied and the observed compatible-world contraction matches the prediction;
4. preserve the case where no candidate can distinguish the remaining worlds;
5. preserve the case where a positive candidate is unsupported by every compatible world and therefore challenges the declared universe;
6. only then choose the next scientific expansion from an explicit need, not from novelty pressure.

Deferred choices include:

- imperfect detection / surveyed absence evidence;
- calibrated durations/calendar time;
- hypothetical historical sources;
- continuous/large world universes requiring stronger certification;
- large-raster forecasting;
- new empirical promotion claims.
