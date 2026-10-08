# Matched-information geometry comparison: development design

Freeze before scoring. No previously scored seed or response is reused.

## Shared information and methods

Seeds 901,907,911,919,929,937,941,947; 120 independent eight-node graphs per
seed. Geometry, Gaussian displacement SD0.12, two sources, radii0.45/0.65,
edge kernel exp(-distance/0.4), loss0.3, four-step horizon, and six targets per
graph match the preceding geometry experiment. Both methods receive the exact
same two transition matrices, source set, source weights, and horizon.

EOG uses total first-passage support. The comparator uses the maximum product
of transition probabilities over one first-arrival path of at most four steps.
It therefore uses the same transition normalization and loss, not a privileged
true-radius graph or unlimited-distance horizon. Both representations average
across sources inside each world, then use the mean and population standard
deviation across worlds. Current minus fixed reference gives two innovations.
Primary comparison: ridge-logistic offsets using those two features. Ten EOG
innovations, RF concatenation of two EOG innovations, and permuted two-feature
offset are secondary controls. Offset ridge0.1, no intercept, fit-only RMS.

## Independent response generation and limits

One of the two candidate worlds is sampled uniformly per graph and hidden from
every learner; it is held fixed across reference/current. Conditional on that
world, diffusion truth uses independently simulated killed walks: 512 trajectories
from each source per geometry, four steps, record ever-hit fraction at each node,
then average across sources. Walk simulation uses transition sampling, not EOG
summary outputs. Finite simulation error is retained; there is no refitting or
resampling to obtain favourable results.

Route truth uses best-path support in the hidden world, averaged across sources.
Four response regimes: diffusion change, route change, environment only, and
diffusion change whose sign reverses only for outer graphs. Structural logit
effect is 8*(current_truth-reference_truth); no data-fitted scaling. Conventional
logit is 0.8*(current_x-0.5)-0.4*(current_y-0.5). Same uniforms across regimes.
Each non-null truth intentionally matches one modelling assumption. These are
positive controls and misspecification checks, not neutral evidence of ecological
relevance or a methods-paper superiority claim.

Graphs0:60 fit,60:90 calibration,90:120 outer; graph index modulo3 for baseline
OOF fitting. Conventional predictors, RF settings, clipping, and calibration-only
selection are unchanged from the preceding design. All methods see identical
training responses, and the selected world ID is never a feature. Freeze every
selection before outer scoring; ties return baseline, no refit.

## Reporting and gate

Retain all 32 cases, always-on and selected paired log losses, selections and
per-seed geometry fingerprints. Report two-feature EOG minus two-feature path
paired differences, win counts, and range across seeds, separately per regime.
No score-dependent test or significance gate, no posthoc method promotion. If
neither dominates across assumptions, report conditional usefulness and keep
defaults unchanged. Larger dimensions must earn their keep against two features.
All old records and biological admission STOPs remain untouched.
