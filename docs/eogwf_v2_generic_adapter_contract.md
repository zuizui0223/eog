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
4. executable negative/zero semantics through a frozen observation contract;
5. prediction safety through response-independent Layer-B eligibility.

None of these layers implies predictive superiority.

## Observation-process boundary

Module:

src/eog/v2/observation_process.py

The response-facing contract has two explicit modes after effort-eligible candidate units
have already been frozen.

### explicit_binary_tokens

Every eligible unit must be explicitly mapped to positive, negative or unavailable.
Missing response rows never become zero. The frozen Louisiana King Rail acoustic matrix
fits this mode because its response contract defines exact 1, 0 and unavailable tokens.

### complete_source_zero

Eligible units not mapped to a focal positive may become recorded non-detections only
after the caller explicitly certifies that the complete response source was parsed.
Azores yellow-eel receiver-weeks and Tampa seagrass transect visits fit this mode under
their frozen contracts.

The response-free replay:

benchmarks/observation_process_contract_replay.py

reads only the three frozen contract documents and maps telemetry, passive acoustics and
transect monitoring onto these two modes. No response rows are opened.

This layer does not infer biological absence. It only makes the sampling-process meaning
of zero executable and auditable.

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
- machine-readable binary observation contract when predictive scoring is intended;
- optional prediction-facing eligibility result.

Structural response access and predictive outcome access are separate decisions. A
Tampa-like Layer-B design can therefore remain available for Layer-A structural work
while being blocked from predictive scoring. Conversely, structural inadequacy blocks
response access even when the prediction-facing representation would otherwise be
eligible. Even a structurally adequate, prediction-eligible design cannot open a
predictive outcome unless its machine-readable observation contract is already frozen.

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

Schema, tabular parsing, coordinate registry, observation semantics, structural
adequacy and prediction eligibility now have reusable contracts.

The remaining genericity gap is **candidate-unit construction itself**: camera deployment
intervals, acoustic occasions, telemetry receiver activity and transect completeness are
still normalized by dataset-specific code before reaching NormalizedPreResponseProblem.

The next increment should therefore define a minimal effort/context ledger whose only
job is to certify which node-context units were genuinely surveyed. It must allow
modality-specific effort calculations upstream but expose one common output:

node_id + context_id + eligibility + provenance

It must not infer effort from focal detections and must keep unsurveyed units outside the
binary endpoint.

After that ledger is exercised response-blind on at least two different modalities, v2
will have a credible generic adapter path suitable for a new separately preregistered
real-system validation.
