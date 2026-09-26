# EOG world-survival regime predictability programme

## Scientific question

EOG can reconstruct a finite declared world universe and eliminate worlds that are
incompatible with observed positive occurrences. The unresolved question is now one
level earlier:

> Can the survival regime of a declared world universe be forecast from response-blind
> structure before ever-positive occurrence nodes are opened?

This is not a predictive-complementarity study. It does not use log loss, Random Forests,
baseline covariates, response-balanced folds, or Layer-B summaries.

## Historical anomaly motivating the programme

The already-consumed evidence is endpoint-heavy.

- STOC: all 20 declared falsifiable worlds were rejected before predictive comparison.
- Southwest Louisiana: all six local falsifiable worlds were eliminated; only the
  prospectively universal external_open sentinel remained.
- Tampa: all four local falsifiable worlds survived in every fold, as did external_open.

Therefore the scientifically comparable falsifiable-world regimes are:

- STOC: falsified_universe;
- Southwest Louisiana: falsified_universe;
- Tampa: saturated.

There is no historical contracting example among these systems.

The historical systems motivate the question but must not be used to tune the prospective
forecast rule.

## Critical denominator rule

A world that is prospectively defined as non-falsifiable must never enter the survival
fraction denominator.

For example, Southwest Louisiana froze external_open as supporting every site and never
being eliminated by positive observations. Counting that sentinel would turn a complete
local-mechanism falsification into an apparent 1/7 partial contraction and would make
0/7 logically impossible.

Primary regime denominators therefore contain falsifiable worlds only. Non-falsifiable
sentinels remain visible in Layer A and are reported separately.

## Separation of adequacy and outcome forecast

### A. Structural adequacy is a prerequisite

Before response access:

1. construct the response-blind structural ladder;
2. use plan_adequacy_complete_lcc_targets so the ladder can test its own declared
   LCC/isolation adequacy criteria at finite node count;
3. audit the complete declared world universe;
4. apply the frozen structural adequacy gate.

A failed gate is a pre-response STOP. It is not a predicted or observed survival regime.

For this programme, horizon reachability is not permitted as an adequacy-gate criterion.
That quantity is reserved for the regime forecast, preventing the same structural signal
from being used both to make a system eligible and to predict its outcome.

### B. World-survival regime is an outcome

After the adequacy gate passes, a response-blind rule predicts one of:

- falsified_universe: predicted falsifiable-world survival fraction = 0;
- contracting: predicted fraction is strictly between 0 and 1;
- saturated: predicted fraction = 1.

Only then may the ever-positive occurrence set be opened once.

## Structural variables available from the existing audit

audit_world_universe_structure already returns, per world:

- node count;
- directed edge count;
- weak component count;
- largest weak component size and fraction;
- isolated node count and fraction;
- mean, median and maximum out-degree;
- median, minimum and maximum horizon-reachable fraction;
- declared horizon;
- deterministic fingerprint.

The v1 primary prediction rule deliberately uses only two already-returned quantities:

- largest_weak_component_fraction;
- median_horizon_reachable_fraction.

All other audit values are recorded but are not allowed to alter the v1 regime call.

## V1 zero-fit prediction rule

For each falsifiable world w define

    H_w = median_horizon_reachable_fraction_w
          / largest_weak_component_fraction_w

H_w is the horizon-realization ratio.

Interpretation:

> Relative to the largest weakly connected scale that the world makes structurally
> available, how much of that scale can a typical node actually realize within the
> declared structural horizon?

The single prospective cutoff is fixed at 0.5.

- H_w >= 0.5 -> predict that world survives;
- H_w < 0.5 -> predict that world is falsified.

The system-level predicted survival fraction is the fraction of falsifiable worlds
predicted to survive. The three-state regime follows mechanically from 0 / intermediate
/ 1.

The 0.5 cutoff is not estimated from STOC, Louisiana, Tampa, or any later biological
response. It is a zero-fit majority criterion: the median node must realize at least half
of the largest weak-component scale.

