# EOG-WF v2 generic adapter contract

## Status

This is a separate post-closure development line. It does not reopen the frozen
three-endpoint EOG-WF result, alter the favorable / favorable / adverse synthesis, or
permit repair of any consumed fresh endpoint.

## Problem exposed by the fresh funnel

The closed EOG-WF programme reached three scored endpoints but also accumulated many
pre-response and pre-model STOPs. Those STOPs mixed two very different classes:

1. scientifically necessary failures, such as an unrecoverable survey universe,
   indefensible recorded-negative semantics, or a structurally inadequate world family;
2. interface brittleness, such as source transport details, physical column spellings,
   or over-strict coordinate identity rules.

The second class limits portability without adding scientific protection.

A concrete example is the first STOC once-only attempt: the released data used lowercase
x_wgs84 / y_wgs84 while the frozen runner expected uppercase X_WGS84 / Y_WGS84. The
attempt correctly stopped under its frozen protocol, but the lesson for a future version
is that physical spelling should be an adapter concern rather than a core scientific
assumption.

## Schema boundary

Module:

src/eog/v2/schema_adapter.py

The module separates:

physical source schema
    -> prospectively declared exact aliases
    -> frozen canonical semantic roles
    -> dataset-neutral EOG problem contract

The core rule is:

> EOG may generalize across predeclared source representations, but it must not discover
> schema repairs after response access.

A role such as x-coordinate can prospectively declare the finite alias set:

- X_WGS84
- x_wgs84

The observed header may contain one of those aliases. It may not contain an undeclared
spelling and still pass. If multiple aliases for one role occur simultaneously, the
adapter stops rather than guessing.

The adapter does not case-fold unknown columns, use fuzzy matching or edit distance,
infer aliases from values, choose among ambiguous aliases, or discover a new alias after
biological response access.

It records separate contract, physical-header and semantic-resolution fingerprints so
interoperability and exact provenance are not conflated.

A strict physical CSV layer now sits immediately above this contract:

- src/eog/v2/tabular_adapter.py
- explicit UTF-8/BOM policy;
- duplicate-header rejection;
- exact row-width checks;
- no implicit cell stripping or imputation;
- canonical row fingerprints derived from the frozen schema resolution.

This replaces repeated dataset-specific combinations of CSV parsing, required-column
checks and in-memory renaming without weakening the response firewall.

## Coordinate-registry boundary

Module:

src/eog/v2/coordinate_registry.py

Repeated deployments may contain small coordinate differences for one stable node. v2
now treats that as an explicit response-independent registry contract rather than forcing
every dataset into exact floating-point identity.

CoordinateRegistryPolicy freezes:

- tolerance;
- units;
- representative-coordinate policy: first, mean or median.

The audit evaluates the full within-node x and y span. It does not compare only adjacent
rows, so a chain of individually small drifts cannot exceed the frozen total bound
without being detected.

If the span exceeds the declared tolerance, the registry fails closed. If variation is
within tolerance, aggregation is allowed only under the explicitly declared
representative-coordinate policy. No implicit snapping or averaging occurs.

## Integration with the existing v2 boundary

The existing problem_contract.py defines the dataset-neutral downstream object:

- stable nodes;
- contexts;
- candidate units;
- observation semantics;
- baseline roles;
- heldout split;
- world-family identity.

The schema and coordinate contracts belong upstream of that object. Dataset-specific
code should resolve physical fields, audit the stable coordinate registry, then construct
a NormalizedPreResponseProblem. Their fingerprints should be included in source
provenance; the EOG mathematical core should not depend on original physical spellings
or accidental row-level coordinate noise.

The existing world_scale_ladder.py and world_adequacy.py then provide a response-blind
structural bracket and adequacy gate. This prevents the opposite generality failure:
accepting a portable input source whose declared world universe is nevertheless too
local to represent the intended forecast domain.

Prediction remains a separate gate. predictive_state_gate.py blocks Tampa-like
prediction-facing states when:

- train and serve feature generators differ;
- source selection depends on arbitrary source labels;
- repeated endpoints reuse one static state without a prospective opt-in.

Thus v2 genericity is deliberately layered:

1. source portability through schema aliases;
2. registry portability through frozen coordinate tolerance;
3. structural eligibility through response-blind scale and adequacy checks;
4. prediction safety through response-independent Layer-B eligibility.

None of these layers implies predictive superiority.

## Joined pre-response certificate

Module:

src/eog/v2/pre_response_certificate.py

The certificate binds:

- exact response-independent source artifact identities;
- schema-resolution fingerprint;
- coordinate-registry fingerprint;
- NormalizedPreResponseProblem identity;
- exact declared world-family fingerprint;
- re-applied structural adequacy gate;
- optional prediction-facing eligibility result.

Structural response access and predictive outcome access are separate decisions. A
Tampa-like Layer-B design can therefore remain available for Layer-A structural work
while being blocked from predictive scoring. Conversely, structural inadequacy blocks
response access even when the prediction-facing representation would otherwise be
eligible.

## Integrated known-truth path

Benchmark:

benchmarks/eogwf_v2_generality_known_truth.py

The benchmark uses no biological response. It verifies one complete generic pre-response
path:

strict CSV bytes
    -> predeclared schema aliases
    -> canonical records
    -> bounded coordinate drift
    -> content-addressed source provenance
    -> normalized problem
    -> structural scale ladder
    -> structural adequacy
    -> prediction-facing eligibility
    -> joined pre-response certificate

The safe sequential/source-symmetric design reaches predictive_complement_candidate,
while a Tampa-like train/serve-mismatched static design is stopped before any outcome is
needed.

This benchmark is representation and protocol evidence only. It does not count as a new
fresh endpoint and cannot modify the frozen manuscript conclusion.

## Historical STOP replays

Two response-free replays define what genericity is and is not allowed to rescue.

### STOC schema replay

benchmarks/stoc_schema_contract_replay.py

The frozen STOC failure recorded lowercase x_wgs84 / y_wgs84 in the physical file while
the predeclared interface used uppercase X_WGS84 / Y_WGS84. The generic exact-alias
contract reproduces that mapping without opening biological responses or changing any
world definition. This is interface variation that v2 should absorb prospectively.

### Algar coordinate replay

benchmarks/algar_coordinate_contract_replay.py

The frozen Algar safe deployment source contains ALG069 at longitude -113.5075 in one
deployment and -112.5074726 in later deployments at the same latitude. This is roughly a
one-degree longitude discontinuity, not numerical rounding. The frozen 1e-9-degree rule
fails, but so does a much looser 0.01-degree rule; accepting the node requires roughly one
full degree of tolerance.

Therefore v2 must preserve this STOP. Genericity means removing harmless interface
brittleness, not making registry contradictions disappear.

## What this development line still does not repair

It does not:

- change observation semantics;
- invent surveyed negatives;
- infer missing temporal registries;
- bypass unavailable source transport;
- rescue a world universe that fails structural adequacy;
- turn reachability into occupancy;
- promote Layer B after seeing predictive outcomes;
- rerun consumed or stopped fresh endpoints.

Those remain scientific or protocol boundaries.

## Next development step

The adapter/provenance/certificate path now exists. The next development increment should
therefore target a second major source of bespoke validation code: observation-process
normalization.

Specifically, define a small generic effort/context contract that can represent repeated
camera, acoustic, telemetry and transect occasions without teaching the EOG core any
dataset-specific response syntax. It must keep surveyed-negative semantics explicit and
must never infer absence from a missing row.

Only after that contract is exercised by response-free replays from at least two distinct
monitoring modalities should v2 attempt a new independently preregistered real-system
translation test.
