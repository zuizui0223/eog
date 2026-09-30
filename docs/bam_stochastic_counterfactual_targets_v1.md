# BAM stochastic counterfactual targets v1

## Purpose

The deterministic BAM successor showed that parameter-world, exact future-map and
decision identifiability are different targets.

Phase VI asks whether the same separation persists when the target is an **exact
conditional stochastic forecast distribution** rather than a deterministic future map.

## Independent generator

The counterfactual target generator lives in:

`benchmarks/independent_stochastic_counterfactual_generator_v1.py`

and imports no EOG module.

The current ecological histories are the unchanged 384 runs from the independent
stochastic BAM v3 design:

- 6 frozen truth scenarios;
- 64 replicates per scenario;
- 32 candidate BAM worlds;
- 40 current-history steps.

Survivor sets are formed from accumulated positive occurrence evidence at horizon 40.
Unobserved cells are not treated as absences.

## Exact one-step stochastic forecast

For each run, the observed final occupied snapshot is used only as the conditioning
state for the future transition.

For each surviving BAM world, node occupancy probabilities at the next step are
calculated analytically:

- transformed-ineligible node: probability 0;
- currently occupied eligible node: persistence probability 0.86;
- currently unoccupied eligible node with (k) currently occupied accessible
  neighbours:

[
p=1-(1-0.48)^k.
]

Conditional node outcomes are the same independent Bernoulli updates used by the
generator.  Thus the ordered 96-node probability vector is the exact one-step
conditional predictive distribution representation for this audit; no Monte Carlo
forecast comparison is needed.

The historical founding source is not forced immortal after the conditioning time.

## Frozen transformations

The same three synthetic structured transformations used in deterministic Phase V are
applied:

1. climate shift: temperature +0.08, moisture -0.04;
2. biotic stress: one partner erosion shell + one antagonist dilation shell;
3. barrier restoration: force barrier permeability.

Each world is compared with its own untransformed one-step expectation.

Binary targets are expected occupancy decline for climate/biotic stress and expected
occupancy increase for barrier restoration.

## Identifiability targets

For the current survivor set:

1. parameter-world identity;
2. exact stochastic forecast identity — identical 96-node probability vector;
3. binary counterfactual decision identity.

The guaranteed refinement is

[
	ext{parameter world}
ightarrow
	ext{stochastic probability vector}
ightarrow
	ext{binary decision}.
]

Phase VI therefore tests whether a coarse stochastic decision can be identified even
when the generating world or full predictive distribution is not.