No alternative cutoff is allowed after candidate or response inspection.

## Structural horizon

The regime programme is intended to work without a temporal estimability requirement.

For the static ever-positive version, freeze the structural horizon as:

    node_count - 1

before response access.

This is a graph-closure horizon, not a biological dispersal-time claim. It removes an
otherwise free temporal tuning axis and asks a purely structural question about the
declared transition graph.

If a later programme wants a biologically calibrated horizon, it requires a new protocol
version and independent external justification before response access.

## World construction

Default primary geography ladder before any secondary axes:

- declared LCC targets: 0.25, 0.50, 0.75, 0.90;
- adequacy declaration: largest weak component >= 0.90 and isolated-node fraction <= 0.05;
- plan_adequacy_complete_lcc_targets may add finite-n targets required to test those
  criteria;
- all equal-distance ties are admitted together;
- structurally generated thresholds remain analyst-choice scales, not biological
  dispersal limits.

Secondary environmental or barrier worlds may be included only under predeclared rules.
Primary-only worlds must remain available so secondary intersections cannot erase the
structural bracket.

## Response requirement

The primary outcome needs only:

- stable node identity;
- whether the focal taxon was ever positively observed at that node.

At least two ever-positive nodes are required for source-symmetric positive compatibility.

No requirement is imposed for:

- positive and negative counts inside predictive folds;
- a materialized strong baseline learner;
- effort covariates sufficient for supervised prediction;
- 50 nodes as a universal minimum;
- 17 temporal contexts;
- heldout predictive log loss.

Transport, source identity, join integrity, and once-only response authorization remain
required.

## Source symmetry

Arbitrary lexicographic source selection is forbidden.

The ever-positive set is evaluated under a source-label-invariant policy declared before
response access. The v1 default is the existing self-excluded positive-source policy:
each observed positive is evaluated as a target while all other observed positives form
the peer-source envelope.

This is a compatibility diagnostic, not a claim that all peers were historical sources.

## Observed regime

Record an initial pre-evidence state containing all declared worlds.

After positive evidence is consumed, record the surviving falsifiable worlds. If natural,
response-independent contexts exist, update sequentially and record:

- surviving falsifiable-world count by context;
- contraction event count;
- contraction context positions.

If such contexts do not exist, use one final ever-positive update. Temporal structure is
not required for primary eligibility.

Final observed regime:

- 0 surviving falsifiable worlds -> falsified_universe;
- all falsifiable worlds survive -> saturated;
- otherwise -> contracting.

## Primary and secondary endpoints

Primary:

- exact three-state regime match per system;
- aggregate exact-match fraction.

Predeclared simple chance reference:

- 1/3 for the three labels;
- one-sided exact binomial tail reported as a reference, not as evidence that empirical
  class prevalence is truly uniform.

Secondary:

- predicted versus observed falsifiable-world survival fraction;
- absolute error;
- contraction event count and context positions where available;
- observed class prevalence.

## Failure conditions

The programme is allowed to fail cleanly.

1. Match rate is not distinguishable from the fixed 1/3 reference:
   structural quantities do not predict the regime under this rule.
2. Adequacy-complete systems still produce only falsified or saturated outcomes:
   the missing intermediate regime is a limitation of the finite-world declaration
   framework or the sampled ecological systems.
3. Adequacy-complete ladders cannot be constructed for many real systems:
   the method has a structural applicability limitation.
4. Contracting occurs but the v1 rule systematically misses it:
   the zero-fit horizon-realization hypothesis is rejected.

No failure authorizes retuning the 0.5 cutoff within the same programme.

## Existing implementation

- src/eog/v2/world_adequacy.py
- src/eog/v2/adequacy_complete_ladder.py
- src/eog/v2/world_survival_regime.py
- src/eog/v2/occurrence_constraints.py
- existing once-only response-access and source-integrity infrastructure

The new module contains the response-blind regime forecaster, falsifiable-world observed
regime classifier, and cross-system score aggregation.
