# Response-blind candidate preflight

## Purpose

Fresh empirical EOG validation should not require a candidate-specific workflow merely to discover that the system cannot support the declared validation estimand.

`src/eog/v2/candidate_preflight.py` provides a validation-only metadata gate before the structural geometry gate and long before row-level outcome access.

It is not an ecological operator and does not choose a dataset because its eventual result looks favourable.

## Inputs

Each attempt prospectively declares its own minima with `CandidatePreflightDeclaration`:

- minimum node count;
- minimum heldout/outer-unit count;
- minimum number of nodes repeated across time;
- whether response-independent coordinate geometry is required;
- whether geometry and response must be physically separable.

There are deliberately no universal EOG node-count or time-series cutoffs in this module.

`CandidatePreflightEvidence` records only response-blind metadata evidence:

- immutable source identity;
- exact geometry source/file/member identity;
- exact response source/file/member identity;
- whether those roles are physically separable;
- whether response-independent coordinates exist;
- known node / outer-unit / repeated-node counts;
- broad layout design;
- whether response bytes or rows have already been opened.

Unknown metadata is represented as `None`; it is never silently treated as a pass.

## Decisions

Hard STOP statuses include:

- `stop_response_already_opened`;
- `stop_inseparable_geometry_response`;
- `stop_no_response_independent_coordinate_geometry`;
- `stop_insufficient_nodes`;
- `stop_insufficient_outer_units`;
- `stop_insufficient_repeated_nodes`.

If required evidence is genuinely unresolved, the result is:

`incomplete_response_blind_metadata`

The only positive disposition is:

`ready_for_geometry_gate`

That status does **not** mean the candidate is empirically suitable. It permits the next response-blind stage to build/audit the actual geometry using the already existing world-scale and structural-adequacy machinery.

## Layout warnings

A known regular grid yields:

`regular_grid_structural_scale_collapse_risk`

A linear transect yields:

`linear_layout_requires_geometry_gate_for_scale_diversity`

These are warnings, not automatic scientific STOPs. Actual scale diversity remains an empirical property of the frozen geometry and is decided only by the structural gate.

## Why this exists

Post-complementarity candidate screening produced several different response-blind failures:

- regular-grid candidates whose structural scales collapsed;
- an otherwise strong system whose external coordinate registry was incomplete;
- a long-term camera survey with sparse released periods;
- a long-term amphibian system whose site predictors were cleanly separated from observations but had no response-independent coordinates.

Those failures are useful evidence. They also show that source/schema suitability should be assessed once through reusable validation infrastructure rather than by expanding ecological operators or repeatedly writing ad-hoc candidate code.

## Boundary with later gates

Candidate preflight does not replace:

- response-token schema freezing;
- process/source-closure justification;
- world-scale construction;
- structural adequacy;
- prospective estimability;
- the 16-key once-only outcome-access contract;
- paired predictive-complementarity evaluation.

It only ensures that a candidate is worth entering those more expensive stages while response content is still untouched.
