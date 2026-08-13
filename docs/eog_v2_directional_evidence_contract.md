# EOG v2 independent directional-evidence discrimination contract

## Status

Prospective method-development contract for issue #141. This contract is frozen before any new empirical directional, occurrence or genetic outcome is used to discriminate candidate transition rules. It does not alter or rescue any frozen EOG result.

## Motivation

The frozen occurrence-rule compatibility confirmation established two boundaries:

1. occurrence configuration can constrain a candidate rule that cannot support observed occurrence states;
2. occurrence-only compatibility cannot identify a unique generating rule because an over-permissive rule may also support all occurrences.

The next valid step is therefore to add **independent discriminating evidence**, not to make the transition graph more permissive or search more occurrence datasets.

This first discrimination layer uses prospectively declared directional/order evidence because its interpretation can remain explicit without treating non-detection as biological absence.

## Directional evidence unit

A `DirectionalOrderConstraint` declares:

- an evidence ID;
- an `earlier` / upstream node;
- a `later` / downstream node.

The evidence source must be independent of the candidate transition-rule construction when used for confirmation.

Examples that could justify such a constraint in later empirical work include independently established colonisation order or directional movement evidence. The software object itself does not certify provenance; provenance must be frozen by the empirical contract.

## Directional support comparison

For each constraint and candidate operator, calculate finite-horizon first-passage support in both directions:

- forward: `earlier -> later`;
- reverse: `later -> earlier`.

Use a predeclared `minimum_support_ratio > 1` as an evidential resolution threshold.

Allowed per-constraint statuses are:

- `supports_declared_direction`;
- `contradicts_declared_direction`;
- `bidirectional_or_ambiguous`;
- `unresolved`.

If both directions are positive but differ by less than the declared ratio, the evidence remains ambiguous. The method must not force an arrow from a small numerical difference.

The support ratio threshold is a declared resolution rule, not a universal biological constant.

## Combining with occurrence compatibility

Occurrence compatibility and independent directional evidence remain separate evidence objects with separate fingerprints.

The combined rule status may be:

- `occurrence_incompatible`;
- `contradicted_by_directional_evidence`;
- `compatible_with_occurrence_and_direction`;
- `indistinguishable_directional_evidence`;
- `unresolved`.

The order of these checks is conservative:

1. a rule unable to support the observed occurrence set remains occurrence-incompatible;
2. a fully occurrence-compatible rule can still be contradicted by independent directional evidence;
3. bidirectional/permissive rules remain indistinguishable if they do not resolve the declared direction;
4. unresolved evidence remains unresolved.

## No winner or posterior

The combined evidence object does not return:

- a winner;
- a scalar score;
- a posterior rule probability;
- a Bayes factor;
- a migration probability;
- a unique historical route.

A candidate being `compatible_with_occurrence_and_direction` means only that the tested evidence did not contradict it under the frozen operator and thresholds.

## Synthetic confirmation gate

Before empirical use, freeze candidate operators and show at minimum:

1. all candidate rules are occurrence-compatible under the same fixed source and observed occurrence set;
2. a true one-way forward chain supports every declared directional constraint;
3. a symmetric over-permissive rule remains `bidirectional_or_ambiguous` rather than being promoted;
4. a reverse-dominant but still occurrence-compatible rule is contradicted by the declared directional evidence;
5. the combined statuses are respectively compatible, indistinguishable and contradicted;
6. no winner score is introduced;
7. no empirical directional, occurrence or genetic outcome is used to construct the candidate rules or choose the confirmation thresholds after inspection.

## Empirical boundary

Passing the synthetic gate permits only this claim:

> independent directional evidence can discriminate among some candidate transition rules that are indistinguishable from occurrence compatibility alone.

It does not establish that a single empirical rule is the true historical process. Additional evidence types must remain separately auditable, and conflicting evidence must remain visible rather than averaged into a tuned omnibus score.
