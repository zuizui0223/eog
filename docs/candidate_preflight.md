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
- whether geometry and response must be physically separable;
- optionally, whether a **closed analysis registry** is required before the geometry gate;
- optionally, whether at least one response-blind safe-source transport route must be live-qualified before candidate lock.

There are deliberately no universal EOG node-count or time-series cutoffs in this module.

`CandidatePreflightEvidence` records only response-blind metadata evidence:

- immutable source identity;
- exact geometry source/file/member identity;
- exact response source/file/member identity;
- whether those roles are physically separable;
- whether response-independent coordinates exist;
- whether the geometry registry is already closed on the intended analysis-node universe;
- known node / outer-unit / repeated-node counts;
- broad layout design;
- whether response bytes or rows have already been opened;
- whether response-blind source transport has already been qualified;
- the fingerprint of the transport-qualification evidence.

Unknown metadata is represented as `None`; it is never silently treated as a pass.

## Closed analysis registry

Physical separation is necessary but not sufficient for a fresh candidate.

A geometry source counts as `analysis_registry_closed=True` only when response-blind metadata already establish one of the following **before candidate geometry is opened**:

1. the geometry registry is one-to-one with the intended analysis nodes; or
2. a deterministic filtering / point-construction rule is specified externally and prospectively, and that rule uniquely closes the registry on the intended analysis nodes.

Examples that do **not** establish closure by themselves:

- a source-wide location catalogue with more rows than the analysis;
- a generic site registry whose relation to the analyzed subset is unstated;
- polygon/bounding-box metadata when the analysis requires point coordinates but no external point-construction rule is declared;
- a coordinate table known to be missing some analysis IDs;
- a registry that can be made to match only through fuzzy aliases learned after opening the candidate geometry.

The declaration field `require_closed_analysis_registry` defaults to `False` for backward compatibility with historical workflows. New fresh paired-complementarity attempts should set it to `True`.

When required:

- `analysis_registry_closed=None` → `incomplete_response_blind_metadata`;
- `analysis_registry_closed=False` → `stop_analysis_registry_not_closed`;
- `analysis_registry_closed=True` → this requirement is satisfied, but the actual geometry must still pass the structural gate.

## Response-blind transport qualification

New fresh real-system attempts should qualify source transport **before** the system is
locked as the active scientific candidate.

`src/eog/v2/source_transport_preflight.py` records prospectively declared acquisition
routes such as:

- physically separate safe registry / effort files;
- bounded mixed-archive inventory;
- a published member inventory;
- another explicitly declared response-blind route.

The gate asks only whether at least one route has actually demonstrated access to the
required safe inputs while focal response payload bytes remain zero. It does **not**
promote a particular HTTP status code, URL shape or hosting provider into an ecological
criterion.

A failed route can coexist with a different qualified route when both routes were
declared before candidate lock. For example, a server ignoring a Range request does not
invalidate the dataset if an independent predeclared safe inventory route already
qualifies. Conversely, a mixed archive with no response-blind inventory route is rejected
before it consumes the fresh scientific attempt.

For candidates that set
`require_response_blind_transport_qualification=True`:

- unknown transport status -> `incomplete_response_blind_metadata`;
- known unqualified transport -> `stop_response_blind_transport_unqualified`;
- qualified transport -> this requirement is satisfied and the candidate may proceed to
  the geometry gate.

The Endure coastal-dune aphid attempt illustrates the reason for this boundary. Its
frozen mixed-archive Range probe returned HTTP 200 rather than the attempt-specific
required 206, and correctly stopped with zero archive/member/response bytes opened.
Under the new preflight that transport fact would reject the source **before** focal
candidate lock, rather than consuming a scientific attempt and then discovering an
interface limitation.

## Geometry schema boundary

Geometry is response-blind. Therefore candidate preflight should freeze the **source identity and coordinate semantics**, not guess an exact physical header when external metadata do not provide one.

A later response-blind geometry gate may resolve physical column names against a finite, prospectively declared semantic contract. That is different from changing geometry semantics after seeing outcome data.

Once a candidate-specific geometry rule has been declared and the geometry has been opened, however, that same candidate must not be rescued by inventing new filters, centroids, aliases, scales or distance definitions merely because the first rule failed.

## Decisions

Hard STOP statuses include:

- `stop_response_already_opened`;
- `stop_inseparable_geometry_response`;
- `stop_no_response_independent_coordinate_geometry`;
- `stop_analysis_registry_not_closed`;
- `stop_response_blind_transport_unqualified`;
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

The France-wolf fresh attempt demonstrated why this remains a warning rather than a universal ban: its 10-km complete grid collapsed all four frozen LCC targets onto one threshold, but that result is evidence about that geometry and scale construction, not proof that every regular design must collapse.

## Why this exists

Post-complementarity candidate screening produced several different response-blind failures:

- regular-grid candidates whose structural scales collapsed;
- otherwise strong systems whose external coordinate registry was incomplete;
- a long-term bird system whose advertised study-location catalogue had 186 bounding-box records rather than the 183 point-level analysis nodes;
- a long-term camera survey with sparse released periods;
- a long-term amphibian system whose site predictors were cleanly separated from observations but had no response-independent coordinates.

Those failures are useful evidence. They also show that source/schema suitability should be assessed once through reusable validation infrastructure rather than by expanding ecological operators or repeatedly writing ad-hoc candidate code.

## Boundary with later gates

Candidate preflight does not replace:

- response-header and response-token schema freezing;
- process/source-closure justification;
- world-scale construction;
- structural adequacy;
- prospective estimability;
- the 16-key once-only outcome-access contract;
- paired predictive-complementarity evaluation.

It only ensures that a candidate is worth entering those more expensive stages while response content is still untouched. For new real-system protocols, transport qualification should be completed before the candidate is counted as the active fresh attempt.
